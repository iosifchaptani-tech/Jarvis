# 30-day master plan (days 5-34 · 2-31 October 2026)

One plan for everything: the **Pivendo** store, **legal and admin**, the **Wok Wang** website, **Jarvis**, and **money decisions**.

- Each day has **one main focus 🎯** plus a short list. Do the focus first. If you only manage that, the day still counts.
- 👤 = you · 🤖 = Claude (me or PowerShell Claude) · ⚙️ = the n8n agents (automatic)

## 📍 Status (updated Mon 13 Oct, day 16). New chats start here.

**Done ✅**
- **System:** n8n and the agents run at https://n8n.pivendo.com. The bot works (`/help`, `/content`), and research comes daily at 07:00 while the PC is on.
- **Research agent (9 Oct):** stricter brief. Passes the 3-second video test, not cheap on Amazon or in local shops, not saturated, not seasonal.
- **Store plan (9 Oct):** a growing general store. 2 new products every 2-3 weeks; videos focus on the newest products. Electric products are OK now (no lasers, no built-in lithium). Price rule: 1.5× landed cost, at least $7 above it.
- **Gewerbe:** confirmed (6 Oct).
- **Wok Wang:** closed. They said no (owner told Claude on 11 Oct). The concept site stays as a portfolio piece.
- **Shopify:**
  - pivendo.com connected (primary domain + SSL; `n8n.pivendo.com` untouched)
  - Dawn design published, policy fixes live
  - Markets US/CA/AU active, Germany off, backup region United States, store currency USD
  - Shipping: US free, CA/AU $7.99
  - Payments verified; payout in EUR to Revolut (Shopify converts at about 1.5-2%)
- **Webhook:** event **Order payment** (fixed from "Cart creation").
- **Test order** in test mode worked (Telegram alert, email, Shopify, and synced to CJ). Test mode is OFF again.
- **CJ:** both products connected; every variant mapped (account CJ5881021).
- **Products:**
  - **Step Drill Bit Set** $34.99: 3 step bits 4-12 / 4-20 / 4-32 mm
  - **3-in-1 Knit Winter Set** $24.99: adults only, 4 colors, "buy 2 for $39.99"
- **Agents model:** Sonnet (half the price of Opus). To switch back, set the Anthropic Chat Model nodes to `claude-opus-5-5`.
- **Trading agents, Step 1 (12 Oct):** data plus the 2 Lines back-test are done. **Verdict: FAIL, no edge.** On unseen 2022–2026 data it averaged −0.135 R per trade, and before costs it is about zero. Report card: `Desktop\Trading Agents\reports\2lines-report-card.md`. Waiting for the owner's OK on Step 2.
- **Trading agents, Step 2 (12 Oct, owner OK; demo trader comes last):**
  - Notion **Trading Journal** made (private, next to the study guide).
  - The other 3 strategies were back-tested: **all fail too** (`reports/other3-report-card.md`).
  - Review agent built: runs on request ("review my trades").
  - **Demo trader built** (folder `Trading Agents/trader` on the Desktop): trades 2 Lines on the TradeLocker DEMO (GatesFX).
  - **Owner next:**
    1. Change the demo password.
    2. Double-click `setup-login.cmd`.
    3. Run `start-paper.cmd` before a session.
    4. Show Claude the logs.
    5. Then switch to demo.

- **Higgsfield (13 Oct):** auto-renewal **cancelled** by the owner. The page says "Auto-renewal cancelled. Your access lasts until October 13 at 23:26." No €59 charge.
- **Second Claude account (13 Oct):** the desktop app runs on a new Claude account. The old account's private artifact links and desktop reminders are not visible there. PowerShell Claude was still on the old account (weekly limit until 16 Oct, 13:00); the owner signed it in to the new account on 13 Oct and a test answered OK. Claude's Chrome window is logged in to n8n (11 workflows, 00-05 and 07 published).

- **Private pages back on the new account (13 Oct):** Lattelino, Wok Wang, holiday flat, Start-Kit, Galaxy showcase and Pitch Playbook were republished unchanged. The new links are in each project's STATUS.md and in the global notes.
- **Wreath product page (13 Oct, owner's decision "add it to the page now"):** the projection is on the page. Text: "in a dark room it also works as a mini projector … best in a dark room … photos come from the manufacturer". Two ceiling photos (stills from CJ's clip) were added, and the doubled description block was removed. **CJ has still not confirmed the projection**: if the real effect is weaker, expect refunds. Asking CJ support stays worth doing.
- **Videos v2 (13 Oct, free re-render with Remotion, no credits):** 12 files in `Desktop/Pivendo Videos/v2`: each of the 6 videos as `-halloween` (use until 17 Oct) and `-xmas` (from 18 Oct). Fixed: end card 2.5 s with a question box inside the safe area on every video, bigger "AI presenter" note, sound at about −14 to −16 LUFS, no silent ending, standard colour range, and character2 now uses the **real** CJ plug-in clip (the AI hand scene is gone). The source backup is `.playwright-mcp/video/remotion/src-backup-2026-10-13`. Captions and the posting order are in `v2/POSTING-PLAN.txt`.

**Video check (13 Oct, Claude looked at all 6 frame by frame)**
- The 2 character videos show the AI person for 8 s before the product appears; hook4 and hook1 show the product or the effect in the first second. **New posting order: hook4 → hook1 → character2 → hook2 → hook3 → character1.**
- I can't hear the character's voice; only the loudness was measured.
- TikTok @pivendoteam on 13 Oct, 02:20: bio is set, 0 public videos. Instagram `pivendoteam` and YouTube `@PivendoTeam` exist (seen in the owner's browser tabs on 13 Oct).

**Owner decisions on 24/7 posting (13 Oct)** (this one job is allowed although the plan says "no new automations until the first sales")
- **No outside posting service.** Instagram and YouTube are posted from n8n through the official APIs. **TikTok stays manual:** the owner schedules in TikTok Studio (at most 10 days ahead), because TikTok only lets self-made apps post private videos.
- **Nothing goes public without the owner's ✅ in Telegram.**
- Consequences:
  - YouTube can be uploaded early with a publish time, so it also goes out with the PC off.
  - Instagram has no such timer in its API: it posts only while n8n is running. With the PC off it needs a server (Oracle free: card needed, now 2 cores/12 GB; Hetzner about €5.50-6 a month plus VAT). **Server decision still open.**
- **Later on 13 Oct the owner asked for 2 videos a day, times chosen by Claude, with ongoing analysis so it gets better over time.**
  - **Times: 12:30 and 20:30 US Eastern** (US lunch and US evening; 18:30 and 02:30 German time in most weeks). These are a starting point: a time only changes when the numbers show it, as a rule the owner approves.
  - **Daily analysis:** a scheduled task in the Claude desktop app ("Pivendo: daily social stats and next steps", every day about 15:00, only while the PC and the app are on). It reads TikTok Studio, YouTube and Instagram **read-only** in Claude's Chrome window, saves the numbers to `Desktop/Pivendo Videos/stats/stats.csv`, writes `stats/REPORT.md`, and keeps a short "Social stats (latest)" block in this plan.
  - **TikTok, prepared by Claude on 13 Oct, each waiting for the owner's final click:** hook4 (post now), hook1 (13 Oct 18:30), character2 (14 Oct 02:30, AI label on). Still to prepare: hook2 (14 Oct 18:30), hook3 (15 Oct 02:30), character1 (15 Oct 18:30, AI label on). All have "Your brand" on.
  - **Video supply:** 6 different videos last 3 days at 2 a day. After that new ones are needed: free re-edits of the real footage (a limited number before they look alike), more CJ clips, a filmed sample, or AI-character clips (credits; ask before each one).
  - **Still open:** TikTok cannot post by itself without an outside service (owner chose none), so it stays "Claude prepares, owner clicks". Instagram and the analysis need the PC on until there is a server.
- Being built: workflow "08 · Social publisher" (`/queue`, ✅/❌, YouTube upload, Instagram publish, 48 h stats into the feedback table). It needs API logins that only the owner can create (Meta developer app, Google Cloud project); the steps will be in `dropshipping/SOCIAL-SETUP.md`.
- **Repo and tools (13 Oct, cloud Claude):**
  - PR #3 merged. The store work and this plan now live on **main**; every Claude pulls and pushes `main` (CLAUDE.md updated).
  - **Jarvis Galaxy**, a map of every function, section and file in this repo: **that page was deleted by mistake on 13 Oct** (desktop Claude took it for a leftover test page of its own "Jarvis Galaxy" showcase and the owner agreed to delete it; the old link is dead). It can be published again from `graphify-out/graph.html` when the owner says so.
  - The knowledge graph behind it is committed in `graphify-out/` (how to use it: CLAUDE.md).

**Social stats (latest)** (13 Oct, 15:00, first automatic check)
- **No numbers read.** The logged-in Chrome window was in use by another Claude chat, and the public pages show cookie walls or hide the videos. Nothing was clicked or changed.
- Total views: TikTok not read (last known 83 on hook1 v1, 13 Oct 13:40) · YouTube not read · Instagram not read (no Reels visible).
- Best video: too early to say (one public video).
- **Next:** press Schedule on the prepared TikTok uploads (hook4, character2, hook2; pick the music first), and keep the Chrome window free of other chats at 15:00, or press "Run now" on the task later. Details: `Desktop/Pivendo Videos/stats/REPORT.md`.

**Shipping rules for paying orders in CJ**
- US drill: **LuWei Ordinary US** or **YunExpress Ordinary**. Both are DDP.
- Winter set to the US: the **US warehouse** (CJ picks it by itself).
- CA/AU: **CJPacket Ordinary**, but only if the product page shows **no yellow "DDU" box**.
- Wreath: US **LuWei Ordinary US**, CA **CJPacket JYSP Sensitive** (or Ordinary), AU **CJPacket Ordinary** (never Eub, it's DDU).
- ❌ Never choose a method with the "DDU" box.

**▶️ Tomorrow (start here)** (rewritten 13 Oct, 04:10, for Tue 13 Oct after sleep)

**TikTok state (13 Oct, 04:10):** three uploads are prepared in Claude's Chrome window with the **no-music** versions, captions and labels, each waiting for the owner: hook4 (post now), hook1 (13 Oct 18:30), character2 (14 Oct 02:30, AI label on). **Owner's rule: he chooses the music himself before every post (Sounds → pick → Save), and Claude reminds him each time.** Still to prepare: hook2 (14 Oct 18:30), hook3 (15 Oct 02:30), character1 (15 Oct 18:30, AI label on). The old "one a day at 01:00" plan is out of date.

**👤 Owner's to-do list for 13 Oct, outside TikTok**
1. **Oracle, 2 steps (5 min).** Claude is not allowed to change network settings there. In the Oracle tab: (a) trading-bot → IP administration → row `10.0.0.107` → Actions → Edit → Ephemeral public IP → confirm; (b) Instances → trading-bot → Networking → "Connect public subnet to internet" → Connect. Then write "oracle done": Claude installs Docker and n8n and copies n8n over. The final switch needs the owner once more for the Cloudflare tunnel.
2. **Claude app (2 min).** Sidebar → Scheduled → "Pivendo: daily social stats and next steps" → Run now once, and approve the browser tools. Connect Notion and n8n with the Connect buttons if Claude should use them on the new account. Close the old PowerShell Claude window and open a new one.
3. **Instagram + YouTube, first posts by hand (15 min).** Until the automation is live: post **hook4** from the phone apps and pick the music there. The no-music files are in OneDrive: `Desktop/Pivendo Videos/v2/no-music`; captions are in `v2/POSTING-PLAN.txt`. Switch the AI label on for the two character videos only.
4. **API logins for the automation (about 1 hour, can wait a day).** Follow `dropshipping/SOCIAL-SETUP.md`: Part 1 YouTube (about 20 min), Part 2 Instagram (about 40 min). Type keys only into n8n, never into chat. Claude imports the workflow only after the review is finished.
5. **Ask CJ about the projection (5 min).** The shop page now says the wreath projects shapes onto the ceiling, but CJ never confirmed it. Ask CJ support for a real customer video or a clear yes/no. Claude can write the message.
6. **Shop admin (10 min).** Decide "Taxes included" (Settings → Taxes and duties; US prices are normally shown without tax). Delete test order #1002 in CJ ("Mehr" → delete/ignore; never pay it).
7. **ELSTER (10 min).** Create the account at elster.de. The activation letter takes 1-2 weeks, so starting now saves time.
8. **Telegram, as every day.** Read the 07:00 research, tap ✅/❌ on the 21:30 Coach report, and pay CJ yourself if an order alert comes (AU = CJPacket Ordinary, never Eub).
9. **Higgsfield, optional, before 23:26.** Trial access ends tonight with about 66 credits left; nothing more to cancel. Claude asks before every single generation.
10. **If there is time: trading bot.** Change the demo password, double-click `trader/setup-login.cmd`, run `start-paper.cmd`, show Claude the logs.

**▶ Resumed on 13 Oct, 13:40:**
- **n8n was offline from the shutdown until 13:40**: Docker Desktop did not start with Windows, so the 07:00 research did not run. Claude started Docker; `n8n.pivendo.com` answers again. To avoid this: Docker Desktop → Settings → General → "Start Docker Desktop when you sign in" (owner's click), or the move to Oracle.
- **TikTok already has one public video:** the owner posted **hook1 (v1)** himself on 12 Oct at 18:29 (83 views, 0 likes on 13 Oct, 13:40). So hook1 is left out of the new batch.
- **Three uploads are prepared again in Claude's Chrome window** (no-music versions, captions, "Your brand"), each waiting for the owner to pick the music and press Schedule: **hook4 → 13 Oct 18:30**, **character2 → 14 Oct 02:30 (AI label on)**, **hook2 → 14 Oct 18:30**. Next to prepare: hook3 (15 Oct 02:30), character1 (15 Oct 18:30, AI label on).
- TikTok Studio restored the last unsaved draft with "Continue" after the restart (only one draft is kept).
- **Workflow 08 review fixes: all 7 done (13 Oct, about 14:10) and checked by Claude:** 66 tests pass, the generator output is stable, workflows 00, 01 and 03-07 are unchanged, no money setting was touched, `setup.ps1` parses, and workflow 08 contains no delete call. Still **uncommitted and not imported** (backup: `.playwright-mcp/backup/social-publisher-2026-10-13-fixed/`). The fix list in the "Paused" block below is finished.
- **Next step for workflow 08 = import, only with the owner's OK and with him at the PC,** because it replaces the live Telegram workflow 02: `-ReplaceWorkflows -OnlyWorkflows 02,08` (see `dropshipping/SOCIAL-SETUP.md`, Step 0). `setup.ps1` switches on what it imports; 08 stays in to-do mode until `youtube_auto` / `instagram_auto` are set to `yes`. Never live-tested yet: the swap of workflow 02 in real n8n 2.41.3, the Telegram buttons, and every YouTube and Instagram call.

**⏸ Paused on 13 Oct, about 04:30, because the owner switched the PC off. Resume from here:**
- **Workflow 08 (social publisher):** built, 61 tests pass, **not imported, not committed** (uncommitted files in `dropshipping/`; a backup copy is in `.playwright-mcp/backup/social-publisher-2026-10-13/`). The reviewer said "safe to import as inactive" **after** these fixes, which are **all still to do** (a fixer was started and stopped before it changed anything):
  1. `setup.ps1` `-OnlyWorkflows 02,08` loads nothing when typed unquoted in PowerShell 5.1 ("2,8"): accept a list, split, pad to 2 digits, stop when nothing matches.
  2. `setup.ps1` archives the old workflow before the new one is proven to start: import new inactive → deactivate old → activate new → on failure reactivate old → archive old only on success.
  3. Reject races: re-check the status right before the Instagram publish call; make `/reject` say clearly when a YouTube video is already scheduled (link and Studio clicks; no delete call).
  4. Wording of a failed YouTube upload ("check Studio before retry"), and a duplicate warning on `/retry` for failed uploads too.
  5. A failed Telegram alert must not block the publishing branches; test that "Save marks" has no onError.
  6. `SOCIAL-SETUP.md`: a re-import resets youtube_auto, instagram_auto, post_times and ig_user_id; how to load the new 02 before any social login exists.
  7. Add "Choose the music first." to the approve and to-do messages and to `BOT-GUIDE.md`.
- **TikTok:** the three prepared uploads lived only in open browser tabs. If the PC was shut down they are gone and must be prepared again (about 5 minutes for Claude; files in `.playwright-mcp/upload/no-music/`, captions in `Pivendo Videos/v2/POSTING-PLAN.txt`). TikTok Studio keeps at most one unsaved draft.
- **Not running after a restart:** Jarvis Galaxy (off on purpose). n8n and the tunnel start again with Docker and Windows.

**🤖 Claude's side, waiting for a word from the owner:** "done" after the three TikTok clicks (then Claude checks them and prepares the next three); "oracle done"; the reviewer's result on workflow 08 (then import as inactive with `-OnlyWorkflows 02,08`); add the "choose the music first" line to the workflow's approve and to-do messages.
- 🤖 **Trading autopilot (owner pasted the prompt on 13 Oct, 15:00):** the 4 files from `claude/wizardly-lamport-m2e3m9` are in `Desktop\Trading Agents\autopilot` (byte-identical, 17 tests pass). A builder is building the rest of `AUTOPILOT.md` (demo only, nothing started yet). Owner only: change the demo password, make the trading Telegram bot with @BotFather and type its token into the setup window, and run the autostart script himself (Task Scheduler and power plan are system settings). `rules/active/` starts empty: the autopilot trades nothing until a rule passes the gate and the shadow stage.
- Wok Wang is closed (they said no). Shopify store name is already "Pivendo" (checked 11 Oct).
- ✅ Owner decision (11 Oct): **no more wreath videos for now.** The 6 are enough; post them first and only make new ones (more of the winning format) after the stats.
- 🎬 **6 videos ready** in `Desktop/Pivendo Videos`: pivendo-hook1..4.mp4 (real footage only) + pivendo-character1/2.mp4 (owner's AI character, voice checked OK).
- 👤 Posting plan (TikTok @pivendoteam, 1 video per day, US evening = about 00:00-03:00 German time, or schedule it):
  1. Day 1: **hook4** (v2; shows the product in the first second)
  2. Day 2: **hook1** (v2; opens on the ceiling effect)
  3. Day 3: **character2** (v2; real plug-in clip)
  4. Then hook2, hook3, character1 (order changed on 13 Oct after the frame check; the old order started with character2)
  - Every post: Content disclosure → "Your brand" ON. Character videos also: "AI-generated" label ON. Caption with "pivendo.com", and pin a comment "Shop: pivendo.com 🎄".
- 🤖 48 h after each post: owner logs in to TikTok in the Playwright browser window and writes "analyze" → Claude reads TikTok Studio (read-only), compares the hooks, writes stats into the n8n feedback table.
- ✅ **Higgsfield trial: auto-renewal cancelled on 13 Oct** (see Done ✅). Trial access ends 13 Oct at 23:26; 66 credits were left at 02:00. Free AI Influencer gens: 1 left (owner decides each one).
- Video project for new edits: `Boss Jarvis/.playwright-mcp/video/remotion` (Remotion 4.0.528; compositions WreathHook1-4, WreathCharacter, WreathCharacter2).
- Shop: public since 10 Oct. On a Telegram order alert: pay it in CJ yourself (AU = CJPacket Ordinary, never Eub). Stop US sales about Dec 8.
- Still open (owner): "Taxes included" decision; delete test order #1002 in CJ; profile name "PivendoTeam" + Impressum line in the TikTok bio.

**Older notes (9 Oct)**

- Already done by PowerShell Claude (9 Oct):
  - winter set archived, its "buy 2" discount off
  - collections Tools / Christmas (empty) / All products
  - menu Home · Christmas · Tools · Contact
  - honest About us page, linked in the footer
- 👤 Owner:
  1. Log in to CJ in the Chrome tab PowerShell Claude opened, then write "logged in" to PowerShell Claude.
  2. ✅ (done 10 Oct by Claude in n8n)
- ✅ Done 10 Oct (desktop Claude): real CJ cost for the wreath, see "Wreath costs" below.
- ✅ Done 10 Oct: wreath listed with the CJ app and set to **Draft** in Shopify: $24.99, variants Christmas (CJYS315715002BY) + Halloween (CJYS315715001AZ), no compare-at price, collection Christmas, CJ default shipping LuWei Ordinary US.
- ✅ Done 10 Oct: wreath draft cleaned up: type Christmas Decor, variants renamed **Christmas / Halloween**, only 3 photos (tree, Christmas gift box, Halloween). Projection and 6PCS photos removed from the gallery and the description, because we don't know yet whether it projects onto the ceiling.
- ✅ Done 10 Oct: automatic discount **"Buy 2 wreaths, save $4.99"** created (wreath only, min. 2 items, once per order) and **deactivated** (shows "Expired"). To turn it on: Discounts → the discount → Edit the schedule (remove the end date). Then add "Buy 2 for $44.99 (you save $4.99)" to the description and test it with a test-mode order.
- ❓ Open: does the wreath project stars/snowflakes onto the ceiling? Ask CJ or order a sample. If yes, add it to the text and the photos back.
- ✅ Done 10 Oct: homepage built in a theme **copy** ("Copy of Dawn", not live yet): tagline "Useful finds, delivered." + "🎄 Christmas gifts to the US: please order by December 8." under the banner, and the 4 trust boxes now have the heading "Why Pivendo". Checked on desktop and phone. Live "Dawn" is unchanged.
- ✅ Done 10 Oct: wreath **Active** ($24.99, description has "Buy 2 for $44.99"), discount "Buy 2 wreaths, save $4.99" **Active** (no end date).
- ✅ Done 10 Oct: wreath banner (image with text + "Shop the wreath" button) added at the top of the homepage in "Copy of Dawn". The drill banner is now second.
- ✅ Done 10 Oct: owner published "Copy of Dawn" = new live theme (old "Dawn" kept as backup). Phone check OK: homepage (wreath banner first) + wreath product page (Christmas/Halloween buttons, $24.99).
- ✅ Done 10 Oct: new theme copy **"Copy of Copy of Dawn"** (not live yet): drill banner removed; dark "Welcome" section at the top with the white Pivendo logo, "Useful finds, delivered.", Christmas note, buttons "Shop the wreath" + "About us"; teal logo in the header (150 px) + favicon. Checked on desktop and phone. White logo uploaded to Content → Files. Separate landing page: decided against (it costs buyers a click).
- ✅ Done 10 Oct: owner published "Copy of Copy of Dawn" = live theme with logo + welcome section.
- ✅ Done 10 Oct: wreath added to the n8n **products** table (row 15, SKU CJYS315715002BY, status testing), so `/content CJYS315715002BY` works. Note for agents: never claim projection.
- ✅ Done 10 Oct (Claude, directly in the n8n feedback table, same as the /product command): winter set CJNSFSMZ00628-Dark black = **killed**, wreath CJYS315715002BY = **testing**.
- 🧑 **Pivendo presenter = option 4** (man, late 20s, short curly hair, short beard, green knit sweater, cosy room with fairy lights). Reference picture: Boss Jarvis/.playwright-mcp/higgsfield/presenter/pivendo-presenter-main.png (local). Always use this face; never the other options.
- 🎬 Video decision (10 Oct): no samples (no money now). Videos = the real CJ product footage + an AI presenter (Higgsfield) for hook/talking parts only. AI must never generate the wreath itself, never act as a real customer, and every video gets the platform's "AI-generated" label.
- ✅ Done 10 Oct: Higgsfield account (free plan, 10 credits). Higgsfield CLI on this PC is logged in. 4 presenter candidates made with Soul 2.0 (0.12 credits each; 9.52 left). Pictures: Boss Jarvis\.playwright-mcp\higgsfield\option-1..4.png (local only). Costs: talking video 4 s ≈ 28 credits (Seedance 2.5) / ≈ 7.5 (Kling 3.0 Turbo), so videos need a paid plan or the free CapCut route.
- ❓ Product page says "Taxes included." Check Settings → Taxes and duties (US prices are normally shown without tax). Owner's decision.
- ✅ Done 10 Oct: test-mode order **#1002** (1 Christmas + 1 Halloween): total $44.99 with "Buy 2 wreaths, save $4.99", synced to CJ (DP2610101254190648300) at a CJ cost of **$21.75** via LuWei Ordinary US, exactly as calculated. Test mode is OFF again (checked).
- ✅ Done 10 Oct: Telegram alert for #1002 came (owner). #1002 **cancelled in Shopify** (test refund $44.99, stock back, no customer email).
- ⚠️ #1002 is still listed in CJ "Bestellungen im Laden" (unpaid, harmless). **Never pay it.** Owner can remove it: tick the order → "Mehr" → delete/ignore.
  3. homepage: wreath banner, the 2 products, "Why Pivendo", tagline "Useful finds, delivered.", "Order by December 8" note
  4. phone check + final check
- Then: `/content SKU` for the wreath → start 2-3 videos a day 🎄

**Wreath costs (checked in CJ, 10 Oct)**
- CJ SKU **CJYS315715002BY**, style "Christmas projection light" (USB, 240 g, 6,959 in stock at the factory). Link: https://www.cjdropshipping.com/product/cozy-led-star-projector-light---ceiling-atmosphere-lamp-for-home-decor-christmas-holiday-gift-night-light-p-2609120245271608200.html
- Product $5.90 each. 2 wreaths ship together in one parcel.

| To | Method (no DDU) | Days | 1 wreath | 2 wreaths |
|---|---|---|---|---|
| US | LuWei Ordinary US | 5-11 | $12.74 | $21.75 |
| CA | CJPacket JYSP Sensitive | 7-15 | $12.04 | $21.06 |
| AU | CJPacket Ordinary | 4-8 | $16.97 | $24.51 |

- Profit after Shopify fees (about 5% + $0.30): US 1 ≈ $10.70, US 2 for $44.99 ≈ $20.70. CA/AU are higher because the customer pays $7.99 shipping (CA 1 ≈ $19, AU 1 ≈ $14).
- ❌ AU: CJPacket Eub (the cheapest, CJ's default) shows the **DDU** box. Always switch AU orders to **CJPacket Ordinary**.

**Product decisions (9 Oct)**
- 🎄 **Christmas LED wreath** (USB only, LuWei Ordinary US = DDP, 5-11 days): **new main product**. Add it via ADD-PRODUCT. Price **$24.99** (owner decision 9 Oct; about $11 profit per order). Stop US sales about Dec 8. Halloween version only as a 2nd variant ("Order by Oct 17").
- 🧸 **Squishy mystery box:** only after the owner shows the CPC / ASTM F963 test report. Check whether CJ packs several items in one parcel.
- 🔩 Drill: stays in the shop, no videos for now (later with the AI influencer).
- 🧣 Winter set: **removed** (owner decision 9 Oct). Archive it in Shopify; don't delete it. The store has 2 products: the drill + the Christmas LED wreath.
- ❌ Skipped: pumpkin night lamp (lithium battery, sold as a kids' gift, Halloween too close, 4,275 lists). Plain squishies without certificates (kids' toy, cheap on Amazon).
- Bundles: keep separate products plus an honest "buy together, save $X" offer, so CJ ships every item. Test it with a test-mode order.

**Still to do 🔲**
1. **Open the shop:** remove the password (Online Store → Preferences), if not done yet.
2. **Videos: 2-3 a day for 14 days.** This is the main job now. For the winter set, say "face cover", never "mask", show all 3 pieces, and use adults only.
3. **Kill rule:** about 15 videos and nobody asks "where can I get this?" → kill the product and test the next one.
4. **New products:** check them with `dropshipping/ADD-PRODUCT.md`. Test at most 2-3 at a time.
5. **ELSTER account** → *Fragebogen zur steuerlichen Erfassung* (Kleinunternehmer) → Steuernummer. You need it on invoices.
6. ~~**Wok Wang:** show the draft → changes → go live → send the invoice.~~ Closed: Wok Wang said no (owner, 11 Oct).
7. **NFC review cards** (€39 / €59 / €79).
8. **Open questions:**
   - Ask CJ whether the drill set includes the 3 saw drill bits from the size photo.
   - Ask whether a default shipping method per country can be saved in CJ.

**Trading agents (owner started it 11 Oct, own folder `Desktop\Trading Agents`; read its docs/BRIEF.md):** a trading agent team on a **demo account only**: one agent back-tests the study-guide strategies on old market data, one trades the demo automatically, one reviews the losing trades and proposes rule changes (the owner approves each one), plus a trading journal the owner and Claude keep together. Study guide: https://app.notion.com/p/3f67f95d8d7581958d0fcbbccd473eca. Never a live/real-money account.
- Steps 1 and 2 are done (12 Oct, see Done ✅): journal, all 4 back-tests (no edge in any), review agent and demo trader. **Next: the owner's 5 steps listed under Done ✅** (demo password, `setup-login.cmd`, `start-paper.cmd`, show the logs, then demo).
- **Owner decision 13 Oct: autopilot.** Run 24/7 on the demo. The lab may invent and add its own rules (no ✅ needed, owner can `/reject`). Goal: demo above its start balance 14 days after the start. Cloud Claude wrote the test gate, the safety limits (17 tests) and the build plan: `trading/AUTOPILOT.md` on branch `claude/wizardly-lamport-m2e3m9`. **Next:** the owner pastes the autopilot prompt into the Claude desktop app, which builds and starts it. Owner only: change the demo password and make the trading Telegram bot with @BotFather.
- The CPI pending-order idea is parked.

**Skipped on purpose:** PayPal. It's connected and approved but **Inactive**. Later: rename the PayPal business name from "My Store" to Pivendo, then click **Activate** (Settings → Payments → PayPal).

**Focus:** sell before building anything new. No new tools or automations until the first sales (except Higgsfield videos).

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
- [x] 👤 **Gewerbeanmeldung online** at service-bw.de (about 20 minutes). Activity: *"Onlinehandel mit Waren aller Art (Dropshipping)"*.
- [ ] 👤 **Create an ELSTER account** at elster.de. The activation letter takes 1-2 weeks by post, and you need it for the tax form.
- [x] 👤 Shopify webhook → `https://n8n.pivendo.com/webhook/shopify-order-4u6tpie7jfgx`, then **Send test notification**.
- [x] 👤 Delete the test order in n8n (Data tables → orders).
- [x] 👤 Open research product #1 (garden drill auger) in the CJ app: photos, stock, and whether it fits a normal drill.
- [x] 👤 **Wok Wang:** call or message them. Collect the info list below and **agree a price**.

### Day 6 · Sat 3 Oct (public holiday) · 🎯 Shopify settings
- [x] 👤 **Markets:** turn on **US, CA, AU**. Leave **Germany/EU off** for now, since no product has EU stock and you then don't need LUCID.
- [x] 👤 **Shipping rates:** US free · rest of the world $7.99.
- [x] 👤 Cookie banner on · contact page · policies in the footer.
- [ ] 👤 Create **TikTok, Instagram and YouTube** accounts called "pivendo". Use each normally for 10 minutes, without posting yet. *(TikTok @pivendoteam done 10 Oct; Instagram + YouTube still open)*
- [x] 🤖 Update workflow 01 in n8n to the latest version (the research price fix). Paste the prompt at the end of this file into PowerShell Claude.

### Day 7 · Sun 4 Oct · 🎯 Weekly review #1 + pick the product
- [x] 👤 Compare the research from days 5, 6 and 7, then **pick 1 product**. Send `/product SKU testing`.
- [x] 🤖 **Build the Wok Wang website draft** from the info you collected.
- [x] 👤 15-minute review: what's done, what's stuck? Tell Claude.

### Day 8 · Mon 5 Oct · 🎯 Product page
- [x] 👤 Import the product with the **CJ app** → send `/content SKU` → paste the page text.
  - Add a "**drill not included**" note if it's the auger.
  - Offer a **2-pack bundle**.
- [x] 👤 **Connect pivendo.com to Shopify:** Shopify → Settings → Domains → Connect existing domain. Claude helps with the DNS. Don't touch `n8n.pivendo.com`.
- [x] 👤 Start **Shopify Payments verification** (ID and bank account). Add PayPal.

### Day 9 · Tue 6 Oct · 🎯 Videos
- [x] 👤 Make **5 videos** from the 5 scripts in **CapCut** (product photos + text + voice). Or send `/render ID` for the automatic photo video. *(done 11 Oct: 6 videos with Remotion + Higgsfield, in Desktop/Pivendo Videos)*
- [x] ~~👤 Show the **Wok Wang draft** to the owner and collect their changes.~~ *(closed: Wok Wang said no)*

### Day 10 · Wed 7 Oct · 🎯 Launch (if the Gewerbe is confirmed)
- [x] 👤 Check: Gewerbe confirmed ✅, Payments verified ✅, product page ✅ → **remove the store password**. *(shop public since 10 Oct)*
- [x] 👤 Place 1 real test order with your own card, refund it, and check that Telegram alerts you. *(done 10 Oct in Shopify test mode: order #1002, Telegram alert came, order cancelled)*
- [ ] 👤 **Post the first 2-3 videos.**
- ❗ If the Gewerbe isn't confirmed yet, keep the password on and keep making videos. Launch the day it arrives.

### Day 11 · Thu 8 Oct · 🎯 Wok Wang revisions
- [x] ~~🤖 Make the Wok Wang changes.~~ *(closed: Wok Wang said no)*
- [ ] 👤 Post 3 videos.

---

## Week 2 · Rhythm + first money (days 12-18)

### Day 12 · Fri 9 Oct · 🎯 Wok Wang goes live
- [x] ~~🤖 Put the website online (their domain, cheap or free hosting).~~ *(closed: Wok Wang said no)*
- [x] ~~👤 **Send the invoice.** It's your first real money this month.~~ *(closed: Wok Wang said no)*
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
- [x] ~~👤 Wok Wang: ask for a **Google review** and any **referrals**. Other restaurants need websites too.~~ *(closed: Wok Wang said no)*

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

## Wok Wang: info to collect (day 5) · closed, they said no
- [x] Type of business, name, address, phone, **opening hours**
- [x] **Menu with prices** (photo or PDF is fine)
- [x] ~~Logo, plus photos of the food and the restaurant~~ *(closed: Wok Wang said no)*
- [x] Just information, or **online ordering / delivery** links (Lieferando etc.)? *(online pickup ordering, cash payment)*
- [x] Languages (German only, or English too?) *(German, formal "Sie")*
- [x] ~~Domain (do they have one?) and who pays for hosting~~ *(closed: Wok Wang said no)*
- [x] ~~**Price agreed:** e.g. €300-600 one-off + €15-25/month for hosting and changes~~ *(closed: Wok Wang said no)*

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
Please update only the n8n workflow "01 · Product research (daily)" to the newest version from GitHub branch main (file dropshipping/n8n-workflows/01-product-research.json). Download that one file, then run the setup from the SAME folder I used before, so my saved settings and webhook path are kept:
powershell -ExecutionPolicy Bypass -File dropshipping\setup.ps1 -PublicUrl https://n8n.pivendo.com -ReplaceWorkflows
I'll type any keys myself. Afterwards check that all workflows are active and that https://n8n.pivendo.com still works. Follow CLAUDE.md.
```
