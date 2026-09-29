# The plan: CJ dropshipping with self-improving n8n agents

*Written 2026-09-29, from 4 research reports (see `research/`). Setup steps are in `SETUP.md`.*

## 1. The honest answer first

| Goal | Chance in 14 days |
|---|---|
| Get at least 1 sale | ~30-40% |
| $50+ profit on paper (sales minus all costs) | ~10-20% |
| $50+ actually in your bank by day 14 | ~5-10% |

These are estimates. No rigorous public data on dropshipping success exists, and the popular "80-90% fail" figure has no source. The research agent's own estimate is that fewer than about 1 in 7 beginners reach cash profit by day 14.

**Why it's hard in 2 weeks:**
- **Payment holds.** Shopify is holding some new stores' first payout for 21 days, and PayPal can hold up to 21 days. You pay CJ immediately, but your money arrives later.
- **New video accounts are slow.** The median TikTok post gets about 500 views, however often you post. You need an outlier video.
- **Paid ads lose money at first.** A first ad test typically costs about $83 per sale against about $14 profit per sale.
- **China shipping is slow.** It takes 8-17 days to the US, and there's no duty-free import any more, so use CJ's US or EU warehouses.

**Realistic target:** first sales within 2 weeks, and a clear picture of real profit by days 45-60. What the agents give you is time: they do the research, writing, video editing, order checks and reporting, and they learn from every result.

## 2. How the system works

```
07:00  RESEARCH AGENT ── CJ trending products -> AI picks 3 -> real CJ shipping cost -> fixed pricing rule
                        └─> Telegram: 3 products with cost, price, profit per order, risks
         you: pick one, order a sample in CJ
/content SKU    CONTENT AGENT ── product page copy + 5 video scripts (copies what worked before)
/clips SKU ...  you: film 3-5 hands-only clips of the sample, send the Google Drive links
/render ID      VIDEO AGENT ── script + your clips + CJ photo + AI voice + captions -> MP4 on Telegram
         you: post it on TikTok, Reels and Shorts (auto-posting is blocked for new apps)
customer pays -> Shopify -> CJ app imports the order -> ORDER ALERT on Telegram -> you pay in CJ -> CJ ships
every 3h        ORDER CHECK ── warns about unpaid CJ orders and missing tracking after 48h
new email       SUPPORT AGENT ── looks up the customer's order + tracking -> drafts a reply
                   └─> safe questions can be auto-sent; everything else -> Telegram: /send, /reply or /skip
/video ID views clicks sales    /product SKU testing|winner|killed    <- your results feed the memory
21:30  COACH AGENT ── real numbers -> daily report + 3 actions for tomorrow
                   └─> proposes up to 3 new PLAYBOOK rules with evidence -> you tap ✅ or ❌
next morning: every agent loads the updated playbook -> better picks and better scripts
```

**How "getting better every day" works:**
- The **playbook** is a table of short rules, like *"Start hooks with the finished result: those videos averaged 3x the views"*.
- Every agent reads the active rules before it works.
- Every night the Coach compares predictions with results and proposes changes, each backed by at least 3 data points.
- **Safety:** you approve every change. Rules are versioned, so any change can be rolled back. A code guard blocks:
  - rules that mention money, budgets, URLs or passwords
  - deceptive tactics
  - changes to the 3 protected legal rules

  The agents can never change their code, credentials, prices or spending.
- **The more results you report, the faster it learns.** Send `/video` stats 48 hours after each post.
- **Support learns from your corrections:** every `/reply` you send is shown to the support agent as an example, and the coach can turn patterns into support rules.

| Automated | You do (about 1-2 hours a day) |
|---|---|
| Daily product research with real CJ costs and prices | Choose the product, order the sample |
| Page copy, 5 scripts per product | Paste the copy into Shopify |
| Video editing: voice, captions, scenes | Film clips with your phone (hands-only), post the videos |
| Order alerts, unpaid and late order warnings | Pay each CJ order (one click, card or PayPal) |
| Customer emails: order lookup, tracking, draft replies | Approve with `/send`, or rewrite with `/reply` (it learns from you) |
| Daily profit report, learning, rule proposals | Tap ✅/❌, report video stats |

## 3. Budget

| | $0-50 path | $100-200 path | $300-500 path |
|---|---|---|---|
| Shopify | $1 (then $39/mo after 3 months) | $1 | $1 |
| Domain | skip (myshopify.com) | $11 | $11 |
| Samples | 1 × $10-15 | 2-3 × about $15 | 3 × about $15 |
| Cash to pay CJ for first orders | about $25 | about $60 | $100-150 |
| n8n | $0 (your PC) | €6 (Hetzner) | €6 |
| Claude API | $5 | $10 | $15 |
| Support mailbox | $0 (Gmail) | $0 | $0 |
| JSON2Video | free test tier (watermark) | $49.95 prepaid (≈240 videos) | $49.95 |
| Meta ads test | $0 | $0-60 | $150-250 |
| **Realistic result** | learning, 0-3 sales | first sales from organic video | 1-2 honest product tests |

**Never spend on:** courses, "done-for-you stores", "winning product lists". The FTC has shut down several of these, including Automators ($22M) and Ascend Ecom ($25M).

## 4. Numbers for one product

$29.99 selling price, $6.00 CJ product + $6.50 US-warehouse shipping:

| | |
|---|---|
| Profit per order before ads | **$14.32** (after 2.9% + 30¢ payment fee, 5% refunds, apps) |
| Break-even ad cost per sale | $14.32 → break-even ROAS 2.09 |
| Typical first ad test | about $83 per sale, a **loss of about $69 per order**, so start with free videos |
| Fixes | price at $34.99, or add a 2-pack at $44.99 (about $21 profit per order) |

The research agent sets prices with a fixed rule, never an AI guess: **3× landed cost, at least $15 above it**. You can change this in ⚙️ Settings.

## 5. The 14 days

| Day | You | Agents |
|---|---|---|
| **1** | Shopify ($1 plan), verify Shopify Payments + bank **today**, PayPal, CJ + CJ app, Telegram bot, Claude key. Create TikTok, Instagram and YouTube accounts and use them normally | Set up n8n (`SETUP.md`) |
| **2** | Read the research message, check the products in the CJ app, **order 1-2 samples from the US/EU warehouse**. Browse TikTok Creative Center and the Meta Ad Library by hand to double-check demand | Research runs every morning |
| **3** | Build the one-product page: `/content SKU` → paste the copy. Add policies, bundles (1 / 2 at -15% / 3 at -25%), abandoned-checkout email (Shopify Email, free) | Content agent |
| **4-5** | Before the sample arrives: post 2-3 videos a day made from the CJ photo and an honest demo. Keep them simple | Video agent (`/clips`, `/render`) |
| **6-7** | **Sample arrives:** film 10+ real clips → `/clips` → `/render` for each script. Post 2-4 a day on all 3 platforms. **Day 7 checkpoint** | Coach learns from your `/video` stats |
| **8-10** | Make more of whatever got views. If a kill rule fires, switch to product #2 (`/product SKU killed`) | Research avoids what failed |
| **11-14** | Scale what works or pivot. Day 14 review: revenue vs cash received vs money still owed | Daily report shows 7-day profit |

**Kill and scale rules:**
- 15 videos and none above 1,000 views → change the **hook or format**, not the product.
- 30 videos, 30,000+ views, 100+ store visits, **0 add-to-carts** → kill the product.
- 3+ add-to-carts but no purchases → test the price (-$5) or a bundle for 3 days.
- One video above 50,000 views with "where do I buy this?" comments → post 3-5 variations of it now.
- Paid test (only with the $300+ path): kill a product at $30 spent with 0 add-to-carts, or at $45 with no purchase. Scale when cost per sale is at or below $14 across 3+ sales in 72 hours.

## 6. Legal checklist

- **Everywhere:** Shopify's generated policies (refund, shipping, privacy, terms, contact). Honest delivery times. **No fake reviews, fake discounts, countdowns or AI "customers"** (US FTC fines up to about $53k per violation). No brands or look-alikes.
- **US:** sole proprietor by default. Get a seller's permit if your state has sales tax. China parcels now always pay duty, so prefer CJ's US warehouse.
- **UK:** no need to tell HMRC under £1,000 trading income a year. VAT on imports worth £135 or less is the seller's job, so ask an accountant, or sell UK-warehouse stock.
- **EU:** register a business (rules vary by country; Germany also needs an Impressum). 14-day withdrawal right plus a **withdrawal button** (since 19 June 2026). GPSR "EU responsible person" on listings. €3 customs duty per low-value parcel since 1 July 2026. **Easiest: start with US customers.**
- **Avoid these products:** batteries, kids' products and toys, cosmetics, supplements, anything medical, knives and weapons. The research agent filters these out automatically.

## 7. After the first sales (phase 2)

1. **Payoneer → CJ wallet:** allows fully automatic order payment (CJ `payType=2`), with a spending cap.
2. **Meta ads monitor:** a daily pull of ad numbers plus the kill and scale rules above, as alerts only.
3. **TikTok Shop US:** only with US-warehouse products (6 business days maximum delivery).
4. **Evaluations:** a test set of past scripts, so a new playbook version is only kept if it scores better.

## Sources
- `research/01-setup-costs-legal.md`: channels, CJ, payments, legal, budgets, scams
- `research/02-first-profit-14-days.md`: product research, traffic, unit economics, day-by-day plan
- `research/03-n8n-agent-system.md`: hosting, nodes, self-improvement design, LLM cost
- `research/04-video-automation.md`: render APIs, voices, AI video, labels, music
