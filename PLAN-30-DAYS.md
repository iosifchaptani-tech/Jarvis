# 30-day master plan (days 5-34 · 2-31 October 2026)

One plan for everything: the **Pivendo** store, **legal and admin**, the **Wok Wang** website, **Jarvis**, and **money decisions**.

- Each day has **one main focus 🎯** plus a short list. Do the focus first. If you only manage that, the day still counts.
- 👤 = you · 🤖 = Claude (me or PowerShell Claude) · ⚙️ = the n8n agents (automatic)

## 📍 Status (updated Wed 14 Oct, day 17). New chats start here.

**Done ✅**
- **24/7 posting live (14 Oct 23:25):** Instagram Business + Facebook Page "Pivendo" + Meta app/system user, workflow 08 loaded on the server, auto-posting for YouTube and Instagram switched on (after the owner's ✅).
- **24/7 Part 1 YouTube login (14 Oct 20:10):** Google project `pivendo-posting` (dship00720@gmail.com), app In production, n8n login `YouTube (Pivendo)` tested against the channel PivendoTeam.
- **24/7 step 1 (14 Oct 21:10):** new Telegram workflow 02 (`/queue`, ✅/❌ buttons, `/posts`, to-do lists) and table `social_posts` loaded into n8n on the Oracle server with `load-new-telegram-workflow.cmd`; checked by Claude on the server.
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

- **Roblox game (13 Oct):** Roblox Studio and Blender are connected to PowerShell Claude. The test place is now a small obby, "Escape the Monster" (7 stages, coin shop, monster hall). Blender exports with a "Roblox" FBX preset; a test chest and sword were imported into Studio. Notes: `Desktop\Roblox Game\STATUS.md` and `BLENDER-SETUP.md`. Not published yet, so nothing saves between sessions.
- **Bloodline Dungeon (13 Oct):** first playable of the anime dungeon crawler, built in a new private Roblox place (the obby is backed up and untouched). Lobby with summon stand and bloodline hall, 1 dungeon (3 rooms + boss, 3 enemy types), heroes with race and trait, Normal/Hardcore with heirlooms, skill cards, summons with odds and a visible pity counter, 5 Blender weapons + chest, saving tested on the private place, 2-player test passed. Nothing is public or for sale. Plan and next 3 updates: `Desktop\Roblox Game\GAME-DESIGN.md`; state and open points: `STATUS.md` there. Owner next: play-test it and decide the Hardcore leave rule.
- **Bloodline Dungeon update (14 Oct, evening):** a run is now Gate 1 then straight on to Gate 2 (cards and upgrades carry over), stamina for dodge and Rush, one pick after every room, two shops on the lobby grass (stat upgrades + potions, saved), hotbar 1-5 (weapon, potions), the obby portal (opens after the Gate 2 boss, the owner's "Escape the Monster" inside), a grand Bloodline Hall with the family tree, a new Blender orc, goblin arenas 1.5x bigger, Gate 1 harder (a new player needs 2-3 tries), an owner-only Admin button. Published PRIVATE 15 Oct; saving tested. Notes: `Desktop\Roblox Game\STATUS.md`. ForgeGUI MCP is installed but their login refuses Claude Code (their side).
- **Private pages back on the new account (13 Oct):** Lattelino, Wok Wang, holiday flat, Start-Kit, Galaxy showcase and Pitch Playbook were republished unchanged. The new links are in each project's STATUS.md and in the global notes.
- **Wreath product page (13 Oct, owner's decision "add it to the page now"):** the projection is on the page. Text: "in a dark room it also works as a mini projector … best in a dark room … photos come from the manufacturer". Two ceiling photos (stills from CJ's clip) were added, and the doubled description block was removed. **CJ has still not confirmed the projection**: if the real effect is weaker, expect refunds. Asking CJ support stays worth doing.
- **Videos v2 (13 Oct, free re-render with Remotion, no credits):** 12 files in `Desktop/Pivendo Videos/v2`: each of the 6 videos as `-halloween` (use until 17 Oct) and `-xmas` (from 18 Oct). Fixed: end card 2.5 s with a question box inside the safe area on every video, bigger "AI presenter" note, sound at about −14 to −16 LUFS, no silent ending, standard colour range, and character2 now uses the **real** CJ plug-in clip (the AI hand scene is gone). The source backup is `.playwright-mcp/video/remotion/src-backup-2026-10-13`. Captions and the posting order are in `v2/POSTING-PLAN.txt`.

**Video check (13 Oct, Claude looked at all 6 frame by frame)**
- The 2 character videos show the AI person for 8 s before the product appears; hook4 and hook1 show the product or the effect in the first second. **New posting order: hook4 → hook1 → character2 → hook2 → hook3 → character1.**
- I can't hear the character's voice; only the loudness was measured.
- TikTok @pivendoteam on 13 Oct, 02:20: bio is set, 0 public videos. Instagram `pivendoteam` and YouTube `@PivendoTeam` exist (seen in the owner's browser tabs on 13 Oct).

**Owner decisions on 24/7 posting (13 Oct)** (this one job is allowed although the plan says "no new automations until the first sales") · ⚠️ **Changed on 14 Oct (late):** no more ✅ per post; the bot warns 5 minutes before instead. See "Owner decision 14 Oct (late): 6 videos a day" below.
- **No outside posting service.** Instagram and YouTube are posted from n8n through the official APIs. **TikTok stays manual:** the owner schedules in TikTok Studio (at most 10 days ahead), because TikTok only lets self-made apps post private videos.
- **Nothing goes public without the owner's ✅ in Telegram.**
- Consequences:
  - YouTube can be uploaded early with a publish time, so it also goes out with the PC off.
  - Instagram has no such timer in its API: it posts only while n8n is running. With the PC off it needs a server (Oracle free: card needed, now 2 cores/12 GB; Hetzner about €5.50-6 a month plus VAT). **Server decision still open.**
- **Later on 13 Oct the owner asked for 2 videos a day, times chosen by Claude, with ongoing analysis so it gets better over time.**
  - **Times: 12:30 and 20:30 US Eastern** (US lunch and US evening; 18:30 and 02:30 German time in most weeks). These are a starting point: a time only changes when the numbers show it, as a rule the owner approves.
  - **Daily analysis:** a scheduled task in the Claude desktop app ("Pivendo: daily social stats and next steps", every day about 15:00, only while the PC and the app are on). It reads TikTok Studio, YouTube and Instagram **read-only** in Claude's Chrome window, saves the numbers to `Desktop/Pivendo Videos/stats/stats.csv`, writes `stats/REPORT.md`, and keeps a short "Social stats (latest)" block in this plan.
  - **TikTok (13 Oct, checked in TikTok Studio at 16:15):** the owner chose the music and pressed the buttons himself. **character2 is live** (posted 13 Oct 16:12, not at 02:30), **hook4 is scheduled for 13 Oct 18:30**, **hook2 for 14 Oct 21:30**. The owner's own older post (hook1 v1, 12 Oct) has 83 views. Still to prepare: hook3 and character1 (AI label on). All have "Your brand" on. Both presenter videos were rendered again on 13 Oct with the caption box higher (above the face) and without the burnt-in "AI presenter" note.
  - **YouTube and Instagram (13 Oct):** both are logged in in Claude's Chrome window. They have no sound picker on the PC, so the music is inside the file. Claude's first pick ("Fearless", a pop song) did not fit Christmas; the owner said so. **Now: "Christmas Village" (Aaron Kenny, YouTube Audio Library, no credit needed)**, a soft start and the rise when the lights go off. Files: `Desktop/Pivendo Videos/v2/youtube-instagram`. **Done by the owner on 13 Oct about 18:00, checked by Claude:** YouTube shows 3 scheduled Shorts (hook4 13 Oct 18:30, character2 14 Oct 02:30 with "altered content: yes", hook2 14 Oct 18:30); the Instagram Reel hook4 is shared (2 posts on the profile). Three older YouTube **drafts** with the wrong song are still in the content list: the owner deletes them (Claude may not delete). An older Short from 12 Oct ("Christmas LED Wreath") is already public on YouTube.
  - **Video supply:** 6 different videos last 3 days at 2 a day. After that new ones are needed: free re-edits of the real footage (a limited number before they look alike), more CJ clips, a filmed sample, or AI-character clips (credits; ask before each one).
  - **Still open:** TikTok cannot post by itself without an outside service (owner chose none), so it stays "Claude prepares, owner clicks". Instagram and the analysis need the PC on until there is a server.
- Being built: workflow "08 · Social publisher" (`/queue`, ✅/❌, YouTube upload, Instagram publish, 48 h stats into the feedback table). It needs API logins that only the owner can create (Meta developer app, Google Cloud project); the steps will be in `dropshipping/SOCIAL-SETUP.md`.
- **Repo and tools (13 Oct, cloud Claude):**
  - PR #3 merged. The store work and this plan now live on **main**; every Claude pulls and pushes `main` (CLAUDE.md updated).
  - **Jarvis Repo Map**, a map of every function, section and file in this repo: https://claude.ai/artifact/XcuH8BVkPTEgERqfA5dsVw (private; share it from the page's Share menu). It was published again on 13 Oct from `graphify-out/graph.html`, unchanged (260 points, 441 links). The first page ("Jarvis Galaxy", link ending `…SGXBmq`) was deleted by mistake the same day by desktop Claude; that old link is dead.
  - The knowledge graph behind it is committed in `graphify-out/` (how to use it: CLAUDE.md).

**Money plan to 12 Nov (13 Oct, from two research runs; honest numbers)**
- **What to expect:** new accounts get about 350 views per video, and one sale needs very roughly 70,000 views or more. Posting alone will probably not bring profit in 30 days. A realistic win by 12 Nov: **1-3 real orders** and known numbers (clicks, add-to-cart). Order deadline for Christmas delivery from China: about **25 Nov**.
- **1. Pinterest (free, best chance without money):** people search there for Christmas ideas from October, and a Pin links straight to the product. 👤 Owner creates a Pinterest business account; 🤖 Claude makes the Pin pictures (the video factory makes one per video) and prepares the Pins.
- **2. Store checks before any traffic:** a working link in every bio, the full price with no surprise at checkout, an honest delivery range on the product page, contact and returns easy to find, guest checkout. 🤖 Claude checks and lists what is missing; changes in Shopify only with the owner's OK.
- **3. Small paid test (the most likely way to a first sale; the owner's money, his decision):** about $140-200 over 7-10 days for roughly 200 clicks. Stop rules: 100 clicks without an add-to-cart, or 200 clicks without an order. Claude never pays or starts ads.
- **4. Videos:** 2 a day on TikTok, YouTube and Instagram in the formats that work for Christmas sellers: lights-off reveal, unboxing to switch-on, same room before and after, "any USB port", gift under $25, honest test in a small dark room. Music: soft instrumental Christmas, a quiet second, then the rise at the reveal. From mid-November 3 a day.
- **5. Ask CJ (owner or cloud Claude):** delivery time to the US in November, and who pays the new US import duty on small parcels (the duty-free rule ended in 2026).
- **Video factory: built and checked (13 Oct).** Folder `Boss Jarvis\.playwright-mcp\video\factory` (read its `README.md`). `make-videos.cmd 2` makes the next 2 videos from real footage: a no-music file for TikTok, a music file for YouTube/Instagram ("Christmas Village", rise at the reveal), a Pinterest picture, a captions file and a line in `Pivendo Videos/factory/queue.csv`. 14 recipes in 6 formats; 59 tests pass; the first two (r01 lights-off reveal, r02 unboxing) are in `Desktop/Pivendo Videos/factory/2026-10-13`. Limits: only about 13 seconds of real footage exist, so the videos share clips; more footage (a sample filmed by the owner) would help most. Recipe r07 says "I tested it": post it only after the owner really tested a sample. Videos made before 18 Oct carry the Halloween end card; from 18 Oct use `--xmas`.

- **Meshy for the Roblox game (13 Oct):** `Desktop/Roblox Game/setup-meshy.cmd` is ready and tested with a fake key (the owner double-clicks it and types his Meshy API key there, hidden). Rules are in `Roblox Game/BLENDER-SETUP.md`: only when the owner asks, check credits first, 5,000 triangles or less, every model through Blender. Buying a Meshy plan is the owner's decision.
- **Meshy is connected (14 Oct).** Two models made and cleaned in Blender, FBX files in `Roblox Game/blender/exports/`: `DungeonWallTorch` and `GoblinArena` (a goblin camp floor: 4 stone totems, bone gate, cauldron, green slime; the owner's idea after a Meshy community model). **Neither is in Roblox Studio yet.** The ground fog is not part of the model: build it in Studio with particles and green lights. About 1,000 Meshy credits left. How-to and table: `Roblox Game/BLENDER-SETUP.md`.
- **TikTok inspirations (14 Oct).** The owner saves videos in TikTok Studio > Inspiration > My inspiration. Two so far, both from accounts under 1,000 followers: (1) @noleux, 19 s, 30K views, all AI-made: "Christmas Decor in 1980" (old decor gets thrown out), "Vs...", unboxing, "Christmas Decor in 2026" (the product lights up), "Link in bio". (2) one still info picture with a trending Christmas sound, 61K views, shared a lot because it is useful. **Plan for Pivendo:** copy the structure of (1), but only the opening and the reaction shot are AI; the product stays real footage. Needs about 2 AI clips on Higgsfield (about 10 credits each; 50 free credits are there).
- **Viral playbook (14 Oct):** `Desktop/Pivendo Videos/VIRAL-PLAYBOOK.md`, made read-only from the 10 videos in @pivendoteam's Liked/Favourites: 5 patterns, 5 wreath scripts and 1 drill script. Findings: our CJ wreath clips are other creators' TikToks (their captions were cropped away), so stop making videos from them (taking down the old posts is the owner's call); `pivendo.com` in the TikTok bio is not a clickable link, so say it in words; all 7 posts stopped at about 90 views and are marked DE. **Make first: W1 "Plug it in", W2 "1995 vs 2026", W4 "We tested one first" (or W3)**, all from one sample (ordering it is the owner's decision); ask CJ for projection proof, a written OK for the drill video and the US delivery window. Higgsfield: 1.02 credits, nothing spent.
- **"Then vs now" video: made (14 Oct, owner said "use all 50 credits and make the best video").** Folder `Pivendo Videos/v3-then-vs-now/`: version A (the Pivendo character fights a tangle of old lights and drops it in a box) and version B (he is wrapped up in the lights), each as a no-music file for TikTok and a music file for YouTube/Instagram, plus a captions file. Timeline: "Christmas lights in 1980", "Vs..." (real unboxing and USB plug-in), he looks up, "Christmas lights in 2026" (real ceiling footage), toast with "pivendo.com" and the end card. Only the three presenter shots are AI (Higgsfield, free plan: Hailuo video model); the product is real footage. **AI label must be ON when posting.** The first cut used about 32 of the 50 Higgsfield credits. Render again: `factory/then_vs_now.py` with `remotion/props-then-vs-now.json` (or `-b.json`). What the free plan can and cannot do is in `playbooks/HIGGSFIELD-PLAYBOOK.md`. **14 Oct, later:** the owner liked the idea and wanted the presenter to SPEAK at the start ("no sound looks like cheap AI"). Done: A says "Every... single... year.", B says "Uh... a little help?", in the character's own voice with lip-sync (Higgsfield `seed_audio` + `sync_so`; run `factory/then_vs_now_voice.py` after every re-render). **Prepared in the Chrome window, waiting for the owner's Schedule/Share click:** TikTok A for 15 Oct 02:30 and B for 16 Oct 02:30 (brand label and AI label on; he picks the sound and keeps the original sound audible), YouTube A and B at the same times (altered content: yes), Instagram A at the Share button. About 3 Higgsfield credits are left. **Scheduled (14 Oct, about 02:30):** YouTube A for 15 Oct 02:30 and B for 16 Oct 02:30 (Claude pressed Schedule on the owner's word "schedule those everywhere"); TikTok A by the owner himself for 15 Oct 09:30, TikTok B was being set by the owner (16 Oct 03:30); Instagram A still waits at the Share button (Instagram cannot schedule on the PC). **Owner's wish (14 Oct): the video factory should run 24/7 and tell him on Telegram.** Today it runs on his PC once a day and only prepares. The 24/7 part is built but not switched on: the new workflow 02 (`/queue`, ✅/❌) and workflow 08 (posts to YouTube and Instagram from the server after his ✅, TikTok always by hand) still have to be loaded into n8n ON THE SERVER (adapt `dropshipping/setup.ps1` first: it still targets the PC), then the owner does `dropshipping/SOCIAL-SETUP.md` (about 1 hour, keys typed only into n8n). The owner plans to buy a Higgsfield plan on 14 Oct and wants to try Genjutsu (motion transfer: fine for the character; object swap: not on the product) and Katana (ready-made presets; read its instructions first).
- **Roblox:** the owner wants PowerShell Claude to put `GoblinArena` and `DungeonWallTorch` into Bloodline Dungeon after it finishes its current task (the prompt was given to the owner in chat on 14 Oct).

**Claude learned Higgsfield and Blender (13 Oct, owner's wish)**
- Playbooks for every Claude: `.playwright-mcp/video/playbooks/` on the owner's PC (not in git). Start with `HIGGSFIELD-PLAYBOOK.md` and `BLENDER-PLAYBOOK.md`.
- Higgsfield: all 16 Academy courses (175 lessons with prompts) and the 46 camera-move prompts were saved from the owner's account and distilled into four guides. The owner's paid access ended 13 Oct 23:26; a new plan is his decision.
- Blender 5.2 is on the PC and Claude drives it by script (tested: 3D logo, lights, camera move, 3-second video in 88 s). Use: 3D logo, end cards, titles, backgrounds, transitions. **The product itself stays real footage.**

**n8n runs on the Oracle server since 13 Oct 19:35 (PC can be off)**
- Same n8n 2.41.3, same data, same address: `https://n8n.pivendo.com` answers from the server (Docker container `n8n`, Cloudflare tunnel as the service `cloudflared`). 8 workflows are active as before: 00, 01, 02, 03, 04, 05, 06, 07. The Shopify webhook and the Telegram bot did not have to be changed.
- The owner ran `Desktop/Oracle Server/move-n8n-to-server.cmd` himself (it copies n8n's data and the tunnel key; Claude may not). Claude prepared and tested the server before and checked it after.
- **On the PC n8n is off on purpose:** the Docker container `n8n` is stopped and will not restart, and the Windows service `Cloudflared` is disabled. Docker Desktop is no longer needed for the shop. A backup of n8n's data from before the move is in `C:/Users/<owner>/n8n-backups` (private: it holds the saved keys).
- ⚠️ **`dropshipping/setup.ps1` still assumes n8n on this PC. Do not run it (or `SETUP_DROPSHIPPING.bat`) until it is adapted**: it would start a second n8n. Importing workflow 08 has to be done against the server.
- Still open on the server: a nightly backup of n8n's data, and updates.

**Evening of 13 Oct (checked in the browser by desktop Claude)**
- **Pinterest is live:** the owner made a business account (profile "PivendoTeam"). Board "Christmas Decor & Gift Ideas" with the first Pin, linked to the wreath's product page. Next Pins: one picture per new video is made by the video factory; Claude prepares them, the owner presses Publish.
- **TikTok now:** character2 live (about 50 views), hook4 13 Oct 18:30, the new factory video "Wait for the ceiling" (r01) 14 Oct 02:30, hook2 14 Oct 21:30. **YouTube:** 3 Shorts scheduled. **Instagram:** 2 posts.
- **Owner's decision:** new videos say **"Order early for Christmas"** instead of "US: order by Dec 8" (end card and the posting notes are changed). The date comes back only when CJ confirms delivery times. The videos already posted or scheduled still carry the old line.
- **Daily video task** ("Pivendo: make 2 new videos and prepare the uploads", about 16:40): it makes and checks the videos by itself. It cannot use Chrome while another Claude chat holds it, so the owner writes "prepare the videos" in the main chat and that chat fills TikTok, YouTube and Instagram. Waiting in the queue: r02 (unboxing).

**Social stats (latest)** (14 Oct, 15:05, automatic check, all 3 logged in)
- Total views: TikTok 414 (6 posts, all stop at about 90; most viewers leave at second 1) · YouTube 715 (5 Shorts) · Instagram 251 (3 Reels).
- Best video: **hook4** (product in the first second): YouTube 270 views, 7 likes, +2 subscribers; Instagram 68. On TikTok it got only 4 views. then-vs-now is the best Reel (182) but has the shortest TikTok watch (1.8 s; it opens on the AI presenter).
- **Next:** only 1 TikTok post is still scheduled (15 Oct 09:30): schedule more, and open every new video with the real wreath in the first second. Unposted v2 files use other creators' CJ clips (see `VIRAL-PLAYBOOK.md`): posting them is the owner's call. Details: `Desktop/Pivendo Videos/stats/REPORT.md`.
- **Daily videos (13 Oct, automatic run):** no new videos made: r01 (wait for the ceiling) and r02 (unboxing) were already waiting and passed the picture check. **Not put into the browser:** Claude's Chrome window was in use by another Claude chat, so nothing is prepared on TikTok, YouTube or Instagram yet. Open question for the owner: the end card says "US: order by Dec 8", but this plan says about 25 Nov and CJ has not confirmed delivery times.

- **Gmail (13 Oct):** dship00720@gmail.com is connected to cloud Claude (Gmail connector). Claude reads and drafts; it asks before sending or deleting.
- ⚠️ **Fake-buyer emails:** since the shop went public, about 9 emails like "can I order to Italy/France?", "are you open?", "I need the manager" came from odd addresses. This is a known scam aimed at new shops. Don't reply, don't click their links, and never take payment outside the Shopify checkout. Real buyers just order on pivendo.com.

- **Owner decision 14 Oct (AI videos):** AI may now show the products in a changed or stylized look (for example Higgsfield Genjutsu styles or object swap), as long as every such post has TikTok's "AI-generated" label on and says "AI-made" in the caption. This replaces the 10 Oct rule "AI never generates the wreath". Claude's note: realistic-looking clips should still match the real product (size, brightness, what it projects), because a label does not make a misleading product claim OK under German/EU law and leads to refunds.
- **Owner decision 14 Oct (late): 6 videos a day, made and posted by the agents.**
  1. Every day the agents first show the owner **6 video plans and ask**. Nothing is built without his OK.
  2. After his OK they build **all 6 at once** and show him the finished videos.
  3. The 6 are spread over the next **24 hours** (one every 4 hours).
  4. They are **posted automatically** on YouTube, Instagram and **Facebook** (new). **5 minutes before each post** the bot sends the video in Telegram with a **❌ Stop** button. **No answer = it posts** (owner's choice). This replaces the ✅-per-post rule of 13 Oct.
  5. **TikTok and Pinterest: free route** (owner's choice, no paid posting service). Claude applies for TikTok's and Pinterest's API reviews (TikTok 2-6 weeks, Pinterest 10+ days, both can be refused). Until they pass, the owner posts those two by hand from the bot's to-do lists.
  - Claude's honest notes: 6 truly different videos a day need more footage than the 13 s we have (a filmed sample or AI clips that cost credits; every spend is asked first). Videos sent through the bot must stay under 19 MB.
  - **Built by cloud Claude (14 Oct, night), branch `claude/jolly-carson-nvnner`, NOT merged to main, NOT loaded into n8n yet.** New workflow 09 (the PC sends each finished video with a secret key; the bot shows it in Telegram with ❌ Stop, writes the texts, gives it the next of 6 daily slots, sends TikTok + Pinterest to-dos, and serves a public video link from Telegram so the PC can be off). Workflow 08: runs every 5 min, warns 5-10 min before each post and makes nothing public before that warning; YouTube is uploaded private and made public at the slot (so ❌ Stop keeps it private); Facebook Reels on the Page. 79 tests pass; an independent review found 5 real problems, all fixed and tested. Steps: `dropshipping/SOCIAL-SETUP.md` Part 5 (the PowerShell Claude prompt) and Part 6 (TikTok/Pinterest reviews). The Meta token needs `pages_manage_posts` for Facebook. Not live-tested yet: the list is at the end of SOCIAL-SETUP.md.
- **Owner decision 14 Oct (late), trading:** "no rules, they should just trade and learn from the market." No test gate and no shadow wait: the lab's ideas trade straight on the **DEMO** at small size and are scored on live demo trades (retired after 20 trades with a negative average R). Safety limits stay (Claude's default; the owner did not choose: he can say "remove limits"). Never a real-money account. Prompt for PowerShell Claude given in chat; not done yet.

**Shipping rules for paying orders in CJ**
- US drill: **LuWei Ordinary US** or **YunExpress Ordinary**. Both are DDP.
- Winter set to the US: the **US warehouse** (CJ picks it by itself).
- CA/AU: **CJPacket Ordinary**, but only if the product page shows **no yellow "DDU" box**.
- Wreath: US **LuWei Ordinary US**, CA **CJPacket JYSP Sensitive** (or Ordinary), AU **CJPacket Ordinary** (never Eub, it's DDU).
- ❌ Never choose a method with the "DDU" box.

**▶️ Tomorrow (start here)** (rewritten 14 Oct, 02:40; the owner stopped because his usage limit was close and PowerShell Claude was still working on the Roblox game)

1. **"go 24/7": LIVE (14 Oct 23:25).** YouTube + Instagram auto-posting is switched on: the bot sends each video in Telegram, the owner taps ✅, workflow 08 (`Hj0Kn8shIR5O6aA3`, server) posts at 12:30/20:30 New York time; TikTok stays by hand. Logins in n8n: `YouTube (Pivendo)` (Google project `pivendo-posting`, dship00720@gmail.com, tested: channel PivendoTeam) and `Instagram (Pivendo)` (Meta system user `n8n` in business portfolio "Pivendo" id 1693801832364051, app "Pivendo posting" id 3509575095886269, never-expiring token; tested: Page Pivendo 1340569832476933 + IG @pivendoteam 17841475694267923). 02 Settings: youtube_auto=yes, instagram_auto=yes. **Never live-tested yet: the first real post.** Check it with the first `/queue`. Helper workflows `zz · YouTube login test`, `zz · Instagram login test` (1 and 2) are inactive and safe to delete. Known small bug: `setup.ps1` tries to switch on the archived old 02 (id 56DI…) from `.setup-state.json` (harmless warning). Still open: two old YouTube drafts with the wrong music went public on 14 Oct; and the scheduled "then vs now" posts contain CJ clips that are other creators' TikToks (owner decides whether to set them Private).
2. **Check the scheduled posts.** YouTube A (15 Oct 02:30) and B (16 Oct 02:30) are scheduled. TikTok A is scheduled by the owner for 15 Oct 09:30; TikTok B was still open in his tab (16 Oct 03:30): look in TikTok Studio whether it is scheduled. Instagram A waited at the Share button in a tab: if the tab is gone, prepare it again (`.playwright-mcp/upload/then-vs-now/`, music file) and tell him.
3. **Higgsfield: Lite Monthly bought by the owner (14 Oct, 10 EUR, 250 credits/month, all models incl. Genjutsu/Katana paid with credits).** 3 new TikToks are being made (budget 250 credits; director scripts in `Pivendo Videos/new/SCRIPTS.md`). Old text: The owner wants to buy a plan and try Genjutsu and Katana. Show him the live prices first (`show_plans_and_credits`); buying is his click. Read the Katana preset instructions before any spend. With a paid plan, remake the opening of the "then vs now" video with a model that has its own sound (Kling 3.0 or Seedance), keep the product real footage. Ask before each spend (the "use all 50 credits" OK is used up; about 3 credits left).
4. **Trading test mode.** **New owner decision (14 Oct, late): no test gate, it just trades on the DEMO and learns (see Status).** Built and fixed on the PC, 982 tests pass, guard and gate untouched, still paper, NOT on the server. Next: one more independent review of the fixes, then copy the code to the server (restart of the service is the owner's double-click), one day paper, then demo. With the saved start balance of 1,000 only GBPUSD rules fit (NAS100 needs about 17,400).
5. **Roblox.** PowerShell Claude puts `GoblinArena` and `DungeonWallTorch` into Bloodline Dungeon after its current task (the owner has the prompt). **UI art is ready too (14 Oct):** `Roblox Game/ui-art/pieces/` holds 25 UI pieces (bars, slots, buttons, frames) and 25 icons as see-through PNGs, with `README.txt` saying which number is which; not in the game yet.
6. **Daily videos.** New flow from the owner (14 Oct, late): ask with 6 plans → build all 6 → post over 24 h (see Status). Until workflow 09 is live: when the owner writes "prepare the videos", r02 is waiting; from 18 Oct use `--xmas`.
7. **Worktrees (set up 14 Oct, owner's wish):** every agent has its own copy. All six Desktop projects use git now (only Boss Jarvis is on GitHub). PowerShell Claude starts with `claude.cmd -w powershell`; desktop Claude works in `.claude/worktrees/desktop`; finished work is merged into the Desktop folder. Rules: the owner's global `~/.claude/CLAUDE.md`, section "Worktrees".

**Older start notes (13 Oct), kept for reference:**

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
- 🤖 **Trading autopilot (13 Oct): built, reviewed, running in PAPER mode since 16:58** (pretend: no order is sent). Folder `Desktop\Trading Agents\autopilot` (owner guide: `README.md` there). The demo login works (TradeLocker demo, 1,000 USD; the owner set a new trading password). Tests: 250 autopilot + 162 trader + 17 guard/gate pass; the four given files are unchanged. An independent review found six weak points (loss stop could reset after an unreadable file, waiting orders survived the daily pause, late setups, shadow stage could be skipped by moving a file, the old bot traded without the guard, hand-made trades were not counted); all six were fixed and tested, a second check of the fixes is running. **No rule is active, so it trades nothing** until a rule passes the test gate and the shadow stage; the lab runs every night at 23:15.
  - **Telegram is connected (13 Oct 17:32):** the owner made the bot and saved it; the autopilot was restarted and answers his commands (`/status`, `/help`). **The trading bot runs on the Oracle server since 13 Oct 19:22 (PC can be off).** Server `trading-bot` (Frankfurt, Ubuntu 24.04, 1 core, 6 GB), address 130.61.140.11, project in `/home/ubuntu/trading`, service `trading-autopilot` (starts at boot, restarts 60 s after a crash). All 250 autopilot tests pass there; still paper mode, same 14-day run, Telegram works from the server. The owner did the Oracle network clicks and ran `autopilot\move-to-server.cmd` himself (it copied his two login files; Claude may not move those or install services). **On the PC the bot is off on purpose:** `start-autopilot.cmd` refuses while `autopilot\state\moved-to-server.flag` exists, and the Windows autostart task stays off. To look at the server: `ssh -i ~/.ssh/oracle_trading ubuntu@130.61.140.11`, then `systemctl status trading-autopilot` and `tail ~/trading/autopilot/logs/autopilot.log` (times there are UTC). Code changes are made on the PC and copied over; the address changes only if the server is stopped and started in Oracle. Not on the server: the optional AI ideas for the lab (no Claude CLI there); the lab's fixed idea list still runs at 23:15. n8n is still on the PC.
  - **Demo mode (orders on the demo account) stays off** until a clean paper run through both sessions and the second review are through. `trader\start-demo.cmd` no longer trades on its own.
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
- **Owner decision 13 Oct: autopilot.** Run 24/7 on the demo. The lab may invent and add its own rules (no ✅ needed, owner can `/reject`). Goal: demo above its start balance 14 days after the start. Cloud Claude wrote the test gate, the safety limits (17 tests) and the build plan: `trading/AUTOPILOT.md` on branch `claude/wizardly-lamport-m2e3m9`. **Built 13 Oct and running in paper mode:** see the 🤖 Trading autopilot entry above for the owner's next steps.
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
- [ ] 👤 Create **TikTok, Instagram and YouTube** accounts called "pivendo". Use each normally for 10 minutes, without posting yet. *(TikTok @pivendoteam done 10 Oct; Instagram @pivendoteam done 12 Oct, seen in Gmail; YouTube still open)*
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
