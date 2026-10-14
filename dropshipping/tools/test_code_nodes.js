// Tests the JavaScript inside the generated n8n Code nodes with fake node outputs.
// Run: npm install luxon@3 && node test_code_nodes.js
const fs = require('fs');
const path = require('path');
const { DateTime } = require('luxon');

const DIR = path.join(__dirname, '..', 'n8n-workflows');
const load = f => JSON.parse(fs.readFileSync(path.join(DIR, f), 'utf8'));

// opts.now sets the clock ($now), opts.runIndex the loop counter of a node that runs again and again.
// A node name that is missing from `outputs` counts as "not executed" ($('name').isExecuted === false).
async function run(file, nodeName, outputs, inputItems, opts = {}) {
  const wf = load(file);
  const node = wf.nodes.find(n => n.name === nodeName);
  if (!node) throw new Error(`no node ${nodeName} in ${file}`);
  const $ = name => {
    const has = name in outputs;
    const items = has ? outputs[name].map(json => ({ json })) : [];
    const need = () => { if (!has) throw new Error(`test missing output for $('${name}')`); return items; };
    return { isExecuted: has, all: () => need(), first: () => need()[0], get item() { return need()[0]; } };
  };
  const $input = { all: () => inputItems.map(json => ({ json })), first: () => ({ json: inputItems[0] }) };
  const fn = new Function('$', '$input', '$now', 'DateTime', '$runIndex', 'return (async () => {' + node.parameters.jsCode + '})()');
  const result = await fn($, $input, opts.now || DateTime.now(), DateTime, opts.runIndex || 0);
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
  await test('01 Cheapest variant is priced, not a 2-pack', async () => {
    const det = [{ code: 200, data: { variants: [
      { vid: 'V2PK', variantSku: 'CJ333-2PCS', variantSellPrice: 5.84, inventories: [{ countryCode: 'US', totalInventory: 50 }] },
      { vid: 'V1', variantSku: 'CJ333-1PC', variantSellPrice: 2.4, inventories: [{ countryCode: 'US', totalInventory: 50 }] }] } }];
    const s1 = { ...settings01, sell_countries: 'US' };
    const r = await run(research, 'Plan shipping routes', { '⚙️ Settings': [s1], 'Parse picks': [picks[0]] }, det);
    assert(r.length === 1 && r[0].vid === 'V1', 'route vid ' + JSON.stringify(r));
    const [p] = await run(research, 'Price & margin', { '⚙️ Settings': [s1], 'Parse picks': [picks[0]], 'CJ: product details': det, 'Plan shipping routes': r },
      [{ code: 200, data: [{ logisticName: 'USPS+', logisticPrice: 5.1, logisticAging: '3-5' }] }]);
    assert(p.sku === 'CJ333-1PC' && p.cj_cost === 2.4 && p.sell_price === 22.99, JSON.stringify(p));
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
    assert(m.text.includes('search CJ for CJ333)') && m.text.includes('Open in CJ: https://www.cjdropshipping.com/product/magnetic-cable-organizer-p-P3.html'), m.text);
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

  // ------------------------------------------------ social posts: 02 (/queue, approve, to-dos) + 08 (publisher)
  const soc = '08-social-publisher.json';
  const intake = '09-video-intake.json';
  const header = name => fs.readFileSync(path.join(__dirname, '..', 'templates', name + '.csv'), 'utf8').split('\n')[0].trim();
  const postCols = header('social_posts');
  const berlin = iso => DateTime.fromISO(iso, { zone: 'Europe/Berlin' });
  const utc = iso => DateTime.fromISO(iso, { zone: 'Europe/Berlin' }).toUTC().toISO();
  const utcT = iso => DateTime.fromISO(iso, { zone: 'utc' });
  const s02p = { telegram_chat_id: '123', post_times: '12:30,20:30', post_timezone: 'America/New_York', time_zone: 'Europe/Berlin', min_lead_hours: 2,
    youtube_auto: 'yes', instagram_auto: 'yes', shop_url: 'pivendo.com' };
  const vurl = 'https://cdn.shopify.com/videos/c/o/v/star_lamp-1.mp4';

  await test('02 Parse command: button taps and the post commands', async () => {
    const s = [{ telegram_chat_id: '123' }];
    const tap = (data, chat = 123) => [{ callback_query: { id: 'Q77', from: { id: chat }, message: { chat: { id: chat }, text: 'old text' }, data } }];
    let [r] = await run(cmds, 'Parse command', { '⚙️ Settings': s, 'Telegram message in': tap('approve:P1013025812') }, []);
    assert(r.route === 'approve' && r.args[0] === 'P1013025812' && r.tapId === 'Q77' && r.chatId === '123', JSON.stringify(r));
    [r] = await run(cmds, 'Parse command', { '⚙️ Settings': s, 'Telegram message in': tap('reject:P1013025812') }, []);
    assert(r.route === 'reject' && r.args[0] === 'P1013025812', JSON.stringify(r));
    const stranger = await run(cmds, 'Parse command', { '⚙️ Settings': s, 'Telegram message in': tap('approve:P1013025812', 999) }, []);
    assert(stranger.length === 0, 'a tap from another chat must be ignored');
    [r] = await run(cmds, 'Parse command', { '⚙️ Settings': s, 'Telegram message in': tg(`/queue ${vurl} CJ1 ai stars on the wall`) }, []);
    assert(r.route === 'queue' && r.args.length === 7 && r.tapId === '', JSON.stringify(r));
    const wf = load(cmds);
    const outs = wf.nodes.find(n => n.name === 'Route').parameters.rules.values.map(v => v.outputKey);
    for (const c of ['queue', 'approve', 'reject', 'posts', 'tiktok', 'youtube', 'instagram', 'retry']) {
      [r] = await run(cmds, 'Parse command', { '⚙️ Settings': s, 'Telegram message in': tg(`/${c} P1 done`) }, []);
      assert(r.route === c && outs.includes(c), 'route ' + c);
    }
    const wired = wf.connections.Route.main;
    assert(wired.length === outs.length && wired.every(o => o.length === 1), 'every Route output must lead somewhere');
    const trigger = wf.nodes.find(n => n.name === 'Telegram message in');
    assert(trigger.parameters.updates.join() === 'message,callback_query', 'the one trigger must also receive button taps');
    assert(wf.nodes.filter(n => n.type === 'n8n-nodes-base.telegramTrigger').length === 1, 'one bot = one trigger');
  });

  const lamp = { pid: 'P9', sku: 'CJYS315', name: 'Star & Moon Lamp', sell_price: 29.99, ship_days: '7-12', ship_method: 'CJPacket',
    target_buyer: 'renters who want a cozy bedroom', angle: 'dark room, stars appear', risks: 'seasonal' };
  const postBrief = (args, posts = [{}]) => run(cmds, 'Build post brief', { '⚙️ Settings': [s02p], 'Parse command': [{ route: 'queue', args }],
    'Load products (post)': [lamp], 'Load playbook (post)': [...playbook, { rule_id: 'R020', agent: 'content', rule: 'Name the room.', status: 'active', version: 1 }],
    'Load videos (post)': [{ content_id: 'V1', hook: 'Result first', format: 'before-after' }, { content_id: 'V2', hook: 'never measured' }],
    'Load stats (post)': [{ kind: 'video', ref: 'V1', views: 5000, clicks: 40, sales: 2 }], 'Load posts (queue)': posts }, []);
  let pbrief;
  await test('02 Build post brief: /queue parsing, ai flag, product + rules, no price or delivery time', async () => {
    [pbrief] = await postBrief([vurl, 'cjys315', 'AI', 'presenter', 'holds', 'the', 'lamp']);
    assert(pbrief.ok && pbrief.ai === 'yes' && pbrief.shows === 'presenter holds the lamp' && pbrief.sku === 'CJYS315', JSON.stringify(pbrief).slice(0, 300));
    assert(pbrief.prompt.includes('Star & Moon Lamp') && pbrief.prompt.includes('pivendo.com') && pbrief.prompt.includes('an AI presenter'), 'prompt facts');
    assert(pbrief.prompt.includes('[R020] Name the room.') && !pbrief.prompt.includes('[R001]') && !pbrief.prompt.includes('[R004]'), 'only active content rules');
    assert(pbrief.prompt.includes('"Result first"') && !pbrief.prompt.includes('never measured'), 'learning from measured videos');
    assert(!pbrief.prompt.includes('29.99') && !pbrief.prompt.includes('7-12'), 'the agent must not be given a price or a delivery time');
    assert(pbrief.rules_version === 'R020v1', pbrief.rules_version);
    let [b] = await postBrief([vurl + '?v=17', 'P9', 'stars', 'on', 'the', 'wall']);
    assert(b.ok && b.ai === 'no' && b.shows === 'stars on the wall' && b.prompt.includes('no AI.'), 'pid lookup, no ai: ' + JSON.stringify(b).slice(0, 200));
    [b] = await postBrief([vurl, 'CJYS315']);
    assert(b.ok && b.prompt.includes('not described'), 'no description');
  });
  await test('02 Build post brief: bad link, unknown SKU, same video twice', async () => {
    for (const bad of [['http://x.y/a.mp4', 'CJYS315'], ['https://x.y/a.mov', 'CJYS315'], ['https://drive.google.com/file/d/abc/view', 'CJYS315'],
                       ['https://x.y/ä.mp4', 'CJYS315'], [vurl], [], ['CJYS315', vurl]]) {
      const [b] = await postBrief(bad);
      assert(b.ok === false && b.reply.startsWith('Usage: /queue &lt;video link&gt;'), 'should be refused: ' + JSON.stringify(bad) + ' -> ' + JSON.stringify(b).slice(0, 120));
    }
    let [b] = await postBrief([vurl, 'NOPE']);
    assert(!b.ok && b.reply.includes('NOPE'), b.reply);
    [b] = await postBrief([vurl, 'CJYS315'], [{ post_id: 'P7', video_url: vurl, status: 'awaiting_ok' }]);
    assert(!b.ok && b.reply.includes('P7'), 'the same video must not be queued twice: ' + JSON.stringify(b).slice(0, 200));
    [b] = await postBrief([vurl, 'CJYS315'], [{ post_id: 'P7', video_url: vurl, status: 'awaiting_ok' }, { post_id: 'P7', status: 'rejected' }]);
    assert(b.ok, 'a rejected video may be queued again');
  });

  const T0 = berlin('2026-10-13T20:15:42');
  const checkTexts = (out, brief = pbrief) => run(cmds, 'Check post texts', { '⚙️ Settings': [s02p], 'Build post brief': [brief],
    'Post agent': [{ output: typeof out === 'string' ? out : JSON.stringify(out) }] }, [], { now: T0 });
  const goodTexts = {
    caption_tiktok: 'Lights off. Stars on. This little lamp puts a night sky on your wall. Best in a dark room.', hashtags_tiktok: ['#starprojector', 'room decor', 'fyp', '#viral'],
    caption_instagram: 'Lights off, stars on.\nA small USB lamp that puts a night sky on your ceiling. Best in a dark room. #cozy', hashtags_instagram: ['starprojector', 'roomdecor', 'bedroomideas', 'cozyroom', 'nightlight', 'ledlights', 'homedecor', 'giftidea'],
    yt_title: 'Star projector lamp <b>for a cozy bedroom</b>: a night sky on your wall and ceiling in seconds, shown in a dark room at home',
    yt_description: 'A small USB lamp that puts stars on the wall. Best in a dark room.', hashtags_youtube: ['Shorts', 'starprojector'] };
  let queued;
  await test('02 Check post texts: length limits, hashtags, shop link, row shape', async () => {
    [queued] = await checkTexts(goodTexts);
    const r = queued.row;
    assert(queued.ok && Object.keys(r).join(',') === postCols, 'row columns ' + Object.keys(r).join(','));
    assert(r.post_id === 'P1013201542' && r.status === 'awaiting_ok' && r.ai === 'yes' && r.video === 'star_lamp-1' && r.video_url === vurl, JSON.stringify(r).slice(0, 300));
    assert(r.yt_status === '' && r.ig_status === '' && r.post_at === '' && r.slot === '' && r.note === 'presenter holds the lamp' && r.rules_version === 'R020v1', 'nothing is scheduled before the owner approves');
    assert(queued.text.includes('next free slot (12:30 or 20:30 in America/New_York; I tell you the time in Europe/Berlin)'), queued.text);
    assert(r.yt_title.length <= 100 && !/[<>]/.test(r.yt_title) && r.yt_title.endsWith('…'), 'title: ' + r.yt_title.length + ' ' + r.yt_title);
    assert((r.caption_instagram.match(/#/g) || []).length === 5 && !r.caption_instagram.includes('#cozy '), 'Instagram: 5 hashtags at most: ' + r.caption_instagram);
    assert(r.caption_tiktok.endsWith('#starprojector #roomdecor') && !/#(fyp|viral)/.test(r.caption_tiktok), 'TikTok tags: ' + r.caption_tiktok);
    for (const k of ['caption_tiktok', 'caption_instagram', 'yt_description']) assert(r[k].includes('pivendo.com'), k + ' has no shop link');
    assert(r.yt_description.includes('Shop: https://pivendo.com') && r.yt_description.endsWith('#Shorts #starprojector'), r.yt_description);
    assert(queued.text.includes('Star &amp; Moon Lamp') && !/[<>]/.test(queued.text) && queued.text.includes('/approve P1013201542'), 'approval message must be HTML-safe');
    assert(queued.text.includes(r.caption_tiktok) && queued.text.includes(r.yt_title), 'the owner must see the exact texts');
  });
  await test('02 Check post texts: very long texts stay inside every platform limit', async () => {
    const long = 'A small lamp that puts stars on the wall in a dark room. '.repeat(120);
    const manyTags = Array.from({ length: 40 }, (_, i) => 'tag' + i);
    const [q] = await checkTexts({ caption_tiktok: long, hashtags_tiktok: manyTags, caption_instagram: long, hashtags_instagram: manyTags,
      yt_title: long, yt_description: '🌙'.repeat(3000), hashtags_youtube: manyTags });
    const r = q.row;
    assert(q.ok && r.yt_title.length <= 100, 'YouTube title max 100: ' + r.yt_title.length);
    assert(Buffer.byteLength(r.yt_description, 'utf8') <= 5000, 'YouTube description max 5000 bytes: ' + Buffer.byteLength(r.yt_description, 'utf8'));
    assert(r.caption_instagram.length <= 2200 && (r.caption_instagram.match(/#/g) || []).length <= 5, 'Instagram limits');
    assert(r.caption_tiktok.length <= 2200 && (r.caption_tiktok.match(/#/g) || []).length <= 5, 'TikTok limits');
    assert(r.caption_tiktok.includes('Shop: pivendo.com') && r.caption_instagram.includes('Shop: pivendo.com'), 'the shop link survives the cut');
    assert(q.text.length <= 4096 && q.text.includes(r.caption_instagram), 'the whole text fits into one Telegram message: ' + q.text.length);
  });
  await test('02 Check post texts: honesty rules block the post', async () => {
    const broken = { 'a discount': '50% off today', 'a discount or sale': 'Big sale on now', 'a countdown': 'Last chance, only 3 left',
      'a delivery promise': 'Free shipping, arrives in 3 days', 'a review or customer claim': 'Our customers love it', 'a review': 'Rated 5 stars',
      'a customer claim': 'I bought this and it is great', 'an overclaim': 'It lights up the whole ceiling', 'an overclaim 2': 'Fills your room with stars', 'a price': 'Now only $19' };
    for (const [label, bad] of Object.entries(broken)) {
      for (const field of ['caption_tiktok', 'yt_title']) {
        const [q] = await checkTexts({ ...goodTexts, [field]: bad });
        assert(q.ok === false && q.reply.startsWith('Not queued.') && !('row' in q), `"${bad}" in ${field} (${label}) must not be queued: ` + JSON.stringify(q).slice(0, 160));
      }
    }
    let [q] = await checkTexts('Sorry, I cannot do that.');
    assert(!q.ok && q.reply.includes('did not return usable texts'), q.reply);
    [q] = await checkTexts({ ...goodTexts, caption_instagram: ' #only #tags ' });
    assert(!q.ok && q.reply.includes('left a text empty'), q.reply);
  });

  const basePost = { id: 1, day: '2026-10-13', at: '2026-10-13T18:15:42.000Z', post_id: 'P1', sku: 'CJYS315', product: 'Star & Moon Lamp', video: 'star_lamp-1',
    video_url: vurl, ai: 'yes', status: 'awaiting_ok', caption_tiktok: 'tt cap\n\nShop: pivendo.com\n\n#a #b', caption_instagram: 'ig cap', yt_title: 'yt title', yt_description: 'yt desc', rules_version: 'R020v1' };
  let rowId = 100;
  const ev = (post_id, changes, at = '2026-10-13T19:00:00.000Z') => ({ id: rowId++, at, post_id, ...changes });
  const action = (text, rows, now, settings = s02p) => run(cmds, 'Build post action', { '⚙️ Settings': [settings], 'Load posts': rows,
    'Parse command': [{ route: text.split(/\s+/)[0].slice(1), args: text.split(/\s+/).slice(1), text }] }, [], { now });
  // Approve n new posts one after the other, like the owner tapping Approve n times. Returns for each one
  // the slot name, the stored moment (UTC) and the time the owner is shown (Berlin).
  const approveAll = async (now, n, settings = s02p, table = []) => {
    const out = [];
    for (let i = 1; i <= n; i++) {
      const id = 'Q' + i;
      table.push({ ...basePost, id: rowId++, post_id: id });
      const [r] = await action('/approve ' + id, table, now, settings);
      if (!r.ok) throw new Error('approve failed: ' + r.reply);
      table.push({ ...r.rows[0], id: rowId++ });
      out.push({ slot: r.rows[0].slot, post_at: r.rows[0].post_at, shown: r.msgs[0].match(/Slot: (.+?) \(/)[1] });
    }
    return out;
  };
  const slotOf = async (now, settings = s02p, table = []) => { const [x] = await approveAll(now, 1, settings, table); return `${x.slot} ${x.post_at}`; };
  const approved = (post_id, post_at, slot = '12:30') => [{ ...basePost, id: rowId++, post_id },
    ev(post_id, { status: 'approved', post_at, slot, yt_status: 'queued', ig_status: 'queued', tiktok_status: 'todo' })];
  const hoursBetween = list => list.slice(1).map((x, i) => (DateTime.fromISO(x.post_at).toMillis() - DateTime.fromISO(list[i].post_at).toMillis()) / 3600e3).join();

  await test('02 Slot: two slots a day (12:30 and 20:30 New York), one post per slot, at least 2 hours ahead', async () => {
    // Tue 13 Oct 2026, 10:00 in Berlin = 04:00 in New York: both slots of that day are free, then it rolls over
    const five = await approveAll(berlin('2026-10-13T10:00'), 5);
    assert(five.map(x => `${x.slot} ${x.post_at}`).join(' | ') === '12:30 2026-10-13T16:30:00.000Z | 20:30 2026-10-14T00:30:00.000Z | '
      + '12:30 2026-10-14T16:30:00.000Z | 20:30 2026-10-15T00:30:00.000Z | 12:30 2026-10-15T16:30:00.000Z', JSON.stringify(five));
    // the owner is always shown Berlin time
    assert(five.map(x => x.shown).join(' | ') === 'Tue 13 Oct at 18:30 | Wed 14 Oct at 02:30 | Wed 14 Oct at 18:30 | Thu 15 Oct at 02:30 | Thu 15 Oct at 18:30', five.map(x => x.shown).join(' | '));
    assert(hoursBetween(five) === '8,16,8,16', hoursBetween(five));
    // at least 2 hours ahead
    assert(await slotOf(utcT('2026-10-13T14:30:00')) === '12:30 2026-10-13T16:30:00.000Z', 'exactly 2 hours ahead is allowed');
    assert(await slotOf(utcT('2026-10-13T14:31:00')) === '20:30 2026-10-14T00:30:00.000Z', 'lunch is too close -> the evening slot of the same day');
    assert(await slotOf(utcT('2026-10-13T23:00:00')) === '12:30 2026-10-14T16:30:00.000Z', 'evening is too close -> lunch the next day');
    assert(await slotOf(utcT('2026-10-14T00:30:00')) === '12:30 2026-10-14T16:30:00.000Z', 'exactly at slot time -> the next slot');
    // a rejected post frees its slot; a post at another moment (an old setting, a retry) blocks nothing
    const table = [...approved('P2', '2026-10-13T16:30:00.000Z'), ev('P2', { status: 'rejected' }),
                   ...approved('P3', '2026-10-14T00:30:00.000Z', '20:30'), ...approved('P4', '2026-10-13T17:00:00.000Z', '13:00')];
    const two = await approveAll(berlin('2026-10-13T10:00'), 2, s02p, table);
    assert(two.map(x => x.post_at).join() === '2026-10-13T16:30:00.000Z,2026-10-14T16:30:00.000Z', 'taken slots are skipped: ' + JSON.stringify(two));
    // the clock of the n8n server does not matter
    assert(await slotOf(DateTime.fromISO('2026-10-13T08:00:00Z', { zone: 'Asia/Tokyo' })) === '12:30 2026-10-13T16:30:00.000Z', 'server in another time zone');
    // settings
    assert(await slotOf(berlin('2026-10-13T10:00'), { ...s02p, post_times: ' 20:30;9:05 , 9:05, 25:00, soon' }) === '09:05 2026-10-13T13:05:00.000Z', 'times are cleaned, sorted and de-duplicated');
    assert(await slotOf(berlin('2026-10-13T10:00'), { ...s02p, min_lead_hours: 0, post_times: '04:10' }) === '04:10 2026-10-13T08:10:00.000Z', 'no lead time');
    assert(await slotOf(berlin('2026-10-13T10:00'), { telegram_chat_id: '123' }) === '12:30 2026-10-13T16:30:00.000Z', 'missing settings -> 12:30 and 20:30 New York');
    assert(await slotOf(berlin('2026-10-13T10:00'), { ...s02p, post_times: '', post_timezone: 'Mars/Phobos' }) === '12:30 2026-10-13T16:30:00.000Z', 'unusable settings -> the defaults');
    assert(await slotOf(berlin('2026-10-13T10:00'), { ...s02p, post_times: '19:00', post_timezone: 'Europe/Berlin' }) === '19:00 2026-10-13T17:00:00.000Z', 'slots in another zone');
  });
  await test('02 Slot: the weeks around 25 Oct 2026 (Europe changes its clocks) and 1 Nov 2026 (the US changes)', async () => {
    // New York is 6 hours behind Berlin, but only 5 from 25 Oct to 1 Nov. The slots stay 12:30 and 20:30 in New York.
    const eu = await approveAll(berlin('2026-10-24T10:00'), 4);
    assert(eu.map(x => x.post_at).join() === '2026-10-24T16:30:00.000Z,2026-10-25T00:30:00.000Z,2026-10-25T16:30:00.000Z,2026-10-26T00:30:00.000Z', JSON.stringify(eu));
    assert(eu.map(x => x.shown).join(' | ') === 'Sat 24 Oct at 18:30 | Sun 25 Oct at 02:30 | Sun 25 Oct at 17:30 | Mon 26 Oct at 01:30', eu.map(x => x.shown).join(' | '));
    assert(eu.map(x => x.slot).join() === '12:30,20:30,12:30,20:30' && hoursBetween(eu) === '8,16,8', 'for the buyers nothing moves: ' + hoursBetween(eu));
    const us = await approveAll(berlin('2026-10-31T10:00'), 5);
    assert(us.map(x => x.post_at).join() === '2026-10-31T16:30:00.000Z,2026-11-01T00:30:00.000Z,2026-11-01T17:30:00.000Z,2026-11-02T01:30:00.000Z,2026-11-02T17:30:00.000Z', JSON.stringify(us));
    assert(us.map(x => x.shown).join(' | ') === 'Sat 31 Oct at 17:30 | Sun 1 Nov at 01:30 | Sun 1 Nov at 18:30 | Mon 2 Nov at 02:30 | Mon 2 Nov at 18:30', us.map(x => x.shown).join(' | '));
    assert(us.map(x => x.slot).join() === '12:30,20:30,12:30,20:30,12:30' && hoursBetween(us) === '8,17,8,16', 'the New York day of 1 Nov has 25 hours: ' + hoursBetween(us));
    // approving in the very hours the clocks change
    assert(await slotOf(utcT('2026-10-25T00:45:00')) === '12:30 2026-10-25T16:30:00.000Z', 'Berlin, first 02:45 of 25 Oct');
    assert(await slotOf(utcT('2026-10-25T01:45:00')) === '12:30 2026-10-25T16:30:00.000Z', 'Berlin, second 02:45 of 25 Oct');
    assert(await slotOf(utcT('2026-11-01T05:30:00')) === '12:30 2026-11-01T17:30:00.000Z', 'New York, first 01:30 of 1 Nov');
    assert(await slotOf(utcT('2026-11-01T06:30:00')) === '12:30 2026-11-01T17:30:00.000Z', 'New York, second 01:30 of 1 Nov');
    assert(await slotOf(utcT('2026-11-01T15:31:00')) === '20:30 2026-11-02T01:30:00.000Z', 'lead time is counted in real hours');
  });
  await test('02 Slot: spring 2027 (US 14 Mar, Europe 28 Mar), and slots set in Berlin time on the nights the clocks change', async () => {
    const us = await approveAll(berlin('2027-03-13T10:00'), 4);
    assert(us.map(x => x.post_at).join() === '2027-03-13T17:30:00.000Z,2027-03-14T01:30:00.000Z,2027-03-14T16:30:00.000Z,2027-03-15T00:30:00.000Z', JSON.stringify(us));
    assert(us.map(x => x.shown).join(' | ') === 'Sat 13 Mar at 18:30 | Sun 14 Mar at 02:30 | Sun 14 Mar at 17:30 | Mon 15 Mar at 01:30', us.map(x => x.shown).join(' | '));
    const eu = await approveAll(berlin('2027-03-27T10:00'), 4);
    assert(eu.map(x => x.post_at).join() === '2027-03-27T16:30:00.000Z,2027-03-28T00:30:00.000Z,2027-03-28T16:30:00.000Z,2027-03-29T00:30:00.000Z', JSON.stringify(eu));
    assert(eu.map(x => x.shown).join(' | ') === 'Sat 27 Mar at 17:30 | Sun 28 Mar at 01:30 | Sun 28 Mar at 18:30 | Mon 29 Mar at 02:30', eu.map(x => x.shown).join(' | '));
    // One slot at 01:00 Berlin time: 25 Oct 2026 has 25 hours, 28 Mar 2027 has 23
    const de = { ...s02p, post_times: '01:00', post_timezone: 'Europe/Berlin' };
    const oct = await approveAll(berlin('2026-10-23T20:00'), 3, de);
    assert(oct.map(x => x.post_at).join() === '2026-10-23T23:00:00.000Z,2026-10-24T23:00:00.000Z,2026-10-26T00:00:00.000Z' && hoursBetween(oct) === '24,25', JSON.stringify(oct));
    assert(oct.map(x => x.shown).join(' | ') === 'Sat 24 Oct at 01:00 | Sun 25 Oct at 01:00 | Mon 26 Oct at 01:00', oct.map(x => x.shown).join(' | '));
    const mar = await approveAll(berlin('2027-03-26T20:00'), 3, de);
    assert(mar.map(x => x.post_at).join() === '2027-03-27T00:00:00.000Z,2027-03-28T00:00:00.000Z,2027-03-28T23:00:00.000Z' && hoursBetween(mar) === '24,23', JSON.stringify(mar));
    assert(mar.map(x => x.shown).join(' | ') === 'Sat 27 Mar at 01:00 | Sun 28 Mar at 01:00 | Mon 29 Mar at 01:00', mar.map(x => x.shown).join(' | '));
    // 02:30 Berlin time does not exist on 28 Mar 2027 and comes twice on 25 Oct 2026: still exactly one slot that day
    const odd = { ...s02p, post_times: '02:30', post_timezone: 'Europe/Berlin' };
    const gap = await approveAll(berlin('2027-03-27T12:00'), 2, odd);
    assert(gap.map(x => x.post_at).join() === '2027-03-28T01:30:00.000Z,2027-03-29T00:30:00.000Z' && gap[0].shown === 'Sun 28 Mar at 03:30' && gap[0].slot === '02:30', JSON.stringify(gap));
    const twice = await approveAll(berlin('2026-10-24T12:00'), 2, odd);
    assert(['2026-10-25T00:30:00.000Z', '2026-10-25T01:30:00.000Z'].includes(twice[0].post_at) && twice[1].post_at === '2026-10-26T01:30:00.000Z' && twice[0].shown === 'Sun 25 Oct at 02:30', JSON.stringify(twice));
  });

  await test('02 Approve: row, TikTok to-do with checklist, auto or by hand', async () => {
    let [r] = await action('/approve p1', [basePost], berlin('2026-10-13T20:00'));
    assert(r.ok && r.save && r.rows.length === 1 && Object.keys(r.rows[0]).join(',') === postCols, 'row columns');
    const row = r.rows[0];
    assert(row.status === 'approved' && row.yt_status === 'queued' && row.ig_status === 'queued' && row.tiktok_status === 'todo' && row.caption_tiktok === '', JSON.stringify(row));
    // 20:00 in Berlin is 14:00 in New York: lunch is over, so it gets the evening slot. Stored in UTC, shown in Berlin time.
    assert(row.post_at === '2026-10-14T00:30:00.000Z' && row.slot === '20:30', 'slot: ' + row.slot + ' ' + row.post_at);
    assert(r.msgs.length === 2 && r.msgs[0].includes('P1 approved. Slot: Wed 14 Oct at 02:30 (Europe/Berlin). That is the 20:30 slot in America/New_York.'), r.msgs[0]);
    const todo = r.msgs[1];
    assert(todo.includes('TikTok to-do for P1') && todo.includes(vurl) && todo.includes('Schedule it for Wed 14 Oct at 02:30 (Europe/Berlin)'), todo);
    assert(todo.includes('"Your brand" ON') && todo.includes('"AI-generated content" ON') && todo.includes('"Shop: pivendo.com" and pin it') && todo.includes('/tiktok P1 done'), todo);
    assert(todo.includes('<code>tt cap\n\nShop: pivendo.com\n\n#a #b</code>'), 'caption to copy: ' + todo);
    assert(todo.replace(/<\/?code>/g, '').match(/[<>]/) === null, 'only <code> tags may be in the message');
    // no AI in the video, and both platforms by hand
    [r] = await action('/approve P1', [{ ...basePost, ai: 'no' }], berlin('2026-10-13T20:00'), { ...s02p, youtube_auto: 'no', instagram_auto: '' });
    assert(r.rows[0].yt_status === 'todo' && r.rows[0].ig_status === 'todo' && r.msgs.length === 4, 'by hand: ' + JSON.stringify(r.rows[0]));
    assert(!r.msgs.join('\n').includes('AI-generated') && !r.msgs.join('\n').includes('Altered content') && r.msgs[2].includes('/youtube P1 done') && r.msgs[2].includes('not made for kids') && r.msgs[3].includes('/instagram P1 done'), 'to-dos');
    [r] = await action('/approve P1', [basePost], berlin('2026-10-13T20:00'), { ...s02p, youtube_auto: 'no' });
    assert(r.msgs[2].includes('Altered content: choose "Yes"') && r.msgs[2].includes('<code>yt title</code>') && r.msgs[2].includes('<code>yt desc</code>'), r.msgs[2]);
    // second tap, rejected post, unknown post
    [r] = await action('/approve P1', [basePost, ev('P1', { status: 'approved', post_at: '2026-10-14T00:30:00.000Z', slot: '20:30' })], berlin('2026-10-13T20:05'));
    assert(!r.ok && r.reply.includes('already approved for Wed 14 Oct at 02:30'), 'a second tap must not move the slot: ' + JSON.stringify(r));
    [r] = await action('/approve P1', [basePost, ev('P1', { status: 'rejected' })], berlin('2026-10-13T20:05'));
    assert(!r.ok && r.reply.includes('was rejected'), r.reply);
    [r] = await action('/approve P404', [basePost], berlin('2026-10-13T20:05'));
    assert(!r.ok && r.reply.includes('P404'), r.reply);
    [r] = await action('/approve', [{}], berlin('2026-10-13T20:05'));
    assert(!r.ok && r.reply.includes('(missing id)'), r.reply);
  });
  const live = [basePost, ev('P1', { status: 'approved', post_at: '2026-10-14T00:30:00.000Z', slot: '20:30', yt_status: 'queued', ig_status: 'queued', tiktok_status: 'todo' })];
  await test('02 Music: the owner chooses it himself and is reminded in the approval request, the approve message and every to-do', async () => {
    const MUSIC = 'Choose the music first.';
    const bot = 'the bot posts them and cannot add a sound, so the music must already be inside the video file';
    const request = async settings => (await run(cmds, 'Check post texts', { '⚙️ Settings': [settings], 'Build post brief': [pbrief], 'Post agent': [{ output: JSON.stringify(goodTexts) }] }, [], { now: T0 }))[0].text;
    // the request for the OK (the message with the Approve button): before anything is decided
    let t = await request(s02p);
    assert(t.includes('🎵 Choose the music first. TikTok: in TikTok Studio tap Sounds, pick one, then Save.') && t.includes(bot), t);
    assert(t.indexOf(MUSIC) > t.indexOf('YOUTUBE DESCRIPTION') && t.indexOf(MUSIC) < t.indexOf('✅ Approve'), 'the reminder sits right above the buttons\' explanation');
    assert((t.match(/Choose the music first\./g) || []).length === 1, 'one short line');
    t = await request({ ...s02p, instagram_auto: 'no' });
    assert(t.includes('YouTube: the bot posts it and cannot add a sound, so the music must already be inside the video file') && !t.includes('Instagram: the bot'), t);
    t = await request({ ...s02p, youtube_auto: 'no', instagram_auto: '' });
    assert(t.includes(MUSIC) && t.includes('TikTok Studio tap Sounds') && !t.includes('cannot add a sound'), 'by hand only: the to-dos say the rest: ' + t);
    // the approve message
    let [r] = await action('/approve P1', [basePost], berlin('2026-10-13T20:00'));
    assert(r.msgs[0].includes('🎵 Choose the music first. TikTok: in TikTok Studio tap Sounds, pick one, then Save.') && r.msgs[0].includes('YouTube and Instagram: ' + bot), r.msgs[0]);
    assert(r.msgs[0].indexOf(MUSIC) < r.msgs[0].indexOf('Changed your mind?') && (r.msgs[0].match(/Choose the music first\./g) || []).length === 1, r.msgs[0]);
    // the to-do for every platform the owner posts by hand: TikTok always, YouTube and Instagram when they are not automatic
    [r] = await action('/approve P1', [basePost], berlin('2026-10-13T20:00'), { ...s02p, youtube_auto: 'no', instagram_auto: 'no' });
    assert(r.msgs.length === 4 && !r.msgs[0].includes('cannot add a sound'), 'three to-dos, and no "inside the file" sentence when the owner posts by hand');
    const [tiktok, youtube, instagram] = r.msgs.slice(1);
    assert(tiktok.includes('Choose the music first. In TikTok Studio tap Sounds, pick one, then Save.') && youtube.includes('Choose the music first. It must already be inside the video file, or add the sound in the YouTube app instead of Studio.')
      && instagram.includes('Choose the music first. In the Reel editor tap the music icon (Audio), pick one, then Done.'), r.msgs.slice(1).join('\n---\n'));
    for (const m of r.msgs.slice(1)) assert((m.match(/Choose the music first\./g) || []).length === 1, 'one line per to-do');
    // the music is chosen before the caption is pasted and before the post is scheduled
    assert(tiktok.indexOf(MUSIC) < tiktok.indexOf('Paste the caption') && tiktok.indexOf(MUSIC) < tiktok.indexOf('Schedule it for'), tiktok);
    assert(instagram.indexOf(MUSIC) < instagram.indexOf('Paste the caption') && youtube.indexOf(MUSIC) < youtube.indexOf('Paste the title'), 'order of the steps');
    assert(tiktok.replace(/<\/?code>/g, '').match(/[<>]/) === null && instagram.replace(/<\/?code>/g, '').match(/[<>]/) === null, 'still HTML-safe');
    // when the bot posts YouTube and Instagram there is no to-do for them, and so no extra reminder there
    [r] = await action('/approve P1', [basePost], berlin('2026-10-13T20:00'));
    assert(r.msgs.length === 2 && (r.msgs.join('\n').match(/Choose the music first\./g) || []).length === 2, 'approve message + TikTok to-do');
  });
  await test('02 Music: the agents never pick or name a song (prompts, the brief they get, and a check on their texts)', async () => {
    const wf = load(cmds);
    for (const agentName of ['Content agent', 'Post agent']) {
      const sys = wf.nodes.find(n => n.name === agentName).parameters.options.systemMessage;
      assert(sys.includes('the owner chooses the music of every video himself') && sys.includes('Never name, suggest or pick a song, a sound, an artist'), agentName + ' must be told that the owner picks the music');
    }
    assert(!/music|song|sound|audio/i.test(pbrief.prompt), 'the brief for the Post agent must not invite it to talk about music: ' + pbrief.prompt);
    for (const [label, bad] of Object.entries({ 'a note sign': 'Cozy nights ♪ with this lamp', 'a credit': 'Music by DJ Dream', 'an original sound': 'Original sound - someone', 'a trending sound': 'Set to a trending sound',
      'a label': 'Sound: Cozy Nights', 'feat': 'Cozy Nights feat. Someone' })) {
      for (const field of ['caption_tiktok', 'caption_instagram', 'yt_description']) {
        const [q] = await checkTexts({ ...goodTexts, [field]: bad });
        assert(q.ok === false && q.reply.startsWith('Not queued.') && q.reply.includes('a song or sound credit'), `"${bad}" in ${field} (${label}) must not be queued: ` + JSON.stringify(q).slice(0, 160));
      }
    }
    // an ordinary word is fine: a product can really play music, and "sound on" is not a song
    for (const fine of ['Plays music over Bluetooth in a dark room', 'Turn the sound on for the best effect', 'A sound sleeper\'s night light']) {
      const [q] = await checkTexts({ ...goodTexts, caption_instagram: fine });
      assert(q.ok === true, `"${fine}" is fine: ` + JSON.stringify(q).slice(0, 160));
    }
  });
  await test('02 Reject, /posts, /tiktok done, /retry', async () => {
    let [r] = await action('/reject P1', [basePost], berlin('2026-10-13T20:00'));
    assert(r.ok && r.rows[0].status === 'rejected' && r.rows[0].post_at === '' && r.msgs[0].includes('Nothing will be posted'), JSON.stringify(r));
    [r] = await action('/reject P1', [...live, ev('P1', { yt_status: 'scheduled', yt_video_id: 'YT1' })], berlin('2026-10-13T20:30'));
    assert(r.ok && r.rows[0].status === 'rejected' && r.msgs[0].includes('will not post anything more'), r.msgs[0]);
    // An uploaded YouTube video is private until the bot makes it public at the slot: after ❌ Stop it simply stays private
    const m = r.msgs[0];
    assert(m.includes('YouTube has it as a private video: it stays private, nobody can see it. You can delete it if you like') && !m.includes('goes public by itself'), m);
    assert(m.includes('https://studio.youtube.com/video/YT1/edit') && m.includes('1. Open YouTube Studio → Content (left menu).') && m.includes('three dots ⋮ (Options) → Delete forever') && m.includes('3. Tick the box and click Delete forever.'), m);
    assert(!m.match(/[<>]/), 'the message is sent as HTML, so only escaped text is allowed');
    // still private after the slot time (n8n was late, or "make public" failed): still private, not "may be public"
    [r] = await action('/reject P1', [...live, ev('P1', { yt_status: 'scheduled', yt_video_id: 'YT1' })], berlin('2026-10-14T03:30'));
    assert(r.msgs[0].includes('it stays private') && !r.msgs[0].includes('already public'), r.msgs[0]);
    // already public, or being made public: Reject cannot take it back, the owner gets the link and the clicks
    for (const [st, words] of [['published', 'it is already public'], ['publishing', 'it may be public already'], ['stuck', 'it may be public already']]) {
      [r] = await action('/reject P1', [...live, ev('P1', { yt_status: st, yt_video_id: 'YT1' })], berlin('2026-10-14T03:30'));
      assert(r.msgs[0].includes(`YouTube: ${words.startsWith('it is') ? 'it is already public' : 'it was being made public, so it may be public already'}`)
        && r.msgs[0].includes('Rejecting does not remove it, and the bot cannot delete videos') && r.msgs[0].includes('studio.youtube.com/video/YT1/edit'), st + ': ' + r.msgs[0]);
    }
    // being uploaded right now (no id yet, private), a failed or stuck upload (a video may be there), Instagram on its way or out
    [r] = await action('/reject P1', [...live, ev('P1', { yt_status: 'uploading' }), ev('P1', { ig_status: 'publishing' })], berlin('2026-10-13T20:30'));
    assert(r.msgs[0].includes('YouTube is uploading it right now as a private video. It stays private') && r.msgs[0].includes('Delete forever'), r.msgs[0]);
    assert(r.msgs[0].includes('Instagram is busy with it right now') && r.msgs[0].includes('"not posted" means it is stopped'), r.msgs[0]);
    for (const st of ['failed', 'stuck']) {
      [r] = await action('/reject P1', [...live, ev('P1', { yt_status: st })], berlin('2026-10-13T20:30'));
      assert(r.msgs[0].includes('may still have left a video') && r.msgs[0].includes('Delete forever'), st + ': ' + r.msgs[0]);
    }
    [r] = await action('/reject P1', [...live, ev('P1', { ig_status: 'published' })], berlin('2026-10-13T20:30'));
    assert(r.msgs[0].includes('already on Instagram: delete the Reel') && !r.msgs[0].includes('YouTube'), r.msgs[0]);
    [r] = await action('/reject P1', [...live, ev('P1', { ig_status: 'stuck' })], berlin('2026-10-13T20:30'));
    assert(r.msgs[0].includes('Instagram may have posted it'), r.msgs[0]);
    [r] = await action('/reject P1', live, berlin('2026-10-13T20:30'));
    assert(!r.msgs[0].includes('⚠️'), 'nothing is out yet, so there is nothing to delete: ' + r.msgs[0]);
    // Facebook: on its way, out, or unknown
    [r] = await action('/reject P1', [...live, ev('P1', { fb_status: 'publishing' })], berlin('2026-10-13T20:30'));
    assert(r.msgs[0].includes('Facebook is busy with it right now') && r.msgs[0].includes('"not posted" means it is stopped'), r.msgs[0]);
    [r] = await action('/reject P1', [...live, ev('P1', { fb_status: 'published' })], berlin('2026-10-13T20:30'));
    assert(r.msgs[0].includes('already on Facebook: delete the Reel on your Facebook Page'), r.msgs[0]);
    [r] = await action('/reject P1', [...live, ev('P1', { fb_status: 'stuck' })], berlin('2026-10-13T20:30'));
    assert(r.msgs[0].includes('Facebook may have posted it'), r.msgs[0]);
    [r] = await action('/reject P1', [...live, ev('P1', { fb_status: 'queued' })], berlin('2026-10-13T20:30'));
    assert(!r.msgs[0].includes('⚠️'), 'Facebook not started: nothing to delete: ' + r.msgs[0]);
    [r] = await action('/reject P1', [basePost, ev('P1', { status: 'rejected' })], berlin('2026-10-13T20:00'));
    assert(!r.ok && r.reply.includes('already rejected'), r.reply);

    [r] = await action('/posts', [...live, ...approved('P2', '2026-10-12T16:30:00.000Z'), ev('P2', { yt_status: 'scheduled', ig_status: 'published', tiktok_status: 'done' }),
      { ...basePost, id: rowId++, post_id: 'P3' }], berlin('2026-10-13T20:00'));
    assert(r.ok && !r.save && r.msgs.length === 1, 'list only');
    const list = r.msgs[0];
    assert(list.indexOf('WAITING FOR YOUR OK') < list.indexOf('COMING UP') && list.indexOf('COMING UP') < list.indexOf('LAST POSTS'), list);
    assert(list.includes('/approve P3') && list.includes('P1 · Wed 14 Oct at 02:30') && list.includes('YouTube ⏳ waiting · Instagram ⏳ waiting · TikTok ☐ you post it'), list);
    assert(list.includes('P2 · Mon 12 Oct at 18:30') && list.includes('(times in Europe/Berlin)') && list.includes('YouTube ✅ uploaded, private until the slot · Instagram ✅ posted · TikTok ✅ done'), list);
    // Facebook shows up only for posts the bot posts there
    [r] = await action('/posts', [...live, ev('P1', { fb_status: 'published' })], berlin('2026-10-13T20:00'));
    assert(r.msgs[0].includes('Instagram ⏳ waiting · Facebook ✅ posted · TikTok ☐ you post it'), r.msgs[0]);
    [r] = await action('/posts', [{}], berlin('2026-10-13T20:00'));
    assert(r.ok && r.msgs[0].includes('No posts yet') && r.msgs[0].includes('&lt;video link&gt;'), r.msgs[0]);

    [r] = await action('/tiktok P1 done', live, berlin('2026-10-13T21:00'));
    assert(r.ok && r.rows[0].tiktok_status === 'done' && r.rows[0].status === '' && r.msgs[0].includes('/video P1-tt &lt;views&gt;'), JSON.stringify(r).slice(0, 300));
    assert(r.videos.length === 1 && Object.keys(r.videos[0]).join(',') === header('content'), 'content row columns ' + Object.keys(r.videos[0]));
    assert(r.videos[0].content_id === 'P1-tt' && r.videos[0].format === 'tiktok, slot 20:30' && r.videos[0].day === '2026-10-14' && r.videos[0].hook === 'tt cap' && r.videos[0].rules_version === 'R020v1', JSON.stringify(r.videos[0]));
    [r] = await action('/tiktok P1', live, berlin('2026-10-13T21:00'));
    assert(!r.ok && r.reply.startsWith('Usage: /tiktok'), r.reply);
    [r] = await action('/tiktok P1 done', [...live, ev('P1', { tiktok_status: 'done' })], berlin('2026-10-13T21:00'));
    assert(!r.ok && r.reply.includes('already marked'), r.reply);
    [r] = await action('/youtube P1 done', live, berlin('2026-10-13T21:00'));
    assert(!r.ok && r.reply.includes('handled by the bot'), 'the bot posts YouTube here: ' + r.reply);
    [r] = await action('/tiktok P1 done', [basePost], berlin('2026-10-13T21:00'));
    assert(!r.ok && r.reply.includes('not approved'), r.reply);

    [r] = await action('/retry P1', live, berlin('2026-10-13T21:00'));
    assert(!r.ok && r.reply.includes('Nothing to retry'), 'nothing failed: ' + r.reply);
    [r] = await action('/retry P1', [...live, ev('P1', { yt_status: 'scheduled', yt_video_id: 'YT1' }), ev('P1', { ig_status: 'late' })], berlin('2026-10-14T15:00'));
    // 15:00 in Berlin is 09:00 in New York: a late retry is not a lunch or evening post, and its slot says so
    assert(r.ok && r.rows[0].ig_status === 'queued' && r.rows[0].yt_status === '' && r.rows[0].post_at === '2026-10-14T13:00:00.000Z' && r.rows[0].slot === '09:00', 'retry of a late post goes out now: ' + JSON.stringify(r.rows[0]));
    assert(r.msgs[0].includes('Instagram will be tried again') && !r.msgs[0].includes('YouTube') && r.msgs[0].includes('right away'), r.msgs[0]);
    // an uploaded YouTube video that was not made public (late, failed or stuck while being made public) is only made
    // public again: back to "scheduled", never a second upload, and no "posted twice" warning
    for (const st of ['late', 'failed', 'stuck']) {
      [r] = await action('/retry P1', [...live, ev('P1', { yt_status: st, yt_video_id: 'YT1' })], berlin('2026-10-14T15:00'));
      assert(r.ok && r.rows[0].yt_status === 'scheduled' && !r.msgs[0].includes('posted twice') && r.msgs[0].includes('YouTube will be tried again'), st + ': ' + JSON.stringify(r).slice(0, 300));
    }
    [r] = await action('/retry P1', [...live, ev('P1', { fb_status: 'failed' })], berlin('2026-10-14T15:00'));
    assert(r.ok && r.rows[0].fb_status === 'queued' && r.msgs[0].includes('Facebook will be tried again'), JSON.stringify(r).slice(0, 300));
    [r] = await action('/retry P1', [...live, ev('P1', { yt_status: 'failed' }), ev('P1', { ig_status: 'stuck' })], berlin('2026-10-13T21:00'));
    assert(r.ok && r.rows[0].yt_status === 'queued' && r.rows[0].ig_status === 'queued' && r.rows[0].post_at === '' && r.rows[0].slot === '' && r.msgs[0].includes('posted twice'), 'before the slot time the slot stays: ' + JSON.stringify(r));
    // the duplicate warning: for "stuck" (nobody knows) and also for a failed YouTube upload (a video may be there); not for a plain failed Instagram post or a late one
    const warned = async changes => (await action('/retry P1', [...live, ev('P1', changes)], berlin('2026-10-13T21:00')))[0].msgs[0].includes('If it is already there, it will be posted twice');
    assert(await warned({ yt_status: 'failed' }), 'a failed YouTube upload may have left a video: the retry must warn about a second copy');
    assert(await warned({ yt_status: 'stuck' }) && await warned({ ig_status: 'stuck' }), 'stuck warns on both platforms');
    assert(!(await warned({ ig_status: 'failed' })) && !(await warned({ ig_status: 'late' })) && !(await warned({ yt_status: 'late' })), 'nothing was sent in these cases, so no warning');
  });

  // ---- 08: the publisher
  const s08 = { telegram_chat_id: '123', ig_user_id: '17841400000000000', fb_page_id: '1000000000000001', ig_token_expires: 'never', graph_api: 'https://graph.facebook.com/v25.0',
    max_late_hours: 12, stuck_minutes: 30, stats_after_hours: 48, time_zone: 'Europe/Berlin', warn_minutes: 5 };
  const SLOT = '2026-10-25T01:00:00.000+02:00';
  // the owner was warned 10 minutes before the slot (the warning itself has its own tests below)
  const WARNED = '2026-10-24T22:50:00.000Z';
  const livePost = (changes = {}) => [{ ...basePost }, ev('P1', { status: 'approved', post_at: SLOT, yt_status: 'queued', ig_status: 'queued', tiktok_status: 'todo', warned: WARNED, ...changes })];
  const plan = (rows, now, settings = s08) => run(soc, 'Plan this run', { '⚙️ Settings': [settings], 'Load posts': rows }, [], { now });
  await test('08 Plan this run: nothing without the owner\'s OK', async () => {
    assert((await plan([{}], berlin('2026-10-25T01:05'))).length === 0, 'empty table');
    assert((await plan([{ ...basePost, post_at: SLOT, yt_status: 'queued', ig_status: 'queued' }], berlin('2026-10-25T01:05'))).length === 0, 'awaiting_ok is never posted');
    assert((await plan([...livePost(), ev('P1', { status: 'rejected' })], berlin('2026-10-25T01:05'))).length === 0, 'rejected after approval is never posted');
    assert((await plan(livePost({ yt_status: 'todo', ig_status: 'todo' }), berlin('2026-10-25T01:05'))).length === 0, 'platforms the owner posts by hand are left alone');
  });
  await test('08 Plan this run: YouTube right after approval (private), Instagram at slot time, marks first', async () => {
    let [p] = await plan(livePost(), berlin('2026-10-24T20:00'));
    assert(p.ig === null && p.yt && p.yt.post_id === 'P1' && !('publish_at' in p.yt) && p.yt.ai === 'yes' && p.yt.title === 'yt title', JSON.stringify(p.yt));
    assert(p.rows.length === 1 && p.rows[0].yt_status === 'uploading' && p.rows[0].ig_status === '' && Object.keys(p.rows[0]).join(',') === postCols, 'mark row: ' + JSON.stringify(p.rows[0]));
    assert(p.alerts.length === 0, 'no alerts');
    const afterYt = [...livePost(), ev('P1', { yt_status: 'scheduled', yt_video_id: 'YT1' }, '2026-10-24T18:02:00.000Z')];
    assert((await plan(afterYt, berlin('2026-10-25T00:59'))).length === 0, 'Instagram and the YouTube "make public" wait for the slot time');
    [p] = await plan(afterYt, berlin('2026-10-25T01:00'));
    assert(p.yt === null && p.ig && p.ig.create_url === 'https://graph.facebook.com/v25.0/17841400000000000/media' && p.ig.publish_url.endsWith('/17841400000000000/media_publish'), JSON.stringify(p.ig));
    assert(JSON.stringify(p.ig.query) === JSON.stringify({ media_type: 'REELS', video_url: vurl, caption: 'ig cap', share_to_feed: 'true', is_ai_generated: 'true' }), JSON.stringify(p.ig.query));
    // at the slot the private YouTube video is made public, with every status field sent again
    assert(p.yt_pub && p.yt_pub.video_id === 'YT1' && JSON.stringify(p.yt_pub.update) === JSON.stringify({ id: 'YT1', status: { privacyStatus: 'public', selfDeclaredMadeForKids: false,
      embeddable: true, license: 'youtube', publicStatsViewable: true, containsSyntheticMedia: true } }), JSON.stringify(p.yt_pub));
    assert(p.rows.length === 2 && p.rows.find(r => r.ig_status === 'publishing') && p.rows.find(r => r.yt_status === 'publishing'), JSON.stringify(p.rows));
    [p] = await plan([{ ...basePost, ai: 'no' }, ...afterYt.slice(1)], berlin('2026-10-25T01:00'));
    assert(!('is_ai_generated' in p.ig.query) && p.ig.ai === 'no' && p.yt_pub.update.status.containsSyntheticMedia === false, 'no AI label without AI');
    // n8n was off until after the slot: the upload and Instagram in the same run (the upload stays private)
    [p] = await plan(livePost(), berlin('2026-10-25T03:00'));
    assert(p.yt && p.ig && p.rows.length === 2, 'late but inside the limit: ' + JSON.stringify(p));
  });
  await test('08 Plan this run: the double-post guard', async () => {
    const tick1 = berlin('2026-10-25T01:00');
    const rows = [...livePost({ yt_status: 'todo' })];
    const [p1] = await plan(rows, tick1);
    assert(p1.ig && p1.rows[0].ig_status === 'publishing', 'first run takes the post');
    // the mark is in the table before any API call, so no later run takes the post again
    rows.push({ ...p1.rows[0], id: rowId++ });
    assert((await plan(rows, tick1)).length === 0, 'same minute');
    assert((await plan(rows, berlin('2026-10-25T01:10'))).length === 0, 'next run, 10 minutes later');
    // a crash half-way: reported once as stuck, and still never posted by itself
    const [stuck] = await plan(rows, berlin('2026-10-25T01:40'));
    assert(stuck.ig === null && stuck.yt === null && stuck.rows.length === 1 && stuck.rows[0].ig_status === 'stuck' && stuck.alerts[0].includes('/retry P1'), JSON.stringify(stuck));
    rows.push({ ...stuck.rows[0], id: rowId++ });
    assert((await plan(rows, berlin('2026-10-25T01:50'))).length === 0, 'stuck is reported once and not posted');
    for (const st of ['published', 'failed', 'late', 'done']) {
      assert((await plan([...livePost({ yt_status: 'todo' }), ev('P1', { ig_status: st })], berlin('2026-10-25T02:00'))).length === 0, `"${st}" must never be posted again by itself`);
    }
    for (const st of ['uploading', 'scheduled', 'failed', 'late', 'stuck']) {
      assert((await plan([...livePost({ ig_status: 'todo' }), ev('P1', { yt_status: st }, '2026-10-24T23:55:00.000Z')], berlin('2026-10-25T02:00'))).filter(x => x.yt).length === 0, `YouTube "${st}" must never be uploaded again by itself`);
    }
    // only /retry (the owner) puts it back
    const [again] = await plan([...rows, ev('P1', { ig_status: 'queued' })], berlin('2026-10-25T02:00'));
    assert(again.ig && again.rows[0].ig_status === 'publishing', 'after /retry');
    // one post per run and platform
    const two = [...livePost({ yt_status: 'todo' }), { ...basePost, id: rowId++, post_id: 'P2' }, ev('P2', { status: 'approved', post_at: '2026-10-25T00:30:00.000+02:00', yt_status: 'todo', ig_status: 'queued', warned: '2026-10-24T22:20:00.000Z' })];
    const [one] = await plan(two, berlin('2026-10-25T01:00'));
    assert(one.ig.post_id === 'P2' && one.rows.length === 1, 'the oldest due post goes first, the other waits for the next run');
  });
  await test('08 Plan this run: more than max_late_hours late -> not posted, the owner is told', async () => {
    // the slot is 24 Oct 23:00 UTC (01:00 summer time on the night the clocks go back)
    const z = iso => DateTime.fromISO(iso, { zone: 'utc' });
    let [p] = await plan(livePost({ yt_status: 'todo' }), z('2026-10-25T10:59:00'));
    assert(p.ig && p.alerts.length === 0, '11 h 59 min late is still posted');
    [p] = await plan(livePost({ yt_status: 'todo' }), z('2026-10-25T11:01:00'));
    assert(p.ig === null && p.rows.length === 1 && p.rows[0].ig_status === 'late' && p.rows[0].note.includes('passed 12 hours ago'), JSON.stringify(p.rows));
    assert(p.alerts.length === 1 && p.alerts[0].includes('Instagram: P1 was NOT posted') && p.alerts[0].includes('/retry P1'), p.alerts[0]);
    [p] = await plan(livePost(), berlin('2026-10-26T09:00'));
    assert(p.yt === null && p.ig === null && p.rows.map(r => r.yt_status + r.ig_status).join() === 'late,late' && p.alerts.length === 2, 'both platforms: ' + JSON.stringify(p.rows));
    // an uploaded video that is too late to be made public stays private, and the owner is told so
    [p] = await plan(livePost({ yt_status: 'scheduled', yt_video_id: 'YT1', ig_status: 'todo' }), berlin('2026-10-26T09:00'));
    assert(p.yt_pub === null && p.rows[0].yt_status === 'late' && p.alerts[0].includes('was NOT made public') && p.alerts[0].includes('It stays private'), JSON.stringify(p));
    [p] = await plan(livePost({ yt_status: 'todo' }), berlin('2026-10-25T05:00'), { ...s08, max_late_hours: 3 });
    assert(p.ig === null && p.rows[0].ig_status === 'late', 'the limit comes from Settings');
    [p] = await plan(livePost({ yt_status: 'todo' }), berlin('2026-10-25T01:00'), { ...s08, ig_user_id: 'PASTE_YOUR_INSTAGRAM_ACCOUNT_ID' });
    assert(p.ig === null && p.rows[0].ig_status === 'failed' && p.alerts[0].includes('ig_user_id'), 'missing account id: ' + JSON.stringify(p));
  });

  const ytJob = { post_id: 'P1', video_url: vurl, title: 'yt title', description: 'yt desc', ai: 'yes' };
  await test('08 YouTube: upload check + AI declaration keeps every status field', async () => {
    let [u] = await run(soc, 'YouTube uploaded?', { 'YouTube job': [ytJob], 'Download video': [{}] }, [{ uploadId: 'YT1' }]);
    assert(u.ok && u.declare === true && u.video_id === 'YT1' && u.update.id === 'YT1', JSON.stringify(u));
    assert(JSON.stringify(u.update.status) === JSON.stringify({ privacyStatus: 'private', selfDeclaredMadeForKids: false,
      embeddable: true, license: 'youtube', publicStatsViewable: true, containsSyntheticMedia: true }), 'the update must resend private + not made for kids, and no publish time: ' + JSON.stringify(u.update.status));
    [u] = await run(soc, 'YouTube uploaded?', { 'YouTube job': [{ ...ytJob, ai: 'no' }], 'Download video': [{}] }, [{ uploadId: 'YT1' }]);
    assert(u.ok && u.declare === false, 'no declaration without AI');
    [u] = await run(soc, 'YouTube uploaded?', { 'YouTube job': [ytJob], 'Download video': [{}] }, [{ error: 'The request cannot be completed because you have exceeded your quota.' }]);
    assert(!u.ok && !u.declare && u.reason.includes('exceeded your quota') && u.none === false, JSON.stringify(u));
    [u] = await run(soc, 'YouTube uploaded?', { 'YouTube job': [ytJob], 'Download video': [{ error: { message: '404 Not Found' } }] }, [{ error: 'no binary data' }]);
    assert(!u.ok && u.reason.includes('could not be downloaded (404 Not Found)') && u.none === true, 'only a failed download proves that nothing is on YouTube: ' + JSON.stringify(u));
    [u] = await run(soc, 'YouTube uploaded?', { 'YouTube job': [ytJob], 'Download video': [{}] }, [{}]);
    assert(!u.ok && u.reason.includes('did not return a video id') && u.none === false, 'no id = not uploaded, but maybe on YouTube: ' + JSON.stringify(u));
    const wf = load(soc);
    const up = wf.nodes.find(n => n.name === 'YouTube: upload').parameters;
    assert(up.options.privacyStatus === 'private' && up.options.selfDeclaredMadeForKids === false && !('publishAt' in up.options), 'upload must be private (made public later by the bot), not made for kids');
  });
  await test('08 YouTube result: row + message', async () => {
    const set = { '⚙️ Settings': [s08], 'YouTube job': [ytJob], 'Load posts': livePost() };
    const okUp = { ok: true, declare: true, video_id: 'YT1' };
    let [r] = await run(soc, 'YouTube result', { ...set, 'YouTube uploaded?': [okUp] }, [{ id: 'YT1', status: { privacyStatus: 'private', publishAt: '2026-10-24T23:00:00Z', containsSyntheticMedia: true } }]);
    assert(Object.keys(r.row).join(',') === postCols && r.row.yt_status === 'scheduled' && r.row.yt_video_id === 'YT1' && r.row.note === '', JSON.stringify(r.row));
    assert(r.text.includes('is uploaded as a private video. The bot makes it public at its slot, Sun 25 Oct at 01:00 (Europe/Berlin), after your 10-minute warning.') && r.text.includes('studio.youtube.com/video/YT1/edit') && r.text.includes('AI label: set'), r.text);
    [r] = await run(soc, 'YouTube result', { ...set, 'YouTube uploaded?': [okUp] }, [{ error: { code: 403, message: 'Forbidden' } }]);
    assert(r.row.yt_status === 'scheduled' && r.row.note.includes('AI label not confirmed') && r.text.includes('⚠️ AI label') && r.text.includes('Forbidden'), r.text);
    [r] = await run(soc, 'YouTube result', { ...set, 'YouTube uploaded?': [okUp] }, [{ id: 'YT1', status: { privacyStatus: 'public', containsSyntheticMedia: true } }]);
    assert(r.text.includes('shows it as "public", not as a private video'), r.text);
    [r] = await run(soc, 'YouTube result', { ...set, 'YouTube uploaded?': [{ ok: true, declare: false, video_id: 'YT2' }] }, [{ ok: true, declare: false, video_id: 'YT2' }]);
    assert(r.row.yt_video_id === 'YT2' && !r.text.includes('AI label'), r.text);
    [r] = await run(soc, 'YouTube result', { ...set, 'YouTube uploaded?': [{ ok: false, declare: false, none: false, reason: 'quota <exceeded>' }] }, [{}]);
    assert(r.row.yt_status === 'failed' && r.row.yt_video_id === '' && r.row.note === 'YouTube: quota <exceeded>' && r.text.includes('quota &lt;exceeded&gt;') && r.text.includes('/retry P1'), JSON.stringify(r));
    // a failed upload is not proof that nothing is on YouTube (the chunked upload can fail after its last chunk)
    assert(r.text.includes('The upload failed. Check YouTube Studio before you retry: the video may still be there.') && !r.text.includes('Nothing is on YouTube'), r.text);
    // only when the download failed (the upload never started) is it certain
    [r] = await run(soc, 'YouTube result', { ...set, 'YouTube uploaded?': [{ ok: false, declare: false, none: true, reason: 'the video file could not be downloaded (404 Not Found)' }] }, [{}]);
    assert(r.text.includes('Nothing is on YouTube') && !r.text.includes('may still be there') && r.text.includes('/retry P1') && r.row.yt_status === 'failed', r.text);
  });

  const igJob = { post_id: 'P1', ai: 'yes', graph: 'https://graph.facebook.com/v25.0', create_url: 'x', publish_url: 'y', query: {} };
  await test('08 Instagram: container status loop', async () => {
    const st = (json, runIndex = 0) => run(soc, 'Container status', {}, [json], { runIndex }).then(x => x[0]);
    assert((await st({ status_code: 'FINISHED', id: 'C1' })).state === 'done', 'finished');
    assert((await st({ status_code: 'IN_PROGRESS' })).state === 'wait', 'in progress');
    assert((await st({ error: { message: 'temporary' } }, 3)).state === 'wait', 'one failed check is not the end');
    let r = await st({ status_code: 'IN_PROGRESS' }, 19);
    assert(r.state === 'error' && r.sure === true && r.reason.includes('10 minutes'), JSON.stringify(r));
    r = await st({ status_code: 'ERROR', status: 'Error: unsupported video format' });
    assert(r.state === 'error' && r.sure === true && r.reason.includes('unsupported video format'), JSON.stringify(r));
    r = await st({ status_code: 'PUBLISHED' });
    assert(r.state === 'error' && r.sure === false, 'an already published container is never published again: ' + JSON.stringify(r));
  });
  await test('08 Instagram result: published only with a media id', async () => {
    const base = { 'Instagram job': [igJob] };
    let [r] = await run(soc, 'Instagram result', { ...base, 'Instagram: create container': [{ id: 'C1' }], 'Container status': [{ state: 'done' }],
      'Instagram: publish': [{ id: '1790000000' }], 'Instagram: get link': [{ permalink: 'https://www.instagram.com/reel/abc/', id: '1790000000' }] }, [{}]);
    assert(Object.keys(r.row).join(',') === postCols && r.row.ig_status === 'published' && r.row.ig_media_id === '1790000000', JSON.stringify(r.row));
    assert(r.text.includes('P1 is live') && r.text.includes('instagram.com/reel/abc') && r.text.includes('AI info'), r.text);
    [r] = await run(soc, 'Instagram result', { ...base, 'Instagram: create container': [{ error: { message: 'Error validating access token', type: 'OAuthException', code: 190 } }] }, [{}]);
    assert(r.row.ig_status === 'failed' && r.row.ig_media_id === '' && r.row.note.includes('Error validating access token') && r.text.includes('/retry P1'), JSON.stringify(r));
    [r] = await run(soc, 'Instagram result', { ...base, 'Instagram: create container': [{ post_id: 'P1' }] }, [{}]);
    assert(r.row.ig_status === 'failed', 'no container id = failed');
    [r] = await run(soc, 'Instagram result', { ...base, 'Instagram: create container': [{ id: 'C1' }], 'Container status': [{ state: 'error', sure: true, reason: 'Instagram could not use the video (ERROR)' }] }, [{}]);
    assert(r.row.ig_status === 'failed' && r.text.includes('could not use the video'), r.text);
    [r] = await run(soc, 'Instagram result', { ...base, 'Instagram: create container': [{ id: 'C1' }], 'Container status': [{ state: 'error', sure: false, reason: 'already published' }] }, [{}]);
    assert(r.row.ig_status === 'stuck', 'unclear = stuck, the owner looks');
    [r] = await run(soc, 'Instagram result', { ...base, 'Instagram: create container': [{ id: 'C1' }], 'Container status': [{ state: 'done' }],
      'Instagram: publish': [{ error: 'socket hang up' }], 'Instagram: get link': [{ error: 'x' }] }, [{}]);
    assert(r.row.ig_status === 'stuck' && r.row.ig_media_id === '' && r.text.includes('may not have been posted') && r.text.includes('socket hang up'), JSON.stringify(r));
  });
  // The last look before the Reel goes out: up to 10 minutes can lie between "Plan this run" and the publish call
  const marked = [...livePost({ yt_status: 'todo' }), ev('P1', { ig_status: 'publishing' })];
  const recheck = rows => run(soc, 'Check post again (Instagram)', { 'Instagram job': [igJob], 'Reload post (Instagram)': rows }, [{}]).then(x => x[0]);
  await test('08 Instagram: the post is read again right before the publish call (Reject, stuck, never marked)', async () => {
    assert((await recheck(marked)).ok === true, 'approved and marked "publishing" by this run: publish');
    assert((await recheck([...marked, ev('P1', { yt_status: 'scheduled', yt_video_id: 'YT1' })])).ok === true, 'another platform changing does not matter');
    let c = await recheck([...marked, ev('P1', { status: 'rejected' })]);
    assert(c.ok === false && c.rejected === true && c.reason === 'you rejected it before it went out', 'rejected while Instagram converted the video: ' + JSON.stringify(c));
    c = await recheck([...marked, ev('P1', { ig_status: 'stuck' })]);
    assert(c.ok === false && c.rejected === false && c.reason.includes('Instagram status changed to "stuck"'), 'a later run reported it as stuck: ' + JSON.stringify(c));
    c = await recheck([...marked, ev('P1', { ig_status: 'stuck' }), ev('P1', { ig_status: 'queued' })]);
    assert(c.ok === false && c.reason.includes('"queued"'), 'after /retry a new run owns the post, this one must not publish: ' + JSON.stringify(c));
    c = await recheck(livePost({ yt_status: 'todo' }));
    assert(c.ok === false && c.reason.includes('"queued"'), 'never marked = never published (the mark is the double-post guard): ' + JSON.stringify(c));
    c = await recheck([{}]);
    assert(c.ok === false && c.reason.includes('could not be read again'), JSON.stringify(c));
    c = await recheck([...marked, ev('P1', { status: 'awaiting_ok' })]);
    assert(c.ok === false && c.rejected === false && c.reason.includes('status changed to "awaiting_ok"'), JSON.stringify(c));
  });
  await test('08 Instagram result: a post that was rejected (or changed) while the video was prepared is not published and says so', async () => {
    const base = { 'Instagram job': [igJob], 'Instagram: create container': [{ id: 'C1' }], 'Container status': [{ state: 'done' }] };
    let [r] = await run(soc, 'Instagram result', { ...base, 'Check post again (Instagram)': [{ ok: false, rejected: true, reason: 'you rejected it before it went out' }] }, [{}]);
    assert(Object.keys(r.row).join(',') === postCols && r.row.ig_status === 'cancelled' && r.row.ig_media_id === '' && r.row.note === 'Instagram: not posted, you rejected it before it went out', JSON.stringify(r.row));
    assert(r.text.includes('Instagram: P1 was not posted: you rejected it before it went out') && r.text.includes('Nothing is on Instagram'), r.text);
    [r] = await run(soc, 'Instagram result', { ...base, 'Check post again (Instagram)': [{ ok: false, rejected: false, reason: 'its Instagram status changed to "stuck" while the video was being prepared' }] }, [{}]);
    assert(r.row.ig_status === '' && r.row.note.includes('not posted, its Instagram status changed to "stuck"') && r.text.includes('Nothing is on Instagram'), 'the status someone else set is not overwritten: ' + JSON.stringify(r.row));
    // when the check passed, the result is built from the publish call as before
    [r] = await run(soc, 'Instagram result', { ...base, 'Check post again (Instagram)': [{ ok: true }], 'Instagram: publish': [{ id: '1790000000' }], 'Instagram: get link': [{ permalink: 'https://www.instagram.com/reel/abc/', id: '1790000000' }] }, [{}]);
    assert(r.row.ig_status === 'published' && r.row.ig_media_id === '1790000000', JSON.stringify(r.row));
    // the new status is shown in /posts like the others
    const [list] = await action('/posts', [...live, ev('P1', { ig_status: 'cancelled' })], berlin('2026-10-13T20:00'));
    assert(list.msgs[0].includes('Instagram 🚫 cancelled'), list.msgs[0]);
  });

  // ---- 08: daily numbers
  const dayNow = berlin('2026-10-27T21:00');
  const done = (id, post_at, slot, changes) => [{ ...basePost, id: rowId++, post_id: id }, ev(id, { status: 'approved', post_at, slot, yt_status: 'scheduled', yt_video_id: 'YT' + id, ig_status: 'published', ig_media_id: 'IG' + id, tiktok_status: 'done', ...changes })];
  const table = [
    ...done('PA', '2026-10-25T00:30:00.000Z', '20:30'),                                        // 67 h old -> due
    ...done('PB', '2026-10-26T16:30:00.000Z', '12:30'),                                        // 27 h old -> too early
    ...done('PC', '2026-10-20T00:30:00.000Z', '20:30', { stats_done: 'yes' }),                 // already done
    ...done('PD', '2026-10-23T16:30:00.000Z', '12:30', { yt_status: 'todo', yt_video_id: '', ig_status: 'done', ig_media_id: '', tiktok_status: 'todo' }),  // by hand
    { ...basePost, id: rowId++, post_id: 'PE' },                                               // never approved
  ];
  const daily = (rows, now = dayNow, settings = s08) => run(soc, 'Plan daily run', { '⚙️ Settings': [settings], 'Load posts': rows }, [], { now }).then(x => x[0]);
  const igInsights = v => ({ data: Object.entries(v).map(([name, value]) => ({ name, period: 'lifetime', values: [{ value }] })) });
  const stats = async (rows, ytAnswer, igAnswers, now = dayNow, settings = s08, numbers = [{}]) => {
    const planned = await daily(rows, now, settings);
    const calls = await run(soc, 'Instagram calls', { '⚙️ Settings': [settings], 'Plan daily run': [planned] }, []);
    const [out] = await run(soc, 'Build stats', { '⚙️ Settings': [settings], 'Load posts': rows, 'Load feedback': numbers, 'Plan daily run': [planned],
      'YouTube: read stats': [ytAnswer], 'Instagram calls': calls }, igAnswers, { now });
    return { planned, calls, out };
  };
  let statRun;
  await test('08 Daily numbers: posts older than 48 hours, feedback rows like /video', async () => {
    statRun = await stats(table, { items: [{ id: 'YTPA', statistics: { viewCount: '1204', likeCount: '33', commentCount: '2' }, status: { privacyStatus: 'public' } }] },
      [igInsights({ views: 356, reach: 300, likes: 12, comments: 1, shares: 4, saved: 5 })]);
    const { planned, calls, out } = statRun;
    assert(planned.due.map(p => p.post_id).join() === 'PD,PA' && planned.yt_call.url.endsWith('/youtube/v3/videos') && planned.yt_call.query.id === 'YTPA' && planned.yt_call.query.part === 'statistics,status' && planned.use_yt && planned.use_ig && planned.warn === '', JSON.stringify({ ...planned, due: planned.due.map(p => p.post_id) }));
    assert(calls.length === 1 && calls[0].post_id === 'PA' && calls[0].url === 'https://graph.facebook.com/v25.0/IGPA/insights' && calls[0].query.metric === 'views,reach,likes,comments,shares,saved', JSON.stringify(calls));
    // the same shape /video writes, so workflow 05 needs no change
    const [byHand] = await run(cmds, 'Build feedback', { 'Parse command': [{ route: 'video', args: ['V1', '1200', '14', '1'] }] }, []);
    assert(out.feedback.length === 2 && out.feedback.map(f => f.ref).join() === 'PA-yt,PA-ig', JSON.stringify(out.feedback));
    for (const f of out.feedback) {
      assert(Object.keys(f).join(',') === Object.keys(byHand.row).join(',') && Object.keys(f).join(',') === header('feedback'), 'feedback columns ' + Object.keys(f));
      for (const k of Object.keys(f)) assert(typeof f[k] === typeof byHand.row[k], `feedback.${k} must be a ${typeof byHand.row[k]}`);
      assert(f.kind === 'video' && f.clicks === 0 && f.sales === 0 && f.status === '' && f.day === '2026-10-27', JSON.stringify(f));
    }
    assert(out.feedback[0].views === 1204 && out.feedback[0].note.includes('33 likes, 2 comments') && out.feedback[1].views === 356 && out.feedback[1].note.includes('reach 300'), JSON.stringify(out.feedback));
    assert(out.feedback.every(f => f.note.includes('after 48 h, slot 20:30:')), 'the slot is in the note: ' + out.feedback[0].note);
    assert(out.videos.map(v => v.content_id).join() === 'PA-yt,PA-ig' && out.videos.every(v => Object.keys(v).join(',') === header('content')), 'content rows ' + JSON.stringify(out.videos.map(v => v.content_id)));
    assert(out.videos[0].format === 'youtube-short, views only, slot 20:30' && out.videos[0].hook === 'yt title' && out.videos[1].format === 'instagram-reel, views only, slot 20:30' && out.videos[0].day === '2026-10-25', JSON.stringify(out.videos[0]));
    assert(out.rows.length === 2 && out.rows.every(r => r.stats_done === 'yes' && Object.keys(r).join(',') === postCols), JSON.stringify(out.rows.map(r => [r.post_id, r.stats_done])));
    assert(out.rows.every(r => r.post_at === '' && r.slot === '' && r.status === ''), 'the stats run never moves a post or changes a time');
    assert(out.text.includes('PA Star &amp; Moon Lamp: YouTube 1204 views, Instagram 356 views') && out.text.includes('TikTok: send /video PA-tt &lt;views&gt;'), out.text);
    assert(out.text.includes('PD') && out.text.includes('YouTube: not marked as posted. Posted it? Send /youtube PD done') && out.text.includes('Instagram: send /video PD-ig'), out.text);
    assert(!out.text.includes('PB') && !out.text.includes('PC') && !out.text.includes('PE') && !out.text.includes('🔑'), out.text);
  });
  await test('08 Daily numbers reach the Coach and the Content agent unchanged (workflow 05 is not touched)', async () => {
    const { out } = statRun;
    const [n] = await run(coach, 'Compute numbers', { ...coachOutputs, 'Load feedback': [...coachOutputs['Load feedback'], ...out.feedback],
      'Load content': [...coachOutputs['Load content'], ...out.videos] }, []);
    // "views only" tells the Coach that the 0 clicks and 0 sales of a bot-read row are "not known", not "none"
    // and "slot 20:30" lets the Coach compare lunch against evening (the Coach's prompt shows the format, not the note)
    assert(n.prompt.includes('- PA-yt [youtube-short, views only, slot 20:30] "yt title" (Star & Moon Lamp; rules R020v1): 1204 views, 0 clicks, 0 sales'), n.prompt.slice(0, 900));
    assert(n.prompt.includes('- PA-ig [instagram-reel, views only, slot 20:30] "ig cap"') && n.unmeasured === 1, 'Instagram row, and no extra reminder for videos the bot measured');
    const [b] = await run(cmds, 'Build content brief', { 'Parse command': [{ route: 'content', args: ['cj333-bk'] }], 'Load products': priced,
      'Load feedback': out.feedback, 'Load content history': out.videos, 'Load playbook': playbook }, []);
    assert(b.prompt.includes('"yt title" (youtube-short, views only, slot 20:30) -> 1204 views'), 'the Content agent learns from posts too');
  });
  await test('08 Daily numbers: best and weakest video of the last 7 days, with platform and slot', async () => {
    const ytA = { items: [{ id: 'YTPA', statistics: { viewCount: '1204', likeCount: '33', commentCount: '2' }, status: { privacyStatus: 'public' } }] };
    const igA = [igInsights({ views: 356 })];
    // only today's two numbers: PA on YouTube against PA on Instagram
    let { out } = await stats(table, ytA, igA);
    assert(out.text.includes('🏆 Last 7 days: best PA on YouTube, 1204 views, slot 20:30 (02:30 in Europe/Berlin). Weakest PA on Instagram, 356 views, slot 20:30 (02:30 in Europe/Berlin).'), out.text);
    // with the numbers of the week from the feedback table (the bot's own and the ones sent with /video)
    const week = [
      { kind: 'video', ref: 'PD-ig', views: 12000, clicks: 40, sales: 2, day: '2026-10-26' },   // the owner sent these with /video
      { kind: 'video', ref: 'PC-yt', views: 40, clicks: 0, sales: 0, day: '2026-10-22' },
      { kind: 'video', ref: 'PC-yt', views: 87, clicks: 0, sales: 0, day: '2026-10-23' },       // newer numbers for the same video win
      { kind: 'video', ref: 'PC-ig', views: 3, clicks: 0, sales: 0, day: '2026-10-20' },        // older than 7 days
      { kind: 'video', ref: 'V1', views: 99999, clicks: 1, sales: 0, day: '2026-10-26' },       // a /content script, not a post
      { kind: 'product', ref: 'PC-yt', views: 0, day: '2026-10-26' },
    ];
    ({ out } = await stats(table, ytA, igA, dayNow, s08, week));
    assert(out.text.includes('🏆 Last 7 days: best PD on Instagram, 12000 views, slot 12:30 (18:30 in Europe/Berlin). Weakest PC on YouTube, 87 views, slot 20:30 (02:30 in Europe/Berlin).'), out.text);
    assert(out.rows.every(r => r.post_at === '' && r.slot === ''), 'the times are never changed by the bot');
    assert(!out.text.includes('/video PD-ig') && out.text.includes('/video PA-tt'), 'numbers the owner already sent are not asked for again: ' + out.text);
    // one number is nothing to compare
    ({ out } = await stats(table.slice(0, 2), ytA, [{ error: 'x' }]));
    assert(out.feedback.length === 1 && !out.text.includes('🏆'), out.text);
  });
  await test('08 Daily numbers: one platform fails -> asked again tomorrow, nothing written twice', async () => {
    let { out } = await stats(table.slice(0, 2), { items: [{ id: 'YTPA', statistics: { viewCount: '9' }, status: { privacyStatus: 'private' } }] }, [{ error: { message: 'Please reduce the amount of data', code: 1 } }]);
    assert(out.feedback.map(f => f.ref).join() === 'PA-yt' && out.videos.length === 1 && out.rows[0].stats_done === 'yt', JSON.stringify(out.rows));
    assert(out.text.includes('still shows it as "private"') && out.text.includes('Instagram: numbers not readable today (Please reduce'), out.text);
    assert(out.text.includes('🔑 Instagram did not answer the daily check: Please reduce') && !out.text.includes('🔑 YouTube'), 'the reason is passed on: ' + out.text);
    const next = [...table.slice(0, 2), ev('PA', { stats_done: 'yt' })];
    const second = await stats(next, { items: [] }, [igInsights({ views: 80, likes: 2 })], berlin('2026-10-28T21:00'));
    assert(!('id' in second.planned.yt_call.query) && second.calls[0].post_id === 'PA', 'YouTube is not asked again');
    assert(second.out.feedback.map(f => f.ref).join() === 'PA-ig' && second.out.videos.map(v => v.content_id).join() === 'PA-ig' && second.out.rows[0].stats_done === 'yes', JSON.stringify(second.out.rows));
    assert(!second.out.text.includes('/video PA-tt'), 'the TikTok reminder is sent once');
    // still nothing after a week: stop asking
    const week = await stats([...table.slice(0, 2), ev('PA', { stats_done: 'tried' })], { error: 'timeout' }, [{ error: 'timeout' }], berlin('2026-11-05T21:00'));
    assert(week.out.feedback.length === 0 && week.out.rows[0].stats_done === 'yes', 'give up after 7 days: ' + JSON.stringify(week.out.rows));
    // a deleted YouTube video
    const gone = await stats(table.slice(0, 2), { items: [] }, [igInsights({ views: 5 })]);
    assert(gone.out.feedback.map(f => f.ref).join() === 'PA-ig' && gone.out.rows[0].stats_done === 'yes' && gone.out.text.includes('video not found'), gone.out.text);
  });
  await test('08 Daily check: logins and the token end date', async () => {
    // nothing due: one small call per platform proves the logins still work, and the owner hears nothing
    const quiet = await stats(table.slice(2, 4), { kind: 'youtube#channelListResponse', items: [{ id: 'UC123' }] }, [{ username: 'pivendoteam', id: '17841400000000000' }], berlin('2026-10-21T21:00'));
    assert(quiet.planned.due.length === 0 && quiet.planned.yt_call.url.endsWith('/youtube/v3/channels') && quiet.planned.yt_call.query.mine === 'true' && quiet.calls[0].url === 'https://graph.facebook.com/v25.0/17841400000000000' && quiet.calls[0].query.fields === 'username', JSON.stringify(quiet.calls));
    assert(quiet.out.text === '' && quiet.out.feedback.length === 0 && quiet.out.rows.length === 0, 'silent when all is fine: ' + quiet.out.text);
    assert((await run(soc, 'Daily summary', {}, [quiet.out])).length === 0, 'no empty message');
    const broken = await stats(table.slice(2, 4), { error: { code: 401, message: 'Invalid Credentials' } }, [{ error: { message: 'Error validating access token: Session has expired', type: 'OAuthException', code: 190 } }], berlin('2026-10-21T21:00'));
    assert(broken.out.text.includes('🔑 YouTube did not answer the daily check: Invalid Credentials') && broken.out.text.includes('🔑 Instagram did not answer the daily check: Error validating access token'), broken.out.text);
    assert(broken.out.text.includes('"YouTube (Pivendo)"') && broken.out.text.includes('"Instagram (Pivendo)"'), 'names the credential to fix');
    // platforms the bot does not post on are not checked
    const byHand = await stats(table.slice(6, 8), { error: 'no credentials' }, [{ error: 'no credentials' }], berlin('2026-10-24T21:00'));
    assert(!byHand.planned.use_yt && !byHand.planned.use_ig && !byHand.out.text.includes('🔑'), 'no alarm for unused platforms: ' + byHand.out.text);
    // a token with an end date: warned from 14 days before, every evening
    const warn = async date => (await daily(table.slice(2, 4), berlin('2026-10-21T21:00'), { ...s08, ig_token_expires: date })).warn;
    assert(await warn('never') === '' && await warn('') === '' && await warn('2026-11-30') === '', 'no warning');
    assert((await warn('2026-11-06')) === '', '15 days before: not yet');
    assert((await warn('2026-11-05')).includes('runs out in 14 day(s)'), '14 days before: first warning');
    assert((await warn('2026-11-04')).includes('runs out in 13 day(s), on 4 Nov 2026'), await warn('2026-11-04'));
    assert((await warn('2026-11-01')).includes('runs out in 10 day(s)'), 'warned at least 10 days before');
    assert((await warn('2026-10-20')).includes('ran out on 20 Oct 2026'), await warn('2026-10-20'));
    const withWarn = await stats(table.slice(2, 4), { items: [] }, [{ username: 'pivendoteam' }], berlin('2026-10-21T21:00'), { ...s08, ig_token_expires: '2026-11-01' });
    assert(withWarn.out.text.includes('runs out in 10 day(s)'), withWarn.out.text);
    // setup help: while ig_user_id is empty, the check asks Meta for the account and tells the owner its ID
    const noId = { ...s08, ig_user_id: 'PASTE_YOUR_INSTAGRAM_ACCOUNT_ID' };
    const first = await stats([{}], { items: [] }, [{ data: [{ name: 'Pivendo', id: '1055', instagram_business_account: { id: '17841400000000000', username: 'pivendoteam' } }] }], berlin('2026-10-21T21:00'), noId);
    assert(first.calls[0].url === 'https://graph.facebook.com/v25.0/me/accounts' && first.calls[0].query.fields.includes('instagram_business_account'), JSON.stringify(first.calls));
    assert(first.out.text.includes('🆔 Your Instagram account ID is 17841400000000000 (@pivendoteam)') && first.out.text.includes('ig_user_id'), first.out.text);
    assert(!first.out.text.includes('Facebook Page ID'), 'fb_page_id is set here: ' + first.out.text);
    // the same help for the Facebook Page ID, also when the Instagram ID is already set
    const noPage = { ...s08, fb_page_id: 'PASTE_YOUR_FACEBOOK_PAGE_ID' };
    const fbHelp = await stats([{}], { items: [] }, [{ data: [{ name: 'Pivendo', id: '1055', instagram_business_account: { id: '17841400000000000', username: 'pivendoteam' } }] }], berlin('2026-10-21T21:00'), noPage);
    assert(fbHelp.calls[0].url === 'https://graph.facebook.com/v25.0/me/accounts', JSON.stringify(fbHelp.calls));
    assert(fbHelp.out.text.includes('🆔 Your Facebook Page ID is 1055 (Pivendo)') && fbHelp.out.text.includes('fb_page_id') && !fbHelp.out.text.includes('Instagram account ID'), fbHelp.out.text);
    const noLink = await stats([{}], { items: [] }, [{ data: [{ name: 'Pivendo', id: '1055' }] }], berlin('2026-10-21T21:00'), noId);
    assert(noLink.out.text.includes('has no Instagram account linked'), noLink.out.text);
    const noToken = await stats([{}], { error: 'x' }, [{ error: { message: 'An active access token must be used', code: 2500 } }], berlin('2026-10-21T21:00'), noId);
    assert(noToken.out.text === '', 'before the setup is done the evening run stays silent: ' + noToken.out.text);
  });
  await test('08 Workflow shape: nothing reaches a platform before the mark is saved; credentials; schedules', async () => {
    const wf = load(soc);
    const next = name => ((wf.connections[name] || {}).main || []).flat().map(c => c.node);
    const reach = (from, without) => { const seen = new Set(); const todo = [...from];
      while (todo.length) { const n = todo.pop(); if (seen.has(n) || n === without) continue; seen.add(n); todo.push(...next(n)); } return seen; };
    const triggers = wf.nodes.filter(n => n.type === 'n8n-nodes-base.scheduleTrigger').map(n => n.name);
    assert(triggers.join() === 'Every 5 minutes,Every evening 21:00', triggers.join());
    const cron = Object.fromEntries(wf.nodes.filter(n => triggers.includes(n.name)).map(n => [n.name, n.parameters.rule.interval[0].expression]));
    assert(cron['Every 5 minutes'] === '*/5 * * * *' && cron['Every evening 21:00'] === '0 21 * * *', JSON.stringify(cron));
    const coachCron = load(coach).nodes.find(n => n.type === 'n8n-nodes-base.scheduleTrigger').parameters.rule.interval[0].expression;
    assert(coachCron === '30 21 * * *', 'the numbers must be saved before the Coach runs: ' + coachCron);
    const all = reach(triggers), unmarked = reach(triggers, 'Save marks');
    for (const n of ['Download video', 'YouTube: upload', 'YouTube: declare AI content', 'YouTube: make public', 'Instagram: create container', 'Instagram: publish',
      'Facebook: page key', 'Facebook: start', 'Facebook: upload', 'Facebook: publish', 'Warn with video', 'Warn with text']) {
      assert(all.has(n) && !unmarked.has(n), `"${n}" must only run after "Save marks"`);
    }
    const posting = wf.nodes.filter(n => n.type === 'n8n-nodes-base.httpRequest' && n.name !== 'Download video');
    assert(posting.length === 12 && posting.every(n => n.onError === 'continueRegularOutput'), 'API calls: ' + posting.map(n => n.name));
    const stored = posting.filter(n => n.parameters.authentication === 'predefinedCredentialType');
    assert(stored.filter(n => n.parameters.nodeCredentialType === 'youTubeOAuth2Api').length === 3 && stored.filter(n => n.parameters.nodeCredentialType === 'facebookGraphApi').length === 6, 'credential types: ' + stored.map(n => n.name));
    // Facebook Reels need a Page key: read at run time with the stored Meta login, and used only by the three Reel calls
    const pageKeyed = posting.filter(n => n.parameters.authentication === 'none');
    assert(pageKeyed.map(n => n.name).sort().join() === 'Facebook: publish,Facebook: start,Facebook: upload', 'calls with the Page key: ' + pageKeyed.map(n => n.name));
    for (const n of pageKeyed) {
      const used = JSON.stringify(n.parameters).includes("$('Facebook: page key').first().json.access_token");
      assert(used, `${n.name} must use the Page key read in this run`);
    }
    // The marks are the double-post guard, so the node that saves them has no error setting at all: if the marks
    // cannot be saved, the run stops with an error and nothing is sent to YouTube or Instagram.
    const marks = wf.nodes.find(n => n.name === 'Save marks');
    assert(marks.type === 'n8n-nodes-base.dataTable' && marks.parameters.operation === 'insert' && marks.parameters.dataTableId.value === 'social_posts', '"Save marks" is the insert into social_posts');
    assert(!('onError' in marks) && !('continueOnFail' in marks) && !('alwaysOutputData' in marks), '"Save marks" must not continue on error: ' + JSON.stringify(marks));
    // every node that WRITES to YouTube or Instagram is reachable only through "Save marks" (the evening run only reads)
    const writes = wf.nodes.filter(n => n.type === 'n8n-nodes-base.youTube' || (n.type === 'n8n-nodes-base.httpRequest'
      && ['youTubeOAuth2Api', 'facebookGraphApi'].includes(n.parameters.nodeCredentialType) && n.parameters.method !== 'GET'));
    writes.push(...pageKeyed);
    assert(writes.map(n => n.name).sort().join() === 'Facebook: publish,Facebook: start,Facebook: upload,Instagram: create container,Instagram: publish,YouTube: declare AI content,YouTube: make public,YouTube: upload', 'nodes that write: ' + writes.map(n => n.name));
    for (const n of writes) assert(all.has(n.name) && !unmarked.has(n.name), `"${n.name}" writes to a platform and must only run after "Save marks"`);
    // and the Reel is only published through the last look at the post
    const unlooked = reach(triggers, 'Still approved? (Instagram)');
    assert(all.has('Instagram: publish') && !unlooked.has('Instagram: publish'), '"Instagram: publish" must only run after "Still approved? (Instagram)"');
    const verdict = wf.connections['Still approved? (Instagram)'].main;
    assert(verdict[0].map(c => c.node).join() === 'Instagram: publish' && verdict[1].map(c => c.node).join() === 'Instagram result', 'true = publish, false = report why not');
    assert(wf.connections['Container ready?'].main[0].map(c => c.node).join() === 'Reload post (Instagram)', 'the wait loop ends with a fresh read of the post');
    // the Facebook Reel too: published only through the last look at the post, after the upload
    const unlookedFb = reach(triggers, 'Still approved? (Facebook)');
    assert(all.has('Facebook: publish') && !unlookedFb.has('Facebook: publish'), '"Facebook: publish" must only run after "Still approved? (Facebook)"');
    const fbVerdict = wf.connections['Still approved? (Facebook)'].main;
    assert(fbVerdict[0].map(c => c.node).join() === 'Facebook: publish' && fbVerdict[1].map(c => c.node).join() === 'Facebook result', 'true = publish, false = report why not');
    // the warning carries the ❌ Stop button that workflow 02 already understands ("reject:P…")
    for (const name of ['Warn with video', 'Warn with text']) {
      const b = wf.nodes.find(n => n.name === name).parameters.inlineKeyboard.rows[0].row.buttons;
      assert(b.length === 1 && b[0].text === '❌ Stop' && b[0].additionalFields.callback_data.includes("'reject:'"), name + ': ' + JSON.stringify(b));
    }
    // a Telegram message that cannot be sent must never stop the posting branches that come after it
    const telegrams = wf.nodes.filter(n => n.type === 'n8n-nodes-base.telegram');
    assert(telegrams.length === 8 && telegrams.every(n => n.onError === 'continueRegularOutput'), 'every Telegram node in 08 must continue on error: ' + telegrams.map(n => n.name + ':' + n.onError));
    // the bot has no call that deletes a video or a Reel
    for (const f of [soc, cmds, intake]) for (const n of load(f).nodes) {
      assert(String((n.parameters || {}).method || '').toUpperCase() !== 'DELETE' && !(n.type === 'n8n-nodes-base.youTube' && /delete/i.test(String(n.parameters.operation))), `"${n.name}" deletes something`);
    }
    // no secrets in the workflow files: the only "access_token" values are the Page key read at run time
    for (const f of [soc, cmds, intake]) {
      const text = JSON.stringify(load(f));
      assert(!/client_secret|Bearer |EAA[A-Za-z0-9]{20}|ya29\./.test(text), 'no secrets in ' + f);
      for (const n of load(f).nodes) for (const q of ((n.parameters.queryParameters || {}).parameters || [])) {
        if (q.name === 'access_token') assert(q.value === "={{ $('Facebook: page key').first().json.access_token }}", `${n.name}: access_token must be the Page key read at run time`);
      }
    }
    // community nodes are not allowed; only nodes that ship with n8n
    for (const f of [soc, cmds, intake]) assert(load(f).nodes.every(n => /^(n8n-nodes-base|@n8n\/n8n-nodes-langchain)\./.test(n.type)), 'built-in nodes only in ' + f);
    // every Telegram text built by the new nodes is sent as HTML (plain Markdown breaks on "_" in links and hashtags)
    const html = n => n.parameters.additionalFields && n.parameters.additionalFields.parse_mode === 'HTML';
    assert(wf.nodes.filter(n => n.type === 'n8n-nodes-base.telegram').every(html), '08 Telegram nodes must use HTML');
    for (const name of ['Ask to approve post', 'Queue problem', 'Send post action', 'Post action problem']) assert(html(load(cmds).nodes.find(n => n.name === name)), name + ' must use HTML');
    const ask = load(cmds).nodes.find(n => n.name === 'Ask to approve post').parameters;
    const buttons = ask.inlineKeyboard.rows[0].row.buttons;
    assert(ask.replyMarkup === 'inlineKeyboard' && buttons.length === 2 && buttons[0].additionalFields.callback_data.includes("'approve:'") && buttons[1].additionalFields.callback_data.includes("'reject:'"), JSON.stringify(buttons));
  });

  await test('02 + 08 small pass-on nodes, and the start values in Settings', async () => {
    const rowA = { post_id: 'P1', status: 'approved' }, rowB = { post_id: 'P1', tiktok_status: 'done' };
    const act = { 'Build post action': [{ rows: [rowA, rowB], videos: [{ content_id: 'P1-tt' }], msgs: ['one', 'two'] }] };
    assert(JSON.stringify(await run(cmds, 'Post action rows', act, [{}])) === JSON.stringify([rowA, rowB]), 'Post action rows');
    assert(JSON.stringify(await run(cmds, 'Post video rows', act, [{}])) === '[{"content_id":"P1-tt"}]', 'Post video rows');
    assert(JSON.stringify(await run(cmds, 'Post action messages', act, [{}])) === '[{"text":"one"},{"text":"two"}]', 'Post action messages');
    assert(JSON.stringify(await run(cmds, 'Post row', {}, [{ ok: true, row: rowA, text: 't' }])) === JSON.stringify([rowA]), 'Post row');
    const planned = { rows: [rowA], alerts: ['late!'], yt: { post_id: 'P1' }, ig: null };
    assert(JSON.stringify(await run(soc, 'Mark rows', {}, [planned])) === JSON.stringify([rowA]), 'Mark rows');
    assert(JSON.stringify(await run(soc, 'Alerts', { 'Plan this run': [planned] }, [{}])) === '[{"text":"late!"}]', 'Alerts');
    assert(JSON.stringify(await run(soc, 'YouTube job', { 'Plan this run': [planned] }, [{}])) === '[{"post_id":"P1"}]', 'YouTube job');
    assert((await run(soc, 'Instagram job', { 'Plan this run': [planned] }, [{}])).length === 0, 'no Instagram job -> that branch does not run');
    assert((await run(soc, 'Alerts', { 'Plan this run': [{ ...planned, alerts: [] }] }, [{}])).length === 0, 'no alerts -> no message');
    for (const n of ['YouTube row', 'Instagram row']) assert(JSON.stringify(await run(soc, n, {}, [{ row: rowA, text: 't' }])) === JSON.stringify([rowA]), n);
    const built = { feedback: [{ ref: 'P1-yt' }], videos: [{ content_id: 'P1-yt' }], rows: [rowB], text: 'hello' };
    assert(JSON.stringify(await run(soc, 'Feedback rows', {}, [built])) === '[{"ref":"P1-yt"}]', 'Feedback rows');
    assert(JSON.stringify(await run(soc, 'Video rows', {}, [built])) === '[{"content_id":"P1-yt"}]', 'Video rows');
    assert(JSON.stringify(await run(soc, 'Stats done rows', {}, [built])) === JSON.stringify([rowB]), 'Stats done rows');
    assert(JSON.stringify(await run(soc, 'Daily summary', {}, [built])) === '[{"text":"hello"}]', 'Daily summary');
    // start values the docs promise: the bot posts nothing by itself until the owner switches a platform to "yes"
    const settingsOf = f => Object.fromEntries(load(f).nodes.find(n => n.name === '⚙️ Settings').parameters.assignments.assignments.map(a => [a.name, a.value]));
    const a = settingsOf(cmds), b = settingsOf(soc);
    assert(a.post_times === '12:30,20:30' && a.post_timezone === 'America/New_York' && a.time_zone === 'Europe/Berlin' && a.min_lead_hours === 2, JSON.stringify(a));
    assert(a.youtube_auto === 'no' && a.instagram_auto === 'no' && a.shop_url === 'pivendo.com' && !('post_time' in a), JSON.stringify(a));
    assert(b.max_late_hours === 12 && b.stats_after_hours === 48 && b.ig_token_expires === 'never' && b.time_zone === 'Europe/Berlin' && String(b.ig_user_id).startsWith('PASTE'), JSON.stringify(b));
    // the money settings of the other workflows are not touched by this change
    const research01 = settingsOf(research), pay07 = settingsOf(ap);
    assert(research01.markup === 1.5 && research01.min_profit_usd === 7, 'workflow 01 pricing: ' + JSON.stringify(research01));
    assert(pay07.auto_pay === 'no' && pay07.max_order_usd === 40 && pay07.daily_limit_usd === 100 && pay07.min_profit_usd === 3, 'workflow 07 money rules: ' + JSON.stringify(pay07));
  });

  // ---- 08: the warning 5-10 minutes before a post goes public (owner's rule, 14 Oct: no answer = it goes out)
  const unwarned = (changes = {}) => livePost({ warned: '', yt_status: 'todo', ...changes }).map(r => { const x = { ...r }; delete x.warned; return x; });
  await test('08 Warning: about 10 minutes before the slot, once, with the video; nothing goes public before it', async () => {
    // 30 and 11 minutes before: nothing yet
    assert((await plan(unwarned(), berlin('2026-10-25T00:30'))).length === 0, '30 minutes before: nothing');
    assert((await plan(unwarned(), berlin('2026-10-25T00:49'))).length === 0, '11 minutes before: nothing');
    // 10 minutes before: the warning, and it is marked before it is sent
    let [p] = await plan(unwarned({ tg_file_id: 'TGFILE1' }), berlin('2026-10-25T00:50'));
    assert(p.warn && p.warn.post_id === 'P1' && p.warn.file === 'TGFILE1' && p.ig === null && p.yt === null, JSON.stringify(p));
    assert(p.rows.length === 1 && p.rows[0].warned === '2026-10-24T22:50:00.000Z' && Object.keys(p.rows[0]).join(',') === postCols, JSON.stringify(p.rows));
    assert(p.warn.text.includes('⏰ In about 10 minutes P1 goes out on Instagram.') && p.warn.text.includes('Star &amp; Moon Lamp (AI label on)')
      && p.warn.text.includes("Don't like it? Tap ❌ Stop. No answer = it goes out."), p.warn.text);
    assert(p.warn.fallback.includes('Video: ' + vurl) && p.warn.fallback.includes('/reject P1') && p.warn.text.length < 1000, p.warn.fallback);
    // a video without a Telegram file (queued with a link) is warned with its link
    [p] = await plan(unwarned(), berlin('2026-10-25T00:52'));
    assert(p.warn.file === vurl, p.warn.file);
    // every platform the bot still has to make public is named
    [p] = await plan(unwarned({ yt_status: 'scheduled', yt_video_id: 'YT1', fb_status: 'queued' }), berlin('2026-10-25T00:52'));
    assert(p.warn.text.includes('goes out on YouTube, Instagram, Facebook.'), p.warn.text);
    // at the slot time without a warning: nothing is made public, the warning goes out first
    [p] = await plan(unwarned({ yt_status: 'scheduled', yt_video_id: 'YT1', fb_status: 'queued' }), berlin('2026-10-25T01:00'));
    assert(p.warn && p.ig === null && p.yt_pub === null && p.fb === null && p.rows.length === 1, 'warning first: ' + JSON.stringify(p));
  });
  await test('08 Warning: the post waits warn_minutes after the warning, also when the warning came late', async () => {
    const warnedAt = iso => livePost({ yt_status: 'scheduled', yt_video_id: 'YT1', fb_status: 'queued', warned: utc(iso) });
    // warned 10 minutes before: everything goes at the slot
    let [p] = await plan(warnedAt('2026-10-25T00:50'), berlin('2026-10-25T01:00'));
    assert(p.ig && p.yt_pub && p.fb && !p.warn, JSON.stringify(p));
    // n8n was off: warned only at 01:30, half an hour after the slot -> not before 01:34 (5 minutes, one minute of slack)
    assert((await plan(warnedAt('2026-10-25T01:30'), berlin('2026-10-25T01:33'))).length === 0, '3 minutes after the warning: still waiting');
    [p] = await plan(warnedAt('2026-10-25T01:30'), berlin('2026-10-25T01:35'));
    assert(p.ig && p.yt_pub && p.fb, '5 minutes after the warning: out');
    // a missed warning is sent late (here 30 minutes after the slot), and only one warning per run
    const two = [...unwarned({ tg_file_id: 'A' }), { ...basePost, id: rowId++, post_id: 'P2' },
      ev('P2', { status: 'approved', post_at: '2026-10-25T01:10:00.000+02:00', yt_status: 'todo', ig_status: 'queued', tiktok_status: 'todo' })];
    [p] = await plan(two, berlin('2026-10-25T01:30'));
    assert(p.warn.post_id === 'P1' && p.rows.length === 1 && p.warn.text.includes('In about 5 minutes'), 'the oldest first: ' + JSON.stringify(p));
    two.push({ ...p.rows[0], id: rowId++ });
    [p] = await plan(two, berlin('2026-10-25T01:35'));
    assert(p.warn.post_id === 'P2' && p.ig && p.ig.post_id === 'P1', 'next run: P2 is warned, P1 goes out: ' + JSON.stringify(p));
    // "failed" = the warning did not arrive: it is sent again and nothing is posted meanwhile
    [p] = await plan(livePost({ yt_status: 'todo', warned: 'failed' }), berlin('2026-10-25T01:05'));
    assert(p.warn && p.ig === null, 'resend after a failed warning: ' + JSON.stringify(p));
    // no warning for a post the owner posts all by himself, nor for a rejected one, nor when it is too late anyway
    assert((await plan(unwarned({ ig_status: 'todo' }), berlin('2026-10-25T00:55'))).length === 0, 'all by hand: no warning');
    assert((await plan([...unwarned(), ev('P1', { status: 'rejected' })], berlin('2026-10-25T00:55'))).length === 0, 'stopped: no warning');
    [p] = await plan(unwarned(), berlin('2026-10-26T09:00'));
    assert(!p.warn && p.rows[0].ig_status === 'late', 'too late: reported, not warned');
    // the warning time comes from Settings
    [p] = await plan(unwarned(), berlin('2026-10-25T00:44'), { ...s08, warn_minutes: 15 });
    assert(p.warn && p.warn.text.includes('In about 16 minutes'), JSON.stringify(p.warn));
  });
  await test('08 Warning nodes: video first, then text, then "failed" so the next run tries again', async () => {
    const job = { post_id: 'P1', file: 'TGFILE1', text: 't', fallback: 'f' };
    let [w] = await run(soc, 'Warning sent?', { 'Warning job': [job] }, [{ ok: true, result: { message_id: 7 } }]);
    assert(w.sent === true && w.post_id === 'P1', JSON.stringify(w));
    [w] = await run(soc, 'Warning sent?', { 'Warning job': [job] }, [{ error: { message: 'Bad Request: wrong file identifier' } }]);
    assert(w.sent === false && w.fallback === 'f', JSON.stringify(w));
    assert((await run(soc, 'Warning failed?', { 'Warning job': [job] }, [{ ok: true, result: { message_id: 8 } }])).length === 0, 'the text arrived: nothing to save');
    const [row] = await run(soc, 'Warning failed?', { 'Warning job': [job] }, [{ error: { message: 'Forbidden: bot was blocked by the user' } }]);
    assert(row.post_id === 'P1' && row.warned === 'failed' && row.note.includes('bot was blocked') && Object.keys(row).join(',') === postCols, JSON.stringify(row));
    assert((await run(soc, 'Warning job', { 'Plan this run': [{ warn: null }] }, [{}])).length === 0 && (await run(soc, 'Warning job', { 'Plan this run': [{ warn: job }] }, [{}]))[0].file === 'TGFILE1', 'Warning job');
    const wf = load(soc);
    const video = wf.nodes.find(n => n.name === 'Warn with video').parameters;
    assert(video.operation === 'sendVideo' && video.file === '={{ $json.file }}' && video.additionalFields.caption === '={{ $json.text }}', JSON.stringify(video));
    assert(wf.connections['Video warning arrived?'].main[1].map(c => c.node).join() === 'Warn with text' && !(wf.connections['Video warning arrived?'].main[0] || []).length, 'only a missing video warning goes on to the text warning');
  });

  // ---- 08: YouTube made public at the slot, Facebook Reels
  await test('08 YouTube: made public at the slot; a locked or failed one stays private and the owner is told', async () => {
    let [p] = await plan(livePost({ yt_status: 'publishing', yt_video_id: 'YT1', ig_status: 'todo' }), berlin('2026-10-25T01:31'));
    assert(p.rows[0].yt_status === 'stuck' && p.alerts[0].includes('making P1 public did not finish') && p.alerts[0].includes('/retry P1'), JSON.stringify(p));
    const job = { post_id: 'P1', video_id: 'YT1' };
    let [r] = await run(soc, 'YouTube public result', { 'YouTube publish job': [job] }, [{ id: 'YT1', status: { privacyStatus: 'public' } }]);
    assert(r.row.yt_status === 'published' && r.text.includes('📺 YouTube: P1 is public now.') && r.text.includes('https://youtube.com/shorts/YT1') && Object.keys(r.row).join(',') === postCols, JSON.stringify(r));
    [r] = await run(soc, 'YouTube public result', { 'YouTube publish job': [job] }, [{ id: 'YT1', status: { privacyStatus: 'private' } }]);
    assert(r.row.yt_status === 'failed' && r.text.includes('YouTube still shows it as "private"') && r.text.includes('Private (locked)') && r.text.includes('/retry P1') && r.text.includes('stays private'), r.text);
    [r] = await run(soc, 'YouTube public result', { 'YouTube publish job': [job] }, [{ error: { code: 403, message: 'The request <is> forbidden' } }]);
    assert(r.row.yt_status === 'failed' && r.row.note.includes('forbidden') && r.text.includes('&lt;is&gt;'), r.text);
  });
  const fbJob = { post_id: 'P1', ai: 'yes', graph: 'https://graph.facebook.com/v25.0', page_id: '1000000000000001', video_url: vurl, description: 'ig cap' };
  await test('08 Facebook: planned at the slot after the warning, with the Instagram caption; Page ID missing; late; stuck', async () => {
    let [p] = await plan(livePost({ yt_status: 'todo', ig_status: 'todo', fb_status: 'queued' }), berlin('2026-10-25T01:00'));
    assert(JSON.stringify(p.fb) === JSON.stringify(fbJob) && p.rows[0].fb_status === 'publishing', JSON.stringify(p));
    [p] = await plan(livePost({ yt_status: 'todo', ig_status: 'todo', fb_status: 'queued' }), berlin('2026-10-25T01:00'), { ...s08, fb_page_id: 'PASTE_YOUR_FACEBOOK_PAGE_ID' });
    assert(p.fb === null && p.rows[0].fb_status === 'failed' && p.alerts[0].includes('fb_page_id'), JSON.stringify(p));
    [p] = await plan(livePost({ yt_status: 'todo', ig_status: 'todo', fb_status: 'queued' }), berlin('2026-10-26T09:00'));
    assert(p.fb === null && p.rows[0].fb_status === 'late' && p.alerts[0].includes('Facebook: P1 was NOT posted'), JSON.stringify(p));
    [p] = await plan([...livePost({ yt_status: 'todo', ig_status: 'todo' }), ev('P1', { fb_status: 'publishing' }, '2026-10-24T23:00:00.000Z')], berlin('2026-10-25T01:31'));
    assert(p.rows[0].fb_status === 'stuck' && p.alerts[0].includes('Open your Facebook Page'), JSON.stringify(p));
    assert((await plan(livePost({ yt_status: 'todo', ig_status: 'todo', fb_status: '' }), berlin('2026-10-25T01:00'))).length === 0, 'no Facebook when it is not switched on');
  });
  await test('08 Facebook result: only the publish call makes it public; Stop in between; stuck when unsure', async () => {
    const key = { access_token: 'PAGEKEY', id: '1000000000000001' };
    const start = { video_id: 'FBV1', upload_url: 'https://rupload.facebook.com/video-upload/v25.0/FBV1' };
    const res = async (outs, input = [{}]) => (await run(soc, 'Facebook result', { 'Facebook job': [fbJob], ...outs }, input))[0];
    let r = await res({ 'Facebook: page key': [{ error: { message: 'Unsupported get request', code: 100 } }] });
    assert(r.row.fb_status === 'failed' && r.text.includes('Page key could not be read (Unsupported get request)') && r.text.includes('Nothing is public on Facebook'), r.text);
    r = await res({ 'Facebook: page key': [key], 'Facebook: start': [{ error: { message: '(#200) No permission' } }] });
    assert(r.row.fb_status === 'failed' && r.text.includes('(#200) No permission') && !JSON.stringify(r).includes('PAGEKEY'), 'the key never goes into a row or a message: ' + JSON.stringify(r));
    r = await res({ 'Facebook: page key': [key], 'Facebook: start': [start], 'Facebook: upload': [{ debug_info: { message: 'file_url could not be fetched' } }] });
    assert(r.row.fb_status === 'failed' && r.row.fb_video_id === 'FBV1' && r.text.includes('Nothing is public on Facebook'), r.text);
    r = await res({ 'Facebook: page key': [key], 'Facebook: start': [start], 'Facebook: upload': [{ success: true }], 'Check post again (Facebook)': [{ ok: false, rejected: true, reason: 'you stopped it before it went out' }] });
    assert(r.row.fb_status === 'cancelled' && r.text.includes('🚫 Facebook: P1 was not posted: you stopped it before it went out.'), r.text);
    r = await res({ 'Facebook: page key': [key], 'Facebook: start': [start], 'Facebook: upload': [{ success: true }], 'Check post again (Facebook)': [{ ok: true }], 'Facebook: publish': [{}] });
    assert(r.row.fb_status === 'stuck' && r.text.includes('may not have been posted') && r.text.includes('/retry P1'), r.text);
    r = await res({ 'Facebook: page key': [key], 'Facebook: start': [start], 'Facebook: upload': [{ success: true }], 'Check post again (Facebook)': [{ ok: true }], 'Facebook: publish': [{ success: true }] });
    assert(r.row.fb_status === 'published' && r.row.fb_video_id === 'FBV1' && r.text.includes('https://www.facebook.com/reel/FBV1') && r.text.includes('"AI-made video."'), JSON.stringify(r));
    // the last look at the post
    const look = async rows => (await run(soc, 'Check post again (Facebook)', { 'Facebook job': [fbJob], 'Reload post (Facebook)': rows }, []))[0];
    const busy = livePost({ yt_status: 'todo', ig_status: 'todo', fb_status: 'publishing' });
    assert((await look(busy)).ok === true, 'still approved and publishing');
    const stopped = await look([...busy, ev('P1', { status: 'rejected' })]);
    assert(stopped.ok === false && stopped.rejected === true, JSON.stringify(stopped));
    assert((await look([...busy, ev('P1', { fb_status: 'stuck' })])).ok === false, 'reported as stuck meanwhile');
  });

  // ---- 02: Facebook in the approve message, the music line and the AI-made line
  await test('02 Approve with Facebook switched on; the warning is announced; the AI-made line in every text', async () => {
    let [r] = await action('/approve P1', [basePost], berlin('2026-10-13T20:00'), { ...s02p, facebook_auto: 'yes' });
    assert(r.rows[0].fb_status === 'queued' && r.msgs[0].includes('Facebook: the bot posts it on your Page at the slot time.'), r.msgs[0]);
    assert(r.msgs[0].includes('⏰ About 10 minutes before the slot you get the video again with a ❌ Stop button. No answer = it goes out.'), r.msgs[0]);
    assert(r.msgs[0].includes('YouTube, Instagram and Facebook: the bot posts them and cannot add a sound'), r.msgs[0]);
    [r] = await action('/approve P1', [basePost], berlin('2026-10-13T20:00'));
    assert(r.rows[0].fb_status === '' && !r.msgs[0].includes('Facebook'), 'Facebook off: not mentioned, no to-do');
    [r] = await action('/approve P1', [basePost], berlin('2026-10-13T20:00'), { ...s02p, youtube_auto: 'no', instagram_auto: 'no' });
    assert(!r.msgs[0].includes('Stop button'), 'all by hand: no warning announced');
    // AI in the video: "AI-made video." in the TikTok and Instagram captions and the YouTube description, never twice
    const ai = await run(cmds, 'Check post texts', { '⚙️ Settings': [s02p], 'Build post brief': [pbrief], 'Post agent': [{ output: JSON.stringify(goodTexts) }] }, [], { now: T0 });
    for (const f of ['caption_tiktok', 'caption_instagram', 'yt_description']) {
      const v = ai[0].row[f];
      assert((v.match(/AI-made video\./g) || []).length === 1 && v.indexOf('AI-made video.') < v.indexOf('Shop:'), f + ': ' + v);
    }
    assert(!ai[0].row.yt_title.includes('AI-made'), 'not in the title');
    const no = await run(cmds, 'Check post texts', { '⚙️ Settings': [s02p], 'Build post brief': [{ ...pbrief, ai: 'no' }], 'Post agent': [{ output: JSON.stringify(goodTexts) }] }, [], { now: T0 });
    assert(!JSON.stringify(no[0].row).includes('AI-made'), 'no AI, no line');
    const already = await run(cmds, 'Check post texts', { '⚙️ Settings': [s02p], 'Build post brief': [pbrief], 'Post agent': [{ output: JSON.stringify({ ...goodTexts, caption_tiktok: 'AI-generated lights demo' }) }] }, [], { now: T0 });
    assert(!already[0].row.caption_tiktok.includes('AI-made video.'), 'the text already says it: ' + already[0].row.caption_tiktok);
  });

  // ---- 09: the finished videos from the PC
  const s09 = { telegram_chat_id: '123', post_times: '00:30,04:30,08:30,12:30,16:30,20:30', post_timezone: 'America/New_York', time_zone: 'Europe/Berlin',
    min_lead_hours: 1, youtube_auto: 'yes', instagram_auto: 'yes', facebook_auto: 'yes', shop_url: 'pivendo.com', pinterest_board: 'Christmas Decor & Gift Ideas',
    video_link_base: 'https://n8n.pivendo.com/webhook/pivendo-video', max_mb: 19 };
  // run() has no binary data, so "Check upload" is run here with a $() that also hands over the uploaded file
  const uploadWith = async (body, binary) => {
    const wf = load(intake);
    const node = wf.nodes.find(n => n.name === 'Check upload');
    const $ = name => ({ isExecuted: true, first: () => (name === 'Video in' ? { json: { body }, binary } : { json: s09 }), all: () => [] });
    const fn = new Function('$', '$input', '$now', 'DateTime', '$runIndex', 'return (async () => {' + node.parameters.jsCode + '})()');
    return (await fn($, { all: () => [], first: () => ({ json: {} }) }, DateTime.now(), DateTime, 0)).map(r => r.json);
  };
  const mp4 = (size = '12.4 MB', extra = {}) => ({ video: { mimeType: 'video/mp4', fileName: 'r03-lights-off.mp4', fileSize: size, ...extra } });
  await test('09 Check upload: a video, a message, and every reason to refuse', async () => {
    let [u] = await uploadWith({ sku: 'CJYS315', ai: 'yes', shows: 'lights  go off,\n stars on the ceiling', name: 'r03-lights-off.mp4' }, mp4());
    assert(u.mode === 'video' && u.name === 'r03-lights-off.mp4' && u.mb === 12.4 && u.post.sku === 'CJYS315' && u.post.ai === 'yes' && u.post.shows === 'lights go off, stars on the ceiling', JSON.stringify(u));
    assert(/^https:\/\/n8n\.pivendo\.com\/webhook\/pivendo-video\?v=[a-z0-9]{20}\.mp4$/.test(u.post.url), u.post.url);
    const [u2] = await uploadWith({ sku: 'CJYS315', ai: 'yes' }, mp4());
    assert(u2.post.url !== u.post.url, 'every video gets its own random link');
    [u] = await uploadWith({ sku: 'CJYS315', ai: 'no' }, mp4(undefined, { fileSize: undefined, bytes: 18900000 }));
    assert(u.mode === 'video' && u.mb === 18.9, 'size in bytes: ' + JSON.stringify(u));
    const refuse = async (body, binary, words) => { const [x] = await uploadWith(body, binary); assert(x.mode === 'error' && x.error.includes(words), words + ': ' + JSON.stringify(x)); };
    await refuse({ sku: 'CJYS315', ai: 'yes' }, mp4('19.5 MB'), 'is 19.5 MB. The limit is 19 MB');
    await refuse({ sku: 'CJYS315', ai: 'yes' }, mp4('0 B'), 'empty');
    await refuse({ sku: 'CJYS315', ai: 'yes' }, { video: { mimeType: 'video/quicktime', fileName: 'a.mov', fileSize: '3 MB' } }, 'only MP4');
    await refuse({ ai: 'yes' }, mp4(), 'SKU is missing');
    await refuse({ sku: 'CJYS315', ai: 'maybe' }, mp4(), '"ai" must be yes or no');
    await refuse({}, {}, 'Nothing to do');
    // a short message for the owner, escaped for Telegram
    [u] = await uploadWith({ message: '6 video plans are ready <open the Claude app>' }, {});
    assert(u.mode === 'message' && u.text === '6 video plans are ready &lt;open the Claude app&gt;', JSON.stringify(u));
  });
  await test('09 The video goes through the same brief and checks as /queue', async () => {
    const [shim] = await run(intake, 'Parse command', { 'Check upload': [{ post: { url: 'https://n8n.pivendo.com/webhook/pivendo-video?v=abcdefghijkmnpqrstuv.mp4', sku: 'cjys315', ai: 'yes', shows: 'stars' } }] }, []);
    assert(shim.route === 'queue' && shim.post.sku === 'cjys315', JSON.stringify(shim));
    const brief = async post => (await run(intake, 'Build post brief', { '⚙️ Settings': [s09], 'Parse command': [{ route: 'queue', args: [], post }],
      'Load products (post)': [lamp], 'Load playbook (post)': playbook, 'Load videos (post)': [{}], 'Load stats (post)': [{}], 'Load posts (queue)': [{}] }, []))[0];
    let b = await brief(shim.post);
    assert(b.ok && b.ai === 'yes' && b.sku === 'CJYS315' && b.shows === 'stars' && b.url === shim.post.url && b.prompt.includes('an AI presenter'), JSON.stringify(b).slice(0, 300));
    b = await brief({ ...shim.post, ai: 'no' });
    assert(b.ok && b.ai === 'no', 'ai no');
    b = await brief({ ...shim.post, url: 'http://x/y.mp4' });
    assert(!b.ok && b.reply.includes('its link is not valid') && !b.reply.includes('Usage'), b.reply);
    b = await brief({ ...shim.post, sku: 'NOPE' });
    assert(!b.ok && b.reply.includes('NOPE'), b.reply);
    // the same code in 02 still takes a /queue link of the bot's own video link form
    const [q] = await postBrief(['https://n8n.pivendo.com/webhook/pivendo-video?v=abcdefghijkmnpqrstuv.mp4', 'cjys315']);
    assert(q.ok, '/queue with a bot video link: ' + JSON.stringify(q).slice(0, 200));
  });
  const intakePlan = async (now, table, settings = s09, name = 'r03-lights-off.mp4') => (await run(intake, 'Plan intake', { '⚙️ Settings': [settings],
    'Check upload': [{ name }], 'Check post texts': [{ ok: true, row: { ...basePost, id: undefined, post_id: 'Q' + (rowId++), video: 'pivendo-video', video_url: 'https://n8n.pivendo.com/webhook/pivendo-video?v=abcdefghijkmnpqrstuv.mp4' } }],
    'Load posts (queue)': table }, [], { now }))[0];
  await test('09 Plan intake: 6 videos fill the next 24 hours, no second OK, to-dos for TikTok and Pinterest', async () => {
    const table = [{}];
    const out = [];
    for (let i = 1; i <= 6; i++) {
      const r = await intakePlan(berlin('2026-10-15T14:10'), table, s09, `v${i}.mp4`);
      assert(r.ok, JSON.stringify(r));
      table.push({ ...r.row, id: rowId++ });
      out.push(r);
    }
    // 14:10 in Berlin = 08:10 in New York: the first free slot at least 1 hour ahead is 12:30 New York = 18:30 Berlin
    assert(out.map(r => r.row.slot).join() === '12:30,16:30,20:30,00:30,04:30,08:30', out.map(r => r.row.slot).join());
    assert(out.map(r => r.answer.shown).join(' | ') === 'Thu 15 Oct at 18:30 (Europe/Berlin) | Thu 15 Oct at 22:30 (Europe/Berlin) | Fri 16 Oct at 02:30 (Europe/Berlin) | Fri 16 Oct at 06:30 (Europe/Berlin) | Fri 16 Oct at 10:30 (Europe/Berlin) | Fri 16 Oct at 14:30 (Europe/Berlin)', out.map(r => r.answer.shown).join(' | '));
    const r = out[0];
    assert(r.row.status === 'approved' && r.row.yt_status === 'queued' && r.row.ig_status === 'queued' && r.row.fb_status === 'queued' && r.row.tiktok_status === 'todo' && r.row.video === 'v1', JSON.stringify(r.row));
    assert(Object.keys(r.row).filter(k => k !== 'id').every(k => postCols.split(',').includes(k)), 'only table columns: ' + Object.keys(r.row));
    assert(r.caption.includes('Goes out Thu 15 Oct at 18:30 (Europe/Berlin) on YouTube, Instagram, Facebook.') && r.caption.includes('No answer = it goes out') && r.caption.length < 1024, r.caption);
    assert(r.todos.length === 2 && r.todos[0].includes('TikTok to-do') && r.todos[0].includes('no-music TikTok file of "v1"') && r.todos[0].includes('Schedule it for Thu 15 Oct at 18:30') && r.todos[0].includes('"AI-generated content" ON') && r.todos[0].includes('/tiktok'), r.todos[0]);
    assert(r.todos[1].includes('Pinterest to-do') && r.todos[1].includes('Board: Christmas Decor &amp; Gift Ideas') && r.todos[1].includes('Publish at a later date: Thu 15 Oct at 18:30') && r.todos[1].includes('<code>yt title</code>') && !r.todos[1].includes('Done?'), r.todos[1]);
    for (const m of r.todos) assert(m.replace(/<\/?code>/g, '').match(/[<>]/) === null, 'HTML-safe');
    // platforms that are not switched on get a to-do (YouTube, Instagram) or are left out (Facebook)
    const byHand = await intakePlan(berlin('2026-10-15T14:10'), [{}], { ...s09, youtube_auto: 'no', instagram_auto: 'no', facebook_auto: 'no' });
    assert(byHand.row.yt_status === 'todo' && byHand.row.ig_status === 'todo' && byHand.row.fb_status === '' && byHand.todos.length === 4 && byHand.caption.includes('You post it yourself'), JSON.stringify(byHand.row));
    // the same file twice is never queued twice
    const twin = await intakePlan(berlin('2026-10-15T14:20'), table, s09, 'v1.mp4');
    assert(twin.ok === false && twin.error.includes('v1.mp4 is already queued as'), JSON.stringify(twin));
    const again = await intakePlan(berlin('2026-10-15T14:20'), [...table, ev(out[0].row.post_id, { status: 'rejected' })], s09, 'v1.mp4');
    assert(again.ok === true, 'a stopped video may be sent again');
  });
  await test('09 Intake result, problems, and the public video link', async () => {
    const plan = { row: { post_id: 'P9', status: 'approved' }, answer: { ok: true, post_id: 'P9' } };
    let [r] = await run(intake, 'Intake result', { 'Plan intake': [plan] }, [{ ok: true, result: { message_id: 5, video: { file_id: 'TGF9' } } }]);
    assert(r.ok && r.row.tg_file_id === 'TGF9' && r.answer.post_id === 'P9', JSON.stringify(r));
    [r] = await run(intake, 'Intake result', { 'Plan intake': [plan] }, [{ error: { message: 'Request Entity Too Large' } }]);
    assert(!r.ok && r.error.includes('Telegram did not take the video (Request Entity Too Large). Nothing was queued.'), JSON.stringify(r));
    let [pr] = await run(intake, 'Problem', { 'Check upload': [{ name: 'v1.mp4' }] }, [{ ok: false, reply: 'I can&#39;t find SKU &lt;X&gt;' }]);
    assert(pr.answer.ok === false && pr.answer.error.includes('SKU <X>') && pr.text.includes('(v1.mp4)') && pr.text.includes('&lt;X&gt;'), JSON.stringify(pr));
    [pr] = await run(intake, 'Problem', {}, [{ mode: 'error', error: 'Nothing to do' }]);
    assert(pr.answer.error === 'Nothing to do' && pr.text.startsWith('❌ A video from the PC was not queued:'), JSON.stringify(pr));
    const link = 'https://n8n.pivendo.com/webhook/pivendo-video?v=abcdefghijkmnpqrstuv.mp4';
    const rows = [{ ...basePost, video_url: link }, ev('P1', { status: 'approved', tg_file_id: 'TGF1' })];
    const find = async (v, table = rows) => (await run(intake, 'Find video', { 'Video link': [{ query: { v } }], 'Load posts (link)': table }, []))[0];
    assert(JSON.stringify(await find('abcdefghijkmnpqrstuv.mp4')) === '{"found":true,"file_id":"TGF1"}', 'found');
    assert((await find('abcdefghijkmnpqrstuv.mp4', [...rows, ev('P1', { status: 'rejected' })])).found === false, 'a stopped video is not served');
    for (const bad of ['', 'abc.mp4', '../x', 'ABCDEFGHIJKMNPQRSTUV.mp4', 'bcdefghijkmnpqrstuvw.mp4']) assert((await find(bad)).found === false, 'not found: ' + bad);
    assert((await find('abcdefghijkmnpqrstuv.mp4', [{ ...basePost, video_url: link, status: 'approved' }])).found === false, 'no Telegram file, nothing to serve');
  });
  await test('09 Workflow shape: login on the intake, every path answers the PC, the link needs no login', async () => {
    const wf = load(intake);
    const node = name => wf.nodes.find(n => n.name === name);
    const vin = node('Video in').parameters, vlink = node('Video link').parameters;
    assert(vin.httpMethod === 'POST' && vin.authentication === 'headerAuth' && vin.responseMode === 'responseNode' && vin.path === 'pivendo-video-in', JSON.stringify(vin));
    assert(vlink.httpMethod === 'GET' && !vlink.authentication && vlink.responseMode === 'responseNode' && vlink.path === 'pivendo-video', JSON.stringify(vlink));
    const s = Object.fromEntries(node('⚙️ Settings').parameters.assignments.assignments.map(a => [a.name, a.value]));
    assert(s.video_link_base.endsWith('/webhook/' + vlink.path) && s.post_times.split(',').length === 6 && s.max_mb === 19, JSON.stringify(s));
    assert(s.youtube_auto === 'no' && s.instagram_auto === 'no' && s.facebook_auto === 'no' && String(s.telegram_chat_id).startsWith('PASTE'), 'nothing is posted by itself before the setup');
    // every path that starts at "Video in" ends in an answer to the PC
    const next = n => ((wf.connections[n] || {}).main || []).flat().map(c => c.node);
    const seen = new Set(), todo = ['Video in'];
    while (todo.length) { const n = todo.pop(); if (seen.has(n)) continue; seen.add(n); todo.push(...next(n)); }
    const leaves = [...seen].filter(n => !next(n).length);
    assert(leaves.length && leaves.every(n => node(n).type === 'n8n-nodes-base.respondToWebhook'), 'leaves: ' + leaves);
    for (const [ifNode, out] of [['What came in?', 2], ['Post brief ok?', 1], ['Post texts ok?', 1], ['Not queued before?', 1], ['Video arrived in Telegram?', 1]]) {
      assert(wf.connections[ifNode].main[out].map(c => c.node).join() === 'Problem', ifNode + ' must report the problem');
    }
    // the video is shown to the owner with the ❌ Stop button, and the table row is only saved once Telegram has the file
    const show = node('Show video to owner').parameters;
    assert(show.operation === 'sendVideo' && show.binaryData === true && show.additionalFields.parse_mode === 'HTML'
      && show.inlineKeyboard.rows[0].row.buttons[0].additionalFields.callback_data.includes("'reject:'"), JSON.stringify(show));
    const unsent = new Set(), q = ['Video in'];
    while (q.length) { const n = q.pop(); if (unsent.has(n) || n === 'Video arrived in Telegram?') continue; unsent.add(n); q.push(...next(n)); }
    assert(seen.has('Save intake') && !unsent.has('Save intake'), '"Save intake" only after Telegram took the video');
    assert(wf.nodes.filter(n => n.type === 'n8n-nodes-base.telegram' && n.name !== 'Get video from Telegram').every(n => n.onError === 'continueRegularOutput'), 'messages never block the answer');
    assert(node('Answer PC (queued)').executeOnce === true, 'one answer, even with several to-dos');
    assert(node('Get video from Telegram').parameters.resource === 'file' && node('Get video from Telegram').parameters.download === true && node('Send the video').parameters.respondWith === 'binary', 'the link streams the file');
  });
  await test('08 + 09 small pass-on nodes and Settings', async () => {
    const planned = { rows: [], alerts: [], warn: null, yt: null, yt_pub: { post_id: 'P1' }, ig: null, fb: { post_id: 'P2' } };
    assert((await run(soc, 'YouTube publish job', { 'Plan this run': [planned] }, [{}]))[0].post_id === 'P1', 'YouTube publish job');
    assert((await run(soc, 'Facebook job', { 'Plan this run': [planned] }, [{}]))[0].post_id === 'P2', 'Facebook job');
    assert((await run(soc, 'Facebook job', { 'Plan this run': [{ ...planned, fb: null }] }, [{}])).length === 0, 'no Facebook job');
    for (const n of ['YouTube public row', 'Facebook row']) assert(JSON.stringify(await run(soc, n, {}, [{ row: { post_id: 'P1' } }])) === '[{"post_id":"P1"}]', n);
    assert(JSON.stringify(await run(intake, 'Intake row', {}, [{ row: { post_id: 'P1' } }])) === '[{"post_id":"P1"}]', 'Intake row');
    assert(JSON.stringify(await run(intake, 'To-do messages', { 'Plan intake': [{ todos: ['a', 'b'] }] }, [{}])) === '[{"text":"a"},{"text":"b"}]', 'To-do messages');
    const b = Object.fromEntries(load(soc).nodes.find(n => n.name === '⚙️ Settings').parameters.assignments.assignments.map(a => [a.name, a.value]));
    assert(String(b.fb_page_id).startsWith('PASTE') && b.warn_minutes === 5, JSON.stringify(b));
  });

  await test('setup.ps1: -OnlyWorkflows takes a list, and a replaced workflow is archived only after the new one is on', async () => {
    // The script is never run by these tests; they only guard the order of its steps against a careless edit.
    const ps = fs.readFileSync(path.join(__dirname, '..', 'setup.ps1'), 'utf8');
    assert(/\[string\[\]\]\$OnlyWorkflows/.test(ps), 'PowerShell 5.1 turns an unquoted -OnlyWorkflows 02,08 into the numbers 2 and 8, so the parameter must be a list');
    assert(!/\$f\.Name\.StartsWith\(/.test(ps), 'matching must be on the two-digit prefix, not a prefix of the typed text');
    const swap = ps.slice(ps.indexOf('function Replace-Workflow'), ps.indexOf('function Ensure-Workflows'));
    const first = s => swap.indexOf(s), last = s => swap.lastIndexOf(s);
    const create = first("N8n 'POST' '/rest/workflows' $body"), offOld = first('/rest/workflows/$($old.id)/deactivate'),
      onNew = first('/rest/workflows/$($created.id)/activate'), onOldAgain = first('/rest/workflows/$($old.id)/activate'), retire = last('Retire-OldWorkflow $old');
    assert([create, offOld, onNew, onOldAgain, retire].every(i => i > 0), 'the five steps of the swap must all be there: ' + [create, offOld, onNew, onOldAgain, retire]);
    assert(create < offOld && offOld < onNew && onNew < retire, 'order: import new (off) -> switch old off -> switch new on -> archive old');
    assert(onNew < onOldAgain && onOldAgain < retire, 'a new copy that will not switch on puts the old one back on, before anything is archived');
    // the old copy is archived in exactly two places: when it was off anyway (before the swap), and after the new copy is on
    assert(swap.split('Retire-OldWorkflow $old').length - 1 === 2 && first('Retire-OldWorkflow $old') < offOld && !swap.includes('Archive-Workflow $old'), 'the old copy must not be archived anywhere else');
    const ensure = ps.slice(ps.indexOf('function Ensure-Workflows'), ps.indexOf('function Activate-Workflows'));
    assert(!ensure.includes('/archive') && !ensure.includes('/deactivate'), 'Ensure-Workflows must not archive or switch off anything itself');
    // The old and the new workflow 02 share one Telegram webhook address, and switching a copy off makes n8n remove that
    // webhook at Telegram. So a copy is switched off exactly once, the old one, before the new one is switched on; a copy
    // that is already off (the failed new one, the old one after the swap) is only archived, never "switched off" again.
    assert((ps.match(/\/deactivate/g) || []).length === 1 && offOld > 0, 'only the old copy is ever switched off, once, inside the swap');
    // workflow 09 waits for its own login, and that login (a Header Auth key like JSON2Video's) only ever goes on its node "Video in"
    const ensureWf = ps.slice(ps.indexOf('function Ensure-Workflows'), ps.indexOf('function Activate-Workflows'));
    assert(ensureWf.includes("$f.Name -like '09-*' -and -not $old -and -not $credIds.ContainsKey('videoIntake')"), '09 must not be imported without its login');
    assert(/\$node\.name -eq 'Video in' -and \$credIds\.ContainsKey\('videoIntake'\)/.test(ps) && !/\$CredentialFor[^\n]*webhook/.test(ps), 'the intake key is attached by node name, never by node type');
    assert(ps.indexOf('$OnlyList = @(Get-OnlyWorkflows)') > ps.indexOf('Dropshipping agents - setup') && ps.indexOf('$OnlyList = @(Get-OnlyWorkflows)') < ps.indexOf('$state = Load-State'), 'a wrong workflow number must stop the script before anything is asked or changed');
  });

  console.log(failures ? `\n${failures} FAILED` : '\nALL TESTS PASSED');
  process.exit(failures ? 1 : 0);
})();
