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
MODEL = "claude-sonnet-5-5"  # cheaper than Opus and good enough for these agents; use "claude-opus-5-5" for the strongest model

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


def telegram(wf, name, text_expr, pos, chat_expr="={{ $('⚙️ Settings').first().json.telegram_chat_id }}",
             html=False, buttons=None, **extra):
    fields = {"appendAttribution": False}
    if html:
        # n8n sends Telegram text as Markdown unless told otherwise, and one stray "_" or "*" (a link, a
        # hashtag) makes Telegram refuse the whole message. HTML mode only needs & < > escaped, which the
        # Code nodes do with esc(). <code>...</code> also gives the owner tap-to-copy text.
        fields["parse_mode"] = "HTML"
    params = {"chatId": chat_expr, "text": text_expr, "additionalFields": fields}
    if buttons:
        # Inline buttons. A tap comes back through the one Telegram trigger (workflow 02) as a callback query.
        params["replyMarkup"] = "inlineKeyboard"
        params["inlineKeyboard"] = {"rows": [{"row": {"buttons": [
            {"text": label, "additionalFields": {"callback_data": data}} for label, data in buttons]}}]}
    return wf.add(name, "n8n-nodes-base.telegram", 1.2, params, pos, **extra)


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

# Shared JavaScript for the social posts (workflows 02 and 08); needs JS_RULES. The social_posts table is
# append-only, like the playbook: every change is a new row that holds only the columns that changed, and a
# post's current state is all of its rows merged in order. Nothing is edited or deleted, so two workflows
# can write at the same time and the table is also the log of what happened to a post.
JS_POSTS = r"""
const POST_COLS = ['day', 'at', 'post_id', 'sku', 'product', 'video', 'video_url', 'ai', 'status', 'post_at', 'slot',
  'caption_tiktok', 'caption_instagram', 'yt_title', 'yt_description', 'yt_status', 'yt_video_id',
  'ig_status', 'ig_media_id', 'tiktok_status', 'stats_done', 'note', 'rules_version'];
function postRow(post_id, changes) {
  const row = Object.fromEntries(POST_COLS.map(c => [c, '']));
  return { ...row, day: $now.toFormat('yyyy-MM-dd'), at: $now.toUTC().toISO(), post_id, ...changes };
}
function foldPosts(rows) {
  const posts = {};
  for (const r of [...rows].sort((a, b) => (Number(a.id) || 0) - (Number(b.id) || 0))) {
    if (!r || !r.post_id) continue;
    const p = posts[r.post_id] = posts[r.post_id] || {};
    for (const c of POST_COLS) if (r[c] !== undefined && r[c] !== null && r[c] !== '') p[c] = r[c];
    if (r.yt_status) p.yt_since = r.at;   // when each platform last changed, to spot a post that got stuck half-way
    if (r.ig_status) p.ig_since = r.at;
  }
  return Object.values(posts);
}
const esc = t => String(t ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');   // Telegram HTML mode
const ms = iso => DateTime.fromISO(String(iso || '')).toMillis();                                       // NaN when empty
const zoneOf = s => { const z = String(s.time_zone || '').trim(); return z && DateTime.now().setZone(z).isValid ? z : 'Europe/Berlin'; };
const when = (iso, zone) => DateTime.fromISO(String(iso || ''), { zone, locale: 'en' }).toFormat("ccc d LLL 'at' HH:mm");
const shopOf = s => String(s.shop_url || 'pivendo.com').trim().replace(/^https?:\/\//i, '').replace(/\/+$/, '');
// The owner chooses the music for every video himself, before it is posted, and is reminded every time. The agents
// never pick or name a song. The bot cannot add a sound to a YouTube or Instagram post (their APIs have no call for
// it), so for the platforms the bot posts, the music must already be inside the video file.
function musicLine(s) {
  const bot = [['youtube_auto', 'YouTube'], ['instagram_auto', 'Instagram']].filter(([k]) => String(s[k] || '').trim().toLowerCase() === 'yes').map(x => x[1]);
  return '🎵 Choose the music first. TikTok: in TikTok Studio tap Sounds, pick one, then Save.'
    + (bot.length ? ` ${bot.join(' and ')}: the bot posts ${bot.length > 1 ? 'them' : 'it'} and cannot add a sound, so the music must already be inside the video file.` : '');
}
// Why an API call failed, in one line. Reads Meta and Google error answers and n8n's own error items.
const apiError = j => {
  const e = j && j.error;
  if (!e) return '';
  if (typeof e === 'string') return e.slice(0, 300);
  return String(e.error_user_msg || e.message || e.description || JSON.stringify(e)).slice(0, 300);
};
// Posting slots: post_times are wall-clock times in post_timezone (where the buyers are). The owner is shown
// every time in his own zone (time_zone). post_at is stored in UTC, so it is one exact moment everywhere.
const postZoneOf = s => { const z = String(s.post_timezone || '').trim(); return z && DateTime.now().setZone(z).isValid ? z : 'America/New_York'; };
function postTimes(s) {
  const list = String(s.post_times || '').split(/[\s,;]+/).map(t => {
    const m = t.match(/^(\d{1,2}):(\d{2})$/);
    return m && +m[1] < 24 && +m[2] < 60 ? m[1].padStart(2, '0') + ':' + m[2] : null;
  }).filter(Boolean);
  return list.length ? [...new Set(list)].sort() : ['12:30', '20:30'];
}
// The next free slot: at most one post per slot, and at least min_lead_hours from now. `taken` holds the
// moments (in milliseconds) that already have an approved post. Luxon keeps the wall-clock time when the
// clocks change (the gap to the owner's zone then moves by an hour for a week or two, because the US and
// Europe change on different days), and moves a time that does not exist that night to the next valid one.
function nextSlot(now, taken, s) {
  const lead = isNaN(num(s.min_lead_hours)) ? 2 : Math.max(0, num(s.min_lead_hours));
  const earliest = now.toMillis() + lead * 3600e3;
  let day = now.setZone(postZoneOf(s)).startOf('day');
  for (let i = 0; i < 400; i++, day = day.plus({ days: 1 })) {
    const free = postTimes(s).map(slot => ({ slot, at: day.set({ hour: +slot.slice(0, 2), minute: +slot.slice(3) }) }))
      .filter(c => c.at.toMillis() >= earliest && !taken.has(c.at.toMillis()))
      .sort((a, b) => a.at.toMillis() - b.at.toMillis())[0];
    if (free) return { slot: free.slot, post_at: free.at.toUTC().toISO() };
  }
  throw new Error('No free posting slot found in the next 400 days');
}
// A posted video also gets a row in the content table. The Coach and the Content agent join video stats
// (feedback ref "P...-yt", "P...-ig", "P...-tt") with that table, exactly like the stats of a /content script.
// The format is what both agents see next to the numbers, so it also carries two facts they need:
// - "views only": numbers the bot read itself have no link clicks or sales, a 0 there is not "no sales";
// - "slot 12:30": the posting slot, so the Coach can compare lunch against evening and propose a better time.
const PLATFORM = { yt: ['youtube-short', 'yt_title'], ig: ['instagram-reel', 'caption_instagram'], tt: ['tiktok', 'caption_tiktok'] };
function contentRow(p, tag, zone, viewsOnly = false) {
  const [name, field] = PLATFORM[tag];
  const format = name + (viewsOnly ? ', views only' : '') + (p.slot ? `, slot ${p.slot}` : '');
  const text = String(p[field] || '');
  const posted = DateTime.fromISO(String(p.post_at || ''), { zone });
  return { day: (posted.isValid ? posted : $now).toFormat('yyyy-MM-dd'), content_id: `${p.post_id}-${tag}`,
    sku: p.sku || '', product: p.product || '', format, hook: text.split('\n')[0].slice(0, 200), shots: p.video_url || '',
    on_screen_text: '', voiceover: '', caption: tag === 'yt' ? String(p.yt_description || '') : text, rules_version: p.rules_version || '' };
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

RESEARCH_SYSTEM = """You are the Product Research agent of a growing general store (like a small Amazon) that adds 2 new products every 2-3 weeks. The supplier is CJ Dropshipping and traffic comes from free short phone videos (TikTok, Instagram Reels, YouTube Shorts) that the owner films with a product sample.

A good product for this store:
- sells for $20-60 at about 1.5x its landed cost (product + shipping). A small profit per order is fine; cheap products that sell often are welcome;
- shows a visible problem and a satisfying result within the first 2 seconds of a video;
- is light, not fragile, has no sizes, is not branded and does not copy a brand;
- may be electric (USB, plug or motor are fine). Prefer USB or AA-battery power; avoid built-in lithium batteries (shipping limits) and anything with lasers;
- passes the 3-second test: a viewer who has never seen it stops scrolling because something unexpected happens on screen (a problem solved, a transformation). If everyone already knows what it does and how it looks in use, score it low;
- gives a buyer a reason to wait 1-2 weeks for shipping: it is not sold in normal local shops and is not cheap and fast on Amazon Prime. If it is, score it low;
- is not saturated: prefer products listed by few CJ stores. A product listed by over 1,000 stores needs a very strong reason to score above 50;
- is not seasonal, or its season starts at least 6 weeks after today's date. Never pick a product whose season ends within 8 weeks;
- is safe and legal: no lithium batteries, children's products, cosmetics, supplements, medical or health claims, weapons.

Explain in "risks" where a buyer could get it faster or cheaper (Amazon, local shops) and how saturated it is.

Follow the PLAYBOOK rules exactly. They were learned from this store's own results and override your general opinion.
Learn from PRODUCTS WE ALREADY TRIED: avoid repeating what failed, look for more of what worked.
Be honest: a low score is more useful than hype. Reply with only the JSON the user asks for."""

RESEARCH_BRIEF_JS = JS_RULES + r"""
const s = $('⚙️ Settings').first().json;
const res = $('CJ: trending products').first().json;
if (res.code !== 200) throw new Error('CJ product list failed: ' + (res.message || JSON.stringify(res).slice(0, 300)));

const products = (res.data?.content || []).flatMap(c => c.productList || []);
const banned = /(lithium|power ?bank|\bkids?\b|child|baby|toddler|infant|\btoys?\b|cosmetic|makeup|serum|cream|lotion|supplement|vitamin|capsule|medical|medicine|\bdrug|vape|e-?cig|knife|weapon|\bgun\b|laser|nike|adidas|iphone|airpods|samsung|disney|marvel|pokemon|lego|barbie|stanley|hello kitty|gucci|louis vuitton|chanel|dyson)/i;
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

JS_MARKETS = r"""
const EU = ['AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','GR','HU','IE','IT','LV','LT','LU','MT','NL','PL','PT','RO','SK','SI','ES','SE'];
const homeCountry = s => String(s.warehouse_country || 'US').trim().toUpperCase();
// The main market (warehouse_country) comes first, then every other country in sell_countries.
// The cheapest variant is the one the research list price refers to (often the single item, not a 2-pack).
const pickVariant = d => {
  const vs = (d && d.variants) || [];
  const priced = vs.filter(v => !isNaN(num(v.variantSellPrice)));
  return (priced.length ? priced.sort((a, b) => num(a.variantSellPrice) - num(b.variantSellPrice))[0] : vs[0]) || {};
};
const marketList = s => [...new Set([homeCountry(s), ...String(s.sell_countries || '').toUpperCase().split(/[\s,;]+/).filter(c => /^[A-Z]{2}$/.test(c))])];
"""

ROUTES_JS = JS_RULES + JS_MARKETS + r"""
const s = $('⚙️ Settings').first().json;
const picks = $('Parse picks').all().map(i => i.json);
const details = $input.all().map(i => i.json);
const home = homeCountry(s);

// For every pick and every market, choose the CJ warehouse that ships the order:
// - a warehouse in the customer's own country if it has stock;
// - EU customers: only a warehouse inside the EU (no customs or import VAT surprises), otherwise not sold there;
// - other countries: China, then the main warehouse.
const routes = [];
picks.forEach((p, i) => {
  const v = pickVariant(details[i]?.data);
  const stock = {};
  for (const inv of v.inventories || []) {
    const c = String(inv.countryCode || '').toUpperCase();
    stock[c] = (stock[c] || 0) + (num(inv.totalInventory) || 0);
  }
  const known = Object.keys(stock).length > 0;
  const has = c => (stock[c] || 0) > 0;
  for (const dest of marketList(s)) {
    let start = null;
    if (has(dest)) start = dest;
    else if (dest === home && !known) start = home;  // no stock data: trust the warehouse we searched in
    else if (EU.includes(dest)) start = EU.find(has) || null;
    else start = ['CN', home].find(has) || (known ? null : 'CN');
    if (start) routes.push({ json: { pick_index: i, dest, start, vid: v.vid || '' } });
  }
});
// Always send at least one item on, so the run still reports the picks
if (!routes.length) routes.push({ json: { pick_index: 0, dest: home, start: home, vid: '' } });
return routes;
"""

PRICE_JS = JS_RULES + JS_MARKETS + r"""
const s = $('⚙️ Settings').first().json;
const picks = $('Parse picks').all().map(i => i.json);
const details = $('CJ: product details').all().map(i => i.json);
const routes = $('Plan shipping routes').all().map(i => i.json);
const freights = $input.all().map(i => i.json);
const day = $now.toFormat('yyyy-MM-dd');
const home = homeCountry(s);
const intlFee = num(s.intl_shipping_fee_usd) || 0;   // what the store charges outside the main market
const minOk = isNaN(num(s.min_country_profit_usd)) ? 5 : num(s.min_country_profit_usd);

const cheapest = k => (Array.isArray(freights[k]?.data) ? freights[k].data : [])
  .map(o => ({ name: o.logisticName, price: num(o.logisticPrice), days: String(o.logisticAging || '?') }))
  .filter(o => !isNaN(o.price))
  .sort((a, b) => a.price - b.price)[0];

return picks.map((p, i) => {
  const d = details[i]?.data || {};
  const v = pickVariant(d);
  const cjCost = num(v.variantSellPrice ?? d.sellPrice ?? p.cost);

  const lines = marketList(s).map(country => {
    const k = routes.findIndex(r => r.pick_index === i && r.dest === country);
    if (k < 0) return { country, ok: false, note: EU.includes(country) ? 'no stock in an EU warehouse' : 'no warehouse has stock' };
    const best = cheapest(k);
    if (!best) return { country, ok: false, from: routes[k].start, note: 'no shipping quote, check in the CJ app' };
    return { country, from: routes[k].start, ship: best.price, method: best.name, days: best.days };
  });
  const main = lines[0];
  const ship = main.ship ?? 0;
  const landed = cjCost + ship;
  // Pricing is a fixed rule, never an AI guess: markup x landed cost in the main market, and at least $min_profit_usd above it.
  const price = Math.ceil(Math.max(landed * s.markup, landed + s.min_profit_usd)) - 0.01;
  const fees = price * 0.029 + 0.30;

  // Same price everywhere; outside the main market the customer pays the flat intl shipping fee.
  for (const l of lines) {
    if (l.ship === undefined) continue;
    const charged = l.country === home ? 0 : intlFee;
    l.profit = round2(price + charged - cjCost - l.ship - ((price + charged) * 0.029 + 0.30));
    l.ok = l.profit >= minOk;
    if (!l.ok) l.note = `profit only $${l.profit}`;
  }
  const markets = lines.map(l => l.ship === undefined
    ? `${l.country} ❌ ${l.note}`
    : `${l.country} ${l.ok ? '✅' : '❌'} $${l.profit} profit, ship $${round2(l.ship)} from ${l.from}, ${l.days} days`).join(' | ');

  return { json: {
    day, pid: p.pid, sku: v.variantSku || p.sku || '', name: p.name, image: p.image,
    cj_cost: round2(cjCost), ship_cost: round2(ship),
    ship_method: main.method || 'unknown - check in the CJ app', ship_days: main.days || '?',
    sell_price: round2(price), profit_per_order: round2(price - landed - fees),
    markets,
    score: Number(p.score) || 0, why: p.why || '', angle: p.angle || '', target_buyer: p.target_buyer || '',
    risks: p.risks || '', prediction: p.prediction || '', status: 'idea',
  } };
});
"""

RESEARCH_MSG_JS = r"""
const picks = $input.all().map(i => i.json);
// Direct CJ product page: CJ finds the product by the id after "-p-"; the name part is only for readability
const cjLink = p => `https://www.cjdropshipping.com/product/${String(p.name || 'product').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 80)}-p-${p.pid}.html`;
const blocks = picks.map((p, n) => `${n + 1}) ${p.name}
CJ SKU: ${p.sku} (search CJ for ${String(p.sku).split('-')[0]})
Open in CJ: ${cjLink(p)}
Cost: $${p.cj_cost} + $${p.ship_cost} shipping (${p.ship_method}, ${p.ship_days} days)
Sell at: $${p.sell_price} -> about $${p.profit_per_order} profit per order before ads
By country:
${String(p.markets || '').split(' | ').map(m => '  ' + m).join('\n')}
Score ${p.score}/100: ${p.why}
Video idea: ${p.angle}
Risks: ${p.risks}`);
const text = `🔎 Product research ${$now.toFormat('yyyy-MM-dd')}

${blocks.join('\n\n')}

❌ = don't sell this product in that country (Shopify -> Markets -> product availability).

Next: check the product page in the CJ app (photos, stock, reviews), then send
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
        ("markup", 1.5),
        ("min_profit_usd", 7),
        ("sell_countries", "US,DE,CA,AU"),
        ("intl_shipping_fee_usd", 7.99),
        ("min_country_profit_usd", 5),
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
    code(wf, "Plan shipping routes", ROUTES_JS, [2640, 0])
    wf.add("CJ: shipping cost", "n8n-nodes-base.httpRequest", 4.2, {
        "method": "POST",
        "url": f"{CJ}/logistic/freightCalculate",
        "sendHeaders": True,
        "headerParameters": {"parameters": [TOKEN_HEADER]},
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ startCountryCode: $json.start, endCountryCode: $json.dest, "
                    "products: [{ quantity: 1, vid: $json.vid }] }) }}",
        "options": {"batching": {"batch": {"batchSize": 1, "batchInterval": 1500}}},
    }, [2860, 0], onError="continueRegularOutput")
    code(wf, "Price & margin", PRICE_JS, [3080, 0])
    table_insert(wf, "Save to products table", "products", [3300, -120])
    code(wf, "Write Telegram message", RESEARCH_MSG_JS, [3300, 120])
    telegram(wf, "Send picks to Telegram", "={{ $json.text }}", [3520, 120])

    wf.chain("Every morning 07:00", "⚙️ Settings", "Load playbook", "Load past products", "Load feedback",
             "CJ: get token", "Wait 2s", "CJ: trending products", "Build research brief", "Research agent",
             "Parse picks", "CJ: product details", "Plan shipping routes", "CJ: shipping cost", "Price & margin")
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

Music: the owner chooses the music of every video himself. Never name, suggest or pick a song, a sound, an artist or "a trending sound" - not in a script, a caption or a voiceover.

Follow the PLAYBOOK rules exactly; they were learned from this store's own results. Copy the patterns of the videos that WORKED and avoid the ones that FLOPPED. Reply with only the JSON the user asks for."""

PARSE_CMD_JS = r"""
const s = $('⚙️ Settings').first().json;
const update = $('Telegram message in').first().json;
// A tap on an inline button arrives as a "callback query" instead of a message. Its data, for example
// "approve:P1013025812", is handled exactly like the typed command "/approve P1013025812".
const tap = update.callback_query;
const msg = (tap ? tap.message : update.message) || {};
const chatId = String(msg.chat?.id ?? tap?.from?.id ?? '');
const text = tap ? '/' + String(tap.data || '').replace(':', ' ') : String(msg.text || '').trim();
const [first, ...args] = text.split(/\s+/);
const cmd = String(first || '').toLowerCase().replace(/^\//, '').replace(/@.*$/, '');

if (String(s.telegram_chat_id).startsWith('PASTE')) return [{ json: { route: 'setup', chatId, args, text } }];
if (chatId !== String(s.telegram_chat_id)) return [];  // ignore everyone except the owner

const known = ['content', 'video', 'product', 'rules', 'clips', 'render', 'send', 'reply', 'skip',
               'queue', 'approve', 'reject', 'posts', 'tiktok', 'youtube', 'instagram', 'retry'];
return [{ json: { route: known.includes(cmd) ? cmd : 'help', chatId, args, text, tapId: tap ? String(tap.id || '') : '' } }];
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
Shipping time to customers: ${product.ship_days} days (${product.ship_method})${product.markets ? `
By country (only promise these times): ${product.markets}` : ''}
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

# ---- social posts: /queue, the Approve / Reject buttons, /posts, /tiktok, /retry (publishing itself is workflow 08)

POST_SYSTEM = """You are the Social Post agent of a one-person online store. You write the texts that go with ONE finished short vertical video: a TikTok caption, an Instagram Reels caption, a YouTube Shorts title and a YouTube description.

You cannot see the video. You only know the product facts and what the owner says the video shows. Describe only that.

What works:
- The first words name the problem or the result. No "hey guys", no brand intro.
- Short, plain words, like a real person. One idea. End with a soft pointer to the shop.
- TikTok: one or two short lines. Instagram: two or three short lines. YouTube title: clear and searchable, what the product is and does.
- Hashtags: a few specific ones per platform (product type, use, room or hobby). No spam tags like #fyp, #viral or #foryou.

Honesty rules you must never break:
- No reviews, testimonials, ratings, star counts or "customers say".
- No discounts, sales, countdowns, "limited", "last chance", "selling fast" or "sold out".
- No prices and no delivery promises ("fast shipping", "free shipping", "arrives in X days").
- No health, medical or safety claims, no competitor brand names, no "best seller", no "number one", no guarantees.
- The video comes from the store. Never write as a buyer ("I bought", "my order", "my review"). An AI presenter is never a "customer", a "buyer" or a real person.
- Do not overclaim what the product does. Say what the footage shows. For lamps and projectors never say "the whole ceiling" or "the whole room": say "on the ceiling" or "on the wall", and add "best in a dark room".

Music: the owner chooses the music of every video himself. Never name, suggest or pick a song, a sound, an artist or "a trending sound", and never credit music in a text.

Follow the PLAYBOOK rules exactly; they were learned from this store's own results. Copy the patterns of the videos that WORKED and avoid the ones that FLOPPED. Reply with only the JSON the user asks for."""

POST_BRIEF_JS = JS_RULES + JS_POSTS + r"""
// /queue, step 1: check the command and build the brief for the Post agent (which product, which rules).
const s = $('⚙️ Settings').first().json;
const cmd = $('Parse command').first().json;
const fail = text => [{ json: { ok: false, reply: esc(text) } }];
const [url = '', skuArg = '', ...rest] = cmd.args || [];
// Instagram and YouTube fetch the file themselves, so it must be a direct, public https link to an .mp4
const okUrl = /^https:\/\/[^\s?#]+\.mp4(\?\S*)?$/i.test(url) && /^[\x21-\x7e]+$/.test(url) && !/[<>"']/.test(url);
if (!okUrl || !skuArg) return fail('Usage: /queue <video link> <SKU> [ai] [what the video shows]\n'
  + 'Example: /queue https://cdn.shopify.com/videos/star-lamp-1.mp4 CJ1234567 ai presenter holds the lamp, stars on the wall\n\n'
  + 'The link must start with https:// and end with .mp4, and it must open without logging in.\n'
  + 'Add "ai" when the video has an AI presenter or an AI voice.');
const ai = String(rest[0] || '').toLowerCase() === 'ai';
const shows = (ai ? rest.slice(1) : rest).join(' ').slice(0, 300);
const key = skuArg.toLowerCase();
const product = [...rowsOf('Load products (post)')].reverse().find(p =>
  String(p.sku).toLowerCase() === key || String(p.pid).toLowerCase() === key);
if (!product) return fail(`I can't find SKU "${skuArg}" in the products table. Use the SKU you used for /content.`);
// The same video is never queued twice
const twin = foldPosts(rowsOf('Load posts (queue)')).find(p => p.video_url === url && p.status !== 'rejected');
if (twin) return fail(`This video is already in your list as ${twin.post_id}. Send /posts to see it.`);

// Learn from past videos, like the Content agent: scripts and posts joined with their latest stats
const stats = {};
for (const f of rowsOf('Load stats (post)')) if (f.kind === 'video') stats[f.ref] = f;
const measured = rowsOf('Load videos (post)')
  .filter(c => stats[c.content_id])
  .map(c => ({ ...c, views: +stats[c.content_id].views || 0, clicks: +stats[c.content_id].clicks || 0, sales: +stats[c.content_id].sales || 0 }))
  .sort((a, b) => b.views - a.views);
const fmt = v => `- "${v.hook}" (${v.format}) -> ${v.views} views, ${v.clicks} link clicks, ${v.sales} sales`;
const worked = measured.slice(0, 5).map(fmt).join('\n') || '- no measured videos yet';
const flopped = measured.length > 5 ? measured.slice(-3).map(fmt).join('\n') : '- not enough data yet';

const rules = activeRules(rowsOf('Load playbook (post)'), ['content']);
const prompt = `Write the texts for ONE finished short vertical video. You cannot see it.

VIDEO
What it shows (told by the owner): ${shows || 'not described - keep it general and claim nothing about what happens on screen'}
Presenter: ${ai ? 'an AI presenter or AI voice made by the store. Never a customer, a buyer or a real person.' : 'no AI. The video comes from the store, not from a customer.'}

PRODUCT
Name: ${product.name}
Who buys it: ${product.target_buyer}
Video idea from research: ${product.angle}
Known risks: ${product.risks}
Shop address: ${shopOf(s)}

PLAYBOOK (rules learned from this store's results - follow them):
${rulesText(rules)}

VIDEOS THAT WORKED (copy these patterns):
${worked}

VIDEOS THAT FLOPPED (avoid these patterns):
${flopped}

Reply with only this JSON (put hashtags only in the hashtag lists, never inside the texts):
{"caption_tiktok":"<max 150 characters>","hashtags_tiktok":["<3-5 tags>"],
 "caption_instagram":"<max 300 characters>","hashtags_instagram":["<3-5 tags>"],
 "yt_title":"<max 70 characters>","yt_description":"<2-4 short sentences>","hashtags_youtube":["<2-3 tags>"]}`;

return [{ json: { ok: true, prompt, url, ai: ai ? 'yes' : 'no', shows, sku: product.sku, product: product.name,
                  rules_version: rules.map(r => r.rule_id + 'v' + r.version).join(',') } }];
"""

CHECK_POST_JS = JS_RULES + JS_PARSE_JSON + JS_POSTS + r"""
// /queue, step 2. Deterministic checks: the AI writes the texts, but only code decides what is stored and
// shown. Texts that break an honesty rule are not queued at all. Everything stays short enough that the
// owner sees the full text before approving, which is also far inside every platform's own limit
// (YouTube title 100 characters, description 5,000 bytes; Instagram and TikTok captions 2,200 characters).
const s = $('⚙️ Settings').first().json;
const brief = $('Build post brief').first().json;
const fail = text => [{ json: { ok: false, reply: esc(text) } }];
let a;
try { a = parseAgentJson('Post agent'); }
catch (e) { return fail('The Post agent did not return usable texts. Send the same /queue command again.'); }

const shop = shopOf(s);
const SPAM = /^#(fyp|foryou|foryoupage|viral|trending|explore|explorepage|follow|followme|like4like)$/i;
const clean = t => String(t ?? '').replace(/<\/?[a-z][^>]*>/gi, '').replace(/[<>]/g, '').replace(/#[\p{L}\p{N}_]+/gu, '').replace(/[ \t]+/g, ' ')
  .replace(/ *\n */g, '\n').replace(/\n{3,}/g, '\n\n').trim();
const tags = (list, max) => [...new Set((Array.isArray(list) ? list : String(list || '').split(/[\s,]+/))
  .map(h => '#' + String(h).replace(/[^\p{L}\p{N}_]/gu, '')).filter(h => h.length > 2 && !SPAM.test(h)))].slice(0, max);
const cut = (t, max) => {
  if (t.length <= max) return t;
  const c = t.slice(0, max - 1).replace(/[\uD800-\uDBFF]$/, ''), sp = c.lastIndexOf(' ');   // never half an emoji
  return (sp > max * 0.6 ? c.slice(0, sp) : c).trimEnd() + '…';
};
// text + the shop address (if the text does not name it) + hashtags, never longer than max
const build = (text, hashtags, max, link) => {
  const tail = (text.toLowerCase().includes(shop.toLowerCase()) ? '' : `\n\n${link}`) + (hashtags.length ? `\n\n${hashtags.join(' ')}` : '');
  return cut(text, max - tail.length) + tail;
};
const raw = { tiktok: clean(a.caption_tiktok), instagram: clean(a.caption_instagram),
              title: clean(a.yt_title).replace(/\n+/g, ' '), description: clean(a.yt_description) };
if (Object.values(raw).some(t => !t)) return fail('The Post agent left a text empty. Send the same /queue command again.');
const caption_tiktok = build(raw.tiktok, tags(a.hashtags_tiktok, 5), 600, `Shop: ${shop}`);
const caption_instagram = build(raw.instagram, tags(a.hashtags_instagram, 5), 900, `Shop: ${shop}`);   // Instagram counts at most 5 hashtags
const yt_title = cut(raw.title, 100);
const yt_description = build(raw.description, tags(a.hashtags_youtube, 5), 1200, `Shop: https://${shop}`);

const HONESTY = [
  [/\b\d{1,3} ?% ?off\b|\b(discounts?|coupons?|promo ?codes?|vouchers?|sale|deals?|half price|clearance|black friday|save \d|save up to)\b/i, 'a discount or sale'],
  [/\b(limited (time|stock|offer|edition)|last chance|hurry|only \d+ left|almost gone|selling (out|fast)|sold out|ends? (today|tonight|soon|at midnight)|while (stocks?|supplies) last|today only|don'?t miss out)\b/i, 'a countdown or "running out" claim'],
  [/\b(free (shipping|delivery)|fast (shipping|delivery)|quick (shipping|delivery)|ships? (in|within|today|tomorrow|fast|free)|arrives? (in|within|by|tomorrow|before)|deliver(y|ed|s)? (in|within|by|before)|next[- ]day|same[- ]day|\d+[- ](day|hour)s? (delivery|shipping)|in time for (christmas|halloween|easter|valentine))/i, 'a delivery promise'],
  [/[★⭐]|\b(\d([.,]\d)? ?(stars?|out of 5)|reviews?|testimonials?|rated|ratings?|customers?|buyers?|i (bought|ordered|purchased)|my (order|review|purchase))\b/i, 'a review or customer claim'],
  [/\b((whole|entire|full) (ceiling|room|house|wall|bedroom)|fills? (the|your|a|any) (whole |entire )?(room|ceiling|bedroom)|guarantee[ds]?|best[- ]sell(er|ing)|number one|world'?s best|life[- ]changing|miracle|cures?|heals?)\b|\b100 ?%|#1\b/i, 'an overclaim'],
  [/[$€£] ?\d|\b\d+([.,]\d{1,2})? ?(usd|dollars?|eur|euros?|bucks)\b/i, 'a price'],
  // the owner chooses the music himself: the texts never name or credit a song (a plain "music" or "sound" is fine)
  [/[♪♫]|\bmusic by\b|\b(original|trending|viral|popular) (sound|song|audio|track)\b|\b(song|sound|audio|track)\s*:|\bfeat\./i, 'a song or sound credit (you choose the music yourself)'],
];
const all = [caption_tiktok, caption_instagram, yt_title, yt_description].join('\n');
const broken = HONESTY.map(([re, label]) => { const m = all.match(re); return m ? `${label}: "${m[0].trim()}"` : null; }).filter(Boolean);
if (broken.length) return fail(`Not queued. The texts broke an honesty rule:\n- ${broken.join('\n- ')}\n\nSend the same /queue command again to get new texts.`);

const post_id = 'P' + $now.toFormat('MMddHHmmss');
const row = postRow(post_id, { sku: brief.sku, product: brief.product,
  video: brief.url.split('?')[0].split('/').pop().replace(/\.mp4$/i, '').slice(0, 80), video_url: brief.url, ai: brief.ai,
  status: 'awaiting_ok', caption_tiktok, caption_instagram, yt_title, yt_description, note: brief.shows, rules_version: brief.rules_version });
const text = `🎬 New post ${post_id} is waiting for your OK
Video: ${brief.url}
Product: ${brief.product} (${brief.sku})
AI presenter or AI voice: ${brief.ai}

TIKTOK CAPTION
${caption_tiktok}

INSTAGRAM CAPTION
${caption_instagram}

YOUTUBE TITLE
${yt_title}

YOUTUBE DESCRIPTION
${yt_description}

${musicLine(s)}

✅ Approve = it gets the next free slot (${postTimes(s).join(' or ')} in ${postZoneOf(s)}; I tell you the time in ${zoneOf(s)}).
❌ Reject = it is dropped.
Buttons not working? Send /approve ${post_id} or /reject ${post_id}`;
return [{ json: { ok: true, row, text: esc(text.slice(0, 3900)) } }];
"""

POST_ACTION_JS = JS_RULES + JS_POSTS + r"""
// The owner's decisions on queued posts: Approve / Reject (button or typed), /posts,
// /tiktok | /youtube | /instagram <id> done (posted by hand) and /retry.
const s = $('⚙️ Settings').first().json;
const cmd = $('Parse command').first().json;
const zone = zoneOf(s);
const shop = shopOf(s);
const now = $now.toMillis();
const posts = foldPosts(rowsOf('Load posts'));
const fail = text => [{ json: { ok: false, reply: esc(text) } }];
const done = (msgs, rows = [], videos = []) => [{ json: { ok: true, save: rows.length > 0, rows, videos, msgs } }];
const LABEL = { queued: '⏳ waiting', uploading: '⏳ uploading', scheduled: '✅ scheduled', publishing: '⏳ posting',
  published: '✅ posted', todo: '☐ you post it', done: '✅ done', failed: '❌ failed', stuck: '❓ check by hand',
  late: '⏰ too late, not posted', cancelled: '🚫 cancelled' };

if (cmd.route === 'posts') {
  const live = posts.filter(p => p.status === 'approved' && !isNaN(ms(p.post_at))).sort((a, b) => ms(a.post_at) - ms(b.post_at));
  const waiting = posts.filter(p => p.status === 'awaiting_ok');
  const line = p => `• ${p.post_id} · ${when(p.post_at, zone)} · ${p.product || p.sku}\n  YouTube ${LABEL[p.yt_status] || '-'} · Instagram ${LABEL[p.ig_status] || '-'} · TikTok ${LABEL[p.tiktok_status] || '-'}`;
  const parts = [];
  if (waiting.length) parts.push('WAITING FOR YOUR OK\n' + waiting.map(p => `• ${p.post_id} · ${p.product || p.sku}\n  /approve ${p.post_id} or /reject ${p.post_id}`).join('\n'));
  const upcoming = live.filter(p => ms(p.post_at) > now);
  if (upcoming.length) parts.push('COMING UP\n' + upcoming.map(line).join('\n'));
  const recent = live.filter(p => ms(p.post_at) <= now).slice(-5).reverse();
  if (recent.length) parts.push('LAST POSTS\n' + recent.map(line).join('\n'));
  const text = parts.length ? `📅 Your posts (times in ${zone})\n\n${parts.join('\n\n')}` : 'No posts yet. Queue a finished video with\n/queue <video link> <SKU>';
  return done([esc(text.slice(0, 3900))]);
}

const id = String((cmd.args || [])[0] || '').toUpperCase();
const p = posts.find(x => String(x.post_id).toUpperCase() === id);
if (!p) return fail(`I can't find post ${id || '(missing id)'}. Send /posts to see your posts.`);

if (cmd.route === 'approve') {
  if (p.status === 'approved') return fail(`${p.post_id} is already approved for ${when(p.post_at, zone)}.`);
  if (p.status !== 'awaiting_ok') return fail(`${p.post_id} was rejected. Send the video again with /queue if you changed your mind.`);
  // one post per slot: slots that already have an approved post are taken
  const taken = new Set(posts.filter(x => x.status === 'approved' && !isNaN(ms(x.post_at))).map(x => ms(x.post_at)));
  const { post_at, slot } = nextSlot($now, taken, s);
  const at = `${when(post_at, zone)} (${zone})`;   // the owner always reads his own time zone
  const auto = k => String(s[k] || '').trim().toLowerCase() === 'yes';
  const yt = auto('youtube_auto'), ig = auto('instagram_auto'), isAi = p.ai === 'yes';
  const row = postRow(p.post_id, { status: 'approved', post_at, slot, yt_status: yt ? 'queued' : 'todo',
                                   ig_status: ig ? 'queued' : 'todo', tiktok_status: 'todo' });
  const msgs = [esc(`✅ ${p.post_id} approved. Slot: ${at}. That is the ${slot} slot in ${postZoneOf(s)}.

YouTube: ${yt ? 'the bot uploads it within 10 minutes. It stays private and YouTube makes it public at the slot time.' : 'you post it yourself (to-do below).'}
Instagram: ${ig ? 'the bot posts it at the slot time.' : 'you post it yourself (to-do below).'}
TikTok: you schedule it yourself (to-do below).

${musicLine(s)}

Changed your mind? /reject ${p.post_id}`)];
  // A to-do for every platform the owner posts by hand. The texts come in <code> blocks: tap to copy.
  const todo = (name, command, steps, copy) => msgs.push(
    esc(`📋 ${name} to-do for ${p.post_id}\n` + steps.map((t, i) => `${i + 1}. ${t}`).join('\n') + `\n\nDone? Send: /${command} ${p.post_id} done`)
    + copy.map(([label, text]) => `\n\n${esc(label)} (tap to copy):\n<code>${esc(text)}</code>`).join(''));
  todo('TikTok', 'tiktok', [
    `Download the video: ${p.video_url}`,
    'Open tiktok.com/tiktokstudio → Upload, and choose the video.',
    'Choose the music first. In TikTok Studio tap Sounds, pick one, then Save.',
    'Paste the caption from below.',
    `Schedule it for ${at}.`,
    'Content disclosure: switch "Your brand" ON.',
    ...(isAi ? ['Switch "AI-generated content" ON.'] : []),
    `When it is live: write the comment "Shop: ${shop}" and pin it.`,
  ], [['Caption', p.caption_tiktok]]);
  if (!yt) todo('YouTube', 'youtube', [
    `Download the video: ${p.video_url}`,
    'Open studio.youtube.com → Create → Upload videos, and choose the video.',
    'Choose the music first. It must already be inside the video file, or add the sound in the YouTube app instead of Studio.',
    'Paste the title and the description from below.',
    'Audience: choose "No, it\'s not made for kids".',
    ...(isAi ? ['Show more → Altered content: choose "Yes".'] : []),
    `Visibility → Schedule: ${at}.`,
  ], [['Title', p.yt_title], ['Description', p.yt_description]]);
  if (!ig) todo('Instagram', 'instagram', [
    `Download the video: ${p.video_url}`,
    'Open the Instagram app → + → Reel, and choose the video.',
    'Choose the music first. In the Reel editor tap the music icon (Audio), pick one, then Done.',
    'Paste the caption from below.',
    ...(isAi ? ['More options → switch "AI label" ON.'] : []),
    `More options → Schedule: ${at}.`,
  ], [['Caption', p.caption_instagram]]);
  return done(msgs, [row]);
}

if (cmd.route === 'reject') {
  if (p.status === 'rejected') return fail(`${p.post_id} is already rejected.`);
  // Reject stops everything that has not happened yet. What is already out, only the owner can delete: the bot has no
  // call that deletes a video or a Reel, on purpose. A YouTube video is uploaded within 10 minutes of the approval and
  // then waits there for its slot time, so Reject cannot take it back. The owner gets its link and the exact clicks.
  const out = [];
  const deleteSteps = '1. Open YouTube Studio → Content (left menu).\n2. Move the mouse over the video and click the three dots ⋮ (Options) → Delete forever.\n3. Tick the box and click Delete forever.';
  if (p.yt_video_id) {
    const wasPublic = ms(p.post_at) <= now;
    out.push(`YouTube already has this video: ${wasPublic ? 'its slot time has passed, so it may be public already' : `it is scheduled, private until ${when(p.post_at, zone)} (${zone}), and then it goes public by itself`}. `
      + `Rejecting does not remove it, and the bot cannot delete videos. To delete it yourself:\nVideo: https://studio.youtube.com/video/${p.yt_video_id}/edit\n${deleteSteps}`);
  } else if (p.yt_status === 'uploading') out.push(`YouTube is uploading it right now and rejecting does not stop an upload that has started. In a few minutes you get a message with the video link. To delete the video yourself:\n${deleteSteps}`);
  else if (['failed', 'stuck'].includes(p.yt_status)) out.push(`A YouTube upload that failed or got stuck may still have left a video. Look in YouTube Studio → Content. If it is there, delete it:\n${deleteSteps}`);
  if (p.ig_status === 'publishing') out.push('Instagram is busy with it right now. Wait for the bot\'s next message: "not posted" means it is stopped. "is live" means you delete the Reel in the Instagram app.');
  else if (p.ig_status === 'published') out.push('It is already on Instagram: delete the Reel in the app.');
  else if (p.ig_status === 'stuck') out.push('Instagram may have posted it: look in the app and delete the Reel if it is there.');
  if ([p.tiktok_status, p.yt_status, p.ig_status].includes('done')) out.push('You marked a platform as done by hand: delete it there too.');
  return done([esc(`❌ ${p.post_id} rejected. ${p.status === 'approved' ? 'The bot will not post anything more for it.' : 'Nothing will be posted.'}`
    + (out.length ? '\n\n' + out.map(t => '⚠️ ' + t).join('\n\n') : ''))], [postRow(p.post_id, { status: 'rejected' })]);
}

const BY_HAND = { tiktok: ['tiktok_status', 'tt', 'TikTok'], youtube: ['yt_status', 'yt', 'YouTube'], instagram: ['ig_status', 'ig', 'Instagram'] };
if (BY_HAND[cmd.route]) {
  const [field, tag, name] = BY_HAND[cmd.route];
  if (String(cmd.args[1] || '').toLowerCase() !== 'done') return fail(`Usage: /${cmd.route} <post id> done\nExample: /${cmd.route} ${p.post_id} done`);
  if (p.status !== 'approved') return fail(`${p.post_id} is not approved, so there is nothing to mark.`);
  if (p[field] === 'done') return fail(`${name} is already marked as done for ${p.post_id}.`);
  if (p[field] !== 'todo') return fail(`${name} for ${p.post_id} is handled by the bot (${LABEL[p[field]] || p[field] || 'not started'}). Nothing to mark.`);
  return done([esc(`✅ ${name} marked as done for ${p.post_id}.

48 hours after it goes live, send its numbers so the agents can learn:
/video ${p.post_id}-${tag} <views> <link clicks> <sales>`)], [postRow(p.post_id, { [field]: 'done' })], [contentRow(p, tag, zone)]);
}

// /retry: only after the bot reported a failure. It is the owner who decides to try again, never the bot.
const again = [['yt_status', 'YouTube'], ['ig_status', 'Instagram']].filter(([k]) => ['failed', 'stuck', 'late'].includes(p[k]));
if (p.status !== 'approved' || !again.length) return fail(`Nothing to retry for ${p.post_id}. /retry only works after the bot told you that YouTube or Instagram failed.`);
const changes = Object.fromEntries(again.map(([k]) => [k, 'queued']));
const passed = ms(p.post_at) <= now;
if (passed) {
  // A slot in the past would be skipped again as "too late", so the post goes out now. Its slot becomes the
  // real local time, so a late post is never counted as a normal lunch or evening post when slots are compared.
  changes.post_at = $now.toUTC().toISO();
  changes.slot = $now.setZone(postZoneOf(s)).toFormat('HH:mm');
}
// "stuck" = nobody knows if it went out. A failed YouTube upload is just as unsure: n8n sends the file in chunks and
// the call can fail after the last one, so the video may be on YouTube although the upload was reported as failed.
const unsure = again.some(([k]) => p[k] === 'stuck' || (k === 'yt_status' && p[k] === 'failed'));
return done([esc(`🔁 ${p.post_id}: ${again.map(x => x[1]).join(' and ')} will be tried again within 10 minutes`
  + (passed ? ', and it goes public right away because the slot time has passed.' : '.')
  + (unsure ? `\n\n⚠️ If it is already there, it will be posted twice. Already there? Send /reject ${p.post_id} now (it drops the whole post).` : ''))],
  [postRow(p.post_id, changes)]);
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
/queue LINK SKU ai - queue a finished video for TikTok, Instagram and YouTube (leave out "ai" if no AI is in it)
/posts - show waiting, coming and last posts
/tiktok P123 done - tell the bot you scheduled a post on TikTok yourself
/retry P123 - try again after the bot said a post failed

Research arrives every morning, the report every evening."""


def build_commands():
    wf = Workflow("02 · Telegram commands (content + feedback)")
    # A bot has only one webhook, so this is the only Telegram trigger in the whole system: every command
    # and every tap on an inline button (callback_query) comes in here and is routed by "Parse command".
    wf.add("Telegram message in", "n8n-nodes-base.telegramTrigger", 1.1,
           {"updates": ["message", "callback_query"], "additionalFields": {}}, [0, 300], webhookId=wf.webhook_id("tg"))
    settings(wf, [
        ("telegram_chat_id", "PASTE_YOUR_TELEGRAM_CHAT_ID"),
        ("voice", "en-US-EmmaMultilingualNeural"),
        ("cta_text", "Link in bio"),
        ("support_email", "PASTE_YOUR_SUPPORT_EMAIL"),
        ("email_signature", "Best regards,\nThe support team"),
        # social posts. post_times are clock times in post_timezone (the buyers: lunch and evening in the US);
        # one approved video per slot. time_zone is the owner's own zone: every message shows times in it.
        # youtube_auto / instagram_auto: "no" = you get a to-do message and post by hand; "yes" after SOCIAL-SETUP.md.
        ("post_times", "12:30,20:30"),
        ("post_timezone", "America/New_York"),
        ("time_zone", "Europe/Berlin"),
        ("min_lead_hours", 2),
        ("youtube_auto", "no"),
        ("instagram_auto", "no"),
        ("shop_url", "pivendo.com"),
    ], [220, 300])
    code(wf, "Parse command", PARSE_CMD_JS, [440, 300])
    switch(wf, "Route", "route", ["content", "video", "product", "rules", "setup", "help", "clips", "render",
                                   "send", "reply", "skip", "queue", "approve", "reject", "posts", "tiktok",
                                   "youtube", "instagram", "retry"], [660, 300])
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

    # A tap on an inline button: tell Telegram it arrived, so the button stops showing its loading circle
    if_true(wf, "Button tap?", "={{ !!$json.tapId }}", [660, 120])
    wf.add("Answer button tap", "n8n-nodes-base.telegram", 1.2, {
        "resource": "callback",
        "operation": "answerQuery",
        "queryId": "={{ $json.tapId }}",
        "additionalFields": {"text": "OK, one moment…"},
    }, [880, 120], onError="continueRegularOutput")
    wf.connect("Parse command", "Button tap?")
    wf.connect("Button tap?", "Answer button tap")

    # /queue: one finished video -> Post agent writes the texts -> saved as "awaiting_ok" -> Approve / Reject buttons
    table_get(wf, "Load products (post)", "products", [880, 2200])
    table_get(wf, "Load playbook (post)", "playbook", [1100, 2200])
    table_get(wf, "Load videos (post)", "content", [1320, 2200])
    table_get(wf, "Load stats (post)", "feedback", [1540, 2200])
    table_get(wf, "Load posts (queue)", "social_posts", [1760, 2200])
    code(wf, "Build post brief", POST_BRIEF_JS, [1980, 2200])
    if_true(wf, "Post brief ok?", "={{ $json.ok }}", [2200, 2200])
    agent(wf, "Post agent", "={{ $json.prompt }}", POST_SYSTEM, [2420, 2100], [2420, 2320])
    code(wf, "Check post texts", CHECK_POST_JS, [2640, 2100])
    if_true(wf, "Post texts ok?", "={{ $json.ok }}", [2860, 2100])
    code(wf, "Post row", "return [{ json: $input.first().json.row }];", [3080, 2040])
    table_insert(wf, "Save post", "social_posts", [3300, 2040])
    post_id = "$('Check post texts').first().json.row.post_id"
    telegram(wf, "Ask to approve post", "={{ $('Check post texts').first().json.text }}", [3520, 2040], reply_chat,
             html=True, buttons=[("✅ Approve", "={{ 'approve:' + %s }}" % post_id),
                                 ("❌ Reject", "={{ 'reject:' + %s }}" % post_id)])
    telegram(wf, "Queue problem", "={{ $json.reply }}", [3080, 2320], reply_chat, html=True)
    wf.chain("Load products (post)", "Load playbook (post)", "Load videos (post)", "Load stats (post)",
             "Load posts (queue)", "Build post brief", "Post brief ok?", "Post agent", "Check post texts",
             "Post texts ok?", "Post row", "Save post", "Ask to approve post")
    wf.connect("Post brief ok?", "Queue problem", out=1)
    wf.connect("Post texts ok?", "Queue problem", out=1)
    wf.connect("Route", "Load products (post)", out=11)

    # Approve / Reject (button or typed), /posts, /tiktok /youtube /instagram <id> done, /retry.
    # Approve only gives the post its slot and writes the to-dos. Uploading and publishing is workflow 08.
    table_get(wf, "Load posts", "social_posts", [880, 2560])
    code(wf, "Build post action", POST_ACTION_JS, [1100, 2560])
    if_true(wf, "Post action ok?", "={{ $json.ok }}", [1320, 2560])
    if_true(wf, "Save a row?", "={{ $json.save }}", [1540, 2500])
    code(wf, "Post action rows", "return $('Build post action').first().json.rows.map(r => ({ json: r }));", [1760, 2440])
    table_insert(wf, "Save post action", "social_posts", [1980, 2440])
    code(wf, "Post video rows", "return $('Build post action').first().json.videos.map(r => ({ json: r }));", [2200, 2340])
    table_insert(wf, "Save post as video", "content", [2420, 2340])
    code(wf, "Post action messages", "return $('Build post action').first().json.msgs.map(text => ({ json: { text } }));",
         [2200, 2560])
    telegram(wf, "Send post action", "={{ $json.text }}", [2420, 2560], reply_chat, html=True)
    telegram(wf, "Post action problem", "={{ $json.reply }}", [1540, 2700], reply_chat, html=True)
    wf.chain("Load posts", "Build post action", "Post action ok?", "Save a row?", "Post action rows",
             "Save post action", "Post action messages", "Send post action")
    wf.connect("Save post action", "Post video rows")
    wf.connect("Post video rows", "Save post as video")
    wf.connect("Save a row?", "Post action messages", out=1)
    wf.connect("Post action ok?", "Post action problem", out=1)
    for i in range(12, 19):
        wf.connect("Route", "Load posts", out=i)
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


# ------------------------------------------------------------ 08 social publisher
#
# Only posts the owner approved in Telegram (workflow 02) are touched here, and only the platforms marked
# "queued" (youtube_auto / instagram_auto = yes in workflow 02). TikTok is always posted by the owner.
#   every 10 minutes: upload approved videos to YouTube (private, YouTube publishes them at the slot time),
#                     and publish Instagram Reels whose slot time has come
#   every evening:    read the 48-hour numbers into the feedback table for the Coach, check the two logins
# Every Code node here only compares rows and builds texts, so each one finishes in a few milliseconds.

PLAN_RUN_JS = JS_RULES + JS_POSTS + r"""
// What to do in this run. At most one YouTube upload and one Instagram post per run; the next run takes the next.
// The double-post guard: a post is only picked while its platform status is "queued". Before any API call
// this node's rows are saved ("uploading" / "publishing"), so if n8n crashes half-way the post is never
// picked again by itself. It is reported as stuck instead, and the owner decides (/retry).
const s = $('⚙️ Settings').first().json;
const zone = zoneOf(s);
const now = $now.toMillis();
const hours = (v, d) => (isNaN(num(v)) ? d : Math.max(0, num(v)));
const maxLate = hours(s.max_late_hours, 12) * 3600e3;
const stuckAfter = hours(s.stuck_minutes, 30) * 60e3;
const graph = String(s.graph_api || 'https://graph.facebook.com/v25.0').trim().replace(/\/+$/, '');
const igUser = String(s.ig_user_id || '').trim();
const posts = foldPosts(rowsOf('Load posts'))
  .filter(p => p.status === 'approved' && !isNaN(ms(p.post_at)))
  .sort((a, b) => ms(a.post_at) - ms(b.post_at));

const rows = [], alerts = [];
let yt = null, ig = null;
for (const p of posts) {
  const late = now - ms(p.post_at);                       // above 0 = the slot time has passed
  const lateText = `Its slot (${when(p.post_at, zone)}) passed ${Math.round(late / 3600e3)} hours ago`;

  // YouTube: upload right after approval. The video stays private and YouTube publishes it at the slot time.
  if (p.yt_status === 'queued') {
    if (late > maxLate) {
      rows.push(postRow(p.post_id, { yt_status: 'late', note: `YouTube: not uploaded, ${lateText}` }));
      alerts.push(`⏰ YouTube: ${p.post_id} was NOT uploaded. ${lateText}, probably because n8n was off.\nSend /retry ${p.post_id} to post it now, or /reject ${p.post_id} to drop it.`);
    } else if (!yt) {
      rows.push(postRow(p.post_id, { yt_status: 'uploading' }));
      // never less than 15 minutes ahead, so YouTube always gets a publish time in the future
      yt = { post_id: p.post_id, video_url: p.video_url, title: p.yt_title, description: p.yt_description, ai: p.ai === 'yes' ? 'yes' : 'no',
             publish_at: DateTime.fromMillis(Math.max(ms(p.post_at), now + 15 * 60e3)).toUTC().toISO() };
    }
  } else if (p.yt_status === 'uploading' && now - ms(p.yt_since) > stuckAfter) {
    rows.push(postRow(p.post_id, { yt_status: 'stuck', note: 'YouTube: the upload did not finish' }));
    alerts.push(`❓ YouTube: the upload of ${p.post_id} did not finish (n8n may have restarted).\nOpen YouTube Studio → Content. If the video is not there, send /retry ${p.post_id}.`);
  }

  // Instagram: publish when the slot time has come, but not if it is more than max_late_hours late.
  if (p.ig_status === 'queued' && late >= 0) {
    if (late > maxLate) {
      rows.push(postRow(p.post_id, { ig_status: 'late', note: `Instagram: not posted, ${lateText}` }));
      alerts.push(`⏰ Instagram: ${p.post_id} was NOT posted. ${lateText}, probably because n8n was off.\nSend /retry ${p.post_id} to post it now, or /reject ${p.post_id} to drop it.`);
    } else if (!/^\d+$/.test(igUser)) {
      rows.push(postRow(p.post_id, { ig_status: 'failed', note: 'Instagram: ig_user_id is missing in the Settings of workflow 08' }));
      alerts.push(`❌ Instagram: ${p.post_id} was not posted. The Instagram account ID is missing: open workflow 08 → ⚙️ Settings → ig_user_id (SOCIAL-SETUP.md, part 3). Then send /retry ${p.post_id}.`);
    } else if (!ig) {
      rows.push(postRow(p.post_id, { ig_status: 'publishing' }));
      const ai = p.ai === 'yes';
      ig = { post_id: p.post_id, ai: ai ? 'yes' : 'no', graph,
             create_url: `${graph}/${igUser}/media`, publish_url: `${graph}/${igUser}/media_publish`,
             // is_ai_generated puts Instagram's AI label on the Reel; it is only sent when the video has AI in it
             query: { media_type: 'REELS', video_url: p.video_url, caption: p.caption_instagram, share_to_feed: 'true',
                      ...(ai ? { is_ai_generated: 'true' } : {}) } };
    }
  } else if (p.ig_status === 'publishing' && now - ms(p.ig_since) > stuckAfter) {
    rows.push(postRow(p.post_id, { ig_status: 'stuck', note: 'Instagram: posting did not finish' }));
    alerts.push(`❓ Instagram: posting ${p.post_id} did not finish (n8n may have restarted).\nOpen Instagram. If the Reel is not there, send /retry ${p.post_id}.`);
  }
}
if (!rows.length) return [];   // nothing to do in this run
return [{ json: { rows, alerts: alerts.map(esc), yt, ig } }];
"""

YT_UPLOADED_JS = JS_RULES + JS_POSTS + r"""
// Did the upload work? If the video has AI in it, prepare the "altered or synthetic content" declaration.
// videos.update replaces the whole "status" part: whatever is not sent again falls back to YouTube's default
// (a missing privacyStatus would make the video public). So everything set at upload is sent again.
const job = $('YouTube job').first().json;
const up = $input.first().json || {};
const video_id = String(up.uploadId || up.id || '');
if (!video_id) {
  // none: the file never reached YouTube (the download failed, so the upload never started). Any other failure is
  // not proof that nothing arrived: n8n sends the file in chunks and the call can fail after the last chunk.
  const dl = apiError($('Download video').first().json);
  return [{ json: { ok: false, declare: false, none: !!dl, reason: dl ? `the video file could not be downloaded (${dl})` : (apiError(up) || 'YouTube did not return a video id') } }];
}
return [{ json: { ok: true, declare: job.ai === 'yes', video_id, update: { id: video_id, status: {
  privacyStatus: 'private', publishAt: job.publish_at, selfDeclaredMadeForKids: false,
  embeddable: true, license: 'youtube', publicStatsViewable: true, containsSyntheticMedia: true } } } }];
"""

YT_RESULT_JS = JS_RULES + JS_POSTS + r"""
// One row for the table and one message for the owner.
const zone = zoneOf($('⚙️ Settings').first().json);
const job = $('YouTube job').first().json;
const up = $('YouTube uploaded?').first().json;
if (!up.ok) {
  // "failed" does not prove that nothing is on YouTube, so the owner is asked to look before a retry makes a second copy
  const text = up.none
    ? `❌ YouTube: ${job.post_id} was not uploaded: ${up.reason}\n\nNothing is on YouTube. Instagram and TikTok are not affected.\nFix it, then send /retry ${job.post_id}`
    : `❌ YouTube: the upload of ${job.post_id} failed: ${up.reason}\n\nThe upload failed. Check YouTube Studio before you retry: the video may still be there.\nInstagram and TikTok are not affected.\nNot there? Fix the problem, then send /retry ${job.post_id}`;
  return [{ json: { row: postRow(job.post_id, { yt_status: 'failed', note: `YouTube: ${up.reason}`.slice(0, 300) }), text: esc(text) } }];
}
const lines = [`📺 YouTube: ${job.post_id} is uploaded. It is private now and goes public ${when(job.publish_at, zone)} (${zone}).`,
               `Check it: https://studio.youtube.com/video/${up.video_id}/edit`];
let note = '';
if (up.declare) {
  // the answer to the declaration call comes in as this node's input
  const st = ($input.first().json || {}).status || {};
  if (st.containsSyntheticMedia === true) lines.push('AI label: set (Altered content = Yes).');
  else {
    note = 'YouTube: AI label not confirmed';
    lines.push(`⚠️ AI label: YouTube did not confirm it${apiError($input.first().json) ? ' (' + apiError($input.first().json) + ')' : ''}. Open the link → Show more → Altered content → Yes.`);
  }
  if (st.privacyStatus && st.privacyStatus !== 'private') lines.push(`⚠️ YouTube shows it as "${st.privacyStatus}", not as a private scheduled video. Check it now.`);
}
return [{ json: { row: postRow(job.post_id, { yt_status: 'scheduled', yt_video_id: up.video_id, note }), text: esc(lines.join('\n')) } }];
"""

CONTAINER_STATUS_JS = r"""
// Instagram fetches and converts the video first. Ask every 30 seconds, for at most 10 minutes.
const r = $input.first().json || {};
const code = String(r.status_code || '');
if (code === 'FINISHED') return [{ json: { state: 'done' } }];
if (code === 'PUBLISHED') return [{ json: { state: 'error', sure: false, reason: 'Instagram says this video is already published' } }];
if (code === 'ERROR' || code === 'EXPIRED')
  return [{ json: { state: 'error', sure: true, reason: `Instagram could not use the video (${code}${r.status ? ': ' + r.status : ''}). Check that the link opens without logging in and that it is a vertical MP4.` } }];
if ($runIndex + 1 >= 20) return [{ json: { state: 'error', sure: true, reason: 'Instagram was still working on the video after 10 minutes' } }];
return [{ json: { state: 'wait' } }];
"""

IG_RECHECK_JS = JS_RULES + JS_POSTS + r"""
// The last look before the Reel is published. From "Plan this run" to here can lie many minutes (Instagram converts
// the video first, and the wait loop allows 10 minutes). In that time the owner may have tapped Reject, or a later
// run may have reported this post as stuck. So the post is read from the table again, and the Reel is only
// published while the post is still approved and still marked "publishing" by this very run.
const job = $('Instagram job').first().json;
const p = foldPosts(rowsOf('Reload post (Instagram)')).find(x => x.post_id === job.post_id);
if (p && p.status === 'approved' && p.ig_status === 'publishing') return [{ json: { ok: true } }];
if (!p) return [{ json: { ok: false, rejected: false, reason: 'the post could not be read again before it was published' } }];
if (p.status !== 'approved') {
  const rejected = p.status === 'rejected';
  return [{ json: { ok: false, rejected, reason: rejected ? 'you rejected it before it went out' : `its status changed to "${p.status}" before it went out` } }];
}
return [{ json: { ok: false, rejected: false, reason: `its Instagram status changed to "${p.ig_status || 'empty'}" while the video was being prepared` } }];
"""

IG_RESULT_JS = JS_RULES + JS_POSTS + r"""
// One row for the table and one message for the owner. A post only counts as published when Instagram
// returned a media id. If the publish call itself got no clear answer, nobody knows whether the Reel went
// out: the post is marked "stuck" and the owner looks, so it can never go out twice by itself.
const job = $('Instagram job').first().json;
const made = $('Instagram: create container').first().json || {};
const ready = $('Container status').isExecuted ? $('Container status').first().json : null;
const recheck = $('Check post again (Instagram)').isExecuted ? $('Check post again (Instagram)').first().json : null;
const pub = $('Instagram: publish').isExecuted ? ($('Instagram: publish').first().json || {}) : null;
if (recheck && recheck.ok === false) {
  // Not published on purpose (see "Check post again (Instagram)"). A rejected post is closed here. In every other case
  // the status stays as whoever changed it set it, and only a note is added to the log.
  return [{ json: {
    row: postRow(job.post_id, { ...(recheck.rejected ? { ig_status: 'cancelled' } : {}), note: `Instagram: not posted, ${recheck.reason}`.slice(0, 300) }),
    text: esc(`🚫 Instagram: ${job.post_id} was not posted: ${recheck.reason}.\n\nNothing is on Instagram.`) } }];
}
const failed = (status, reason, next) => [{ json: {
  row: postRow(job.post_id, { ig_status: status, note: `Instagram: ${reason}`.slice(0, 300) }),
  text: esc(`${status === 'stuck' ? '❓' : '❌'} Instagram: ${job.post_id} ${status === 'stuck' ? 'may not have been posted' : 'was not posted'}: ${reason}\n\n${next}`) } }];
const retry = `Nothing is on Instagram. Fix it, then send /retry ${job.post_id}`;
if (!made.id) return failed('failed', apiError(made) || 'Instagram did not accept the video', retry);
if (!pub) {
  const why = (ready && ready.reason) || 'the video was not ready';
  return ready && ready.sure === false
    ? failed('stuck', why, `Open Instagram and look. If the Reel is not there, send /retry ${job.post_id}`)
    : failed('failed', why, retry);
}
if (!pub.id) return failed('stuck', apiError(pub) || 'the publish call got no answer',
  `Open Instagram and look. If the Reel is not there, send /retry ${job.post_id}`);
const link = $('Instagram: get link').isExecuted ? ($('Instagram: get link').first().json || {}).permalink : '';
const lines = [`📸 Instagram: ${job.post_id} is live.`];
if (link) lines.push(link);
if (job.ai === 'yes') lines.push('It was sent with the AI label. Please open the Reel once and check that it shows "AI info".');
return [{ json: { row: postRow(job.post_id, { ig_status: 'published', ig_media_id: String(pub.id) }), text: esc(lines.join('\n')) } }];
"""

PLAN_DAILY_JS = JS_RULES + JS_POSTS + r"""
// Evening run, before the Coach: which posts are older than 48 hours and still have no numbers?
const s = $('⚙️ Settings').first().json;
const now = $now.toMillis();
const after = (isNaN(num(s.stats_after_hours)) ? 48 : num(s.stats_after_hours)) * 3600e3;
const posts = foldPosts(rowsOf('Load posts')).filter(p => p.status === 'approved' && !isNaN(ms(p.post_at)));
const due = posts.filter(p => p.stats_done !== 'yes' && now - ms(p.post_at) >= after)
  .sort((a, b) => ms(a.post_at) - ms(b.post_at)).slice(0, 10);
const got = p => String(p.stats_done || '').split(',');

// A login is only checked every day while the bot really posts on that platform (a post in the last 30 days)
const BOT = ['queued', 'uploading', 'scheduled', 'publishing', 'published', 'failed', 'stuck', 'late'];
const fresh = posts.filter(p => now - ms(p.post_at) < 30 * 86400e3);
const use_yt = fresh.some(p => BOT.includes(p.yt_status)), use_ig = fresh.some(p => BOT.includes(p.ig_status));

// The Instagram token from SOCIAL-SETUP.md never runs out. If a token with an end date is used instead,
// its date is in Settings (ig_token_expires) and the owner is warned every evening from 14 days before.
let warn = '';
const end = DateTime.fromISO(String(s.ig_token_expires || '').trim(), { zone: 'utc', locale: 'en' });
if (end.isValid) {
  const days = Math.floor((end.toMillis() - now) / 86400e3);
  if (days < 0) warn = `🔑 The Instagram token ran out on ${end.toFormat('d LLL yyyy')}. Instagram posts will fail until you make a new one (SOCIAL-SETUP.md, part 2), paste it into n8n → Credentials → "Instagram (Pivendo)" and change ig_token_expires in workflow 08.`;
  else if (days <= 14) warn = `🔑 The Instagram token runs out in ${days} day(s), on ${end.toFormat('d LLL yyyy')}. Make a new one now (SOCIAL-SETUP.md, part 2), paste it into n8n → Credentials → "Instagram (Pivendo)" and change ig_token_expires in workflow 08.`;
}
// One YouTube request: the numbers of all due videos at once. With no video due, one small request for
// the owner's own channel, which only proves that the YouTube login still works.
const yt_ids = due.filter(p => p.yt_video_id && !got(p).includes('yt')).map(p => p.yt_video_id).join(',');
const youtube = 'https://www.googleapis.com/youtube/v3';
return [{ json: { due, use_yt, use_ig, warn, yt_call: yt_ids
  ? { url: `${youtube}/videos`, query: { part: 'statistics,status', id: yt_ids } }
  : { url: `${youtube}/channels`, query: { part: 'id', mine: 'true' } } } }];
"""

IG_CALLS_JS = JS_RULES + JS_POSTS + r"""
// One Instagram request per Reel that needs numbers. With no Reel due, one small request that only proves
// the token and the account ID still work. While ig_user_id is not filled in yet, that request asks Meta
// which Instagram account the token belongs to, so the owner can be told the ID to paste.
const s = $('⚙️ Settings').first().json;
const plan = $('Plan daily run').first().json;
const graph = String(s.graph_api || 'https://graph.facebook.com/v25.0').trim().replace(/\/+$/, '');
const igUser = String(s.ig_user_id || '').trim();
const calls = plan.due.filter(p => p.ig_media_id && !String(p.stats_done || '').split(',').includes('ig'))
  .map(p => ({ json: { post_id: p.post_id, url: `${graph}/${p.ig_media_id}/insights`, query: { metric: 'views,reach,likes,comments,shares,saved' } } }));
if (calls.length) return calls;
return [{ json: /^\d+$/.test(igUser)
  ? { post_id: '', url: `${graph}/${igUser}`, query: { fields: 'username' } }
  : { post_id: '', url: `${graph}/me/accounts`, query: { fields: 'name,instagram_business_account{id,username}' } } }];
"""

STATS_JS = JS_RULES + JS_POSTS + r"""
// Turn the answers into rows: feedback rows in the same shape /video writes (the Coach reads them at 21:30
// without any change), one content row per video so the Coach can join them, and "stats_done" on the post.
const s = $('⚙️ Settings').first().json;
const zone = zoneOf(s);
const plan = $('Plan daily run').first().json;
const day = $now.toFormat('yyyy-MM-dd');
const now = $now.toMillis();
const yt = $('YouTube: read stats').first().json || {};
const calls = $('Instagram calls').all().map(i => i.json);
const answers = $input.all().map(i => i.json || {});
const ytOk = Array.isArray(yt.items) || /^youtube#/.test(String(yt.kind || ''));
const ytById = Object.fromEntries((yt.items || []).map(v => [v.id, v]));
const igByPost = {};
calls.forEach((c, i) => { if (c.post_id) igByPost[c.post_id] = answers[i] || {}; });
const igOk = answers.some(r => r.username || Array.isArray(r.data));
const metric = (r, name) => {
  const m = (Array.isArray(r.data) ? r.data : []).find(x => x.name === name);
  const v = m ? (m.values?.[0]?.value ?? m.total_value?.value) : null;
  return v === null || v === undefined || isNaN(Number(v)) ? null : Number(v);
};
const n = v => Number(v) || 0;
const giveUp = (isNaN(num(s.stats_after_hours)) ? 48 : num(s.stats_after_hours)) * 3600e3 + 7 * 86400e3;

const sent = new Set(rowsOf('Load feedback').filter(f => f.kind === 'video').map(f => String(f.ref)));
const feedback = [], videos = [], rows = [], lines = [];
for (const p of plan.due) {
  const got = new Set(String(p.stats_done || '').split(',').filter(t => t === 'yt' || t === 'ig'));
  const first = !p.stats_done;
  const parts = [];
  const save = (tag, name, views, detail) => {
    feedback.push({ day, kind: 'video', ref: `${p.post_id}-${tag}`, views, clicks: 0, sales: 0, status: '',
                    note: `${name} after 48 h, slot ${p.slot || 'unknown'}: ${detail} (read by the bot; link clicks and sales are not known)` });
    videos.push(contentRow(p, tag, zone, true));
    got.add(tag);
    parts.push(`${name} ${views} views`);
  };
  if (p.yt_video_id && !got.has('yt')) {
    const v = ytById[p.yt_video_id];
    if (v && v.statistics) {
      save('yt', 'YouTube', n(v.statistics.viewCount), `${n(v.statistics.likeCount)} likes, ${n(v.statistics.commentCount)} comments`);
      if (v.status && v.status.privacyStatus !== 'public') parts.push(`⚠️ YouTube still shows it as "${v.status.privacyStatus}", not public: check it in YouTube Studio`);
    } else if (ytOk) { got.add('yt'); parts.push('YouTube: video not found (deleted?)'); }
    else parts.push('YouTube: numbers not readable today');
  }
  if (p.ig_media_id && !got.has('ig')) {
    const r = igByPost[p.post_id] || {};
    const views = metric(r, 'views');
    if (views !== null) save('ig', 'Instagram', views, `${n(metric(r, 'likes'))} likes, ${n(metric(r, 'comments'))} comments, ${n(metric(r, 'shares'))} shares, ${n(metric(r, 'saved'))} saves, reach ${n(metric(r, 'reach'))}`);
    else parts.push(`Instagram: numbers not readable today${apiError(r) ? ' (' + apiError(r) + ')' : ''}`);
  }
  const need = [p.yt_video_id && 'yt', p.ig_media_id && 'ig'].filter(Boolean);
  const value = need.every(t => got.has(t)) || now - ms(p.post_at) > giveUp ? 'yes' : ([...got].join(',') || 'tried');
  if (value !== p.stats_done) rows.push(postRow(p.post_id, { stats_done: value }));
  // What only the owner can report (asked once per post; after that the Coach's own reminder takes over)
  const mine = [];
  if (first) for (const [field, tag, name, command] of [['tiktok_status', 'tt', 'TikTok', 'tiktok'], ['yt_status', 'yt', 'YouTube', 'youtube'], ['ig_status', 'ig', 'Instagram', 'instagram']]) {
    if (p[field] === 'done' && sent.has(`${p.post_id}-${tag}`)) continue;   // the owner already sent these numbers
    if (p[field] === 'done') mine.push(`${name}: send /video ${p.post_id}-${tag} <views> <link clicks> <sales>`);
    else if (p[field] === 'todo') mine.push(`${name}: not marked as posted. Posted it? Send /${command} ${p.post_id} done`);
  }
  if (parts.length || mine.length) lines.push(`• ${p.post_id} ${p.product || p.sku || ''}: ${parts.join(', ') || 'no numbers from the bot'}` + mine.map(t => '\n  ' + t).join(''));
}

// "Gets better with time": the best and the weakest video by views among the numbers of the last 7 days
// (the bot's own and the ones the owner sent with /video), with platform and slot. The bot never changes
// the posting times by itself: a better time is a rule the Coach proposes and the owner approves.
const NAME = { yt: 'YouTube', ig: 'Instagram', tt: 'TikTok' };
const weekAgo = $now.minus({ days: 6 }).toFormat('yyyy-MM-dd');
const postById = Object.fromEntries(foldPosts(rowsOf('Load posts')).map(p => [p.post_id, p]));
const latest = {};
for (const f of [...rowsOf('Load feedback'), ...feedback]) {
  const m = String(f.ref || '').match(/^(.+)-(yt|ig|tt)$/);
  if (f.kind === 'video' && m && postById[m[1]] && String(f.day) >= weekAgo) latest[f.ref] = { p: postById[m[1]], tag: m[2], views: Number(f.views) || 0 };
}
const ranked = Object.values(latest).sort((a, b) => b.views - a.views);
const medal = x => {
  const at = DateTime.fromISO(String(x.p.post_at || ''), { zone });
  return `${x.p.post_id} on ${NAME[x.tag]}, ${x.views} views, slot ${x.p.slot || 'unknown'}${at.isValid ? ` (${at.toFormat('HH:mm')} in ${zone})` : ''}`;
};
if (lines.length && ranked.length >= 2) lines.push(`🏆 Last 7 days: best ${medal(ranked[0])}. Weakest ${medal(ranked[ranked.length - 1])}.`);

const problems = [];
// Setup help, like the chat ID in workflow 02: while ig_user_id is empty, tell the owner which ID to paste
if (!/^\d+$/.test(String(s.ig_user_id || '').trim())) {
  const pages = answers.flatMap(r => (Array.isArray(r.data) ? r.data : [])).filter(a => a && a.name !== undefined && !a.values);
  const accounts = pages.map(a => a.instagram_business_account).filter(a => a && a.id);
  if (accounts.length) problems.push(`🆔 Your Instagram account ID is ${accounts.map(a => a.id + (a.username ? ` (@${a.username})` : '')).join(' or ')}\nPaste it into workflow 08 → ⚙️ Settings → ig_user_id, then save.`);
  else if (pages.length) problems.push(`🆔 The Instagram token works, but the Facebook Page "${pages[0].name}" has no Instagram account linked to it. Link them (SOCIAL-SETUP.md, part 2, step 2), then run workflow 08 again.`);
}
if (plan.use_yt && !ytOk) problems.push(`🔑 YouTube did not answer the daily check: ${apiError(yt) || 'no answer'}\nIf this comes again tomorrow: n8n → Credentials → "YouTube (Pivendo)" → Sign in with Google again.`);
if (plan.use_ig && !igOk) problems.push(`🔑 Instagram did not answer the daily check: ${apiError(answers[0]) || 'no answer'}\nIf it says the token is invalid or expired: make a new one (SOCIAL-SETUP.md, part 2) and paste it into n8n → Credentials → "Instagram (Pivendo)".`);
if (plan.warn) problems.push(plan.warn);
const text = [lines.length ? '📈 Video numbers after 48 hours (the coach reads them tonight)\n' + lines.join('\n') : '', ...problems]
  .filter(Boolean).join('\n\n');
return [{ json: { feedback, videos, rows, text: esc(text.slice(0, 3900)) } }];
"""


def api(wf, name, method, url, cred, pos, query=None, json_query=None, json_body=None, **extra):
    """One call to the YouTube or Instagram API with the credential the owner made in n8n.
    An API error does not stop the workflow: the answer (or the error) goes on to the next Code node,
    which writes the reason into the table and tells the owner."""
    params = {"method": method, "url": url, "authentication": "predefinedCredentialType", "nodeCredentialType": cred}
    if query:
        params.update(sendQuery=True, queryParameters={"parameters": [{"name": k, "value": v} for k, v in query]})
    if json_query:
        params.update(sendQuery=True, specifyQuery="json", jsonQuery=json_query)
    if json_body:
        params.update(sendBody=True, specifyBody="json", jsonBody=json_body)
    params["options"] = {"response": {"response": {"neverError": True}}}
    return wf.add(name, "n8n-nodes-base.httpRequest", 4.2, params, pos, onError="continueRegularOutput", **extra)


YOUTUBE = "youTubeOAuth2Api"    # n8n credential "YouTube (Pivendo)"
INSTAGRAM = "facebookGraphApi"  # n8n credential "Instagram (Pivendo)": a Meta system-user token that never expires


def build_social():
    wf = Workflow("08 · Social publisher")
    wf.add("Every 10 minutes", "n8n-nodes-base.scheduleTrigger", 1.2,
           {"rule": {"interval": [{"field": "cronExpression", "expression": "*/10 * * * *"}]}}, [0, 0])
    wf.add("Every evening 21:00", "n8n-nodes-base.scheduleTrigger", 1.2,
           {"rule": {"interval": [{"field": "cronExpression", "expression": "0 21 * * *"}]}}, [0, 200])
    settings(wf, [
        ("telegram_chat_id", "PASTE_YOUR_TELEGRAM_CHAT_ID"),
        ("ig_user_id", "PASTE_YOUR_INSTAGRAM_ACCOUNT_ID"),
        ("ig_token_expires", "never"),
        ("graph_api", "https://graph.facebook.com/v25.0"),
        ("max_late_hours", 12),
        ("stuck_minutes", 30),
        ("stats_after_hours", 48),
        ("time_zone", "Europe/Berlin"),
    ], [220, 100])
    table_get(wf, "Load posts", "social_posts", [440, 100])
    if_true(wf, "Daily run?", "={{ $('Every evening 21:00').isExecuted }}", [660, 100])
    wf.chain("Every 10 minutes", "⚙️ Settings", "Load posts", "Daily run?")
    wf.connect("Every evening 21:00", "⚙️ Settings")

    # ---- every 10 minutes: mark first, then call the platforms
    code(wf, "Plan this run", PLAN_RUN_JS, [880, 300])
    code(wf, "Mark rows", "return $input.first().json.rows.map(r => ({ json: r }));", [1100, 300])
    table_insert(wf, "Save marks", "social_posts", [1320, 300])
    code(wf, "Alerts", "return $('Plan this run').first().json.alerts.map(text => ({ json: { text } }));", [1540, 160])
    # A Telegram message that cannot be sent must never stop the posting branches that come after it, so every
    # Telegram node in this workflow continues on error. "Save marks" is the opposite on purpose: no error setting,
    # so if the marks cannot be saved the run stops and nothing is sent to YouTube or Instagram.
    telegram(wf, "Send alerts", "={{ $json.text }}", [1760, 160], html=True, onError="continueRegularOutput")
    wf.connect("Daily run?", "Plan this run", out=1)
    wf.chain("Plan this run", "Mark rows", "Save marks", "Alerts", "Send alerts")

    # YouTube: the built-in node uploads the file as a private video with a publish time ("not made for kids").
    # It cannot set the AI declaration, so that is one more API call with the same credential.
    code(wf, "YouTube job", "const j = $('Plan this run').first().json.yt;\nreturn j ? [{ json: j }] : [];", [1540, 400])
    wf.add("Download video", "n8n-nodes-base.httpRequest", 4.2, {
        "url": "={{ $json.video_url }}",
        "options": {"response": {"response": {"responseFormat": "file"}}, "timeout": 300000},
    }, [1760, 400], onError="continueRegularOutput")
    wf.add("YouTube: upload", "n8n-nodes-base.youTube", 1, {
        "resource": "video",
        "operation": "upload",
        "title": "={{ $('YouTube job').first().json.title }}",
        "regionCode": "US",
        "categoryId": "22",
        "binaryProperty": "data",
        "options": {
            "description": "={{ $('YouTube job').first().json.description }}",
            "privacyStatus": "private",
            "publishAt": "={{ $('YouTube job').first().json.publish_at }}",
            "selfDeclaredMadeForKids": False,
            "notifySubscribers": True,
        },
    }, [1980, 400], onError="continueRegularOutput")
    code(wf, "YouTube uploaded?", YT_UPLOADED_JS, [2200, 400])
    if_true(wf, "Declare AI content?", "={{ $json.declare }}", [2420, 400])
    api(wf, "YouTube: declare AI content", "PUT", "https://www.googleapis.com/youtube/v3/videos", YOUTUBE, [2640, 340],
        query=[("part", "status")], json_body="={{ JSON.stringify($('YouTube uploaded?').first().json.update) }}")
    code(wf, "YouTube result", YT_RESULT_JS, [2860, 400])
    code(wf, "YouTube row", "return [{ json: $input.first().json.row }];", [3080, 400])
    table_insert(wf, "Save YouTube result", "social_posts", [3300, 400])
    telegram(wf, "Tell owner (YouTube)", "={{ $('YouTube result').first().json.text }}", [3520, 400], html=True,
             onError="continueRegularOutput")
    wf.connect("Save marks", "YouTube job")
    wf.chain("YouTube job", "Download video", "YouTube: upload", "YouTube uploaded?", "Declare AI content?",
             "YouTube: declare AI content", "YouTube result", "YouTube row", "Save YouTube result", "Tell owner (YouTube)")
    wf.connect("Declare AI content?", "YouTube result", out=1)

    # Instagram: container (Meta fetches the video from its public link) -> wait until it is ready -> publish
    job = "$('Instagram job').first().json"
    code(wf, "Instagram job", "const j = $('Plan this run').first().json.ig;\nreturn j ? [{ json: j }] : [];", [1540, 700])
    api(wf, "Instagram: create container", "POST", "={{ $json.create_url }}", INSTAGRAM, [1760, 700],
        json_query="={{ JSON.stringify($json.query) }}")
    if_true(wf, "Container created?", "={{ !!$json.id }}", [1980, 700])
    wait(wf, "Wait 30s", 30, [2200, 640])
    api(wf, "Instagram: check container", "GET",
        "={{ %s.graph }}/{{ $('Instagram: create container').first().json.id }}" % job, INSTAGRAM, [2420, 640],
        query=[("fields", "status_code,status")])
    code(wf, "Container status", CONTAINER_STATUS_JS, [2640, 640])
    switch(wf, "Container ready?", "state", ["done", "wait", "error"], [2860, 640])
    # The last look before the Reel goes out: the post is read from the table again, because the owner may have
    # tapped Reject while Instagram was converting the video (this loop can take up to 10 minutes).
    table_get(wf, "Reload post (Instagram)", "social_posts", [3080, 580])
    code(wf, "Check post again (Instagram)", IG_RECHECK_JS, [3300, 580])
    if_true(wf, "Still approved? (Instagram)", "={{ $json.ok }}", [3520, 580])
    api(wf, "Instagram: publish", "POST", "={{ %s.publish_url }}" % job, INSTAGRAM, [3740, 520],
        query=[("creation_id", "={{ $('Instagram: create container').first().json.id }}")])
    api(wf, "Instagram: get link", "GET", "={{ %s.graph }}/{{ $json.id }}" % job, INSTAGRAM, [3960, 520],
        query=[("fields", "permalink")])
    code(wf, "Instagram result", IG_RESULT_JS, [4180, 700])
    code(wf, "Instagram row", "return [{ json: $input.first().json.row }];", [4400, 700])
    table_insert(wf, "Save Instagram result", "social_posts", [4620, 700])
    telegram(wf, "Tell owner (Instagram)", "={{ $('Instagram result').first().json.text }}", [4840, 700], html=True,
             onError="continueRegularOutput")
    wf.connect("Save marks", "Instagram job")
    wf.chain("Instagram job", "Instagram: create container", "Container created?", "Wait 30s",
             "Instagram: check container", "Container status", "Container ready?",
             "Reload post (Instagram)", "Check post again (Instagram)", "Still approved? (Instagram)",
             "Instagram: publish", "Instagram: get link", "Instagram result", "Instagram row",
             "Save Instagram result", "Tell owner (Instagram)")
    wf.connect("Still approved? (Instagram)", "Instagram result", out=1)
    wf.connect("Container created?", "Instagram result", out=1)
    wf.connect("Container ready?", "Wait 30s", out=1)
    wf.connect("Container ready?", "Instagram result", out=2)

    # ---- every evening at 21:00, half an hour before the Coach: numbers after 48 hours + login check
    table_get(wf, "Load feedback", "feedback", [880, -300])
    code(wf, "Plan daily run", PLAN_DAILY_JS, [1100, -300])
    api(wf, "YouTube: read stats", "GET", "={{ $json.yt_call.url }}", YOUTUBE, [1320, -300],
        json_query="={{ JSON.stringify($json.yt_call.query) }}")
    code(wf, "Instagram calls", IG_CALLS_JS, [1540, -300])
    api(wf, "Instagram: read stats", "GET", "={{ $json.url }}", INSTAGRAM, [1760, -300],
        json_query="={{ JSON.stringify($json.query) }}")
    code(wf, "Build stats", STATS_JS, [1980, -300])
    code(wf, "Feedback rows", "return $input.first().json.feedback.map(r => ({ json: r }));", [2200, -480])
    table_insert(wf, "Save stats as feedback", "feedback", [2420, -480])
    code(wf, "Video rows", "return $input.first().json.videos.map(r => ({ json: r }));", [2200, -360])
    table_insert(wf, "Save posts as videos", "content", [2420, -360])
    code(wf, "Stats done rows", "return $input.first().json.rows.map(r => ({ json: r }));", [2200, -240])
    table_insert(wf, "Mark stats done", "social_posts", [2420, -240])
    code(wf, "Daily summary", "const t = $input.first().json.text;\nreturn t ? [{ json: { text: t } }] : [];", [2200, -120])
    telegram(wf, "Send daily summary", "={{ $json.text }}", [2420, -120], html=True, onError="continueRegularOutput")
    wf.connect("Daily run?", "Load feedback", out=0)
    wf.chain("Load feedback", "Plan daily run", "YouTube: read stats", "Instagram calls", "Instagram: read stats", "Build stats")
    for rows_node, save_node in [("Feedback rows", "Save stats as feedback"), ("Video rows", "Save posts as videos"),
                                 ("Stats done rows", "Mark stats done"), ("Daily summary", "Send daily summary")]:
        wf.connect("Build stats", rows_node)
        wf.connect(rows_node, save_node)
    wf.save("08-social-publisher.json")


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
    build_social()
