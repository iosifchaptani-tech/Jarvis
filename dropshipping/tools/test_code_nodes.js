// Tests the JavaScript inside the generated n8n Code nodes with fake node outputs.
// Run: npm install luxon@3 && node test_code_nodes.js
const fs = require('fs');
const path = require('path');
const { DateTime } = require('luxon');

const DIR = path.join(__dirname, '..', 'n8n-workflows');
const load = f => JSON.parse(fs.readFileSync(path.join(DIR, f), 'utf8'));

async function run(file, nodeName, outputs, inputItems) {
  const wf = load(file);
  const node = wf.nodes.find(n => n.name === nodeName);
  if (!node) throw new Error(`no node ${nodeName} in ${file}`);
  const $ = name => {
    if (!(name in outputs)) throw new Error(`test missing output for $('${name}')`);
    const items = outputs[name].map(json => ({ json }));
    return { all: () => items, first: () => items[0], item: items[0] };
  };
  const $input = { all: () => inputItems.map(json => ({ json })), first: () => ({ json: inputItems[0] }) };
  const fn = new Function('$', '$input', '$now', 'return (async () => {' + node.parameters.jsCode + '})()');
  const result = await fn($, $input, DateTime.now());
  if (!Array.isArray(result)) throw new Error(`${nodeName} did not return an array`);
  return result.map(r => r.json);
}

let failures = 0;
async function test(name, f) {
  try { await f(); console.log('ok  ', name); }
  catch (e) { failures++; console.log('FAIL', name, '\n     ', e.stack.split('\n').slice(0, 3).join('\n      ')); }
}
const assert = (c, msg) => { if (!c) throw new Error(msg); };

const today = DateTime.now().toFormat('yyyy-MM-dd');
const playbook = [
  { rule_id: 'R001', agent: 'research', rule: 'cost <= 1/3 price', status: 'active', version: 1, evidence: '' },
  { rule_id: 'R004', agent: 'content', rule: 'hook shows problem', status: 'active', version: 1, evidence: '' },
  { rule_id: 'R004', agent: 'content', rule: 'hook shows problem', status: 'retired', version: 2, evidence: 'data' },
  { rule_id: 'R003', agent: 'research', rule: 'no batteries', status: 'active', version: 1, evidence: '' },
  { rule_id: 'R007', agent: 'content', rule: 'result first', status: 'rejected', version: 1, evidence: '' },
];
const research = '01-product-research.json';
const settings01 = { telegram_chat_id: '123', warehouse_country: 'US', min_cj_price: 2, max_cj_price: 15, min_stock: 50, markup: 3, min_profit_usd: 15, sell_countries: 'US,DE,CA,AU', intl_shipping_fee_usd: 7.99, min_country_profit_usd: 5 };
const cjList = { code: 200, result: true, data: { content: [{ productList: [
  { id: 'P1', nameEn: 'Silicone Sink Splash Guard', sku: 'CJ111', sellPrice: '4.20', nowPrice: '3.90', threeCategoryName: 'Kitchen', warehouseInventoryNum: 900, listedNum: 120, bigImage: 'http://x/1.jpg' },
  { id: 'P2', nameEn: 'Kids Toy Car', sku: 'CJ222', sellPrice: '5', threeCategoryName: 'Toys' },
  { id: 'P3', nameEn: 'Magnetic Cable Organizer', sku: 'CJ333', sellPrice: '2.10 -- 3.50', threeCategoryName: 'Desk', warehouseInventoryNum: 300, listedNum: 40 },
  { id: 'P4', nameEn: 'Portable Power Bank 10000mAh', sku: 'CJ444', sellPrice: '8' },
  { id: 'P5', nameEn: 'Pet Hair Remover Roller', sku: 'CJ555', sellPrice: '6.5', threeCategoryName: 'Pet', warehouseInventoryNum: 80, listedNum: 900 },
] }] } };

(async () => {
  let brief, picks, priced;
  await test('01 Build research brief filters + prompts', async () => {
    [brief] = await run(research, 'Build research brief', {
      '⚙️ Settings': [settings01], 'CJ: trending products': [cjList],
      'Load past products': [{ pid: 'P5', sku: 'CJ555', name: 'Pet Hair Remover', cj_cost: 6.5, ship_cost: 5, sell_price: 34.99, score: 70, status: 'idea', prediction: '800 views' }],
      'Load feedback': [{ kind: 'product', ref: 'cj555', status: 'killed', note: '30 videos no carts' }],
      'Load playbook': playbook,
    }, []);
    const pids = brief.candidates.map(c => c.pid);
    assert(JSON.stringify(pids) === '["P1","P3"]', 'unexpected candidates ' + pids);
    assert(brief.candidates[1].cost === 2.1, 'range price parse ' + brief.candidates[1].cost);
    assert(brief.prompt.includes('killed - 30 videos no carts'), 'history missing');
    assert(brief.prompt.includes('[R001]') && !brief.prompt.includes('[R004]'), 'rules wrong');
  });
  await test('01 Build research brief with empty tables', async () => {
    const [b] = await run(research, 'Build research brief', {
      '⚙️ Settings': [settings01], 'CJ: trending products': [cjList],
      'Load past products': [{}], 'Load feedback': [{}], 'Load playbook': [{}],
    }, []);
    assert(b.prompt.includes('- none yet') && b.prompt.includes('(no rules yet)'), 'empty handling');
  });
  await test('01 CJ error is reported', async () => {
    let msg = '';
    try { await run(research, 'Build research brief', { '⚙️ Settings': [settings01], 'CJ: trending products': [{ code: 1600001, message: 'Invalid API key' }], 'Load past products': [{}], 'Load feedback': [{}], 'Load playbook': [{}] }, []); }
    catch (e) { msg = e.message; }
    assert(msg.includes('Invalid API key'), 'no error: ' + msg);
  });
  await test('01 Parse picks (fenced JSON, unknown pid dropped)', async () => {
    picks = await run(research, 'Parse picks', {
      'Research agent': [{ output: 'Here you go:\n```json\n{"picks":[{"pid":"P3","score":81,"why":"w","angle":"a","target_buyer":"t","risks":"r","prediction":"p"},{"pid":"ZZ","score":1},{"pid":"P1","score":60,"why":"w2"}]}\n```' }],
      'Build research brief': [brief],
    }, []);
    assert(picks.length === 2 && picks[0].pid === 'P3' && picks[0].name === 'Magnetic Cable Organizer', 'picks ' + JSON.stringify(picks));
  });
  const details01 = [
    { code: 200, data: { variants: [{ vid: 'V3', variantSku: 'CJ333-BK', variantSellPrice: 2.4,
      inventories: [{ countryCode: 'US', totalInventory: 500 }, { countryCode: 'CN', totalInventory: 9000 }, { countryCode: 'DE', totalInventory: 0 }] }] } },
    { error: 'timeout' },
  ];
  let routes;
  await test('01 Plan shipping routes (local stock, EU only from EU, no data -> fallbacks)', async () => {
    routes = await run(research, 'Plan shipping routes', { '⚙️ Settings': [settings01], 'Parse picks': picks }, details01);
    const r = routes.map(x => `${x.pick_index}:${x.dest}<${x.start}`).join(' ');
    // pick 0: US stock -> US; DE has no EU stock -> no route; CA, AU -> China. pick 1: no stock data -> US from US, DE none, CA/AU from CN
    assert(r === '0:US<US 0:CA<CN 0:AU<CN 1:US<US 1:CA<CN 1:AU<CN', 'routes ' + r);
    assert(routes[0].vid === 'V3' && routes[3].vid === '', 'vid ' + JSON.stringify(routes));
    const [fr] = await run(research, 'Plan shipping routes', { '⚙️ Settings': [settings01], 'Parse picks': [picks[0]] },
      [{ code: 200, data: { variants: [{ vid: 'V9', inventories: [{ countryCode: 'FR', totalInventory: 20 }, { countryCode: 'US', totalInventory: 5 }] }] } }]).then(x => [x.find(y => y.dest === 'DE')]);
    assert(fr && fr.start === 'FR', 'EU stock in another EU country should ship DE orders: ' + JSON.stringify(fr));
  });
  await test('01 Price & margin per country (one freight call failed)', async () => {
    const q = (price, days = '3-5', name = 'USPS+') => ({ code: 200, data: [{ logisticName: name, logisticPrice: price, logisticAging: days }, { logisticName: 'Slow', logisticPrice: price + 2, logisticAging: '9-12' }] });
    priced = await run(research, 'Price & margin', {
      '⚙️ Settings': [settings01], 'Parse picks': picks, 'CJ: product details': details01, 'Plan shipping routes': routes,
    }, [q(5.1), q(6, '8-15', 'CJPacket'), q(30, '10-20', 'CJPacket'), { error: 'boom' }, q(6, '8-15'), q(6, '8-15')]);
    const a = priced[0];
    assert(a.sku === 'CJ333-BK' && a.ship_cost === 5.1 && a.ship_days === '3-5', 'freight ' + JSON.stringify(a));
    assert(a.sell_price === 22.99, 'price ' + a.sell_price);  // landed 7.5 -> max(22.5, 22.5)=22.5 -> ceil 23 -> 22.99
    assert(a.profit_per_order > 14 && a.profit_per_order < 15, 'profit ' + a.profit_per_order);
    const m = a.markets.split(' | ');
    assert(m[0].startsWith('US ✅') && m[0].includes('from US, 3-5 days'), 'US ' + m[0]);
    assert(m[1] === 'DE ❌ no stock in an EU warehouse', 'DE ' + m[1]);
    // CA: 22.99 + 7.99 - 2.4 - 6 - (30.98*0.029+0.30) = 21.38
    assert(m[2].startsWith('CA ✅ $21.38 profit') && m[2].includes('from CN'), 'CA ' + m[2]);
    assert(m[3].startsWith('AU ❌ $-2.62 profit'), 'AU ' + m[3]);
    assert(priced[1].ship_method.startsWith('unknown') && priced[1].cj_cost === 3.9, 'fallback ' + JSON.stringify(priced[1]));
    assert(priced[1].markets.startsWith('US ❌ no shipping quote') && priced[1].markets.includes('CA ✅'), 'markets 2 ' + priced[1].markets);
    const cols = fs.readFileSync(path.join(__dirname, '..', 'templates', 'products.csv'), 'utf8').split('\n')[0].trim();
    assert(Object.keys(a).join(',') === cols, 'columns ' + Object.keys(a).join(','));
  });
  await test('01 Price & margin with old settings (one market, no stock data)', async () => {
    const old = { telegram_chat_id: '123', warehouse_country: 'us', markup: 3, min_profit_usd: 15 };
    const r = await run(research, 'Plan shipping routes', { '⚙️ Settings': [old], 'Parse picks': [picks[0]] }, [{ code: 200, data: { variants: [{ vid: 'V3' }] } }]);
    assert(r.length === 1 && r[0].dest === 'US' && r[0].start === 'US', 'routes ' + JSON.stringify(r));
    const [p] = await run(research, 'Price & margin', { '⚙️ Settings': [old], 'Parse picks': [picks[0]], 'CJ: product details': [{ code: 200, data: { variants: [{ vid: 'V3', variantSellPrice: 2.4 }] } }], 'Plan shipping routes': r },
      [{ code: 200, data: [{ logisticName: 'USPS+', logisticPrice: 5.1, logisticAging: '3-5' }] }]);
    assert(p.sell_price === 22.99 && p.markets.startsWith('US ✅') && !p.markets.includes('|'), JSON.stringify(p));
  });
  await test('01 Telegram message', async () => {
    const [m] = await run(research, 'Write Telegram message', {}, priced);
    assert(m.text.includes('CJ SKU: CJ333-BK') && m.text.includes('/content SKU'), m.text);
    assert(m.text.includes('By country:\n  US ✅') && m.text.includes('  DE ❌ no stock in an EU warehouse') && m.text.includes('Markets'), m.text);
  });

  // ------------------------------------------------ 02 commands
  const cmds = '02-telegram-commands.json';
  const tg = (text, id = 123) => [{ message: { chat: { id }, text } }];
  await test('02 Parse command: routes, strangers, setup', async () => {
    const s = [{ telegram_chat_id: '123' }];
    let [r] = await run(cmds, 'Parse command', { '⚙️ Settings': s, 'Telegram message in': tg('/content CJ333-BK') }, []);
    assert(r.route === 'content' && r.args[0] === 'CJ333-BK', JSON.stringify(r));
    [r] = await run(cmds, 'Parse command', { '⚙️ Settings': s, 'Telegram message in': tg('/Video@MyBot V1 10 2 0') }, []);
    assert(r.route === 'video' && r.args.length === 4, JSON.stringify(r));
    [r] = await run(cmds, 'Parse command', { '⚙️ Settings': s, 'Telegram message in': tg('hello') }, []);
    assert(r.route === 'help', JSON.stringify(r));
    const stranger = await run(cmds, 'Parse command', { '⚙️ Settings': s, 'Telegram message in': tg('/rules', 999) }, []);
    assert(stranger.length === 0, 'stranger not ignored');
    [r] = await run(cmds, 'Parse command', { '⚙️ Settings': [{ telegram_chat_id: 'PASTE_YOUR_TELEGRAM_CHAT_ID' }], 'Telegram message in': tg('/start', 555) }, []);
    assert(r.route === 'setup' && r.chatId === '555', JSON.stringify(r));
  });
  let cbrief;
  await test('02 Build content brief learns from stats', async () => {
    [cbrief] = await run(cmds, 'Build content brief', {
      'Parse command': [{ route: 'content', args: ['cj333-bk'] }],
      'Load products': priced,
      'Load feedback': [{ kind: 'video', ref: 'V1', views: 5000, clicks: 40, sales: 2 }, { kind: 'video', ref: 'V2', views: 90, clicks: 0, sales: 0 }],
      'Load content history': [{ content_id: 'V1', hook: 'Result first', format: 'before-after' }, { content_id: 'V2', hook: 'Hey guys', format: 'other' }, { content_id: 'V3', hook: 'unmeasured' }],
      'Load playbook': playbook,
    }, []);
    assert(cbrief.found && cbrief.product.pid === 'P3', 'product not found');
    assert(cbrief.prompt.indexOf('"Result first"') < cbrief.prompt.indexOf('"Hey guys"'), 'ordering');
    assert(!cbrief.prompt.includes('unmeasured'), 'unmeasured leaked');
    assert(!cbrief.prompt.includes('[R004]') && !cbrief.prompt.includes('[R007]'), 'retired/rejected rule leaked');
  });
  await test('02 Build content brief: unknown SKU', async () => {
    const [b] = await run(cmds, 'Build content brief', { 'Parse command': [{ route: 'content', args: ['NOPE'] }], 'Load products': [{}], 'Load feedback': [{}], 'Load content history': [{}], 'Load playbook': [{}] }, []);
    assert(b.found === false && b.reply.includes('NOPE'), JSON.stringify(b));
  });
  let rows;
  const agentOut = { output: JSON.stringify({ listing: { title: 'T', bullets: ['a', 'b'], description: 'd', faq: [{ q: 'q?', a: 'a.' }] },
    videos: [1, 2, 3, 4, 5, 6].map(i => ({ format: 'problem-fix', hook: 'h' + i, shots: ['s1', 's2'], on_screen_text: ['t'], voiceover: 'v', caption: 'c', hashtags: ['#tiktokmademebuyit', 'gadget'] })) }) };
  await test('02 Parse content -> content table rows', async () => {
    rows = await run(cmds, 'Parse content', { 'Content agent': [agentOut], 'Build content brief': [cbrief] }, []);
    assert(rows.length === 5, 'len ' + rows.length);
    assert(rows[0].caption === 'c #tiktokmademebuyit #gadget', 'caption ' + rows[0].caption);
    assert(Object.keys(rows[0]).join(',') === 'day,content_id,sku,product,format,hook,shots,on_screen_text,voiceover,caption,rules_version', 'cols');
  });
  await test('02 Split into messages', async () => {
    const msgs = await run(cmds, 'Split into messages', { 'Content agent': [agentOut], 'Build content brief': [cbrief] }, rows);
    assert(msgs.length === 7 && msgs[1].text.includes('/render ' + rows[0].content_id) && msgs[6].text.includes('/clips CJ333-BK'), msgs[6].text);
  });
  await test('02 Build feedback: video + product + bad input', async () => {
    let [f] = await run(cmds, 'Build feedback', { 'Parse command': [{ route: 'video', args: ['V1', '1200', '14', '1', 'great', 'hook'] }] }, []);
    assert(f.valid && f.row.views === 1200 && f.row.note === 'great hook', JSON.stringify(f));
    [f] = await run(cmds, 'Build feedback', { 'Parse command': [{ route: 'product', args: ['CJ333', 'Killed', 'no', 'carts'] }] }, []);
    assert(f.valid && f.row.status === 'killed' && f.row.kind === 'product', JSON.stringify(f));
    [f] = await run(cmds, 'Build feedback', { 'Parse command': [{ route: 'video', args: ['V1', 'lots'] }] }, []);
    assert(!f.valid && f.reply.startsWith('Usage'), JSON.stringify(f));
  });
  await test('02 Format rules shows latest active only', async () => {
    const [m] = await run(cmds, 'Format rules', { 'Load rules': playbook }, []);
    assert(m.text.includes('R001') && m.text.includes('R003') && !m.text.includes('R004') && !m.text.includes('R007'), m.text);
  });


  const vScript = { content_id: 'V1', sku: 'CJ333-BK', hook: 'h', on_screen_text: 'My desk before | 5 seconds later | Fits any desk',
    voiceover: 'My desk was a cable jungle. Then I tried this. It snaps on in seconds! Every cable stays put. Link in bio.', caption: 'cap' };
  const vSettings = [{ voice: 'en-US-EmmaMultilingualNeural', cta_text: 'Link in bio' }];
  const cjPhotos = [{ code: 200, data: { bigImage: 'https://img/big.jpg', productImageSet: ['https://img/1.jpg', 'https://img/2.jpg', 'http://insecure/3.jpg'] } }];
  await test('02 Find video inputs: clips optional, product needed', async () => {
    let [v] = await run(cmds, 'Find video inputs', { 'Parse command': [{ args: ['V1'] }], 'Load scripts': [vScript],
      'Load clips': [{}], 'Load product photos': [{ sku: 'CJ333-BK', pid: 'P3', image: 'https://img/p.jpg' }] }, []);
    assert(v.ok && v.clips.length === 0 && v.pid === 'P3', JSON.stringify(v));
    [v] = await run(cmds, 'Find video inputs', { 'Parse command': [{ args: ['V1'] }], 'Load scripts': [vScript], 'Load clips': [{}], 'Load product photos': [{}] }, []);
    assert(!v.ok && v.reply.includes('/clips CJ333-BK'), JSON.stringify(v));
    [v] = await run(cmds, 'Find video inputs', { 'Parse command': [{ args: ['NOPE'] }], 'Load scripts': [vScript], 'Load clips': [{}], 'Load product photos': [{}] }, []);
    assert(!v.ok && v.reply.includes('NOPE'), JSON.stringify(v));
  });
  await test('02 Build video: no clips -> CJ photo slideshow with voice, text, captions', async () => {
    const inp = { ok: true, id: 'V1', script: vScript, clips: [], pid: 'P3', image: 'https://img/p.jpg' };
    const [v] = await run(cmds, 'Build video', { '⚙️ Settings': vSettings, 'Find video inputs': [inp], 'CJ: product photos': cjPhotos }, []);
    const sc = v.movie.scenes;
    assert(v.ok && v.mode === 'photos' && v.photos === 4 && sc.length === 4, JSON.stringify({ mode: v.mode, photos: v.photos, n: sc.length }));
    assert(sc.every(x => x.elements[0].type === 'image' && x.elements[0].src.startsWith('https://')), 'all scenes are https photos');
    assert(new Set(sc.map(x => x.elements[0].src)).size === 4, 'photos should rotate');
    assert(sc[0].elements[1].text === 'My desk before' && sc[3].elements[1].text === 'Link in bio', 'texts');
    const said = sc.map(x => x.elements.find(e => e.type === 'voice').text).join(' ');
    assert(said === vScript.voiceover, 'voice split lost text: ' + said);
    assert(v.movie.elements[0].type === 'subtitles', 'subs');
  });
  await test('02 Build video: clips win when saved; CJ down still works with clips', async () => {
    const inp = { ok: true, id: 'V1', script: vScript, clips: ['https://a/1.mp4', 'https://a/2.mp4'], pid: 'P3', image: '' };
    let [v] = await run(cmds, 'Build video', { '⚙️ Settings': vSettings, 'Find video inputs': [inp], 'CJ: product photos': cjPhotos }, []);
    const sc = v.movie.scenes;
    assert(v.mode === 'clips' && sc[0].elements[0].src === 'https://a/1.mp4' && sc[2].elements[0].type === 'image' && sc[3].elements[0].src === 'https://a/2.mp4', 'clip layout');
    [v] = await run(cmds, 'Build video', { '⚙️ Settings': vSettings, 'Find video inputs': [inp], 'CJ: product photos': [{ error: 'down' }] }, []);
    assert(v.ok && v.mode === 'clips' && v.movie.scenes.every(x => x.elements[0].type === 'video'), 'clips without photos');
    [v] = await run(cmds, 'Build video', { '⚙️ Settings': vSettings, 'Find video inputs': [{ ...inp, clips: [] }], 'CJ: product photos': [{ error: 'down' }] }, []);
    assert(!v.ok && v.reply.includes("couldn't get CJ photos"), JSON.stringify(v));
  });

  // ------------------------------------------------ 06 support
  const sup = '06-customer-support.json';
  const s06 = [{ support_email: 'help@store.com', store_name: 'Desk Joy', email_signature: 'Best regards,\\nDesk Joy',
    shipping_policy: '3-7 days', refund_policy: '30 days', auto_send: 'yes', min_confidence: 0.85,
    ignore_senders: 'noreply,no-reply,mailer-daemon,shopify.com' }];
  const emails = [
    { from: 'Anna Smith <Anna@Example.com>', subject: 'Where is my order?', textPlain: 'Hi, where is my package?\n\nOn Mon, Sep 28 Desk Joy <help@store.com> wrote:\n> Thanks for your order' },
    { from: 'Shopify <no-reply@shopify.com>', subject: 'New order', textPlain: 'x' },
    { from: 'bob@example.com', subject: 'Re: Order #1002', textHtml: '<p>I want a refund or I will open a <b>chargeback</b></p>' },
    { from: 'Anna Smith <anna@example.com>', subject: 'Automatic reply: away', textPlain: 'x' },
  ];
  const supOut = {
    '⚙️ Settings': s06, 'New customer email': emails,
    'Load orders': [{ day: '2026-09-27', order_name: '#1001', order_id: '555', items: '1x Organizer', country: 'US', email: 'anna@example.com' },
                    { day: '2026-09-28', order_name: '#1002', order_id: '556', items: '1x Organizer', country: 'US', email: 'other@x.com' }],
    'Load support history': [
      { ticket_id: 'T1', decision: 'pending', draft: 'Your order ships soon.', question: 'where?', intent: 'where_is_my_order' },
      { ticket_id: 'T1', decision: 'owner_reply', final_reply: 'Hi! It left our warehouse today, tracking below.', intent: 'where_is_my_order' }],
    'Load playbook': [...playbook, { rule_id: 'R010', agent: 'support', rule: 'Max 120 words.', status: 'active', version: 1 }, { rule_id: 'R006', agent: 'all', rule: 'Refunds go to the owner.', status: 'active', version: 1 }],
    'CJ: recent orders': [{ code: 200, data: { list: [{ orderNum: '1001', orderStatus: 'SHIPPED', trackNumber: 'YT2412345678901234', logisticName: 'YunExpress' }] } }],
  };
  let briefs;
  await test('06 Build support briefs: filters, order facts, danger, learning', async () => {
    briefs = await run(sup, 'Build support briefs', supOut, []);
    assert(briefs.length === 2, 'expected 2 customer emails, got ' + briefs.length);
    const [a, b] = briefs;
    assert(a.from_email === 'anna@example.com' && a.from_name === 'Anna Smith' && a.order_name === '#1001', JSON.stringify(a).slice(0, 200));
    assert(!a.question.includes('Thanks for your order') && a.question.includes('where is my package'), 'quote not stripped: ' + a.question);
    assert(a.prompt.includes('Tracking number: YT2412345678901234') && a.prompt.includes('Status: shipped'), 'facts missing');
    assert(a.known_ids.includes('YT2412345678901234') && !a.danger, 'known ids');
    assert(a.prompt.includes('owner sent instead') && a.prompt.includes('[R010] Max 120 words.') && a.prompt.includes('[R006] Refunds go to the owner.') && !a.prompt.includes('[R001]'), 'learning/rules');
    assert(b.danger && b.order_name === '#1002' && b.question.includes('chargeback'), 'danger/html ' + JSON.stringify(b).slice(0, 300));
    assert(b.prompt.includes('no supplier update yet'), 'unsynced order');
  });
  const decide = (outs, settings = s06) => run(sup, 'Decide (safety check)', { '⚙️ Settings': settings, 'Build support briefs': briefs },
    outs.map(o => ({ output: JSON.stringify(o) })));
  await test('06 Decide: safe WISMO with real tracking is auto-sent, refund is not', async () => {
    const [a, b] = await decide([
      { intent: 'where_is_my_order', confidence: 0.93, needs_owner: false, summary: 's', reply: 'Hi Anna, your order #1001 shipped: YT2412345678901234 https://t.17track.net/en#nums=YT2412345678901234' },
      { intent: 'refund_return', confidence: 0.95, needs_owner: true, reason: 'refund', summary: 's', reply: 'We are looking into it.' }]);
    assert(a.auto === true && a.why === '', 'WISMO should auto-send: ' + a.why);
    assert(b.auto === false && b.why.includes('refund_return') && b.why.includes('chargeback'), 'refund: ' + b.why);
    assert(!('prompt' in a) && !('known_ids' in a), 'internal fields leaked');
  });
  await test('06 Decide: invented tracking, low confidence, promises, auto-send off', async () => {
    let [a] = await decide([{ intent: 'where_is_my_order', confidence: 0.95, reply: 'Tracking: LX999999999CN' }, { intent: 'other', reply: 'x' }]);
    assert(!a.auto && a.why.includes("can't verify"), a.why);
    [a] = await decide([{ intent: 'shipping_time', confidence: 0.5, reply: 'Usually 3-7 days.' }, { intent: 'other', reply: 'x' }]);
    assert(!a.auto && a.why.includes('50% sure'), a.why);
    [a] = await decide([{ intent: 'product_question', confidence: 0.99, reply: 'Yes! And here is a discount code.' }, { intent: 'other', reply: 'x' }]);
    assert(!a.auto && a.why.includes('refunds, discounts'), a.why);
    [a] = await decide([{ intent: 'shipping_time', confidence: 0.99, reply: 'Usually 3-7 days.' }, { intent: 'other', reply: 'x' }], [{ ...s06[0], auto_send: 'no' }]);
    assert(!a.auto && a.why.includes('auto-send is off'), a.why);
    const bad = await run(sup, 'Decide (safety check)', { '⚙️ Settings': s06, 'Build support briefs': briefs }, [{ output: 'sorry, no json' }, { output: '' }]);
    assert(!bad[0].auto && bad[0].why.includes('could not be read'), bad[0].why);
  });
  await test('06 log rows match the support table', async () => {
    const cols = 'day,ticket_id,from_email,from_name,subject,question,intent,confidence,order_name,draft,final_reply,decision,note';
    const t = { ticket_id: 'T9', from_email: 'a@b.c', from_name: 'A', subject: 's', question: 'q', intent: 'shipping_time', confidence: 0.9, order_name: '', draft: 'd', why: 'because' };
    const [auto] = await run(sup, 'Auto-sent rows', { 'Safe to auto-send?': [t] }, []);
    const [wait] = await run(sup, 'Waiting rows', {}, [t]);
    assert(Object.keys(auto).join(',') === cols && Object.keys(wait).join(',') === cols, 'columns');
    assert(auto.decision === 'auto_sent' && auto.final_reply === 'd' && wait.decision === 'pending' && wait.note === 'because', 'values');
  });
  await test('02 ticket commands: /send, /reply, /skip', async () => {
    const hist = [{ ticket_id: 'T5', from_email: 'anna@example.com', from_name: 'Anna', subject: 'Where is it?', intent: 'where_is_my_order', confidence: 0.7, order_name: '#1001', draft: 'Hi Anna, it shipped.', decision: 'pending' }];
    const s02 = [{ email_signature: 'Best regards,\\nDesk Joy' }];
    const act = (route, text, h = hist) => run(cmds, 'Build ticket action', { '⚙️ Settings': s02, 'Load tickets': h,
      'Parse command': [{ route, args: text.split(/\s+/).slice(1), text }] }, []);
    let [r] = await act('send', '/send t5');
    assert(r.ok && r.send && r.body === 'Hi Anna, it shipped.' && r.subject === 'Re: Where is it?' && r.row.decision === 'approved', JSON.stringify(r));
    [r] = await act('send', '/send T5', [...hist, { ...hist[0], decision: 'approved' }]);
    assert(!r.ok && r.reply.includes('already answered'), r.reply);
    [r] = await act('reply', '/reply T5 Hi Anna,\nit left today.');
    assert(r.ok && r.body === 'Hi Anna,\nit left today.\n\nBest regards,\nDesk Joy' && r.row.decision === 'owner_reply' && r.row.final_reply === r.body, JSON.stringify(r.body));
    [r] = await act('skip', '/skip T5');
    assert(r.ok && !r.send && r.row.decision === 'skipped', JSON.stringify(r));
    [r] = await act('send', '/send T404');
    assert(!r.ok && r.reply.includes('T404'), r.reply);
    const cols = 'day,ticket_id,from_email,from_name,subject,question,intent,confidence,order_name,draft,final_reply,decision,note';
    [r] = await act('send', '/send T5');
    assert(Object.keys(r.row).join(',') === cols, 'row columns ' + Object.keys(r.row));
  });


  // ------------------------------------------------ 07 auto-pay
  const ap = '07-cj-auto-pay.json';
  const s07 = [{ max_order_usd: 40, daily_limit_usd: 100, min_profit_usd: 3, payment_fee_pct: 2.9, payment_fee_fixed: 0.3 }];
  await test('07 Orders to confirm', async () => {
    const r = await run(ap, 'Orders to confirm', { 'CJ: open orders': [{ code: 200, data: { list: [
      { orderId: 'C1', orderNum: '#1001', orderStatus: 'CREATED' }, { orderId: 'C2', orderNum: '#1002', orderStatus: 'UNPAID' },
      { orderId: 'C3', orderNum: '#1003', orderStatus: 'IN_CART' }, { orderId: 'C4', orderStatus: 'CREATED', isSandbox: 1 }] } }] }, []);
    assert(r.map(x => x.orderId).join() === 'C1,C3', JSON.stringify(r));
    const none = await run(ap, 'Orders to confirm', { 'CJ: open orders': [{ code: 200, data: { list: [] } }] }, []);
    assert(none.length === 1 && none[0].none, 'none marker');
  });
  await test('07 Money rules: pay good orders, hold the rest, never twice, caps respected', async () => {
    const shopOrders = [{ order_name: '#1001', order_id: '11', revenue: 29.99 }, { order_name: '#1002', order_id: '12', revenue: 29.99 },
      { order_name: '#1003', order_id: '13', revenue: 12 }, { order_name: '#1004', order_id: '14', revenue: 99 },
      { order_name: '#1005', order_id: '15', revenue: 29.99 }, { order_name: '#1007', order_id: '17', revenue: 29.99 }];
    const unpaid = [
      { orderId: 'C1', orderNum: '1001', orderStatus: 'UNPAID', orderAmount: 12.5 },   // pay
      { orderId: 'C2', orderNum: '#1002', orderStatus: 'UNPAID', orderAmount: 12.5 },  // already paid -> skip
      { orderId: 'C3', orderNum: '#1003', orderStatus: 'UNPAID', orderAmount: 11 },    // profit too low -> hold
      { orderId: 'C4', orderNum: '#1004', orderStatus: 'UNPAID', orderAmount: 55 },    // over per-order limit -> hold
      { orderId: 'C6', orderNum: '#9999', orderStatus: 'UNPAID', orderAmount: 10 },    // no Shopify order -> hold
      { orderId: 'C5', orderNum: '#1005', orderStatus: 'UNPAID', orderAmount: 12.5 },  // held earlier today -> hold silently
      { orderId: 'C7', orderNum: '#1007', orderStatus: 'UNPAID', orderAmount: 12.5 },  // balance runs out -> hold
    ];
    const today = DateTime.now().toFormat('yyyy-MM-dd');
    const out = await run(ap, 'Decide payments (money rules)', { '⚙️ Settings': s07, 'CJ: unpaid orders': [{ code: 200, data: { list: unpaid } }],
      'CJ: wallet balance': [{ code: 200, data: { amount: 26 } }], 'Load orders': shopOrders,
      'Load payments': [{ day: today, cj_order_id: 'C2', status: 'paid', amount: 12.5 }, { day: today, cj_order_id: 'C5', status: 'held', amount: 12.5 }] }, []);
    const by = Object.fromEntries(out.map(o => [o.cj_order_id, o]));
    assert(!by.C2, 'paid twice!');
    assert(by.C1.pay === true && by.C1.profit > 15, 'C1 ' + JSON.stringify(by.C1));
    assert(!by.C3.pay && by.C3.note.includes('profit would be only'), 'C3 ' + by.C3.note);
    assert(!by.C4.pay && by.C4.note.includes('$40 limit'), 'C4 ' + by.C4.note);
    assert(!by.C6.pay && by.C6.note.includes('no matching Shopify order'), 'C6 ' + by.C6.note);
    assert(by.C5.pay === true || (!by.C5.pay && by.C5.notify === false), 'C5 must not re-notify ' + JSON.stringify(by.C5));
    const paidSum = out.filter(o => o.pay).reduce((t, o) => t + o.amount, 0);
    assert(paidSum <= 26, 'spent more than the balance: ' + paidSum);
    assert(!by.C7.pay && by.C7.note.includes('balance'), 'C7 ' + JSON.stringify(by.C7));
  });
  await test('07 Money rules: daily limit counts earlier payments; CJ balance error pays nothing', async () => {
    const today = DateTime.now().toFormat('yyyy-MM-dd');
    let out = await run(ap, 'Decide payments (money rules)', { '⚙️ Settings': s07,
      'CJ: unpaid orders': [{ code: 200, data: { list: [{ orderId: 'C9', orderNum: '#1001', orderStatus: 'UNPAID', orderAmount: 12.5 }] } }],
      'CJ: wallet balance': [{ code: 200, data: { amount: 500 } }], 'Load orders': [{ order_name: '#1001', revenue: 29.99 }],
      'Load payments': [{ day: today, cj_order_id: 'X', status: 'paid', amount: 95 }] }, []);
    assert(!out[0].pay && out[0].note.includes('auto-pay limit'), out[0].note);
    out = await run(ap, 'Decide payments (money rules)', { '⚙️ Settings': s07,
      'CJ: unpaid orders': [{ code: 200, data: { list: [{ orderId: 'C9', orderNum: '#1001', orderStatus: 'UNPAID', orderAmount: 12.5 }] } }],
      'CJ: wallet balance': [{ error: 'timeout' }], 'Load orders': [{ order_name: '#1001', revenue: 29.99 }], 'Load payments': [{}] }, []);
    assert(!out[0].pay && out[0].note.includes('balance'), out[0].note);
  });
  await test('07 Payment rows + message; held rows notify once', async () => {
    const orders = [{ day: 'd', cj_order_id: 'C1', order_name: '#1001', amount: 12.5, revenue: 29.99, profit: 16.3 },
                    { day: 'd', cj_order_id: 'C8', order_name: '#1008', amount: 10, revenue: 29.99, profit: 18 }];
    const rows = await run(ap, 'Payment rows', { 'Pay it?': orders }, [{ code: 200, result: true }, { code: 1604000, result: false, message: 'Balance is insufficient' }]);
    assert(rows[0].status === 'paid' && rows[1].status === 'failed' && rows[1].note === 'Balance is insufficient', JSON.stringify(rows));
    assert(Object.keys(rows[0]).join() === 'day,cj_order_id,order_name,amount,revenue,profit,status,note', 'columns');
    const [m] = await run(ap, 'Payment message', {}, rows);
    assert(m.text.includes('Auto-paid 1') && m.text.includes('refused 1'), m.text);
    const held = await run(ap, 'Held rows', {}, [{ ...orders[0], notify: true, note: 'x' }, { ...orders[1], notify: false, note: 'y' }]);
    assert(held.length === 1 && held[0].status === 'held' && !('notify' in held[0]), JSON.stringify(held));
  });

  // ------------------------------------------------ 03 / 04
  await test('03 Order summary', async () => {
    const [o] = await run('03-new-order-alert.json', 'Order summary', { 'Shopify: order paid': [{ body: {
      id: 555, name: '#1001', total_price: '29.99', currency: 'USD', shipping_address: { country_code: 'US' },
      email: 'Anna@Example.com', line_items: [{ quantity: 1, title: 'Cable Organizer', variant_title: 'Black', sku: 'CJ333-BK' }] } }] }, []);
    assert(o.email === 'anna@example.com' && o.revenue === 29.99 && o.items === '1x Cable Organizer (Black)' && o.order_id === '555', JSON.stringify(o));
    const none = await run('03-new-order-alert.json', 'Order summary', { 'Shopify: order paid': [{ body: {} }] }, []);
    assert(none.length === 0, 'non-order not ignored');
  });
  await test('04 Find problems', async () => {
    const old = DateTime.utc().minus({ hours: 60 }).toFormat('yyyy-MM-dd HH:mm:ss');
    const fresh = DateTime.utc().minus({ hours: 5 }).toFormat('yyyy-MM-dd HH:mm:ss');
    const res = { code: 200, data: { list: [
      { orderNum: '#1001', orderStatus: 'CREATED', orderAmount: null },
      { orderNum: '#1002', orderStatus: 'PROCESSING', paymentDate: old, trackNumber: null },
      { orderNum: '#1003', orderStatus: 'PROCESSING', paymentDate: fresh, trackNumber: null },
      { orderNum: '#1004', orderStatus: 'SHIPPED', paymentDate: old, trackNumber: 'TN' },
    ] } };
    const [m] = await run('04-cj-order-check.json', 'Find problems', { '⚙️ Settings': [{ late_hours: 48 }], 'CJ: recent orders': [res] }, []);
    assert(m.text.includes('#1001') && m.text.includes('#1002') && !m.text.includes('#1003') && !m.text.includes('#1004'), m.text);
    const quiet = await run('04-cj-order-check.json', 'Find problems', { '⚙️ Settings': [{ late_hours: 48 }], 'CJ: recent orders': [{ code: 200, data: { list: [] } }] }, []);
    assert(quiet.length === 0, 'should be silent');
  });

  // ------------------------------------------------ 05 coach
  const coach = '05-daily-coach.json';
  const s05 = [{ telegram_chat_id: '123', max_rule_changes: 3, payment_fee_pct: 2.9, payment_fee_fixed: 0.3 }];
  const coachOutputs = {
    '⚙️ Settings': s05,
    'Load orders': [{ day: today, revenue: 29.99 }, { day: today, revenue: 44.99 }, { day: '2020-01-01', revenue: 100 }],
    'CJ: paid orders (7 days)': [{ code: 200, data: { list: [{ orderAmount: 7.5 }, { orderAmount: 12 }] } }],
    'Load feedback': [{ kind: 'video', ref: 'V1', views: 5000, clicks: 40, sales: 2 }, { kind: 'product', ref: 'CJ333-BK', status: 'testing' }],
    'Load content': [{ content_id: 'V1', day: today, hook: 'Result first', format: 'before-after', product: 'Org' }, { content_id: 'V9', day: '2020-01-01', hook: 'x' }],
    'Load products': priced, 'Load playbook': playbook, 'Load reports': [{}],
    'Load support': [
      { ticket_id: 'T1', day: today, decision: 'pending', intent: 'where_is_my_order', question: 'where?', draft: 'soon' },
      { ticket_id: 'T1', day: today, decision: 'owner_reply', final_reply: 'It shipped today, tracking YT1.' },
      { ticket_id: 'T2', day: today, decision: 'auto_sent', intent: 'shipping_time', draft: 'd', final_reply: 'd' },
      { ticket_id: 'T3', day: today, decision: 'pending', intent: 'refund_return', draft: 'x' }],
  };
  let nums;
  await test('05 Compute numbers', async () => {
    [nums] = await run(coach, 'Compute numbers', coachOutputs, []);
    const n = nums.numbers;
    assert(n.orders_today === 2 && n.revenue_today === 74.98 && n.orders_7d === 2 && n.cj_cost_7d === 19.5, JSON.stringify(n));
    assert(Math.abs(n.est_profit_7d - (74.98 - 19.5 - (0.6 + 74.98 * 0.029))) < 0.02, 'profit ' + n.est_profit_7d);
    assert(nums.unmeasured === 1, 'unmeasured ' + nums.unmeasured);
    assert(nums.prompt.includes('R007') && nums.prompt.includes('IDEAS ALREADY REJECTED'), 'rejected list');
    assert(nums.prompt.includes('3 emails: 1 auto-sent, 0 drafts approved as written, 1 rewritten by the owner, 0 skipped, 1 still waiting'), 'support line');
    assert(nums.prompt.includes('owner sent: "It shipped today') && nums.waiting === 1, 'support corrections');
  });
  await test('05 Compute numbers when CJ is down', async () => {
    const [n2] = await run(coach, 'Compute numbers', { ...coachOutputs, 'CJ: paid orders (7 days)': [{ error: 'x' }] }, []);
    assert(n2.numbers.cj_cost_7d === null && n2.prompt.includes('unknown (CJ API unavailable)'), 'cj down');
  });
  await test('05 Guardrails', async () => {
    const out = { report: 'ok', actions: ['a', 'b', 'c'],
      add_rules: [
        { agent: 'content', rule: 'Open with the finished result', evidence: 'V1 V2 V3' },
        { agent: 'content', rule: 'Visit https://evil.example for tips', evidence: 'x' },
        { agent: 'coach', rule: 'wrong agent', evidence: 'x' },
        { agent: 'research', rule: 'Increase the ad budget to $100/day', evidence: 'x' },
        { agent: 'research', rule: 'cost <= 1/3 price', evidence: 'dup' },
        { agent: 'research', rule: 'Prefer desk gadgets', evidence: 'P1 P2 P3' },
      ],
      retire_rules: [{ rule_id: 'R003', reason: 'protected' }, { rule_id: 'R001', reason: 'hurts' }, { rule_id: 'R404', reason: 'missing' }, { rule_id: 'R004', reason: 'already retired' }] };
    const [g] = await run(coach, 'Check proposals (guardrails)', {
      '⚙️ Settings': s05, 'Compute numbers': [nums], 'Coach agent': [{ output: JSON.stringify(out) }], 'Load playbook': playbook,
    }, []);
    const ids = g.changes.map(c => `${c.rule_id}:${c.status}:v${c.version}`);
    assert(JSON.stringify(ids) === '["R008:active:v1","R009:active:v1","R001:retired:v2"]', 'changes ' + ids);
    assert(g.has_changes && g.approval_text.includes('R008') && g.report_text.includes('Tomorrow:\n1. a'), 'texts');
    assert(g.report_text.includes('1 videos have no stats') && g.report_text.includes('1 customer email(s) are waiting'), 'nudges');
    assert(!g.changes.some(c => '_label' in c), 'label leaked into rows');
    const cols = 'day,orders_today,revenue_today,orders_7d,revenue_7d,cj_cost_7d,est_profit_7d,report';
    assert(Object.keys(g.report_row).join(',') === cols, 'report cols');
  });
  await test('05 Guardrails cap at max_rule_changes', async () => {
    const out = { report: 'r', actions: [], add_rules: [1, 2, 3, 4, 5].map(i => ({ agent: 'content', rule: 'Rule number ' + i, evidence: 'e' })), retire_rules: [] };
    const [g] = await run(coach, 'Check proposals (guardrails)', { '⚙️ Settings': s05, 'Compute numbers': [nums], 'Coach agent': [{ output: out }], 'Load playbook': playbook }, []);
    assert(g.changes.length === 3, 'cap ' + g.changes.length);
  });
  await test('05 Rejected ideas keep adds only', async () => {
    const guard = { changes: [{ rule_id: 'R008', status: 'active' }, { rule_id: 'R001', status: 'retired' }] };
    const r = await run(coach, 'Rules to remember as rejected', { 'Check proposals (guardrails)': [guard] }, []);
    assert(r.length === 1 && r[0].status === 'rejected', JSON.stringify(r));
  });

  console.log(failures ? `\n${failures} FAILED` : '\nALL TESTS PASSED');
  process.exit(failures ? 1 : 0);
})();
