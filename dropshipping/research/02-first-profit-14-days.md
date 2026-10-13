# Research 2: First sales and profit within 14 days (CJ, $100-300, late 2026)

*Research agent report, 2026-09-29. "(unverified)" marks facts the agent could not confirm.*

## Bottom line
- **A first sale within 14 days is realistic** if you post content daily or run one proper paid test.
- **Cash profit by day 14 is unlikely.** The agent's own estimate is fewer than about 1 in 7 beginners. Payouts from sales on day 10 or later usually won't reach your bank by day 14.
- **Budget:** $100 is enough for organic content only. $300 pays for one real paid test (about $150-180 in ads) plus organic posting.
- **2026 changes that matter:**
  - The US de minimis exemption is permanently gone, so China-direct parcels pay duty ([Zonos](https://zonos.com/us-tariff-updates)). Prefer CJ's US warehouse.
  - USPS now charges every Ground Advantage parcel under 1 lb at the 1-lb rate, about $6.93 in Zone 1 ([Pirate Ship](https://support.pirateship.com/en/articles/15453569-july-2026-usps-rate-and-rule-changes)).
  - TikTok now requires a label on AI content that shows realistic people or scenes (effective 24 Sep 2026).

## 1. Product research with $0 tools

| Source | Can it feed an automation? | Notes |
|---|---|---|
| **CJ trending lists** | **Yes, officially.** Product List V2 API: `productFlag` (0 = trending, 2 = video products), warehouse country, price and inventory filters ([CJ API](https://developers.cjdropshipping.cn/en/api/api2/api/product.html)) | Safe. The backbone of the research agent. |
| TikTok Creative Center | No official API | TikTok's ToS bans automated scraping; browse by hand |
| TikTok Shop best-sellers | No public API | Kalodata has a 7-day trial with no card |
| Meta Ad Library | Browse by hand for US ads | Scraping breaks Meta's terms. Good signal: the same product in many ad variants running 30+ days |
| Amazon Movers & Shakers | Browse by hand | Use as a price check: skip it if Prime sells it for under $20 |
| Google Trends | Official API is a closed alpha | Look for steady or rising interest, not a single spike |
| Reddit | New API apps need approval | Browse for complaints (problems a product can solve) |

**Good beginner product:**
- Sells for $20-60.
- At least 3× markup on landed cost.
- Solves a visible problem, or shows a result in 2 seconds of video.
- Under 500 g, not fragile, no sizes, not branded.
- In CJ's US warehouse with 100+ units.
- Not cheaper on Amazon Prime.

**Avoid:**
- **Kids' products and toys:** they need a Children's Product Certificate, which you as importer may have to issue ([CPSC](https://www.cpsc.gov/Business--Manufacturing/Testing-Certification/Childrens-Product-Certificate)).
- **Battery products:** shipping restrictions and fire risk.
- **Supplements and health claims:** Shopify Payments bans them, and ads get restricted.
- **Cosmetics:** FDA rules.
- **Apparel:** 20-40% returns.
- **EU sales without a GPSR responsible person.**

## 2. Traffic at near-zero spend

**Organic TikTok, Reels and Shorts**
- **Posting volume:** Buffer analysed 11.4M posts. The **median TikTok post gets about 500 views no matter how often you post**. Posting more mainly raises your chance of an outlier: the top 10% get 3,722 views at 1 post/week and 14,401 at 11+ posts/week ([SEJ/Buffer](https://www.searchenginejournal.com/study-shows-2-5-weekly-tiktoks-deliver-biggest-view-increase/558641/)).
- **Plan for** 2-4 posts a day, cross-posted to Reels and Shorts.
- **Originality:** copied or re-uploaded videos **don't get shown in the For You feed** ([TikTok](https://www.tiktok.com/creator-academy/article/tiktok-originality-policy)). Raw CJ supplier clips are risky, so film your own sample.
- **Formats that work without a face:** hands-only demo, problem → fix, before/after, "3 uses", durability test, reply to a comment.
- **Hooks:** about 90% of underperforming clips lose viewers in the first 3 seconds. Showing the result first performs best ([Opus](https://www.opus.pro/blog/tiktok-hooks-that-go-viral-2026)).
- **Rough funnel (agent's estimate):** 10,000 views → 20-60 store visits → 0.3-1 sale. You need an outlier video.

**Automatic posting**
- TikTok's Content Posting API keeps posts private until your app passes TikTok's audit ([TikTok](https://developers.tiktok.com/docs/en/content-posting-api-get-started)).
- YouTube keeps uploads from unverified API projects private.
- Pinterest's Trial API tier creates pins only you can see.
- **Practical route:** n8n generates the scripts and captions, then you post by hand or through Buffer's free plan (3 channels, 10 queued posts each).

**TikTok Shop and affiliate creators**
- US sellers need a US ID and SSN/ITIN.
- Fees: 6% referral (8% from Aug 2026 reported, unverified). Creator commissions are about 10-15%.
- Samples for creators cost you about $12-15 each.
- Orders must ship within about 2 days, so US warehouse only.
- **Verdict:** slow within 14 days.

**Other free channels**
- **Pinterest:** usually 60-90+ days before meaningful traffic (unverified).
- **Reddit and Facebook groups:** most ban links and promotional DMs. Use them for research and genuine help.

**Smallest paid test worth running**

| | Meta | TikTok |
|---|---|---|
| Minimum | About $5+/day for link clicks | More than $20/day per ad group and more than $50 per campaign ([TikTok](https://ads.tiktok.com/help/article/budget?lang=en)) |
| Benchmarks | Ecommerce CPM €8-18, CTR 1.2-2.5%, CPC €0.50-1.80 | CPM about $5-13, CTR about 0.8-1.2% |

- **Test structure:** one Sales campaign, broad US targeting, $15-20/day, 4-6 *genuinely different* creatives. Meta merges near-duplicate ads.
- **New Meta ad accounts** often hit a $50/day spending limit.
- **Meta is better than TikTok ads at this budget.**

**AI tools and legal limits**
- Free: CapCut, Canva, an LLM for scripts, and ElevenLabs' free tier for voiceover.
- **AI avatars posing as customers are fake testimonials.** The FTC rule allows penalties of up to $51,744 per violation ([FTC](https://www.ftc.gov/news-events/news/press-releases/2024/08/federal-trade-commission-announces-final-rule-banning-fake-reviews-testimonials)).

## 3. Unit economics: $29.99 product with free shipping (CJ costs assumed)

| Line | Shopify (paid or organic) | TikTok Shop + affiliate |
|---|---|---|
| Price | $29.99 | $29.99 |
| Landed cost (product $6.00 + US-warehouse shipping $6.50) | -12.50 | -12.50 |
| Payment fee (2.9% + 30¢) | -1.17 | Referral fee 6-8%: -1.80 to -2.40 |
| Affiliate commission (12%) | – | -3.60 |
| Refunds, chargebacks, replacements (5%) | -1.50 | -1.50 |
| Apps and overhead | -0.50 | – |
| **Left per order before ads** | **$14.32** | **about $10-10.60** |

- **Break-even cost per sale from ads is $14.32**, and **break-even ROAS is 2.09**. To make $5 per order, you need to spend $9.32 or less per sale.
- **Realistic first ad test:** CPM $15, 1.2% CTR and 1.5% conversion give about **$83 per sale, a loss of about $69 per order.**
- **Winning-video case:** CPM $12, 2.5% CTR and 3% conversion give about $16 per sale, roughly break-even. The average Shopify conversion rate is 1.4%.
- **Ways to fix the margin:**
  - Price at $34.99, or charge $4.95 shipping: about $19 left per order.
  - Offer a 2-pack at $44.99: about $21 left.
  - Ship China-direct: cheaper, but 8-17 days delivery means more refunds.
- **Organic fixed costs for 14 days:** Shopify $1, sample $15-30, domain $12. That's covered by about 2-5 orders.

## 4. Conversion basics for a one-product store

**Product page, top to bottom:**
1. A GIF or video that shows the result.
2. Headline stating the benefit.
3. 3-5 bullets.
4. Price anchoring, but only against a genuine previous price.
5. Bundle selector: 1 unit, 2 units (-15%), 3 units (-25%).
6. Honest delivery estimate.
7. Your own sample photos.
8. FAQ.
9. Clear refund policy and a real contact email.

**Never import or fabricate reviews.** An empty review section is better than a fake one.

**Raising order value:** a post-purchase one-click upsell and cart add-ons.

**Abandoned-cart email**
- **Shopify Email:** abandoned-checkout automations are free and don't count toward the 10,000 free emails a month ([Shopify](https://help.shopify.com/en/manual/promoting-marketing/create-marketing/shopify-messaging/email/pricing)).
- Klaviyo Free: 250 profiles, 500 emails a month.
- Omnisend Free: 250 contacts, 500 emails a month.

## 5. Cash flow: revenue vs cash profit
- **Money goes out first:** you pay CJ when the order is placed, and ad spend is charged as it runs.
- **Money comes in later:**
  - Shopify: at least 3 business days, often 5+ for new merchants. Dropshipping stores report 10-30% reserves.
  - PayPal: up to 21 days.
  - TikTok Shop: about 31 days after delivery (unverified).
- **Chargebacks** cost $15 each and can come months later.
- **What this means:** you can show revenue by day 14, but real cash profit is only clear around **days 45-60**. Keep about $60 aside to pay CJ for roughly 5 orders.

## 6. Day-by-day plan

Track A is organic only. Track B adds a Meta test of about $150-180.

| Day | Manual work | What to automate |
|---|---|---|
| 1 | Set up Shopify ($1) and verify Shopify Payments (identity + bank) straight away. Connect the CJ app. Create TikTok, IG and YouTube accounts and use them normally. | Daily CJ trending scan → filter → LLM scoring → Google Sheet |
| 2 | Browse Creative Center, Meta Ad Library and Amazon (price check). Shortlist 3 products. **Order US-warehouse samples.** | LLM builds a one-page dossier per product: angles, objections, hooks |
| 3 | Build the one-product page, bundles and policies. Place a test order. Turn on abandoned-checkout email. | LLM writes the product copy and FAQ |
| 4-5 | Make 15 videos (5 hooks × 3 variants). Post 2-4 a day per platform. | LLM writes 30 hooks and scripts; queue posts in Buffer |
| 5 (Track B) | Set up the Meta pixel. Launch one ad set at $20/day with 4-6 distinct creatives. | Daily ad-numbers pull → alerts when a kill or scale rule fires (alerts only) |
| 6-7 | Samples arrive: film real footage (10 more videos). **Day 7 checkpoint.** | LLM drafts comment/DM replies for you to approve |
| 8-10 | Make variants of the winning hook. Swap to product #2 if a kill rule fires. | Re-run scoring; watch for late tracking |
| 11-14 | Scale or pivot. Day 14 review: revenue vs cash vs money still owed. | Daily profit & loss sheet |

**Kill and scale rules (break-even cost per sale ≈ $14)**
- **Organic:**
  - 15 videos and none above 1,000 views: change the hooks or format, not the product.
  - 30 videos, 30,000+ views, 100+ store visits and **0 add-to-carts**: kill the product.
  - 3+ add-to-carts but no purchase: test the price (-$5) or a bundle for 3 days.
  - One video above 50,000 views with "where do I buy this?" comments: post 3-5 variants of it.
- **Paid (per creative, after about 1,500 impressions):** kill it if CTR is below 0.8% or fewer than 20% watch past 3 seconds.
- **Paid (per product):**
  - Kill at about $30 spent with 0 add-to-carts.
  - Kill at about $45 with add-to-carts but no purchase.
  - Kill at $100 if cost per sale is more than twice break-even.
  - **Scale** when cost per sale is at or below break-even across 3+ purchases in 72 hours: raise the budget 20-30% every 48 hours.

## 7. Honest success rates
- **No rigorous public data exists.**
  - TrueProfit claims only 1-5% of dropshippers reach consistent profit (undisclosed method).
  - "80-90% fail" has no source.
- **Most common reasons beginners fail in month one:**
  1. Too little money to get a real signal.
  2. Saturated products, or ones cheaper on Prime.
  3. Recycled supplier videos and weak first 3 seconds.
  4. A low-trust store or fake reviews.
  5. China-direct shipping, leading to refunds, chargebacks and payment holds.
  6. Ad-account limits and payout holds.
  7. Killing products too early, or holding on to losers.
  8. Spending the budget on courses and tools.
  9. **Building automations instead of posting 30 videos.** Automate research, scripts, reporting and order checks, but not judgment.
