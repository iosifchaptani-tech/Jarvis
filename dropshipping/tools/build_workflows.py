"""
Builds the importable n8n workflow files in ../n8n-workflows/.

Run:  python dropshipping/tools/build_workflows.py

The workflows are generated (instead of hand-written JSON) so node IDs stay
stable, every connection points at a real node, and the shared JavaScript
helpers are identical in every workflow.
"""

import json
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "n8n-workflows")

CJ = "https://developers.cjdropshipping.com/api2.0/v1"
MODEL = "claude-opus-5-5"  # change to "claude-sonnet-5-5" to roughly halve AI cost

# --------------------------------------------------------------------- helpers


class Workflow:
    def __init__(self, name):
        self.name = name
        self.nodes = []
        self.connections = {}
        self._x = 0

    def _id(self, node_name):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"jarvis-dropship/{self.name}/{node_name}"))

    def add(self, name, type_, version, params, pos, **extra):
        node = {
            "parameters": params,
            "id": self._id(name),
            "name": name,
            "type": type_,
            "typeVersion": version,
            "position": pos,
        }
        node.update(extra)
        self.nodes.append(node)
        return name

    def webhook_id(self, name):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"jarvis-dropship/{self.name}/{name}/webhook"))

    def connect(self, src, dst, out=0, kind="main"):
        outs = self.connections.setdefault(src, {}).setdefault(kind, [])
        while len(outs) <= out:
            outs.append([])
        outs[out].append({"node": dst, "type": kind, "index": 0})

    def chain(self, *names):
        for a, b in zip(names, names[1:]):
            self.connect(a, b)

    def save(self, filename):
        names = {n["name"] for n in self.nodes}
        for src, kinds in self.connections.items():
            assert src in names, f"{self.name}: unknown source node {src!r}"
            for outs in kinds.values():
                for out in outs:
                    for c in out:
                        assert c["node"] in names, f"{self.name}: unknown target {c['node']!r}"
        data = {
            "name": self.name,
            "nodes": self.nodes,
            "connections": self.connections,
            "settings": {"executionOrder": "v1"},
            "pinData": {},
            "active": False,
        }
        path = os.path.join(OUT, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("wrote", os.path.relpath(path))


def settings(wf, fields, pos):
    """A Set node holding everything the owner edits, in one place."""
    assignments = []
    for name, value in fields:
        assignments.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{wf.name}/setting/{name}")),
            "name": name,
            "value": value,
            "type": "number" if isinstance(value, (int, float)) else "string",
        })
    return wf.add("⚙️ Settings", "n8n-nodes-base.set", 3.4,
                  {"assignments": {"assignments": assignments}, "options": {}}, pos)


def code(wf, name, js, pos, **extra):
    return wf.add(name, "n8n-nodes-base.code", 2, {"jsCode": js.strip() + "\n"}, pos, **extra)


def table_get(wf, name, table, pos):
    return wf.add(name, "n8n-nodes-base.dataTable", 1.1, {
        "resource": "row",
        "operation": "get",
        "dataTableId": {"__rl": True, "mode": "name", "value": table},
        "returnAll": True,
    }, pos, alwaysOutputData=True, executeOnce=True)


def table_insert(wf, name, table, pos):
    return wf.add(name, "n8n-nodes-base.dataTable", 1.1, {
        "resource": "row",
        "operation": "insert",
        "dataTableId": {"__rl": True, "mode": "name", "value": table},
        "columns": {"mappingMode": "autoMapInputData", "value": {}, "matchingColumns": [], "schema": []},
        "options": {},
    }, pos)


def telegram(wf, name, text_expr, pos, chat_expr="={{ $('⚙️ Settings').first().json.telegram_chat_id }}"):
    return wf.add(name, "n8n-nodes-base.telegram", 1.2, {
        "chatId": chat_expr,
        "text": text_expr,
        "additionalFields": {"appendAttribution": False},
    }, pos)


def cj_token(wf, pos):
    # The CJ API key lives in a "Custom Auth" credential: {"body": {"apiKey": "CJ..."}}
    return wf.add("CJ: get token", "n8n-nodes-base.httpRequest", 4.2, {
        "method": "POST",
        "url": f"{CJ}/authentication/getAccessToken",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpCustomAuth",
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "{}",
        "options": {},
    }, pos, executeOnce=True)


def wait(wf, name, seconds, pos):
    return wf.add(name, "n8n-nodes-base.wait", 1.1, {"amount": seconds, "unit": "seconds"}, pos,
                  webhookId=wf.webhook_id(name))


TOKEN_HEADER = {
    "name": "CJ-Access-Token",
    "value": "={{ $('CJ: get token').first().json.data.accessToken }}",
}


def cj_get(wf, name, path, query, pos, **extra):
    return wf.add(name, "n8n-nodes-base.httpRequest", 4.2, {
        "url": f"{CJ}{path}",
        "sendQuery": True,
        "queryParameters": {"parameters": [{"name": k, "value": v} for k, v in query]},
        "sendHeaders": True,
        "headerParameters": {"parameters": [TOKEN_HEADER]},
        "options": extra.pop("options", {}),
    }, pos, **extra)


def agent(wf, name, prompt_expr, system, pos, model_pos):
    wf.add(name, "@n8n/n8n-nodes-langchain.agent", 3.1, {
        "promptType": "define",
        "text": prompt_expr,
        "options": {"systemMessage": system, "maxIterations": 3},
    }, pos)
    model = f"Claude ({name})"
    wf.add(model, "@n8n/n8n-nodes-langchain.lmChatAnthropic", 1.6, {
        "model": {"__rl": True, "mode": "id", "value": MODEL},
        "options": {"maxTokensToSample": 16000},
    }, model_pos)
    wf.connect(model, name, kind="ai_languageModel")
    return name


def switch(wf, name, field, routes, pos):
    rules = []
    for r in routes:
        rules.append({
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
                "conditions": [{
                    "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{wf.name}/{name}/{r}")),
                    "leftValue": "={{ $json.%s }}" % field,
                    "rightValue": r,
                    "operator": {"type": "string", "operation": "equals"},
                }],
                "combinator": "and",
            },
            "renameOutput": True,
            "outputKey": r,
        })
    return wf.add(name, "n8n-nodes-base.switch", 3.2, {"rules": {"values": rules}, "options": {}}, pos)


def if_true(wf, name, expr, pos):
    return wf.add(name, "n8n-nodes-base.if", 2.2, {
        "conditions": {
            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
            "conditions": [{
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{wf.name}/{name}")),
                "leftValue": expr,
                "rightValue": "",
                "operator": {"type": "boolean", "operation": "true", "singleValue": True},
            }],
            "combinator": "and",
        },
        "options": {},
    }, pos)


# Shared JavaScript: the playbook is append-only. The newest version of each
# rule_id wins, so approving, retiring and rolling back a rule never edits or
# deletes old rows; it only adds new ones.
JS_RULES = r"""
function latestRules(rows) {
  const latest = {};
  for (const r of rows) {
    if (!r || !r.rule_id) continue;
    const v = Number(r.version) || 0;
    if (!latest[r.rule_id] || v >= (Number(latest[r.rule_id].version) || 0)) latest[r.rule_id] = r;
  }
  return Object.values(latest);
}
function activeRules(rows, agents) {
  return latestRules(rows).filter(r => r.status === 'active' && (agents.includes(r.agent) || r.agent === 'all'));
}
function rulesText(rules) {
  return rules.length ? rules.map(r => `- [${r.rule_id}] ${r.rule}`).join('\n') : '- (no rules yet)';
}
function rowsOf(nodeName) {
  return $(nodeName).all().map(i => i.json).filter(r => r && Object.keys(r).length);
}
const num = v => { const m = String(v ?? '').match(/-?\d+(\.\d+)?/); return m ? parseFloat(m[0]) : NaN; };
const round2 = v => Math.round(v * 100) / 100;
"""

JS_PARSE_JSON = r"""
function parseAgentJson(nodeName) {
  const raw = $(nodeName).first().json.output ?? '';
  const text = typeof raw === 'string' ? raw : JSON.stringify(raw);
  const m = text.match(/\{[\s\S]*\}/);
  if (!m) throw new Error(`${nodeName} did not return JSON: ` + text.slice(0, 300));
  return JSON.parse(m[0]);
}
"""

# ------------------------------------------------------------ 00 error alerts


def build_error_alerts():
    wf = Workflow("00 · Error alerts")
    wf.add("When any workflow fails", "n8n-nodes-base.errorTrigger", 1, {}, [0, 0])
    settings(wf, [("telegram_chat_id", "PASTE_YOUR_TELEGRAM_CHAT_ID")], [220, 0])
    telegram(wf, "Alert on Telegram",
             "=⚠️ Workflow failed: {{ $('When any workflow fails').first().json.workflow.name }}\n"
             "Node: {{ $('When any workflow fails').first().json.execution.lastNodeExecuted }}\n"
             "Error: {{ ($('When any workflow fails').first().json.execution.error || {}).message }}\n"
             "Open: {{ $('When any workflow fails').first().json.execution.url }}",
             [440, 0])
    wf.chain("When any workflow fails", "⚙️ Settings", "Alert on Telegram")
    wf.save("00-error-alerts.json")


# -------------------------------------------------------- 01 product research

RESEARCH_SYSTEM = """You are the Product Research agent of a one-person dropshipping store. The supplier is CJ Dropshipping and traffic comes from free short phone videos (TikTok, Instagram Reels, YouTube Shorts) that the owner films with a product sample.

A good product for this store:
- sells for $20-60 and can be priced at 3x its landed cost (product + shipping);
- shows a visible problem and a satisfying result within the first 2 seconds of a video;
- is light, not fragile, has no sizes, is not branded and does not copy a brand;
- is not cheap and fast on Amazon Prime, and is not already listed by a huge number of stores;
- is safe and legal: no batteries, children's products, cosmetics, supplements, medical or health claims, weapons.

Follow the PLAYBOOK rules exactly. They were learned from this store's own results and override your general opinion.
Learn from PRODUCTS WE ALREADY TRIED: avoid repeating what failed, look for more of what worked.
Be honest: a low score is more useful than hype. Reply with only the JSON the user asks for."""

RESEARCH_BRIEF_JS = JS_RULES + r"""
const s = $('⚙️ Settings').first().json;
const res = $('CJ: trending products').first().json;
if (res.code !== 200) throw new Error('CJ product list failed: ' + (res.message || JSON.stringify(res).slice(0, 300)));

const products = (res.data?.content || []).flatMap(c => c.productList || []);
const banned = /(batter(y|ies)|lithium|power ?bank|charger|\bkids?\b|child|baby|toddler|infant|\btoys?\b|cosmetic|makeup|serum|cream|lotion|supplement|vitamin|capsule|medical|medicine|\bdrug|vape|e-?cig|knife|weapon|\bgun\b|laser|nike|adidas|iphone|airpods|samsung|disney|marvel|pokemon|lego|barbie|stanley|hello kitty|gucci|louis vuitton|chanel|dyson)/i;
const tried = rowsOf('Load past products');
const triedPids = new Set(tried.map(p => p.pid));

const candidates = [];
for (const p of products) {
  const cost = num(p.nowPrice || p.sellPrice);
  if (!p.id || !p.nameEn || isNaN(cost)) continue;
  if (banned.test(p.nameEn) || banned.test(p.threeCategoryName || '')) continue;
  if (triedPids.has(p.id)) continue;
  candidates.push({ pid: p.id, sku: p.sku || '', name: p.nameEn, category: p.threeCategoryName || '',
    cost, stock: p.warehouseInventoryNum ?? '?', listed: p.listedNum ?? '?', image: p.bigImage || '' });
}
if (!candidates.length) throw new Error('No CJ candidates left after filtering. Widen the price range in Settings.');
const shortlist = candidates.slice(0, 40);

// What the store learned so far: product outcomes the owner reported with /product
const feedback = rowsOf('Load feedback').filter(f => f.kind === 'product');
const status = {};
for (const f of feedback) status[String(f.ref).toLowerCase()] = f;
const history = tried.slice(-20).map(p => {
  const f = status[String(p.sku).toLowerCase()];
  return `- ${p.name} (landed $${round2((+p.cj_cost || 0) + (+p.ship_cost || 0))}, price $${p.sell_price}, score ${p.score}): `
    + (f ? `${f.status}${f.note ? ' - ' + f.note : ''}` : `status ${p.status}, no result reported yet`)
    + (p.prediction ? ` | prediction was: ${p.prediction}` : '');
}).join('\n') || '- none yet';

const rules = activeRules(rowsOf('Load playbook'), ['research']);
const lines = shortlist.map(c => `${c.pid} | ${c.name} | ${c.category} | $${c.cost} | stock ${c.stock} | listed by ${c.listed} stores`).join('\n');

const prompt = `Today is ${$now.toFormat('yyyy-MM-dd')}. Pick the 3 best products from CANDIDATES for this store.

PLAYBOOK (rules learned from this store's results - follow them):
${rulesText(rules)}

PRODUCTS WE ALREADY TRIED (learn from these):
${history}

CANDIDATES (CJ trending products in stock in the ${s.warehouse_country} warehouse; cost is the CJ price in USD before shipping):
pid | name | category | cost | stock | listed by N stores
${lines}

Reply with only this JSON (exactly 3 picks, best first):
{"picks":[{"pid":"<pid from the list>","score":<0-100>,"why":"<one sentence>","angle":"<the video idea: problem shown, result shown>","target_buyer":"<who buys it>","risks":"<saturation, returns, legal, shipping>","prediction":"<a testable prediction, e.g. 'first 10 videos average over 800 views'>"}]}`;

return [{ json: { prompt, candidates: shortlist, rules_version: rules.map(r => r.rule_id + 'v' + r.version).join(',') } }];
"""

PICKS_JS = JS_PARSE_JSON + r"""
const data = parseAgentJson('Research agent');
const cands = $('Build research brief').first().json.candidates;
const byPid = Object.fromEntries(cands.map(c => [c.pid, c]));
const picks = (data.picks || []).filter(p => byPid[p.pid]).slice(0, 3);
if (!picks.length) throw new Error('Research agent picked no valid products: ' + JSON.stringify(data).slice(0, 300));
return picks.map(p => ({ json: { ...byPid[p.pid], ...p } }));
"""

PRICE_JS = JS_RULES + r"""
const s = $('⚙️ Settings').first().json;
const picks = $('Parse picks').all().map(i => i.json);
const details = $('CJ: product details').all().map(i => i.json);
const freights = $input.all().map(i => i.json);
const day = $now.toFormat('yyyy-MM-dd');

return picks.map((p, i) => {
  const d = details[i]?.data || {};
  const v = (d.variants || [])[0] || {};
  const cjCost = num(v.variantSellPrice ?? d.sellPrice ?? p.cost);
  const options = Array.isArray(freights[i]?.data) ? freights[i].data : [];
  const best = options
    .map(o => ({ name: o.logisticName, price: num(o.logisticPrice), days: String(o.logisticAging || '?') }))
    .filter(o => !isNaN(o.price))
    .sort((a, b) => a.price - b.price)[0];
  const ship = best ? best.price : 0;
  const landed = cjCost + ship;
  // Pricing is a fixed rule, never an AI guess: 3x landed cost, and at least $min_profit_usd above it.
  const price = Math.ceil(Math.max(landed * s.markup, landed + s.min_profit_usd)) - 0.01;
  const fees = price * 0.029 + 0.30;
  return { json: {
    day, pid: p.pid, sku: v.variantSku || p.sku || '', name: p.name, image: p.image,
    cj_cost: round2(cjCost), ship_cost: round2(ship),
    ship_method: best ? best.name : 'unknown - check in the CJ app', ship_days: best ? best.days : '?',
    sell_price: round2(price), profit_per_order: round2(price - landed - fees),
    score: Number(p.score) || 0, why: p.why || '', angle: p.angle || '', target_buyer: p.target_buyer || '',
    risks: p.risks || '', prediction: p.prediction || '', status: 'idea',
  } };
});
"""

RESEARCH_MSG_JS = r"""
const picks = $input.all().map(i => i.json);
const blocks = picks.map((p, n) => `${n + 1}) ${p.name}
CJ SKU: ${p.sku}
Cost: $${p.cj_cost} + $${p.ship_cost} shipping (${p.ship_method}, ${p.ship_days} days)
Sell at: $${p.sell_price} -> about $${p.profit_per_order} profit per order before ads
Score ${p.score}/100: ${p.why}
Video idea: ${p.angle}
Risks: ${p.risks}`);
const text = `🔎 Product research ${$now.toFormat('yyyy-MM-dd')}

${blocks.join('\n\n')}

Next: check the product page in the CJ app, order a sample of the one you like, then send
/content SKU
to get the listing copy and 5 video scripts.`;
return [{ json: { text: text.slice(0, 4000) } }];
"""


def build_research():
    wf = Workflow("01 · Product research (daily)")
    wf.add("Every morning 07:00", "n8n-nodes-base.scheduleTrigger", 1.2,
           {"rule": {"interval": [{"field": "cronExpression", "expression": "0 7 * * *"}]}}, [0, 0])
    settings(wf, [
        ("telegram_chat_id", "PASTE_YOUR_TELEGRAM_CHAT_ID"),
        ("warehouse_country", "US"),
        ("min_cj_price", 2),
        ("max_cj_price", 15),
        ("min_stock", 50),
        ("markup", 3),
        ("min_profit_usd", 15),
    ], [220, 0])
    table_get(wf, "Load playbook", "playbook", [440, 0])
    table_get(wf, "Load past products", "products", [660, 0])
    table_get(wf, "Load feedback", "feedback", [880, 0])
    cj_token(wf, [1100, 0])
    wait(wf, "Wait 2s", 2, [1320, 0])
    cj_get(wf, "CJ: trending products", "/product/listV2", [
        ("page", "1"),
        ("size", "60"),
        ("productFlag", "0"),
        ("countryCode", "={{ $('⚙️ Settings').first().json.warehouse_country }}"),
        ("startSellPrice", "={{ $('⚙️ Settings').first().json.min_cj_price }}"),
        ("endSellPrice", "={{ $('⚙️ Settings').first().json.max_cj_price }}"),
        ("startWarehouseInventory", "={{ $('⚙️ Settings').first().json.min_stock }}"),
    ], [1540, 0])
    code(wf, "Build research brief", RESEARCH_BRIEF_JS, [1760, 0])
    agent(wf, "Research agent", "={{ $json.prompt }}", RESEARCH_SYSTEM, [1980, 0], [1980, 220])
    code(wf, "Parse picks", PICKS_JS, [2200, 0])
    cj_get(wf, "CJ: product details", "/product/query", [("pid", "={{ $json.pid }}")], [2420, 0],
           options={"batching": {"batch": {"batchSize": 1, "batchInterval": 1500}}},
           onError="continueRegularOutput")
    wf.add("CJ: shipping cost", "n8n-nodes-base.httpRequest", 4.2, {
        "method": "POST",
        "url": f"{CJ}/logistic/freightCalculate",
        "sendHeaders": True,
        "headerParameters": {"parameters": [TOKEN_HEADER]},
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ startCountryCode: $('⚙️ Settings').first().json.warehouse_country, "
                    "endCountryCode: $('⚙️ Settings').first().json.warehouse_country, "
                    "products: [{ quantity: 1, vid: (($json.data || {}).variants || [{}])[0].vid || '' }] }) }}",
        "options": {"batching": {"batch": {"batchSize": 1, "batchInterval": 1500}}},
    }, [2640, 0], onError="continueRegularOutput")
    code(wf, "Price & margin", PRICE_JS, [2860, 0])
    table_insert(wf, "Save to products table", "products", [3080, -120])
    code(wf, "Write Telegram message", RESEARCH_MSG_JS, [3080, 120])
    telegram(wf, "Send picks to Telegram", "={{ $json.text }}", [3300, 120])

    wf.chain("Every morning 07:00", "⚙️ Settings", "Load playbook", "Load past products", "Load feedback",
             "CJ: get token", "Wait 2s", "CJ: trending products", "Build research brief", "Research agent",
             "Parse picks", "CJ: product details", "CJ: shipping cost", "Price & margin")
    wf.connect("Price & margin", "Save to products table")
    wf.connect("Price & margin", "Write Telegram message")
    wf.connect("Write Telegram message", "Send picks to Telegram")
    wf.save("01-product-research.json")


# ------------------------------------------------- 02 telegram commands + content

CONTENT_SYSTEM = """You are the Content agent of a one-person dropshipping store. You write (1) the product page copy and (2) short vertical video scripts (15-30 seconds) for TikTok, Instagram Reels and YouTube Shorts.

The owner films every video with their own phone and a real product sample, hands-only (no face needed). So every shot must be something a person can film at home in a few minutes.

What works:
- The first 1-2 seconds show the problem or the finished result, never a logo or "hey guys".
- One idea per video. Short on-screen text. The voiceover sounds like a real person, not an ad.
- Different formats: problem -> fix, before/after, "3 ways to use it", durability test, reply to a comment, "things I wish I bought sooner".

Honesty rules you must never break:
- No invented reviews, testimonials, ratings, "sold out" claims, fake discounts or countdowns.
- Never promise delivery faster than the shipping time you are given.
- No health, medical or safety claims, no competitor brand names.
- Never pretend to be a customer; the videos come from the store.

Follow the PLAYBOOK rules exactly; they were learned from this store's own results. Copy the patterns of the videos that WORKED and avoid the ones that FLOPPED. Reply with only the JSON the user asks for."""

PARSE_CMD_JS = r"""
const s = $('⚙️ Settings').first().json;
const msg = $('Telegram message in').first().json.message || {};
const chatId = String(msg.chat?.id ?? '');
const text = String(msg.text || '').trim();
const [first, ...args] = text.split(/\s+/);
const cmd = String(first || '').toLowerCase().replace(/^\//, '').replace(/@.*$/, '');

if (String(s.telegram_chat_id).startsWith('PASTE')) return [{ json: { route: 'setup', chatId, args, text } }];
if (chatId !== String(s.telegram_chat_id)) return [];  // ignore everyone except the owner

const known = ['content', 'video', 'product', 'rules', 'clips', 'render', 'send', 'reply', 'skip'];
return [{ json: { route: known.includes(cmd) ? cmd : 'help', chatId, args, text } }];
"""

CONTENT_BRIEF_JS = JS_RULES + r"""
const cmd = $('Parse command').first().json;
const key = String(cmd.args[0] || '').toLowerCase();
const products = rowsOf('Load products');
const product = [...products].reverse().find(p =>
  key && (String(p.sku).toLowerCase() === key || String(p.pid).toLowerCase() === key));
if (!product) {
  return [{ json: { found: false, reply: key
    ? `I can't find SKU "${cmd.args[0]}" in the products table. Use a SKU from a research message, e.g. /content CJ1234567`
    : 'Send /content followed by a SKU from a research message, e.g. /content CJ1234567' } }];
}

// Learn from past videos: join each script with the latest stats the owner sent via /video
const stats = {};
for (const f of rowsOf('Load feedback')) if (f.kind === 'video') stats[f.ref] = f;
const measured = rowsOf('Load content history')
  .filter(c => stats[c.content_id])
  .map(c => ({ ...c, views: +stats[c.content_id].views || 0, clicks: +stats[c.content_id].clicks || 0, sales: +stats[c.content_id].sales || 0 }))
  .sort((a, b) => b.views - a.views);
const fmt = v => `- "${v.hook}" (${v.format}) -> ${v.views} views, ${v.clicks} link clicks, ${v.sales} sales`;
const worked = measured.slice(0, 5).map(fmt).join('\n') || '- no measured videos yet';
const flopped = measured.length > 5 ? measured.slice(-3).map(fmt).join('\n') : '- not enough data yet';

const rules = activeRules(rowsOf('Load playbook'), ['content']);
const prompt = `Write the product page copy and 5 video scripts for this product.

PRODUCT
Name: ${product.name}
Selling price: $${product.sell_price}
Shipping time to customers: ${product.ship_days} days (${product.ship_method})
Who buys it: ${product.target_buyer}
Video idea from research: ${product.angle}
Known risks: ${product.risks}

PLAYBOOK (rules learned from this store's results - follow them):
${rulesText(rules)}

VIDEOS THAT WORKED (copy these patterns):
${worked}

VIDEOS THAT FLOPPED (avoid these patterns):
${flopped}

Reply with only this JSON:
{"listing":{"title":"<max 60 characters>","bullets":["<5 benefit bullets>"],"description":"<80-150 words, plain text>","faq":[{"q":"...","a":"..."}]},
 "videos":[{"format":"<problem-fix | before-after | 3-uses | test | comment-reply | other>","hook":"<first 1-2 seconds: what is seen and the on-screen text>","shots":["<shot 1>","<shot 2>","..."],"on_screen_text":["..."],"voiceover":"<what is said, max 70 words>","caption":"<post caption with a soft call to action>","hashtags":["..."]}]}
Write exactly 5 videos, each a different format.`;

return [{ json: { found: true, prompt, product, rules_version: rules.map(r => r.rule_id + 'v' + r.version).join(',') } }];
"""

PARSE_CONTENT_JS = JS_PARSE_JSON + r"""
const data = parseAgentJson('Content agent');
const brief = $('Build content brief').first().json;
const stamp = $now.toFormat('MMddHHmm');
const videos = (data.videos || []).slice(0, 5);
if (!videos.length) throw new Error('Content agent returned no videos');
return videos.map((v, n) => ({ json: {
  day: $now.toFormat('yyyy-MM-dd'),
  content_id: `V${stamp}${n + 1}`,
  sku: brief.product.sku,
  product: brief.product.name,
  format: String(v.format || ''),
  hook: String(v.hook || ''),
  shots: (v.shots || []).join(' | '),
  on_screen_text: (v.on_screen_text || []).join(' | '),
  voiceover: String(v.voiceover || ''),
  caption: `${v.caption || ''} ${(v.hashtags || []).map(h => '#' + String(h).replace(/^#/, '')).join(' ')}`.trim(),
  rules_version: brief.rules_version,
} }));
"""

CONTENT_MSGS_JS = JS_PARSE_JSON + r"""
const data = parseAgentJson('Content agent');
const l = data.listing || {};
const msgs = [];
msgs.push(`🛍️ Product page copy - paste it into Shopify (Products -> the product imported by the CJ app)

TITLE
${l.title || ''}

BULLETS
${(l.bullets || []).map(b => '• ' + b).join('\n')}

DESCRIPTION
${l.description || ''}

FAQ
${(l.faq || []).map(f => 'Q: ' + f.q + '\nA: ' + f.a).join('\n\n')}`);
for (const v of $input.all().map(i => i.json)) {
  msgs.push(`🎬 Video ${v.content_id} (${v.format})

HOOK: ${v.hook}

SHOTS:
${v.shots.split(' | ').map((s, n) => `${n + 1}. ${s}`).join('\n')}

ON-SCREEN TEXT: ${v.on_screen_text}

VOICEOVER: ${v.voiceover}

CAPTION: ${v.caption}

Turn it into a finished video: /render ${v.content_id}
After 48 hours send: /video ${v.content_id} <views> <link clicks> <sales>`);
}
msgs.push(`🎥 Send /render <video id> to get a finished video now, made from the CJ product photos.
Later, real footage gets more views: film 3-5 short vertical clips yourself or get them from a UGC creator, upload them to Google Drive (share: anyone with the link) and send
/clips ${$('Build content brief').first().json.product.sku} <link1> <link2> <link3>
From then on /render uses those clips.`);
return msgs.map(t => ({ json: { text: t.slice(0, 4000) } }));
"""

FEEDBACK_JS = r"""
const cmd = $('Parse command').first().json;
const a = cmd.args;
const day = $now.toFormat('yyyy-MM-dd');
const isNum = v => /^\d+$/.test(String(v));
if (cmd.route === 'video') {
  if (a.length < 4 || !isNum(a[1]) || !isNum(a[2]) || !isNum(a[3])) {
    return [{ json: { valid: false, reply: 'Usage: /video <video id> <views> <link clicks> <sales>\nExample: /video V09291530 1200 14 1' } }];
  }
  return [{ json: { valid: true,
    row: { day, kind: 'video', ref: a[0], views: +a[1], clicks: +a[2], sales: +a[3], status: '', note: a.slice(4).join(' ') },
    reply: `✅ Saved stats for ${a[0]}. The coach will learn from them tonight.` } }];
}
const allowed = ['testing', 'winner', 'killed'];
if (a.length < 2 || !allowed.includes(String(a[1]).toLowerCase())) {
  return [{ json: { valid: false, reply: 'Usage: /product <SKU> <testing|winner|killed> <optional note>\nExample: /product CJ1234567 killed 30 videos, 0 add to carts' } }];
}
return [{ json: { valid: true,
  row: { day, kind: 'product', ref: a[0], views: 0, clicks: 0, sales: 0, status: String(a[1]).toLowerCase(), note: a.slice(2).join(' ') },
  reply: `✅ Marked ${a[0]} as ${String(a[1]).toLowerCase()}. Research will learn from it.` } }];
"""

RULES_LIST_JS = JS_RULES + r"""
const rules = latestRules(rowsOf('Load rules')).filter(r => r.status === 'active');
const text = rules.length
  ? '📘 Active playbook rules\n\n' + rules.map(r => `[${r.rule_id} v${r.version}] (${r.agent}) ${r.rule}`).join('\n\n')
  : 'The playbook is empty. Import playbook.csv into the playbook table.';
return [{ json: { text: text.slice(0, 4000) } }];
"""

CLIPS_JS = r"""
const cmd = $('Parse command').first().json;
const [sku, ...links] = cmd.args;
// Turn share links into direct download links the video renderer can fetch
const direct = u => {
  const drive = u.match(/drive\.google\.com\/(?:file\/d\/|open\?id=|uc\?(?:export=download&)?id=)([\w-]+)/);
  if (drive) return `https://drive.google.com/uc?export=download&id=${drive[1]}`;
  if (/dropbox\.com/.test(u)) return u.replace(/([?&])dl=0/, '$1dl=1').replace(/([?&])raw=0/, '$1raw=1');
  return u;
};
const urls = links.filter(u => /^https:\/\//.test(u)).map(direct);
if (!sku || !urls.length) {
  return [{ json: { valid: false, reply: 'Usage: /clips <SKU> <link1> <link2> <link3>\nUpload vertical 1080p clips (5-10 s each) to Google Drive, share them as "anyone with the link", and paste the links.' } }];
}
const day = $now.toFormat('yyyy-MM-dd');
return [{ json: { valid: true, rows: urls.map(url => ({ day, sku, url })),
  reply: `✅ Saved ${urls.length} clip(s) for ${sku}. Now send /render <video id> for any of its scripts.` } }];
"""

FIND_VIDEO_JS = JS_RULES + r"""
// Video agent, step 1: which script, and which footage (the owner's clips if saved, else CJ product photos).
const cmd = $('Parse command').first().json;
const id = String(cmd.args[0] || '');
const script = rowsOf('Load scripts').reverse().find(c => c.content_id === id);
if (!script) return [{ json: { ok: false, reply: `I can't find video ${id || '(missing id)'}. Use an id from a /content message, e.g. /render V09291530` } }];
const sku = String(script.sku).toLowerCase();
const clips = rowsOf('Load clips').filter(c => String(c.sku).toLowerCase() === sku).map(c => c.url).slice(-5);
const product = rowsOf('Load product photos').reverse().find(p => String(p.sku).toLowerCase() === sku) || {};
if (!clips.length && !product.pid && !product.image) {
  return [{ json: { ok: false, reply: `No clips and no CJ product photos found for ${script.sku}. Send /clips ${script.sku} <link1> <link2> first.` } }];
}
return [{ json: { ok: true, id, script, clips, pid: product.pid || '', image: product.image || '' } }];
"""

RENDER_BRIEF_JS = r"""
// Video agent, step 2: build a JSON2Video movie from the script + the owner's clips, or CJ product photos.
const s = $('⚙️ Settings').first().json;
const inp = $('Find video inputs').first().json;
const script = inp.script, id = inp.id, clips = inp.clips;
const cj = $('CJ: product photos').first().json;
let photos = cj && cj.code === 200 ? [...(cj.data?.productImageSet || []), cj.data?.bigImage] : [];
photos = [...new Set([...photos, inp.image].filter(u => /^https:\/\//.test(String(u || ''))))].slice(0, 8);
if (!clips.length && !photos.length) return [{ json: { ok: false, reply: `I couldn't get CJ photos for ${script.sku} right now. Try again later, or send /clips ${script.sku} <links>.` } }];
const mode = clips.length ? 'clips' : 'photos';

// Split the voiceover into up to 4 lines, one per scene. Each scene lasts as long as its line.
const sentences = String(script.voiceover || '').match(/[^.!?]+[.!?]*/g)?.map(t => t.trim()).filter(Boolean) || [];
if (!sentences.length) return [{ json: { ok: false, reply: `Video ${id} has no voiceover text.` } }];
const nScenes = Math.min(4, sentences.length);
const lines = Array.from({ length: nScenes }, (_, i) =>
  sentences.slice(Math.floor(i * sentences.length / nScenes), Math.floor((i + 1) * sentences.length / nScenes)).join(' '));
const texts = String(script.on_screen_text || '').split(' | ').filter(Boolean);
const hookText = texts[0] || String(script.hook || '').slice(0, 60);

// Every video starts on a different photo, so renders of the same product don't look identical.
const offset = [...id].reduce((a, c) => a + c.charCodeAt(0), 0) % Math.max(1, photos.length);
const textEl = (text, bg = 'rgba(0,0,0,0.55)', color = '#FFFFFF') => ({
  type: 'text', text, style: '001', position: 'custom', x: 'center', y: '12%', width: 960, duration: -2,
  settings: { 'font-family': 'Montserrat', 'font-size': '76px', 'font-weight': '800', color, 'background-color': bg, 'text-align': 'center' },
});
const voice = text => ({ type: 'voice', text, model: 'azure', voice: s.voice });
const clip = i => ({ type: 'video', src: clips[i % clips.length], resize: 'cover', muted: true, loop: -1, duration: -2 });
const photo = i => ({ type: 'image', src: photos[(i + offset) % photos.length], resize: 'cover', zoom: 3 + (i % 2) * 2,
                      pan: i % 2 ? 'left' : 'right', duration: -2 });

const scenes = lines.map((line, i) => {
  const last = i === lines.length - 1 && lines.length > 1;
  const elements = [mode === 'clips' ? (i === 2 && photos.length ? photo(0) : clip(i)) : photo(i)];
  if (i === 0) elements.push(textEl(hookText));
  else if (last) elements.push(textEl(s.cta_text, '#FFE600', '#000000'));
  else if (texts[i]) elements.push(textEl(texts[i]));
  elements.push(voice(line));
  return i === 0 ? { elements } : { transition: { style: i % 2 ? 'slideleft' : 'fade', duration: 0.3 }, elements };
});

const movie = {
  resolution: 'instagram-story',
  quality: 'high',
  scenes,
  elements: [{ type: 'subtitles', language: 'en', settings: {
    style: 'classic-progressive', 'font-family': 'Oswald Bold', 'font-size': 90, 'all-caps': true,
    'word-color': '#FFE600', 'line-color': '#FFFFFF', 'outline-color': '#000000', 'outline-width': 6,
    'max-words-per-line': 3, position: 'mid-bottom-center' } }],
};
return [{ json: { ok: true, movie, mode, content_id: id, caption: script.caption, sku: script.sku,
                  clips: clips.length, photos: photos.length } }];
"""

RENDER_STATUS_JS = r"""
const r = $input.first().json;
const m = r.movie || {};
const tries = $runIndex + 1;
if (m.status === 'done' && m.url) return [{ json: { state: 'done', url: m.url } }];
if (['error', 'timeout'].includes(m.status) || r.success === false)
  return [{ json: { state: 'error', reply: `❌ Render failed: ${m.message || r.message || m.status}. If you used /clips, check that each link opens without logging in.` } }];
if (tries >= 30) return [{ json: { state: 'error', reply: '❌ Render took longer than 10 minutes. Try /render again later.' } }];
return [{ json: { state: 'wait' } }];
"""

POSTING_CHECKLIST = (
    "=🎬 {{ $('Build video').first().json.content_id }} is ready: {{ $json.url }}\n\n"
    "Posting checklist:\n"
    "1. Post the same video on TikTok, Instagram Reels and YouTube Shorts.\n"
    "2. Add a trending sound inside each app at 5-10% volume (no music is baked in, so there are no copyright problems).\n"
    "3. The voice is AI: switch on TikTok's 'AI-generated content' and Instagram's 'AI info' label.\n"
    "4. Caption: {{ $('Build video').first().json.caption }}\n"
    "5. After 48 hours: /video {{ $('Build video').first().json.content_id }} <views> <link clicks> <sales>"
    "{{ $('Build video').first().json.mode === 'photos' ? '\\n\\n💡 Made from CJ product photos. Real footage (yours or a UGC creator\\'s) usually gets more views: /clips ' + $('Build video').first().json.sku + ' <links>' : '' }}"
)

TICKET_JS = JS_RULES + r"""
// Owner decisions on support emails: /send (the draft), /reply (own text), /skip.
const s = $('⚙️ Settings').first().json;
const cmd = $('Parse command').first().json;
const id = String(cmd.args[0] || '').toUpperCase();
const rows = rowsOf('Load tickets').filter(r => String(r.ticket_id).toUpperCase() === id);
if (!id || !rows.length) return [{ json: { ok: false, reply: `I can't find ticket ${id || '(missing id)'}. Use the id from the support message, e.g. /send T0929153001` } }];
const first = rows[0];
const sent = rows.find(r => ['auto_sent', 'approved', 'owner_reply'].includes(r.decision));
const skipped = rows.find(r => r.decision === 'skipped');
const subject = /^re:/i.test(first.subject) ? first.subject : `Re: ${first.subject}`;
const day = $now.toFormat('yyyy-MM-dd');
const row = (decision, final_reply, note) => ({ day, ticket_id: first.ticket_id, from_email: first.from_email, from_name: first.from_name,
  subject: first.subject, question: '', intent: first.intent, confidence: Number(first.confidence) || 0, order_name: first.order_name,
  draft: '', final_reply, decision, note });

if (cmd.route === 'send') {
  if (sent) return [{ json: { ok: false, reply: `Ticket ${id} was already answered (${sent.decision}). Use /reply ${id} <text> to send a follow-up.` } }];
  if (skipped) return [{ json: { ok: false, reply: `Ticket ${id} was skipped. Use /reply ${id} <text> if you still want to answer.` } }];
  if (!first.draft) return [{ json: { ok: false, reply: `Ticket ${id} has no draft. Use /reply ${id} <text>.` } }];
  return [{ json: { ok: true, send: true, to: first.from_email, subject, body: first.draft,
    row: row('approved', first.draft, ''), reply: `✅ Sent the draft to ${first.from_email}.` } }];
}
if (cmd.route === 'reply') {
  const text = String(cmd.text).replace(/^\/reply(@\S+)?\s+\S+\s*/i, '').trim();
  if (text.length < 5) return [{ json: { ok: false, reply: `Write your answer after the ticket id, e.g.\n/reply ${id} Hi Anna, your parcel left our warehouse today...` } }];
  const sig = String(s.email_signature || '').replace(/\\n/g, '\n');
  const body = sig && !text.includes(sig.split('\n').pop()) ? `${text}\n\n${sig}` : text;
  return [{ json: { ok: true, send: true, to: first.from_email, subject, body,
    row: row('owner_reply', body, sent ? 'follow-up after ' + sent.decision : ''),
    reply: `✅ Sent your reply to ${first.from_email}. The support agent will learn from it.` } }];
}
if (sent) return [{ json: { ok: false, reply: `Ticket ${id} was already answered, nothing to skip.` } }];
return [{ json: { ok: true, send: false, row: row('skipped', '', ''), reply: `🗑️ Ticket ${id} closed without a reply.` } }];
"""

HELP_TEXT = """🤖 Commands
/content SKU - product page copy + 5 video scripts
/clips SKU link1 link2 link3 - save your own phone clips (Google Drive/Dropbox links)
/render ID - turn a script + your clips into a finished MP4
/video ID views clicks sales - report how a video did
/product SKU testing|winner|killed note - report how a product did
/rules - show what the agents have learned
/send T123 - send the support agent's draft reply
/reply T123 your text - send your own reply instead (the agent learns from it)
/skip T123 - close a support email without replying

Research arrives every morning, the report every evening."""


def build_commands():
    wf = Workflow("02 · Telegram commands (content + feedback)")
    wf.add("Telegram message in", "n8n-nodes-base.telegramTrigger", 1.1,
           {"updates": ["message"], "additionalFields": {}}, [0, 300], webhookId=wf.webhook_id("tg"))
    settings(wf, [
        ("telegram_chat_id", "PASTE_YOUR_TELEGRAM_CHAT_ID"),
        ("voice", "en-US-EmmaMultilingualNeural"),
        ("cta_text", "Link in bio"),
        ("support_email", "PASTE_YOUR_SUPPORT_EMAIL"),
        ("email_signature", "Best regards,\nThe support team"),
    ], [220, 300])
    code(wf, "Parse command", PARSE_CMD_JS, [440, 300])
    switch(wf, "Route", "route", ["content", "video", "product", "rules", "setup", "help", "clips", "render",
                                   "send", "reply", "skip"], [660, 300])
    reply_chat = "={{ $('Parse command').first().json.chatId }}"

    # /content
    table_get(wf, "Load products", "products", [880, 0])
    table_get(wf, "Load playbook", "playbook", [1100, 0])
    table_get(wf, "Load content history", "content", [1320, 0])
    table_get(wf, "Load feedback", "feedback", [1540, 0])
    code(wf, "Build content brief", CONTENT_BRIEF_JS, [1760, 0])
    if_true(wf, "Product found?", "={{ $json.found }}", [1980, 0])
    agent(wf, "Content agent", "={{ $json.prompt }}", CONTENT_SYSTEM, [2200, -100], [2200, 120])
    code(wf, "Parse content", PARSE_CONTENT_JS, [2420, -100])
    table_insert(wf, "Save scripts", "content", [2640, -220])
    code(wf, "Split into messages", CONTENT_MSGS_JS, [2640, 0])
    telegram(wf, "Send content", "={{ $json.text }}", [2860, 0], reply_chat)
    telegram(wf, "Product not found", "={{ $json.reply }}", [2200, 260], reply_chat)
    wf.chain("Load products", "Load playbook", "Load content history", "Load feedback", "Build content brief",
             "Product found?", "Content agent", "Parse content", "Split into messages", "Send content")
    wf.connect("Parse content", "Save scripts")
    wf.connect("Product found?", "Product not found", out=1)

    # /video and /product
    code(wf, "Build feedback", FEEDBACK_JS, [880, 420])
    if_true(wf, "Valid?", "={{ $json.valid }}", [1100, 420])
    code(wf, "Feedback row", "return [{ json: $input.first().json.row }];", [1320, 360])
    table_insert(wf, "Save feedback", "feedback", [1540, 360])
    telegram(wf, "Confirm feedback", "={{ $('Build feedback').first().json.reply }}", [1760, 360], reply_chat)
    telegram(wf, "Feedback usage", "={{ $json.reply }}", [1320, 540], reply_chat)
    wf.chain("Build feedback", "Valid?", "Feedback row", "Save feedback", "Confirm feedback")
    wf.connect("Valid?", "Feedback usage", out=1)

    # /rules, setup, help
    table_get(wf, "Load rules", "playbook", [880, 720])
    code(wf, "Format rules", RULES_LIST_JS, [1100, 720])
    telegram(wf, "Send rules", "={{ $json.text }}", [1320, 720], reply_chat)
    wf.chain("Load rules", "Format rules", "Send rules")
    telegram(wf, "Send chat ID", "=👋 Your chat ID is {{ $json.chatId }}\nPaste it into the ⚙️ Settings node of every workflow, then save.",
             [880, 900], reply_chat)
    telegram(wf, "Send help", HELP_TEXT, [880, 1080], reply_chat)

    # /clips: the owner's own phone clips for a product
    code(wf, "Build clips", CLIPS_JS, [880, 1260])
    if_true(wf, "Clips valid?", "={{ $json.valid }}", [1100, 1260])
    code(wf, "Clip rows", "return $('Build clips').first().json.rows.map(r => ({ json: r }));", [1320, 1200])
    table_insert(wf, "Save clips", "clips", [1540, 1200])
    wf.add("Confirm clips", "n8n-nodes-base.telegram", 1.2, {
        "chatId": reply_chat, "text": "={{ $('Build clips').first().json.reply }}",
        "additionalFields": {"appendAttribution": False}}, [1760, 1200], executeOnce=True)
    telegram(wf, "Clips usage", "={{ $json.reply }}", [1320, 1380], reply_chat)
    wf.chain("Build clips", "Clips valid?", "Clip rows", "Save clips", "Confirm clips")
    wf.connect("Clips valid?", "Clips usage", out=1)

    # /render: Video agent (script + clips + product photo -> JSON2Video -> MP4 on Telegram)
    table_get(wf, "Load scripts", "content", [880, 1560])
    table_get(wf, "Load clips", "clips", [1100, 1560])
    table_get(wf, "Load product photos", "products", [1320, 1560])
    code(wf, "Find video inputs", FIND_VIDEO_JS, [1540, 1560])
    if_true(wf, "Inputs found?", "={{ $json.ok }}", [1760, 1560])
    cj_token(wf, [1980, 1440])
    wf.nodes[-1]["onError"] = "continueRegularOutput"
    wait(wf, "Wait 2s", 2, [2200, 1440])
    cj_get(wf, "CJ: product photos", "/product/query", [("pid", "={{ $('Find video inputs').first().json.pid }}")],
           [2420, 1440], executeOnce=True, onError="continueRegularOutput")
    code(wf, "Build video", RENDER_BRIEF_JS, [2640, 1440])
    if_true(wf, "Video ready to render?", "={{ $json.ok }}", [2860, 1440])
    wf.add("JSON2Video: start render", "n8n-nodes-base.httpRequest", 4.2, {
        "method": "POST",
        "url": "https://api.json2video.com/v2/movies",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify($json.movie) }}",
        "options": {},
    }, [3080, 1380])
    wait(wf, "Wait 20s", 20, [3300, 1380])
    wf.add("JSON2Video: check", "n8n-nodes-base.httpRequest", 4.2, {
        "url": "https://api.json2video.com/v2/movies",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendQuery": True,
        "queryParameters": {"parameters": [
            {"name": "project", "value": "={{ $('JSON2Video: start render').first().json.project }}"}]},
        "options": {},
    }, [3520, 1380], onError="continueRegularOutput")
    code(wf, "Render status", RENDER_STATUS_JS, [3740, 1380])
    switch(wf, "Render done?", "state", ["done", "wait", "error"], [3960, 1380])
    telegram(wf, "Send video link", POSTING_CHECKLIST, [4180, 1280], reply_chat)
    wf.add("Download video", "n8n-nodes-base.httpRequest", 4.2, {
        "url": "={{ $('Render status').first().json.url }}",
        "options": {"response": {"response": {"responseFormat": "file"}}},
    }, [4400, 1280], onError="continueRegularOutput")
    wf.add("Send video file", "n8n-nodes-base.telegram", 1.2, {
        "operation": "sendVideo",
        "chatId": reply_chat,
        "binaryData": True,
        "binaryPropertyName": "data",
        "additionalFields": {},
    }, [4620, 1280], onError="continueRegularOutput")
    telegram(wf, "Render failed", "={{ $json.reply }}", [4180, 1500], reply_chat)
    telegram(wf, "Cannot render", "={{ $json.reply }}", [3080, 1640], reply_chat)
    wf.chain("Load scripts", "Load clips", "Load product photos", "Find video inputs", "Inputs found?",
             "CJ: get token", "Wait 2s", "CJ: product photos", "Build video", "Video ready to render?",
             "JSON2Video: start render", "Wait 20s", "JSON2Video: check", "Render status", "Render done?",
             "Send video link", "Download video", "Send video file")
    wf.connect("Video ready to render?", "Cannot render", out=1)
    wf.connect("Inputs found?", "Cannot render", out=1)
    wf.connect("Render done?", "Wait 20s", out=1)
    wf.connect("Render done?", "Render failed", out=2)

    wf.chain("Telegram message in", "⚙️ Settings", "Parse command", "Route")
    wf.connect("Route", "Load products", out=0)
    wf.connect("Route", "Build feedback", out=1)
    wf.connect("Route", "Build feedback", out=2)
    wf.connect("Route", "Load rules", out=3)
    wf.connect("Route", "Send chat ID", out=4)
    wf.connect("Route", "Send help", out=5)
    wf.connect("Route", "Build clips", out=6)
    wf.connect("Route", "Load scripts", out=7)

    # /send /reply /skip: owner decisions on support emails
    table_get(wf, "Load tickets", "support", [880, 1900])
    code(wf, "Build ticket action", TICKET_JS, [1100, 1900])
    if_true(wf, "Ticket ok?", "={{ $json.ok }}", [1320, 1900])
    if_true(wf, "Send an email?", "={{ $json.send }}", [1540, 1840])
    wf.add("Email the customer", "n8n-nodes-base.emailSend", 2.1, {
        "fromEmail": "={{ $('⚙️ Settings').first().json.support_email }}",
        "toEmail": "={{ $('Build ticket action').first().json.to }}",
        "subject": "={{ $('Build ticket action').first().json.subject }}",
        "emailFormat": "text",
        "text": "={{ $('Build ticket action').first().json.body }}",
        "options": {"appendAttribution": False},
    }, [1760, 1780])
    code(wf, "Ticket row", "return [{ json: $('Build ticket action').first().json.row }];", [1980, 1840])
    table_insert(wf, "Log ticket", "support", [2200, 1840])
    wf.add("Confirm ticket", "n8n-nodes-base.telegram", 1.2, {
        "chatId": reply_chat, "text": "={{ $('Build ticket action').first().json.reply }}",
        "additionalFields": {"appendAttribution": False}}, [2420, 1840], executeOnce=True)
    telegram(wf, "Ticket problem", "={{ $json.reply }}", [1540, 2020], reply_chat)
    wf.chain("Load tickets", "Build ticket action", "Ticket ok?", "Send an email?", "Email the customer",
             "Ticket row", "Log ticket", "Confirm ticket")
    wf.connect("Send an email?", "Ticket row", out=1)
    wf.connect("Ticket ok?", "Ticket problem", out=1)
    for i in (8, 9, 10):
        wf.connect("Route", "Load tickets", out=i)
    wf.save("02-telegram-commands.json")


# ------------------------------------------------------------ 03 new order alert

ORDER_JS = r"""
const o = $('Shopify: order paid').first().json.body || {};
if (!o.id) return [];  // not an order payload
const items = (o.line_items || []).map(li => `${li.quantity}x ${li.title}${li.variant_title ? ' (' + li.variant_title + ')' : ''}`);
return [{ json: {
  day: $now.toFormat('yyyy-MM-dd'),
  order_name: String(o.name || o.order_number || ''),
  order_id: String(o.id),
  revenue: Number(o.total_price) || 0,
  currency: String(o.currency || ''),
  items: items.join('; '),
  skus: (o.line_items || []).map(li => li.sku).filter(Boolean).join(','),
  country: String(o.shipping_address?.country_code || ''),
  email: String(o.email || o.contact_email || o.customer?.email || '').toLowerCase(),
} }];
"""


def build_order_alert():
    wf = Workflow("03 · New order alert")
    wf.add("Shopify: order paid", "n8n-nodes-base.webhook", 2, {
        "httpMethod": "POST",
        "path": "shopify-order-" + wf.webhook_id("path")[:8],
        "responseMode": "onReceived",
        "options": {},
    }, [0, 0], webhookId=wf.webhook_id("shopify"))
    settings(wf, [("telegram_chat_id", "PASTE_YOUR_TELEGRAM_CHAT_ID")], [220, 0])
    code(wf, "Order summary", ORDER_JS, [440, 0])
    table_insert(wf, "Save order", "orders", [660, -100])
    telegram(wf, "Tell owner to pay CJ",
             "=🛒 New paid order {{ $('Order summary').first().json.order_name }}: "
             "{{ $('Order summary').first().json.revenue }} {{ $('Order summary').first().json.currency }} "
             "({{ $('Order summary').first().json.country }})\n{{ $('Order summary').first().json.items }}\n\n"
             "Next: open CJ -> My Orders and pay it (the CJ app imports Shopify orders automatically; "
             "if it is not there after 30 minutes, press Sync Orders). Pay the same day so it ships fast.",
             [660, 100])
    wf.chain("Shopify: order paid", "⚙️ Settings", "Order summary", "Save order")
    wf.connect("Order summary", "Tell owner to pay CJ")
    wf.save("03-new-order-alert.json")


# --------------------------------------------------------- 04 CJ order check

CHECK_JS = r"""
const s = $('⚙️ Settings').first().json;
const res = $('CJ: recent orders').first().json;
if (res.code !== 200) throw new Error('CJ order list failed: ' + (res.message || JSON.stringify(res).slice(0, 300)));
const list = res.data?.list || [];
const now = Date.now();
const age = d => d ? (now - Date.parse(String(d).replace(' ', 'T') + 'Z')) / 3600e3 : 0;
const unpaid = list.filter(o => ['CREATED', 'IN_CART', 'UNPAID'].includes(o.orderStatus));
const late = list.filter(o => o.paymentDate && !o.trackNumber
  && ['PENDING', 'PROCESSING', 'UNSHIPPED'].includes(o.orderStatus) && age(o.paymentDate) > s.late_hours);
if (!unpaid.length && !late.length) return [];

const parts = [];
if (unpaid.length) parts.push(`💳 ${unpaid.length} CJ order(s) waiting for you to pay:\n`
  + unpaid.map(o => `- ${o.orderNum}${o.orderAmount ? ' ($' + o.orderAmount + ')' : ''}`).join('\n')
  + '\nOpen CJ -> My Orders and pay them.');
if (late.length) parts.push(`⏰ ${late.length} paid order(s) have no tracking after ${s.late_hours}h:\n`
  + late.map(o => `- ${o.orderNum} (paid ${o.paymentDate})`).join('\n')
  + '\nOpen a ticket with your CJ agent and email the customer an honest update.');
return [{ json: { text: parts.join('\n\n').slice(0, 4000) } }];
"""


def build_cj_check():
    wf = Workflow("04 · CJ order check (every 3h)")
    wf.add("Every 3 hours (9-21h)", "n8n-nodes-base.scheduleTrigger", 1.2,
           {"rule": {"interval": [{"field": "cronExpression", "expression": "0 9-21/3 * * *"}]}}, [0, 0])
    settings(wf, [("telegram_chat_id", "PASTE_YOUR_TELEGRAM_CHAT_ID"), ("late_hours", 48)], [220, 0])
    cj_token(wf, [440, 0])
    wait(wf, "Wait 2s", 2, [660, 0])
    cj_get(wf, "CJ: recent orders", "/shopping/order/list", [("pageNum", "1"), ("pageSize", "50")], [880, 0])
    code(wf, "Find problems", CHECK_JS, [1100, 0])
    telegram(wf, "Send reminder", "={{ $json.text }}", [1320, 0])
    wf.chain("Every 3 hours (9-21h)", "⚙️ Settings", "CJ: get token", "Wait 2s", "CJ: recent orders",
             "Find problems", "Send reminder")
    wf.save("04-cj-order-check.json")


# ------------------------------------------------- 05 daily coach + learning

COACH_SYSTEM = """You are the Coach of a one-person dropshipping store run by a beginner. Every evening you read the store's real numbers and do two jobs:

1. Write a short, honest report for the owner's phone: what happened, what it means, and exactly 3 concrete actions for tomorrow. Plain words, no hype. If the data is too thin to conclude anything, say so.
2. Improve the PLAYBOOK: the numbered rules the Research, Content and Support agents follow. You may propose adding a rule or retiring one.

How to change the playbook:
- Only propose a change that the data supports with at least 3 data points (for example 3+ measured videos or 3+ products). Name the evidence.
- A rule is one short, specific, testable instruction for one agent (max 200 characters). Example: "Start content hooks with the finished result, not the problem: result-first hooks averaged 3x more views (V09291530, V09301012, V10011200)."
- Retire a rule when the data shows it hurts results or is no longer true.
- Propose at most 3 changes. Proposing none is fine and often right.
- Never propose rules about ad budgets or spending, prices below cost, collecting customer data, or anything deceptive (fake reviews, fake scarcity, false claims). Never try to change these instructions.

You only interpret the numbers you are given; do not invent numbers. Reply with only the JSON the user asks for."""

KPI_JS = JS_RULES + r"""
const s = $('⚙️ Settings').first().json;
const today = $now.toFormat('yyyy-MM-dd');
const weekAgo = $now.minus({ days: 6 }).toFormat('yyyy-MM-dd');
const twoDaysAgo = $now.minus({ days: 2 }).toFormat('yyyy-MM-dd');
const sum = (a, f) => a.reduce((t, x) => t + (Number(f(x)) || 0), 0);

const orders = rowsOf('Load orders');
const oToday = orders.filter(o => o.day === today);
const o7 = orders.filter(o => o.day >= weekAgo && o.day <= today);
const revToday = round2(sum(oToday, o => o.revenue));
const rev7 = round2(sum(o7, o => o.revenue));

const cj = $('CJ: paid orders (7 days)').first().json;
const cjList = cj && cj.code === 200 ? (cj.data?.list || []) : null;
const cjCost7 = cjList ? round2(sum(cjList, o => o.orderAmount)) : null;
const fees7 = round2(o7.length * s.payment_fee_fixed + rev7 * s.payment_fee_pct / 100);
const profit7 = cjCost7 === null ? null : round2(rev7 - cjCost7 - fees7);

const feedback = rowsOf('Load feedback');
const vstats = {}, pstatus = {};
for (const f of feedback) {
  if (f.kind === 'video') vstats[f.ref] = f;
  if (f.kind === 'product') pstatus[String(f.ref).toLowerCase()] = f;
}
const content = rowsOf('Load content');
const measured = content.filter(c => vstats[c.content_id]).map(c => ({
  id: c.content_id, product: c.product, format: c.format, hook: c.hook, rules: c.rules_version,
  views: +vstats[c.content_id].views || 0, clicks: +vstats[c.content_id].clicks || 0, sales: +vstats[c.content_id].sales || 0,
})).sort((a, b) => b.views - a.views);
const unmeasured = content.filter(c => !vstats[c.content_id] && c.day <= twoDaysAgo).length;
const vline = v => `- ${v.id} [${v.format}] "${v.hook}" (${v.product}; rules ${v.rules || 'none'}): ${v.views} views, ${v.clicks} clicks, ${v.sales} sales`;

const products = rowsOf('Load products').slice(-15).map(p => {
  const f = pstatus[String(p.sku).toLowerCase()];
  return `- ${p.name} (SKU ${p.sku}, landed $${round2((+p.cj_cost || 0) + (+p.ship_cost || 0))}, price $${p.sell_price}, score ${p.score}): `
    + (f ? `${f.status}${f.note ? ' - ' + f.note : ''}` : 'no result reported') + `. Prediction: ${p.prediction || '-'}`;
});

const all = latestRules(rowsOf('Load playbook'));
const active = all.filter(r => r.status === 'active');
const dead = all.filter(r => r.status === 'rejected' || r.status === 'retired').slice(-10);
const last = rowsOf('Load reports').slice(-1)[0];

// Support: what the owner approved, rewrote or had to handle
const tickets = {};
for (const r of rowsOf('Load support')) (tickets[r.ticket_id] = tickets[r.ticket_id] || []).push(r);
const t7 = Object.values(tickets).filter(rs => rs[0].day >= weekAgo);
const has = (rs, d) => rs.some(r => r.decision === d);
const waiting = Object.values(tickets).filter(rs => rs.every(r => r.decision === 'pending')).length;
const corrections = t7.filter(rs => rs[0].draft && has(rs, 'owner_reply')).slice(-3).map(rs =>
  `- [${rs[0].intent}] customer: "${String(rs[0].question).slice(0, 160)}"\n  draft: "${String(rs[0].draft).slice(0, 220)}"\n  owner sent: "${String(rs.find(r => r.decision === 'owner_reply').final_reply).slice(0, 220)}"`);
const intents = {};
for (const rs of t7) intents[rs[0].intent] = (intents[rs[0].intent] || 0) + 1;
const supportLine = `${t7.length} emails: ${t7.filter(rs => has(rs, 'auto_sent')).length} auto-sent, `
  + `${t7.filter(rs => has(rs, 'approved')).length} drafts approved as written, ${t7.filter(rs => has(rs, 'owner_reply')).length} rewritten by the owner, `
  + `${t7.filter(rs => has(rs, 'skipped')).length} skipped, ${waiting} still waiting. Topics: ${Object.entries(intents).map(([k, v]) => k + ' ' + v).join(', ') || '-'}`;
const money = v => v === null ? 'unknown (CJ API unavailable)' : '$' + v;

const prompt = `Date: ${today}

NUMBERS (from Shopify orders and CJ; before ad spend)
Today: ${oToday.length} orders, $${revToday} revenue
Last 7 days: ${o7.length} orders, $${rev7} revenue, CJ costs ${money(cjCost7)}, payment fees ~$${fees7}, profit before ads ${money(profit7)}

VIDEOS WITH STATS (best first)
${measured.slice(0, 8).map(vline).join('\n') || '- none yet'}
${measured.length > 8 ? 'WORST VIDEOS\n' + measured.slice(-3).map(vline).join('\n') : ''}
Videos older than 2 days without stats: ${unmeasured}

PRODUCTS (newest last)
${products.join('\n') || '- none yet'}

ACTIVE PLAYBOOK RULES
${active.map(r => `- ${r.rule_id} v${r.version} (${r.agent}): ${r.rule}`).join('\n') || '- none'}

IDEAS ALREADY REJECTED OR RETIRED (do not propose again)
${dead.map(r => `- ${r.rule_id} (${r.agent}): ${r.rule}`).join('\n') || '- none'}

SUPPORT EMAILS (last 7 days)
${supportLine}
Drafts the owner rewrote (learn the owner's style and facts from these):
${corrections.join('\n') || '- none'}

YESTERDAY'S REPORT
${last ? String(last.report).slice(0, 800) : '- none'}

Reply with only this JSON:
{"report":"<max 700 characters>","actions":["<action 1>","<action 2>","<action 3>"],
 "add_rules":[{"agent":"research|content|support","rule":"<max 200 characters>","evidence":"<which data points>"}],
 "retire_rules":[{"rule_id":"<id>","reason":"<which data points>"}]}`;

return [{ json: {
  prompt, today, unmeasured, waiting,
  numbers: { orders_today: oToday.length, revenue_today: revToday, orders_7d: o7.length, revenue_7d: rev7,
             cj_cost_7d: cjCost7, est_profit_7d: profit7 },
} }];
"""

GUARD_JS = JS_RULES + JS_PARSE_JSON + r"""
// Guardrails: the coach can only add or retire short text rules for known agents.
// It can never touch credentials, code, prices, budgets or the legal/safety rules.
const s = $('⚙️ Settings').first().json;
const brief = $('Compute numbers').first().json;
const out = parseAgentJson('Coach agent');
const all = latestRules(rowsOf('Load playbook'));
const byId = Object.fromEntries(all.map(r => [r.rule_id, r]));
const norm = t => String(t).toLowerCase().replace(/[^a-z0-9 ]/g, '').replace(/\s+/g, ' ').trim();
const known = new Set(all.map(r => norm(r.rule)));
const PROTECTED = new Set(['R003', 'R005', 'R006']);
const AGENTS = ['research', 'content', 'support'];
const BAD = /(https?:|www\.|api.?key|password|token|secret|credential|ignore (all|previous|the above)|system prompt|budget|spend more|fake|fabricat|invent|countdown|scarcity|guarantee)/i;
let next = Math.max(0, ...all.map(r => parseInt(String(r.rule_id).replace(/\D/g, ''), 10) || 0)) + 1;

const changes = [];
for (const a of out.add_rules || []) {
  const rule = String(a.rule || '').trim();
  if (!AGENTS.includes(a.agent) || !rule || rule.length > 200 || BAD.test(rule) || known.has(norm(rule))) continue;
  known.add(norm(rule));
  changes.push({ rule_id: 'R' + String(next++).padStart(3, '0'), agent: a.agent, rule, status: 'active', version: 1,
                 evidence: String(a.evidence || '').slice(0, 300), _label: '➕ add' });
}
for (const r of out.retire_rules || []) {
  const cur = byId[r.rule_id];
  if (!cur || cur.status !== 'active' || PROTECTED.has(r.rule_id)) continue;
  changes.push({ rule_id: cur.rule_id, agent: cur.agent, rule: cur.rule, status: 'retired',
                 version: (Number(cur.version) || 0) + 1, evidence: String(r.reason || '').slice(0, 300), _label: '➖ retire' });
}
const accepted = changes.slice(0, s.max_rule_changes);

const n = brief.numbers;
const money = v => v === null ? '?' : '$' + v;
let report = `📊 Daily report ${brief.today}

Today: ${n.orders_today} orders, $${n.revenue_today}
Last 7 days: ${n.orders_7d} orders, $${n.revenue_7d} revenue, CJ cost ${money(n.cj_cost_7d)}, profit before ads ${money(n.est_profit_7d)}

${String(out.report || '').slice(0, 900)}

Tomorrow:
${(out.actions || []).slice(0, 3).map((a, i) => `${i + 1}. ${a}`).join('\n')}`;
if (brief.waiting > 0) report += `\n\n📨 ${brief.waiting} customer email(s) are waiting for you: answer with /send, /reply or /skip.`;
if (brief.unmeasured > 0) report += `\n\n📝 ${brief.unmeasured} videos have no stats yet. Send /video <id> <views> <clicks> <sales> so the agents can learn.`;

const approval = `🧠 The coach wants to update the playbook (the rules the agents follow):\n\n`
  + accepted.map(c => `${c._label} ${c.rule_id} (${c.agent}): ${c.rule}\n   Evidence: ${c.evidence}`).join('\n\n')
  + '\n\nApprove these changes?';

return [{ json: {
  report_text: report.slice(0, 4000),
  approval_text: approval.slice(0, 4000),
  has_changes: accepted.length > 0,
  changes: accepted.map(({ _label, ...c }) => c),
  report_row: { day: brief.today, orders_today: n.orders_today, revenue_today: n.revenue_today, orders_7d: n.orders_7d,
                revenue_7d: n.revenue_7d, cj_cost_7d: n.cj_cost_7d ?? 0, est_profit_7d: n.est_profit_7d ?? 0,
                report: report.slice(0, 2000) },
} }];
"""


def build_coach():
    wf = Workflow("05 · Daily coach + learning")
    wf.add("Every evening 21:30", "n8n-nodes-base.scheduleTrigger", 1.2,
           {"rule": {"interval": [{"field": "cronExpression", "expression": "30 21 * * *"}]}}, [0, 0])
    settings(wf, [
        ("telegram_chat_id", "PASTE_YOUR_TELEGRAM_CHAT_ID"),
        ("max_rule_changes", 3),
        ("payment_fee_pct", 2.9),
        ("payment_fee_fixed", 0.30),
    ], [220, 0])
    x = 440
    for name, table in [("Load playbook", "playbook"), ("Load products", "products"), ("Load content", "content"),
                        ("Load feedback", "feedback"), ("Load orders", "orders"), ("Load reports", "reports"),
                        ("Load support", "support")]:
        table_get(wf, name, table, [x, 0])
        x += 220
    wf.add("CJ: get token", "n8n-nodes-base.httpRequest", 4.2, {
        "method": "POST",
        "url": f"{CJ}/authentication/getAccessToken",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpCustomAuth",
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "{}",
        "options": {},
    }, [x, 0], executeOnce=True, onError="continueRegularOutput")
    wait(wf, "Wait 2s", 2, [x + 220, 0])
    cj_get(wf, "CJ: paid orders (7 days)", "/shopping/order/list", [
        ("pageNum", "1"),
        ("pageSize", "100"),
        ("paymentDateFrom", "={{ $now.minus({days: 7}).toUTC().toFormat('yyyy-MM-dd HH:mm:ss') }}"),
        ("paymentDateTo", "={{ $now.toUTC().toFormat('yyyy-MM-dd HH:mm:ss') }}"),
    ], [x + 440, 0], onError="continueRegularOutput")
    code(wf, "Compute numbers", KPI_JS, [x + 660, 0])
    agent(wf, "Coach agent", "={{ $json.prompt }}", COACH_SYSTEM, [x + 880, 0], [x + 880, 220])
    code(wf, "Check proposals (guardrails)", GUARD_JS, [x + 1100, 0])
    code(wf, "Report row", "return [{ json: $input.first().json.report_row }];", [x + 1320, 0])
    table_insert(wf, "Save report", "reports", [x + 1540, 0])
    telegram(wf, "Send report", "={{ $('Check proposals (guardrails)').first().json.report_text }}", [x + 1760, 0])
    if_true(wf, "Any rule changes?", "={{ $('Check proposals (guardrails)').first().json.has_changes }}", [x + 1980, 0])
    wf.add("Ask owner to approve", "n8n-nodes-base.telegram", 1.2, {
        "operation": "sendAndWait",
        "chatId": "={{ $('⚙️ Settings').first().json.telegram_chat_id }}",
        "message": "={{ $('Check proposals (guardrails)').first().json.approval_text }}",
        "approvalOptions": {"values": {"approvalType": "double", "approveLabel": "✅ Approve", "disapproveLabel": "❌ Reject"}},
        "options": {"limitWaitTime": {"values": {"limitType": "afterTimeInterval", "resumeAmount": 12, "resumeUnit": "hours"}}},
    }, [x + 2200, -100], webhookId=wf.webhook_id("approve"))
    if_true(wf, "Approved?", "={{ $json.data.approved }}", [x + 2420, -100])
    code(wf, "Rules to activate",
         "return $('Check proposals (guardrails)').first().json.changes.map(c => ({ json: c }));",
         [x + 2640, -200])
    code(wf, "Rules to remember as rejected",
         "return $('Check proposals (guardrails)').first().json.changes\n"
         "  .filter(c => c.status === 'active')\n"
         "  .map(c => ({ json: { ...c, status: 'rejected' } }));",
         [x + 2640, 0])
    table_insert(wf, "Save approved rules", "playbook", [x + 2860, -200])
    table_insert(wf, "Save rejected ideas", "playbook", [x + 2860, 0])

    wf.chain("Every evening 21:30", "⚙️ Settings", "Load playbook", "Load products", "Load content", "Load feedback",
             "Load orders", "Load reports", "Load support", "CJ: get token", "Wait 2s", "CJ: paid orders (7 days)", "Compute numbers",
             "Coach agent", "Check proposals (guardrails)", "Report row", "Save report", "Send report",
             "Any rule changes?", "Ask owner to approve", "Approved?", "Rules to activate", "Save approved rules")
    wf.connect("Approved?", "Rules to remember as rejected", out=1)
    wf.connect("Rules to remember as rejected", "Save rejected ideas")
    wf.save("05-daily-coach.json")

# ------------------------------------------------------- 06 customer support

SUPPORT_SYSTEM = """You are the Support agent of a small online store. You read one customer email and draft the reply the owner would send.

How to answer:
- Friendly, calm, short (under 120 words), plain text, in the customer's language. Use their first name if you know it.
- Only state facts you are given: the ORDER FACTS and the POLICIES. If a fact is missing, say you are checking and will follow up. Never guess a status, a date or a tracking number.
- When there is a tracking number, give it with its tracking link.
- End with the signature you are given.

What you must never do (set needs_owner to true instead):
- Promise or refuse a refund, return, replacement, discount, compensation or anything free.
- Handle damaged, wrong or missing items, complaints, cancellations, address changes, chargebacks, PayPal or bank disputes, or legal threats.
- Admit fault, blame the supplier by name, mention CJ or dropshipping, or share another customer's data.

Follow the PLAYBOOK rules exactly; they come from the owner's feedback. Copy the tone of the APPROVED ANSWERS and learn from the owner's CORRECTIONS. Reply with only the JSON the user asks for."""

SUPPORT_BRIEFS_JS = JS_RULES + r"""
// One brief per new email: who wrote, what they asked, and the facts about their orders.
const s = $('⚙️ Settings').first().json;
const emails = $('New customer email').all().map(i => i.json);
const own = String(s.support_email || '').toLowerCase();
const ignore = String(s.ignore_senders || '').toLowerCase().split(',').map(x => x.trim()).filter(Boolean);
const orders = rowsOf('Load orders');
const history = rowsOf('Load support history');
const cj = $('CJ: recent orders').first().json;
const cjList = cj && cj.code === 200 ? (cj.data?.list || []) : [];
const norm = v => String(v ?? '').toLowerCase().replace(/[^a-z0-9]/g, '');
const human = { CREATED: 'received, being processed', IN_CART: 'received, being processed', UNPAID: 'received, being processed',
  PENDING: 'being prepared at the warehouse', PROCESSING: 'being prepared at the warehouse', UNSHIPPED: 'being prepared at the warehouse',
  SHIPPED: 'shipped', DELIVERED: 'delivered', CANCELLED: 'cancelled' };
const DANGER = /(chargeback|dispute|paypal claim|claim with|lawyer|attorney|legal action|\bsue\b|police|fraud|scam|trading standards|consumer protection|\bbbb\b|small claims)/i;

// What the owner taught the agent: approved answers and rewrites
const tickets = {};
for (const r of history) (tickets[r.ticket_id] = tickets[r.ticket_id] || []).push(r);
const good = history.filter(r => ['approved', 'owner_reply'].includes(r.decision) && r.final_reply).slice(-4)
  .map(r => `- [${r.intent}] ${String(r.final_reply).slice(0, 500)}`).join('\n') || '- none yet';
const fixes = Object.values(tickets).map(rs => {
  const d = rs.find(r => r.draft), o = rs.find(r => r.decision === 'owner_reply');
  return d && o ? `- customer: "${String(d.question).slice(0, 200)}"\n  your draft: "${String(d.draft).slice(0, 300)}"\n  owner sent instead: "${String(o.final_reply).slice(0, 400)}"` : null;
}).filter(Boolean).slice(-3).join('\n') || '- none yet';
const rules = activeRules(rowsOf('Load playbook'), ['support']);
const sig = String(s.email_signature || '').replace(/\\n/g, '\n');

const out = [];
emails.forEach((e, i) => {
  const fromRaw = String(e.from || '');
  const m = fromRaw.match(/<([^>]+)>/);
  const address = (m ? m[1] : fromRaw).trim().toLowerCase();
  const name = (m ? fromRaw.slice(0, fromRaw.indexOf('<')) : '').replace(/"/g, '').trim();
  const subject = String(e.subject || '(no subject)').trim();
  if (!address.includes('@') || address === own || ignore.some(x => address.includes(x))) return;
  if (/^(auto(matic)? ?reply|out of office|undeliverable|delivery status|mail delivery)/i.test(subject)) return;

  let body = String(e.textPlain || '').trim()
    || String(e.textHtml || '').replace(/<(style|script)[\s\S]*?<\/\1>/gi, '').replace(/<br\s*\/?>/gi, '\n').replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ');
  body = body.split(/\n\s*(?:On .{5,200}wrote:|-{2,}\s*Original Message|From: .+@)/i)[0]
    .split('\n').filter(l => !l.trim().startsWith('>')).join('\n').replace(/\n{3,}/g, '\n\n').trim().slice(0, 3000);

  const mentioned = [...`${subject} ${body}`.matchAll(/#?\b(\d{3,8})\b/g)].map(x => x[1]);
  const mine = orders.filter(o => (o.email && String(o.email).toLowerCase() === address)
    || mentioned.some(n => norm(o.order_name) === n || norm(o.order_id) === n)).slice(-3);
  const known = [];
  const facts = mine.map(o => {
    const c = cjList.find(x => x.orderNum && [norm(o.order_name), norm(o.order_id)].includes(norm(x.orderNum)));
    known.push(o.order_name, o.order_id);
    let line = `- Order ${o.order_name} placed ${o.day}: ${o.items} (ship to ${o.country}). Status: `;
    if (!c) line += 'no supplier update yet (orders usually leave the warehouse within 1-3 business days)';
    else {
      line += human[c.orderStatus] || String(c.orderStatus).toLowerCase();
      if (c.trackNumber) {
        known.push(c.trackNumber);
        line += `. Carrier: ${c.logisticName || 'unknown'}. Tracking number: ${c.trackNumber}. Tracking link: https://t.17track.net/en#nums=${c.trackNumber}`;
      }
    }
    return line;
  });

  const prompt = `STORE: ${s.store_name}
POLICIES (the only promises allowed):
Shipping: ${s.shipping_policy}
Returns and refunds: ${s.refund_policy}
Sign every reply with:
${sig}

PLAYBOOK (rules learned from the owner's feedback - follow them):
${rulesText(rules)}

APPROVED ANSWERS (match this tone):
${good}

CORRECTIONS (the owner rewrote these drafts - learn from them):
${fixes}

CUSTOMER: ${name || '(no name)'} <${address}>
ORDER FACTS (from the store and the supplier - the only order facts you may state):
${facts.join('\n') || '- no order found for this email address or order number'}

EMAIL
Subject: ${subject}
${body}

Reply with only this JSON:
{"intent":"where_is_my_order|shipping_time|product_question|order_change|refund_return|damaged_wrong_missing|complaint|legal_chargeback|spam|other","confidence":<0.0-1.0>,"needs_owner":<true|false>,"reason":"<why the owner must decide, or empty>","summary":"<one short line for the owner>","reply":"<the email reply>"}`;

  out.push({ json: {
    ticket_id: 'T' + $now.toFormat('MMddHHmmss') + i,
    from_email: address, from_name: name, subject, question: body,
    order_name: mine.map(o => o.order_name).join(','), has_order: mine.length > 0,
    known_ids: known.filter(Boolean).map(String), danger: DANGER.test(`${subject} ${body}`), prompt,
  } });
});
return out;
"""

SUPPORT_DECIDE_JS = r"""
// Deterministic safety check: the AI drafts, but only code decides what may be sent without the owner.
const s = $('⚙️ Settings').first().json;
const briefs = $('Build support briefs').all().map(i => i.json);
const SAFE = ['where_is_my_order', 'shipping_time', 'product_question'];
const PROMISE = /(refund|money back|reimburs|compensat|discount|coupon|voucher|free (replacement|gift|item|shipping)|guarantee|replacement|we will (send|ship) (you )?(a )?new)/i;
const norm = v => String(v ?? '').toLowerCase().replace(/[^a-z0-9]/g, '');

return $input.all().map((item, i) => {
  const b = briefs[i];
  let a = null;
  try {
    const raw = item.json.output ?? '';
    const text = typeof raw === 'string' ? raw : JSON.stringify(raw);
    a = JSON.parse(text.match(/\{[\s\S]*\}/)[0]);
  } catch (e) { a = null; }
  const reply = String(a?.reply || '').trim();
  const intent = String(a?.intent || 'other');
  const conf = Math.max(0, Math.min(1, Number(a?.confidence) || 0));
  const known = b.known_ids.map(norm);
  const unknownIds = (reply.match(/\b(?=[A-Z0-9]*\d)[A-Z0-9]{10,30}\b/gi) || []).filter(t => !known.includes(norm(t)));

  const why = [];
  if (!a || !reply) why.push('the AI draft could not be read');
  if (String(s.auto_send).toLowerCase() !== 'yes') why.push('auto-send is off, so you approve every reply');
  if (!SAFE.includes(intent)) why.push(`"${intent}" emails always go to you`);
  if (conf < s.min_confidence) why.push(`the AI is only ${Math.round(conf * 100)}% sure`);
  if (a?.needs_owner) why.push('the AI asked for you' + (a.reason ? ': ' + a.reason : ''));
  if (b.danger) why.push('the email mentions a dispute, chargeback or legal step');
  if (PROMISE.test(reply)) why.push('the draft mentions refunds, discounts or replacements');
  if (unknownIds.length) why.push(`the draft contains a number I can't verify (${unknownIds[0]})`);
  if (intent === 'where_is_my_order' && !b.has_order) why.push('no matching order was found');

  const { prompt, known_ids, danger, has_order, ...rest } = b;
  return { json: { ...rest, intent, confidence: Math.round(conf * 100) / 100, summary: String(a?.summary || ''),
    draft: reply, auto: why.length === 0, why: why.join('; ') } };
});
"""

SUPPORT_ROW = """({ day: $now.toFormat('yyyy-MM-dd'), ticket_id: t.ticket_id, from_email: t.from_email, from_name: t.from_name,
  subject: t.subject, question: t.question, intent: t.intent, confidence: t.confidence, order_name: t.order_name,
  draft: t.draft, final_reply: %s, decision: '%s', note: %s })"""

AUTO_ROWS_JS = "return $('Safe to auto-send?').all(0).map(({ json: t }) => ({ json: " + (SUPPORT_ROW % ("t.draft", "auto_sent", "''")) + " }));"
PENDING_ROWS_JS = "return $input.all().map(({ json: t }) => ({ json: " + (SUPPORT_ROW % ("''", "pending", "t.why")) + " }));"

OWNER_MSG = (
    "=📨 Customer email {{ $json.ticket_id }} needs you\n"
    "From: {{ $json.from_name }} <{{ $json.from_email }}>\n"
    "Subject: {{ $json.subject }}\n"
    "Topic: {{ $json.intent }} ({{ Math.round($json.confidence * 100) }}% sure){{ $json.order_name ? ' · order ' + $json.order_name : '' }}\n"
    "Why you: {{ $json.note }}\n\n"
    "They wrote:\n{{ $json.question.slice(0, 1200) }}\n\n"
    "Draft reply:\n{{ ($json.draft || '(no draft)').slice(0, 1800) }}\n\n"
    "➡️ /send {{ $json.ticket_id }} sends this draft\n"
    "➡️ /reply {{ $json.ticket_id }} your text sends your own answer\n"
    "➡️ /skip {{ $json.ticket_id }} closes it without a reply"
)

AUTO_MSG = (
    "=✉️ Auto-replied to {{ $json.from_email }} ({{ $json.intent }}): {{ $json.summary }}\n\n"
    "{{ $json.final_reply.slice(0, 1500) }}\n\n"
    "Not right? /reply {{ $json.ticket_id }} <better answer> sends a correction and teaches the agent."
)


def build_support():
    wf = Workflow("06 · Customer support (email)")
    wf.add("New customer email", "n8n-nodes-base.emailReadImap", 2.1, {
        "mailbox": "INBOX",
        "postProcessAction": "read",
        "format": "simple",
        "options": {},
    }, [0, 0])
    settings(wf, [
        ("telegram_chat_id", "PASTE_YOUR_TELEGRAM_CHAT_ID"),
        ("support_email", "PASTE_YOUR_SUPPORT_EMAIL"),
        ("store_name", "PASTE_YOUR_STORE_NAME"),
        ("email_signature", "Best regards,\\nThe support team"),
        ("shipping_policy", "Orders are processed in 1-3 business days and delivered in 3-7 business days in the US. "
                            "Every order gets a tracking number by email."),
        ("refund_policy", "PASTE A SHORT SUMMARY OF YOUR SHOPIFY REFUND POLICY"),
        ("auto_send", "no"),
        ("min_confidence", 0.85),
        ("ignore_senders", "noreply,no-reply,mailer-daemon,postmaster,notifications,shopify.com,cjdropshipping.com,"
                           "paypal.com,stripe.com,facebookmail.com,tiktok.com,google.com"),
    ], [220, 0])
    table_get(wf, "Load orders", "orders", [440, 0])
    table_get(wf, "Load playbook", "playbook", [660, 0])
    table_get(wf, "Load support history", "support", [880, 0])
    wf.add("CJ: get token", "n8n-nodes-base.httpRequest", 4.2, {
        "method": "POST",
        "url": f"{CJ}/authentication/getAccessToken",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpCustomAuth",
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "{}",
        "options": {},
    }, [1100, 0], executeOnce=True, onError="continueRegularOutput")
    wait(wf, "Wait 2s", 2, [1320, 0])
    cj_get(wf, "CJ: recent orders", "/shopping/order/list", [("pageNum", "1"), ("pageSize", "50")], [1540, 0],
           executeOnce=True, onError="continueRegularOutput")
    code(wf, "Build support briefs", SUPPORT_BRIEFS_JS, [1760, 0])
    agent(wf, "Support agent", "={{ $json.prompt }}", SUPPORT_SYSTEM, [1980, 0], [1980, 220])
    code(wf, "Decide (safety check)", SUPPORT_DECIDE_JS, [2200, 0])
    if_true(wf, "Safe to auto-send?", "={{ $json.auto }}", [2420, 0])
    wf.add("Send reply email", "n8n-nodes-base.emailSend", 2.1, {
        "fromEmail": "={{ $('⚙️ Settings').first().json.support_email }}",
        "toEmail": "={{ $json.from_email }}",
        "subject": "={{ /^re:/i.test($json.subject) ? $json.subject : 'Re: ' + $json.subject }}",
        "emailFormat": "text",
        "text": "={{ $json.draft }}",
        "options": {"appendAttribution": False},
    }, [2640, -120])
    code(wf, "Auto-sent rows", AUTO_ROWS_JS, [2860, -120])
    table_insert(wf, "Log auto replies", "support", [3080, -220])
    telegram(wf, "Tell owner (auto-sent)", AUTO_MSG, [3080, -40])
    code(wf, "Waiting rows", PENDING_ROWS_JS, [2640, 120])
    table_insert(wf, "Log waiting emails", "support", [2860, 60])
    telegram(wf, "Ask owner", OWNER_MSG, [2860, 220])

    wf.chain("New customer email", "⚙️ Settings", "Load orders", "Load playbook", "Load support history",
             "CJ: get token", "Wait 2s", "CJ: recent orders", "Build support briefs", "Support agent",
             "Decide (safety check)", "Safe to auto-send?", "Send reply email", "Auto-sent rows", "Log auto replies")
    wf.connect("Auto-sent rows", "Tell owner (auto-sent)")
    wf.connect("Safe to auto-send?", "Waiting rows", out=1)
    wf.connect("Waiting rows", "Log waiting emails")
    wf.connect("Waiting rows", "Ask owner")
    wf.save("06-customer-support.json")

# ------------------------------------------------------ 07 CJ auto-pay (optional)

TO_CONFIRM_JS = r"""
// CJ orders imported by the CJ app start as CREATED / IN_CART. Confirming them makes CJ calculate the
// final price (status UNPAID). Confirming does not pay anything.
const res = $('CJ: open orders').first().json;
if (res.code !== 200) throw new Error('CJ order list failed: ' + (res.message || JSON.stringify(res).slice(0, 300)));
const list = (res.data?.list || []).filter(o => ['CREATED', 'IN_CART'].includes(o.orderStatus) && !o.isSandbox);
return list.length ? list.map(o => ({ json: { orderId: o.orderId, orderNum: o.orderNum } })) : [{ json: { none: true } }];
"""

DECIDE_PAY_JS = JS_RULES + r"""
// Deterministic money rules. The AI is not involved in paying.
const s = $('⚙️ Settings').first().json;
const today = $now.toFormat('yyyy-MM-dd');
const res = $('CJ: unpaid orders').first().json;
if (res.code !== 200) throw new Error('CJ order list failed: ' + (res.message || JSON.stringify(res).slice(0, 300)));
const bal = $('CJ: wallet balance').first().json;
let balance = bal && bal.code === 200 ? Number(bal.data?.amount) || 0 : 0;
const norm = v => String(v ?? '').toLowerCase().replace(/[^a-z0-9]/g, '');
const shop = rowsOf('Load orders');
const log = rowsOf('Load payments');
let budget = Number(s.daily_limit_usd) - log.filter(r => r.day === today && r.status === 'paid').reduce((t, r) => t + (Number(r.amount) || 0), 0);

const out = [];
for (const o of (res.data?.list || []).filter(o => o.orderStatus === 'UNPAID' && !o.isSandbox)) {
  const mine = log.filter(r => r.cj_order_id === o.orderId);
  if (mine.some(r => r.status === 'paid')) continue;                       // never pay twice
  const amount = round2(Number(o.orderAmount) || 0);
  const sale = shop.find(x => x.order_name && [norm(x.order_name), norm(x.order_id)].includes(norm(o.orderNum)));
  const revenue = sale ? Number(sale.revenue) || 0 : 0;
  const profit = round2(revenue - amount - revenue * s.payment_fee_pct / 100 - s.payment_fee_fixed);
  const why = [];
  if (!(amount > 0)) why.push('CJ has not calculated the price yet');
  if (!sale) why.push('no matching Shopify order was found');
  if (amount > s.max_order_usd) why.push(`it costs $${amount}, above your $${s.max_order_usd} limit per order`);
  if (sale && profit < s.min_profit_usd) why.push(`profit would be only $${profit} (minimum $${s.min_profit_usd})`);
  if (amount > budget) why.push(`today's auto-pay limit ($${s.daily_limit_usd}) would be passed`);
  if (amount > balance) why.push(`your CJ balance ($${round2(balance)}) is too low - top it up with Payoneer`);
  const row = { day: today, cj_order_id: o.orderId, order_name: o.orderNum, amount, revenue: round2(revenue), profit };
  if (!why.length) {
    budget -= amount; balance -= amount;
    out.push({ json: { pay: true, ...row, note: '' } });
  } else {
    // Tell the owner once per order per day, not every 30 minutes
    const told = mine.some(r => r.status === 'held' && r.day === today);
    out.push({ json: { pay: false, notify: !told, ...row, note: why.join('; ') } });
  }
}
return out;
"""

PAID_ROWS_JS = r"""
// Pair each payment answer from CJ with its order (same order as the items that went in).
const orders = $('Pay it?').all(0).map(i => i.json);
return $input.all().map((r, i) => {
  const o = orders[i];
  const ok = r.json.code === 200 && r.json.result !== false;
  return { json: { day: o.day, cj_order_id: o.cj_order_id, order_name: o.order_name, amount: o.amount,
    revenue: o.revenue, profit: o.profit, status: ok ? 'paid' : 'failed', note: ok ? '' : String(r.json.message || r.json.error || 'unknown error').slice(0, 300) } };
});
"""

PAID_MSG_JS = r"""
const rows = $input.all().map(i => i.json);
const paid = rows.filter(r => r.status === 'paid'), failed = rows.filter(r => r.status === 'failed');
const lines = [];
if (paid.length) lines.push(`💸 Auto-paid ${paid.length} CJ order(s), $${paid.reduce((t, r) => t + r.amount, 0).toFixed(2)} in total:\n`
  + paid.map(r => `- ${r.order_name}: paid $${r.amount}, sold for $${r.revenue}, ~$${r.profit} profit`).join('\n'));
if (failed.length) lines.push(`❌ CJ refused ${failed.length} payment(s). Pay these by hand in CJ -> My Orders:\n`
  + failed.map(r => `- ${r.order_name} ($${r.amount}): ${r.note}`).join('\n'));
return [{ json: { text: lines.join('\n\n').slice(0, 4000) } }];
"""

HELD_ROWS_JS = r"""
return $input.all().filter(i => i.json.notify).map(({ json: o }) => ({ json: {
  day: o.day, cj_order_id: o.cj_order_id, order_name: o.order_name, amount: o.amount, revenue: o.revenue,
  profit: o.profit, status: 'held', note: o.note } }));
"""


def build_autopay():
    wf = Workflow("07 · CJ auto-pay (optional)")
    wf.add("Every 30 minutes", "n8n-nodes-base.scheduleTrigger", 1.2,
           {"rule": {"interval": [{"field": "cronExpression", "expression": "*/30 * * * *"}]}}, [0, 0])
    settings(wf, [
        ("telegram_chat_id", "PASTE_YOUR_TELEGRAM_CHAT_ID"),
        ("auto_pay", "no"),
        ("max_order_usd", 40),
        ("daily_limit_usd", 100),
        ("min_profit_usd", 3),
        ("payment_fee_pct", 2.9),
        ("payment_fee_fixed", 0.30),
    ], [220, 0])
    if_true(wf, "Auto-pay switched on?", "={{ $json.auto_pay === 'yes' }}", [440, 0])
    table_get(wf, "Load orders", "orders", [660, 0])
    table_get(wf, "Load payments", "payments", [880, 0])
    cj_token(wf, [1100, 0])
    wait(wf, "Wait 2s", 2, [1320, 0])
    cj_get(wf, "CJ: open orders", "/shopping/order/list", [("pageNum", "1"), ("pageSize", "50")], [1540, 0], executeOnce=True)
    code(wf, "Orders to confirm", TO_CONFIRM_JS, [1760, 0])
    if_true(wf, "Anything to confirm?", "={{ !$json.none }}", [1980, 0])
    wf.add("CJ: confirm order", "n8n-nodes-base.httpRequest", 4.2, {
        "method": "PATCH",
        "url": f"{CJ}/shopping/order/confirmOrder",
        "sendHeaders": True,
        "headerParameters": {"parameters": [TOKEN_HEADER]},
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ orderId: $json.orderId }) }}",
        "options": {"batching": {"batch": {"batchSize": 1, "batchInterval": 1500}}},
    }, [2200, -100], onError="continueRegularOutput")
    wait(wf, "Wait 3s", 3, [2420, 0])
    wf.nodes[-1]["executeOnce"] = True
    cj_get(wf, "CJ: unpaid orders", "/shopping/order/list",
           [("pageNum", "1"), ("pageSize", "50"), ("status", "UNPAID")], [2640, 0], executeOnce=True)
    wait(wf, "Wait 2s (balance)", 2, [2860, 0])
    wf.add("CJ: wallet balance", "n8n-nodes-base.httpRequest", 4.2, {
        "url": f"{CJ}/shopping/pay/getBalance",
        "sendHeaders": True,
        "headerParameters": {"parameters": [TOKEN_HEADER]},
        "options": {},
    }, [3080, 0], executeOnce=True, onError="continueRegularOutput")
    code(wf, "Decide payments (money rules)", DECIDE_PAY_JS, [3300, 0])
    if_true(wf, "Pay it?", "={{ $json.pay }}", [3520, 0])
    wf.add("CJ: pay from balance", "n8n-nodes-base.httpRequest", 4.2, {
        "method": "POST",
        "url": f"{CJ}/shopping/pay/payBalance",
        "sendHeaders": True,
        "headerParameters": {"parameters": [TOKEN_HEADER]},
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ orderId: $json.cj_order_id }) }}",
        "options": {"batching": {"batch": {"batchSize": 1, "batchInterval": 1500}}},
    }, [3740, -100], onError="continueRegularOutput")
    code(wf, "Payment rows", PAID_ROWS_JS, [3960, -100])
    table_insert(wf, "Log payments", "payments", [4180, -200])
    code(wf, "Payment message", PAID_MSG_JS, [4180, 0])
    telegram(wf, "Tell owner (paid)", "={{ $json.text }}", [4400, 0])
    code(wf, "Held rows", HELD_ROWS_JS, [3740, 160])
    table_insert(wf, "Log held orders", "payments", [3960, 100])
    telegram(wf, "Ask owner to pay by hand",
             "=✋ Not auto-paid: CJ order {{ $json.order_name }} (${{ $json.amount }})\nWhy: {{ $json.note }}\n\n"
             "Check it, then pay it in CJ -> My Orders if it's fine.", [3960, 260])

    wf.chain("Every 30 minutes", "⚙️ Settings", "Auto-pay switched on?", "Load orders", "Load payments",
             "CJ: get token", "Wait 2s", "CJ: open orders", "Orders to confirm", "Anything to confirm?",
             "CJ: confirm order", "Wait 3s", "CJ: unpaid orders", "Wait 2s (balance)", "CJ: wallet balance",
             "Decide payments (money rules)", "Pay it?", "CJ: pay from balance", "Payment rows", "Log payments")
    wf.connect("Anything to confirm?", "Wait 3s", out=1)
    wf.connect("Payment rows", "Payment message")
    wf.connect("Payment message", "Tell owner (paid)")
    wf.connect("Pay it?", "Held rows", out=1)
    wf.connect("Held rows", "Log held orders")
    wf.connect("Held rows", "Ask owner to pay by hand")
    wf.save("07-cj-auto-pay.json")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    build_error_alerts()
    build_research()
    build_commands()
    build_order_alert()
    build_cj_check()
    build_coach()
    build_support()
    build_autopay()
