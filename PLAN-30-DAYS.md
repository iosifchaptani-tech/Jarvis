# 30-day master plan (days 5-34 · 2-31 October 2026)

One plan for everything: the **Pivendo** store, **legal and admin**, the **Wok Wang** website, **Jarvis**, and **money decisions**.

- Each day has **one main focus 🎯** plus a short list. Do the focus first. If you only manage that, the day still counts.
- 👤 = you · 🤖 = Claude (me or PowerShell Claude) · ⚙️ = the n8n agents (automatic)

## 📍 Status (updated Mon 5 Oct, day 8). New chats start here.

**Done ✅**
- **System:** n8n and the agents run at https://n8n.pivendo.com; the PC never sleeps. Bot works (`/help`, `/content`); research comes daily at 07:00. Shopify webhook works.
- **Gewerbe:** sent, waiting for the confirmation (Gewerbeschein).
- **Shop products:**
  - **Step Drill Bit Set** $34.99 (main product)
  - **3-in-1 Knit Winter Set**: adults only, 4 colors, $24.99, "buy 2 for $39.99"
- **Shop settings:** Markets US/CA/AU, shipping zones (US free, CA/AU $7.99), cookie banner, footer, contact page, corrected English shipping policy.
- **Wok Wang:** info collected, draft built.

**In progress ⏳**
- **PowerShell Claude:**
  - winter set ships from the US warehouse
  - Germany market off
  - policy check
  - Shopify Payments verification
  - shop design (theme + homepage)
- **CJ human agent:** waiting for the answer on DDP (duties) for US/CA/AU and the drill sizes.
- **You:**
  - ELSTER account
  - TikTok, Instagram and YouTube accounts "pivendo"

**Still to do 🔲**
1. Connect **pivendo.com** to Shopify, without touching `n8n.pivendo.com`.
2. **PayPal** as a 2nd payment method.
3. **Test order:** buy, check the Telegram alert, refund.
4. **Videos** in CapCut from the scripts. Say "face cover", never "mask"; show all 3 pieces; adults only.
5. **Open the shop** (remove the password) once the Gewerbe is confirmed and Payments is verified.
6. **Wok Wang:** show the draft → changes → go live → send the invoice.
7. **NFC review cards:** start selling after the Gewerbe arrives (€39 / €59 / €79).

**Decisions waiting:** n8n agents Opus → Sonnet, to make the API credit last longer.

---

## Every day (20-30 minutes)

| When | What |
|---|---|
| 07:00 | ⚙️ Product research arrives in Telegram. 👤 Read it (2 minutes). |
| Daytime | 👤 Post the day's videos (from day 10). Answer support drafts with `/send` or `/reply`. |
| 48 hours after each post | 👤 Send `/video ID views clicks sales` so the agents learn. |
| 21:30 | ⚙️ The coach sends the daily report. 👤 Tap ✅/❌ on its rule ideas. |

**Rules for this month:**
- Don't start new projects.
- Don't spend money that isn't in this plan.
- Leave the PC and Docker on.

---

## Week 1 · Foundations (days 5-11)

### Day 5 · Fri 2 Oct · 🎯 Admin start
- [ ] 👤 **Gewerbeanmeldung online** at service-bw.de (about 20 minutes). Activity: *"Onlinehandel mit Waren aller Art (Dropshipping)"*.
- [ ] 👤 **Create an ELSTER account** at elster.de. The activation letter takes 1-2 weeks by post, and you need it for the tax form.
- [ ] 👤 Shopify webhook → `https://n8n.pivendo.com/webhook/shopify-order-4u6tpie7jfgx`, then **Send test notification**.
- [ ] 👤 Delete the test order in n8n (Data tables → orders).
- [ ] 👤 Open research product #1 (garden drill auger) in the CJ app: photos, stock, and whether it fits a normal drill.
- [ ] 👤 **Wok Wang:** call or message them. Collect the info list below and **agree a price**.

### Day 6 · Sat 3 Oct (public holiday) · 🎯 Shopify settings
- [ ] 👤 **Markets:** turn on **US, CA, AU**. Leave **Germany/EU off** for now, since no product has EU stock and you then don't need LUCID.
- [ ] 👤 **Shipping rates:** US free · rest of the world $7.99.
- [ ] 👤 Cookie banner on · contact page · policies in the footer.
- [ ] 👤 Create **TikTok, Instagram and YouTube** accounts called "pivendo". Use each normally for 10 minutes, without posting yet.
- [ ] 🤖 Update workflow 01 in n8n to the latest version (the research price fix). Paste the prompt at the end of this file into PowerShell Claude.

### Day 7 · Sun 4 Oct · 🎯 Weekly review #1 + pick the product
- [ ] 👤 Compare the research from days 5, 6 and 7, then **pick 1 product**. Send `/product SKU testing`.
- [ ] 🤖 **Build the Wok Wang website draft** from the info you collected.
- [ ] 👤 15-minute review: what's done, what's stuck? Tell Claude.

### Day 8 · Mon 5 Oct · 🎯 Product page
- [ ] 👤 Import the product with the **CJ app** → send `/content SKU` → paste the page text.
  - Add a "**drill not included**" note if it's the auger.
  - Offer a **2-pack bundle**.
- [ ] 👤 **Connect pivendo.com to Shopify:** Shopify → Settings → Domains → Connect existing domain. Claude helps with the DNS. Don't touch `n8n.pivendo.com`.
- [ ] 👤 Start **Shopify Payments verification** (ID and bank account). Add PayPal.

### Day 9 · Tue 6 Oct · 🎯 Videos
- [ ] 👤 Make **5 videos** from the 5 scripts in **CapCut** (product photos + text + voice). Or send `/render ID` for the automatic photo video.
- [ ] 👤 Show the **Wok Wang draft** to the owner and collect their changes.

### Day 10 · Wed 7 Oct · 🎯 Launch (if the Gewerbe is confirmed)
- [ ] 👤 Check: Gewerbe confirmed ✅, Payments verified ✅, product page ✅ → **remove the store password**.
- [ ] 👤 Place 1 real test order with your own card, refund it, and check that Telegram alerts you.
- [ ] 👤 **Post the first 2-3 videos.**
- ❗ If the Gewerbe isn't confirmed yet, keep the password on and keep making videos. Launch the day it arrives.

### Day 11 · Thu 8 Oct · 🎯 Wok Wang revisions
- [ ] 🤖 Make the Wok Wang changes.
- [ ] 👤 Post 3 videos.

---

## Week 2 · Rhythm + first money (days 12-18)

### Day 12 · Fri 9 Oct · 🎯 Wok Wang goes live
- [ ] 🤖 Put the website online (their domain, cheap or free hosting).
- [ ] 👤 **Send the invoice.** It's your first real money this month.
- [ ] 👤 Post 3 videos.

### Day 13 · Sat 10 Oct · 🎯 Learn from the first videos
- [ ] 👤 Send `/video` stats for every video older than 48 hours.
- [ ] 👤 Post 3 videos.

### Day 14 · Sun 11 Oct · 🎯 Weekly review #2 (first kill/scale check)
- [ ] 👤 **15 videos and none over 1,000 views?** Change the **hook/format**, not the product.
- [ ] 👤 **One video went well?** Make 3 variations of it.
- [ ] 👤 Money check: Shopify, Claude and domain costs vs sales.

### Days 15-17 · Mon 12 – Wed 14 Oct · 🎯 Post 3 a day and improve
- [ ] 👤 Each day: post 3 videos and send stats.
- [ ] 👤 Day 15: open a **Payoneer** account (free) so you're ready to top up CJ.
- [ ] 👤 When the **ELSTER letter** arrives: fill in the *Fragebogen zur steuerlichen Erfassung* and choose **Kleinunternehmer**. Claude helps.
- [ ] 👤 Wok Wang: ask for a **Google review** and any **referrals**. Other restaurants need websites too.

### Day 18 · Thu 15 Oct
- [ ] 👤 Buffer day: catch up on anything left from week 2.

---

## Week 3 · Decide: keep or switch (days 19-25)

### Day 19 · Fri 16 Oct · 🎯 Check the numbers
- [ ] 👤 Has any product had **3+ add-to-carts but no purchase**? Test **$5 cheaper** or a bundle for 3 days.

### Days 20 and 22-24 · Sat 17 Oct and Mon 19 – Wed 21 Oct · 🎯 Content
- [ ] 👤 Post 3 a day, focusing on the best format.
- [ ] 👤 **Black Friday (27 Nov) prep:** note which videos work best. They'll be re-used in November.

### Day 21 · Sun 18 Oct · 🎯 Weekly review #3 (main kill/scale check)
- [ ] 👤 **30 videos, 30,000+ views, 100+ visits, 0 add-to-carts** → kill the product with `/product SKU killed`, then pick the next one from the research.
- [ ] 👤 **3+ sales?** Top up the CJ wallet with **$50 via Payoneer** and let Claude turn on **auto-pay**, with your OK.

### Day 25 · Thu 22 Oct · 🎯 Optional extra
- [ ] 🤖 Optional: **Jarvis voice command** "Jarvis, how's my store?" reads today's orders and profit out loud. Only if everything else is on track.

---

## Week 4 · Month review + plan for November (days 26-34)

### Day 26 · Fri 23 Oct · 🎯 Second product
- [ ] 👤 If product 1 works, add a **second product** from the research for the same buyers. If it doesn't, replace it.

### Day 28 · Sun 25 Oct · 🎯 Weekly review #4 + money decisions
- [ ] 👤 **If profit is at least €10:** consider a **€6/month server** (Hetzner), so n8n runs without your PC.
- [ ] 👤 **A video went viral:** pay a UGC creator €30-100 for real footage.
- [ ] 👤 **Meta ads:** only with proof (a product with sales) and a €300+ budget you can lose.

### Days 27 and 29-33 · Sat 24 Oct and Mon 26 – Fri 30 Oct · 🎯 Steady
- [ ] 👤 Post 3 a day, send stats, answer support.
- [ ] 👤 Prepare the **Black Friday** offer: a bundle or a gift angle, with honest prices and no fake discounts.

### Day 34 · Sat 31 Oct · 🎯 Month review
- [ ] 👤 + 🤖 Go through the numbers together:
  - revenue, costs and profit
  - best videos
  - the playbook rules the agents learned
- [ ] 🤖 Write the **November plan**, centred on Black Friday / Cyber Monday.

---

## Wok Wang: info to collect (day 5)
- [ ] Type of business, name, address, phone, **opening hours**
- [ ] **Menu with prices** (photo or PDF is fine)
- [ ] Logo, plus photos of the food and the restaurant
- [ ] Just information, or **online ordering / delivery** links (Lieferando etc.)?
- [ ] Languages (German only, or English too?)
- [ ] Domain (do they have one?) and who pays for hosting
- [ ] **Price agreed:** e.g. €300-600 one-off + €15-25/month for hosting and changes

## Money rules for this month
| Spend | When |
|---|---|
| Gewerbe €20-60 | day 5 (required) |
| Shopify $1/month, Claude ~$10, domain ✅ | already running |
| CJ orders | only after a customer has paid you |
| Payoneer top-up $50 | only after 3+ sales |
| €6 server, UGC €30-100, ads | only at the day-28 review, and only with profit or proof |

## Prompt for day 6 (update workflow 01)
Paste into PowerShell Claude, opened as administrator in the Jarvis folder:
```
Please update only the n8n workflow "01 · Product research (daily)" to the newest version from GitHub branch claude/great-dirac-2sqgzw (file dropshipping/n8n-workflows/01-product-research.json). Download that one file, then run the setup from the SAME folder I used before, so my saved settings and webhook path are kept:
powershell -ExecutionPolicy Bypass -File dropshipping\setup.ps1 -PublicUrl https://n8n.pivendo.com -ReplaceWorkflows
I'll type any keys myself. Afterwards check that all workflows are active and that https://n8n.pivendo.com still works. Follow CLAUDE.md.
```
