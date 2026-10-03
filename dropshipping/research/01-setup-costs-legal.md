# Research 1: Starting CJ dropshipping on a near-zero budget (late 2026)

*Research agent report, 2026-09-29. "(unverified)" marks facts the agent could not confirm.*

**Bottom line:** The cheapest legitimate route is Shopify ($1/month trial) + CJ (free) + free
short-form video traffic, starting with CJ US/EU/UK-warehouse products. Reliable *profit* within
~2 weeks is unlikely: China shipping is 8-17 days to the US, new-store payouts can be held 21+ days,
and paid-ad tests usually lose money at first. A *first sale* within 2 weeks is possible.

**Minimum setup checklist**
1. Legal status for your country (section 4).
2. A Shopify store with its built-in policies (refund, shipping, privacy, terms, contact).
3. Shopify Payments and PayPal.
4. A free CJ account and the free CJ Shopify app.
5. 1-3 sample orders.
6. A card or PayPal with money set aside to pay CJ for each order.
7. Tax registration where it applies.
8. EU only: GPSR product information and the withdrawal button.
9. n8n for alerts and monitoring. Don't let it create orders if the CJ app already does.

## 1. Sales channels

| Channel | Start cost | Fees | Dropshipping from CJ allowed? | n8n |
|---|---|---|---|---|
| **Shopify** | $1/month for 3 months, then $39/month | 2.9% + 30¢ | Yes | Built-in Shopify Trigger + Shopify nodes; use HTTP Request for fulfilments |
| **WooCommerce** | Hostinger $3.99/month only with 48 months prepaid ($191.52), renews at $16.99/month ([src](https://www.hostinger.com/woocommerce-hosting)); Cloudways $14/month, SiteGround $17.99/month | Stripe US 2.9% + 30¢; UK 1.5% + 20p | Yes; the CJ plugin is free ([src](https://woocommerce.com/vendor/cjdropshipping/)) | Built-in WooCommerce node |
| **TikTok Shop US** | Free; individuals can join with an ID and the last 4 digits of their SSN/ITIN | 6% referral fee (3% for new sellers' first 30 days) | Only with US-stocked items. Orders must be "In Transit" within 2 business days, delivered within 6 business days, with ≥95% valid tracking ([official](https://seller-us.tiktok.com/university/essay?knowledge_id=3995852763301633&lang=en)) | HTTP Request only |
| **TikTok Shop UK** | Sole traders allowed | About 9% (unverified) | Stock must ship from the UK | HTTP Request only |
| **TikTok Shop EU** | Registered business only | 9% since 8 Jan 2026 | Stock must ship from the EU | HTTP Request only |
| **eBay** | Free for 250 listings/month | 13.6% + $0.40 per order | Yes, from a wholesale supplier; must deliver within the listed time ([policy](https://www.ebay.com/help/policies/listing-policies/drop-shipping-policy?id=4176)) | HTTP Request only |
| **Etsy** | – | – | **No**: reselling is banned | – |
| **Facebook/Instagram** | Free | – | Checkout inside the apps was removed in Aug 2025, so these only send traffic to your own store | Graph API |

**Best on a near-zero budget: Shopify plus organic video.**
- The CJ app has 4.9★ from 2,857 reviews ([src](https://apps.shopify.com/cucheng)).
- Fixed cost for the first 3 months is about $3.
- WooCommerce is not cheaper in practice.
- TikTok Shop US has the best free reach, but only works with CJ US-warehouse products and pays new sellers late.

## 2. CJ Dropshipping specifics

- **Membership is free.** You pay product + shipping per order, and storage is free for 30 days ([src](https://revenuegeeks.com/cjdropshipping-pricing/)).
- **Paying for orders.** Card, PayPal, Payoneer, wire and some local methods are accepted.
  - **The CJ wallet can only be topped up by Payoneer or wire transfer (wire minimum $2,000)** ([src](https://cjdropshipping.com/article-details/1374683186952540160)).
  - Fully automatic API payment (`payType=2`) takes money from the wallet.
  - For beginners: create the order automatically, then pay it by hand with a card or PayPal.
- **Processing time:** 1-3 days if the item is in stock, 3-5 days if not (third-party source).
- **Shipping from China:**
  - US: CJPacket quotes 7-12 days; sellers report 8-17 days.
  - EU: about 15-25 days.
  - Q4 adds 3-5 days; Chinese New Year adds 7-14 days ([src](https://www.dailyfulfill.com/cj-dropshipping-shipping-times-promise-vs-reality-2026/)).
- **Local warehouses:**
  - US: CA, NJ, TX, IN. EU: DE, FR, ES, IT. Plus one in the UK.
  - Delivery takes about 2-7 days ([src](https://cjdropshipping.com/blogs/cj-news/CJ-s-Global-Warehouses)).
  - US-warehouse shipping costs about $4-10 (unverified).
  - **Most of CJ's roughly 400k products ship from China.** Filter by warehouse and check real stock there before listing.
- **Samples:** use the "Buy Sample" button. Typical cost is $3-10 plus shipping (unverified).
- **Branding:** some custom packaging is available from 1 unit. You buy it first and it must reach CJ's warehouse before use ([src](https://cjdropshipping.com/customPackaging)).
- **Disputes:**
  - Open disputes on CJ only; opening them elsewhere risks an account block.
  - Evidence is photos and screenshots.
  - "Buyer doesn't like it" is not covered.
  - Refunds go to your CJ balance.
  - The 2018 policy gave 3 days after delivery to claim damage (may be outdated).
  - EU/UK "change of mind" returns are *your* cost.
- **CJ can bill extra later** if the parcel's weight or volume changes ([src](https://cjdropshipping.com/article-details/113)).
- **Reputation:**
  - Trustpilot shows no rating "due to a breach of our guidelines" and says it removed fake reviews ([src](https://www.trustpilot.com/review/cjdropshipping.com)).
  - Recent complaints: orders stuck in "processing", missed delivery estimates, wrong SKUs, damaged items.
  - Sourcing agents get praised.
- **What the CJ Shopify app automates:**
  - Product import, and stock/price sync.
  - Pulling in orders.
  - Pushing tracking numbers back to Shopify.
  - You still confirm and pay each order.
- **CJ webhooks:** events for ORDER, LOGISTIC, STOCK, DISPUTE and MAKEUP (extra-charge bills). Your endpoint must reply within 3 seconds, over HTTPS only.
- **Don't let both the CJ app and n8n create CJ orders**, or you'll get duplicates.

## 3. Payments, payouts, and the cash-flow gap

- **Shopify Payments:**
  - Normal payouts arrive 3 business days after the sale in the US, UK, DE, FR, NL and IE ([src](https://help.shopify.com/en/manual/payments/shopify-payments/payouts/payout-timing)).
  - In April 2026 Shopify staff confirmed a **21-day first-payout hold** for some new stores ([src](https://community.shopify.com/t/21-day-hold-out-on-the-payouts/607717)).
  - Shopify can also hold reserves, e.g. 10% of each sale for 120 days ([src](https://help.shopify.com/en/manual/payments/shopify-payments/payouts/reserves)).
- **PayPal:**
  - New sellers' payments can be held for **up to 21 days** ([src](https://www.paypal.com/us/cshelp/article/new-paypal-account-%E2%80%93-payments-on-hold-and-accessing-your-money-quicker-help848)).
  - With tracking added, the money is released about 24 hours after the courier confirms delivery ([src](https://www.paypal.com/us/cshelp/article/how-can-i-release-my-payments-on-hold-help129)).
  - So push tracking to PayPal as soon as CJ issues it.
- **Stripe:** the first payout takes 7-14 days. The dispute fee is $15 (US) or £20 (UK).
- **TikTok Shop US:** new sellers are paid on an "Introductory" schedule plus a 30-day reserve; third parties say that means about 31 days after delivery.
- **eBay (new sellers):** paid 2-31 days after delivery, depending on the shipping label.
- **Float formula:** orders per day × CJ cost per order × days until payout + ad spend.
  - Example: 5 orders/day × $14 × 21 days ≈ **$1,470**, even when the store is profitable.
  - Growing fast without cash is how beginners go broke.

## 4. Legal and admin minimum

**US**
- You're a sole proprietor by default. Register a DBA if you trade under a brand name.
- Get a seller's permit if your home state has sales tax (free in CA and TX).
- Other states only matter after economic-nexus thresholds, usually $100k in sales.
- Marketplaces collect sales tax for you.

**UK**
- If your gross trading income is **£1,000 or less** a year, you don't need to tell HMRC ([gov.uk](https://www.gov.uk/guidance/tax-free-allowances-on-property-and-trading-income)).
- **VAT on parcels worth £135 or less shipped from abroad:** the seller must charge VAT at the point of sale and register ([gov.uk](https://www.gov.uk/guidance/vat-and-overseas-goods-sold-directly-to-customers-in-the-uk)). Whether that applies to small UK sole traders is unclear, so ask an accountant.
- UK-warehouse stock avoids this.

**EU (varies by country)**
- Business registration: Germany €15-65; Netherlands KVK €85.15; France micro-entrepreneur free.
- Germany requires an **Impressum** (legal contact page). Competitors send paid warning letters over a missing one (example €900).

**US import duties**
- The de minimis (duty-free under $800) rule ended for China in May 2025 and for everyone on 29 Aug 2025. It was made permanent in regulation on 24 Jun 2026.
- Since 24 Jul 2026 postal parcels pay normal duties, including a **12.5% Section 301 tariff on China** ([src](https://zonos.com/us-tariff-updates)).
- CJ said in 2025 its China-to-US freight rates include tariffs (unverified for 2026). Confirm in CJ's freight calculator, or use the US warehouse.

**EU VAT**
- IOSS covers parcels worth €150 or less. CJ's IOSS option charges the VAT plus 3% of the VAT as a handling fee.
- Since 1 Jul 2026 there is also a **€3 customs duty per item category** on these parcels ([EC](https://commission.europa.eu/news-and-media/news/ensuring-fairness-and-safety-eur3-customs-duty-low-value-parcels-2026-06-29_en)).

**Consumer rules**
- **EU and UK buyers have 14 days to cancel** without a reason, and must be refunded within 14 days.
  - If you don't explain this properly, the right extends to 12 months.
  - Since **19 Jun 2026, EU shops need an online withdrawal button** ([Shopify](https://help.shopify.com/en/manual/compliance/legal/eu-right-of-withdrawal)).
- **US FTC Mail Order Rule:** you need a reasonable basis for any shipping time you state. If you'll be late, tell the customer and offer a refund ([FTC](https://www.ftc.gov/business-guidance/resources/business-guide-ftcs-mail-internet-or-telephone-order-merchandise-rule)).
- **EU product safety (GPSR):**
  - Each listing must show the manufacturer, an **EU responsible person**, a product ID and warnings.
  - Options: skip the EU at first, pay a responsible-person service (about €150-500/year), or act as the responsible person yourself.

**What gets beginners banned or sued**
- **Fake reviews:** FTC fines up to $53,088 per violation.
- **UK:** fake reviews and fake countdown timers are banned since 6 Apr 2025, with fines up to 10% of global turnover.
- **EU:** discounts must be measured against the lowest price of the previous 30 days.
- **Meta:** a customer feedback score below 1 stops your ads.
- **Trademarks:** brand names, "dupes" and licensed characters lead to takedowns and bans.

## 5. Budgets (first month, itemised)

**$0-50**
- Shopify: $1.
- Domain: use myshopify.com, or about $10.44 at Cloudflare.
- CJ and its app: $0. n8n on your own PC: $0.
- 1 sample: about $10-15.
- Float for 1-2 orders: about $25.
- Ads: $0.
- Realistic outcome: learning, and maybe 0-3 sales.

**$100-200**
- Everything above, plus a domain ($11).
- 2-3 samples from a US/EU warehouse: about $45.
- Float: about $60.
- Meta ads at $5-10/day: about $60-80.
- TikTok Ads is not practical here (minimum $50/campaign, $20/day per ad group).

**$300-500**
- Domain: $11. Shopify: $1-39.
- Samples: about $50.
- Float: $100-150.
- Ads: $150-250, enough for about 1-2 honest product tests.
- Optional: n8n on a VPS at about $5/month.

**Remember:** Shopify costs $39/month after the 3-month trial.

## 6. Scams and failure data

- **FTC cases against "done-for-you" or "AI" store sellers:**
  - Automators: $22M
  - Ascend Ecom: about $25M, owners banned
  - Ecommerce Empire Builders
  - FBA Machine: $15M
  - Click Profit
  - ([FTC](https://www.ftc.gov/news-events/news/press-releases/2025/08/ftc-case-against-e-commerce-business-opportunity-scheme-its-operators-results-permanent-ban-industry))
- **Fake suppliers or agents** who ask for a wire transfer.
- **Phishing:** "store suspended" or "trademark complaint" emails. Real Shopify email comes only from @shopify.com.
- **Stolen-card orders:** you've already paid CJ, then lose the sale plus a $15 dispute fee.
- **Failure rates:** the widely quoted "80-90% fail" figure **has no traceable primary study** ([src](https://trueprofit.io/blog/dropshipping-success-rate)). Expect your first 1-3 products to fail.
