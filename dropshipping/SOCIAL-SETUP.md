# Social posting setup: YouTube and Instagram

This is your checklist to let the bot post on **YouTube** and **Instagram** by itself.

- **You don't need this to start.** Without it, `/queue` already works: after your ✅ you get a to-do list for every platform and post by hand.
- **TikTok always stays by hand.** TikTok does not allow self-made posting apps. You schedule it in TikTok Studio from the bot's to-do list.
- **Nothing is ever posted without your ✅ in Telegram.**
- **Time:** about 1 hour, once. You can do YouTube today and Instagram another day.
- **Keys and tokens:** you type them only into n8n. Never send them to anyone, not to Claude either. No screenshots of them.

Google and Meta move their buttons now and then. If a name here is not on your screen, send Claude a screenshot of the page (without keys) and ask.

---

## Step 0: Load the new workflow 02 first (today, no login needed)

`/queue`, the ✅/❌ buttons, `/posts` and the to-do lists are part of the new workflow **02 · Telegram commands**. The one in n8n is still the old one. Load the new one first. You do not need a YouTube or Instagram login for this: the bot then works in **to-do mode** (it writes the texts, you tap ✅, and you post by hand from its lists).

Paste this into PowerShell Claude:

> Please run `powershell -ExecutionPolicy Bypass -File .\dropshipping\setup.ps1 -SkipInstall -ReplaceWorkflows -OnlyWorkflows 02` and tell me what it prints. I type my n8n password myself when it asks.

- It creates the `social_posts` table, replaces workflow 02 and leaves every other workflow alone. It says that 08 is not imported yet: that is right, 08 comes in Part 3.
- The swap is safe: the new workflow 02 is loaded switched off, the old one is switched off, the new one is switched on, and only then is the old one archived (archived = put away, not deleted). If the new one does not start, the old one is switched back on and the script says so in yellow.
- **Check:** send `/posts` to your bot. It answers *"No posts yet"*.

**Loading a workflow again resets its ⚙️ Settings to the start values.** The script fills in only the Telegram chat ID (and, in 02, the support email and signature). Everything else you changed goes back to the start value, so write down your values before you load a workflow again, and set them again afterwards: n8n → **Workflows** → the workflow → double-click **⚙️ Settings** → change the value → close the node → **Save** (and **Publish** if n8n shows that button).

| Workflow | Settings that go back to the start value | Set them again |
|---|---|---|
| **02** | `youtube_auto` and `instagram_auto` (back to `no`: the bot posts nothing by itself until you switch them to `yes`), `post_times`, `post_timezone`, `time_zone`, `min_lead_hours`, `shop_url`, `voice`, `cta_text` | Part 3, step 3, and the table "Settings you can change" |
| **08** | `ig_user_id` (back to the `PASTE_…` text, so Instagram posts fail until you paste the number again), `ig_token_expires`, `max_late_hours`, `stuck_minutes`, `stats_after_hours`, `time_zone` | Part 3, step 2 (the same number as before; if you lost it, run the evening check again and Telegram tells you) |

---

## Part 1: YouTube (about 20 minutes)

You create a small "app" at Google that is allowed to upload to your own channel. It costs nothing.

1. Open **console.cloud.google.com** and sign in with the Google account that owns the channel **@PivendoTeam**.
2. At the top, click the project name → **New project** → Project name: `Pivendo posting` → **Create**. Then pick that project at the top.
3. Click ☰ (top left) → **APIs & Services → Library**. Search `YouTube Data API v3`, open it, click **Enable**.
4. Click ☰ → **APIs & Services → OAuth consent screen** → **Get started**:
   - App name: `Pivendo posting`
   - User support email: your own address → **Next**
   - Audience: **External** → **Next**
   - Contact information: your own address → **Next**
   - Tick the box → **Continue** → **Create**
5. In the left menu, click **Audience**. Under "Publishing status" click **Publish app** → **Confirm**. It must now say **In production**.
   - This step is important. In "Testing", Google ends the login after 7 days and the bot stops uploading.
   - You do **not** need to send the app to Google for verification. It only posts to your own channel.
6. Open n8n (**http://localhost:5678**) → **Credentials → Add credential** → search `YouTube OAuth2 API` → **Continue**.
   - Click the name at the top and change it to exactly `YouTube (Pivendo)`.
   - Copy the **OAuth Redirect URL** that n8n shows. Leave this window open.
7. Back at Google, in the left menu: **Clients → Create client**:
   - Application type: **Web application**
   - Name: `n8n`
   - **Authorized redirect URIs → Add URI** → paste the URL from step 6
   - **Create**. A window shows the **Client ID** and the **Client secret**.
8. In the n8n window: paste the **Client ID** and the **Client Secret** → click **Sign in with Google**:
   - choose your Google account, then the channel **PivendoTeam**
   - Google says *"Google hasn't verified this app"*. That is normal, it is your own app. Click **Advanced → Go to Pivendo posting (unsafe)**
   - tick all boxes → **Continue**
   - n8n says **Account connected** → **Save**

---

## Part 2: Instagram (about 40 minutes)

Instagram only lets apps post through Meta (Facebook). There are two ways to get the key. We use the one with a **system user**:

> A system-user token **never runs out**, so there is no 60-day renewal that can be forgotten or fail quietly while the PC is off, and n8n has no built-in way to save a renewed token by itself. The price is a longer one-time setup (a Facebook Page and a business portfolio), but that fails loudly today instead of silently in two months.

You need a personal Facebook account for this. It is only the owner of the Page; nothing is posted on it.

1. **Make the Instagram account professional.** In the Instagram app: your profile → ☰ → **Account type and tools → Switch to professional account** → **Business** → pick a category (for example *Shopping & retail*) → **Done**. The account must be public.
2. **Create a Facebook Page and link it.**
   - Open **facebook.com/pages/create** → Page name: `Pivendo` → pick a category → **Create Page**. The Page can stay empty.
   - On the Page: **Settings → Linked accounts → Instagram → Connect account** → log in as **pivendoteam**.
3. **Create a business portfolio.** Open **business.facebook.com** → **Create a business portfolio** → name: `Pivendo`. Then click ⚙️ **Settings**:
   - **Accounts → Pages → Add → Claim an existing Facebook Page** → `Pivendo`
   - **Accounts → Instagram accounts → Add** → log in as **pivendoteam**
4. **Create the app.** Open **developers.facebook.com** → **My Apps → Create app**:
   - App name: `Pivendo posting`
   - Use case: **Manage messaging & content on Instagram**
   - Business portfolio: **Pivendo** → **Create app**
   - In the app: **Use cases → Customize → API setup with Facebook login**
   - You do not need "App Review": the app only posts to your own account.
5. **Create the system user.** Back in **business.facebook.com** → ⚙️ **Settings → Users → System users → Add**:
   - Name: `n8n`, role: **Admin** → **Create system user**
   - Select it → **Assign assets**:
     - **Apps** → `Pivendo posting` → **Manage app**
     - **Pages** → `Pivendo` → switch on **Content**
     - **Instagram accounts** → `pivendoteam` → switch on **Content** and **Insights**
   - **Save**
6. **Create the token.** Still on the system user, click **Generate token**:
   - App: `Pivendo posting`
   - Token expiration: **Never**
   - Tick these permissions: `instagram_basic`, `instagram_content_publish`, `instagram_manage_insights`, `pages_show_list`, `pages_read_engagement`, `business_management`
   - **Generate token** → copy it. It is shown only once.
7. **Put it into n8n.** n8n → **Credentials → Add credential** → search `Facebook Graph API` → **Continue**:
   - change the name at the top to exactly `Instagram (Pivendo)`
   - paste the token into **Access Token** → **Save**
   - it should say **Connection tested successfully**

If Meta only offers you a token for 60 days, take it. In Part 3 you then write its end date into `ig_token_expires`, and the bot warns you every evening, starting 14 days before.

---

## Part 3: Switch it on

**1. Let Claude load workflow 08.** Paste this into PowerShell Claude:

> The logins "YouTube (Pivendo)" and "Instagram (Pivendo)" are ready in n8n. Please run `powershell -ExecutionPolicy Bypass -File .\dropshipping\setup.ps1 -SkipInstall` and tell me what it prints. I type my n8n password myself when it asks.

This adds workflow **08 · Social publisher**, attaches the two logins to it and switches it on. It does nothing for a post until you switch a platform to `yes` in step 3. Workflow 02 is already new from Step 0 and is not touched, so the Settings you set there stay.

Did you skip Step 0? Then use `-SkipInstall -ReplaceWorkflows -OnlyWorkflows '02,08'` instead, and set the Settings of 02 again afterwards (see the table in Step 0).

**2. Tell the bot your Instagram account ID.**
- n8n → **Workflows → 08 · Social publisher**.
- Move the mouse over the node **Every evening 21:00** and click **Execute workflow**.
- Within a minute Telegram says: *"🆔 Your Instagram account ID is 1784…"*.
- Double-click **⚙️ Settings**, replace the text in `ig_user_id` with that number, close the node, click **Save** (and **Publish** if n8n shows that button).
- No message? Then the Page or the Instagram account is not assigned to the system user: repeat Part 2, step 5.

**3. Hand over the posting.** n8n → **Workflows → 02 · Telegram commands** → double-click **⚙️ Settings**:
- `youtube_auto` → `yes`
- `instagram_auto` → `yes`
- **Save** (and **Publish**).

You can also switch on only one of them. The other one stays a to-do list.

---

## Part 4: The first test post

Use a video you want to post anyway. This one post answers the questions nobody can check without your logins.

1. **Choose the music first and put it inside the video.** The bot cannot add a sound to a YouTube or Instagram post, so the music must already be in the file. (For TikTok you pick the sound in TikTok Studio: **Sounds**, then **Save**.) The bot reminds you with *"Choose the music first."* in every approval message and every to-do list. The agents never pick or name a song. Then put the video online: Shopify admin → **Content → Files → Upload files** → click the link icon to copy the link. It must end with `.mp4`.
2. Send the bot: `/queue LINK SKU ai what the video shows` (leave out `ai` if there is no AI in it). Read the texts, tap **✅ Approve**.
3. **Within 10 minutes:** *"📺 YouTube: P… is uploaded"*. Open the link in that message (YouTube Studio) and look at **Visibility**:
   - **Scheduled** = all good. ✅
   - **Private (locked)** = Google locks uploads from new, unchecked apps. Set `youtube_auto` back to `no` (you get to-do lists again, nothing else changes) and tell Claude: *"YouTube locked my API upload."*
   - For an AI video, **Altered content** must say **Yes**.
4. **At the slot time:** *"📸 Instagram: P… is live"*. Open the link in a **private browser window** (not logged in):
   - You see the Reel = all good. ✅ For an AI video, check in the app that it shows the AI label.
   - You only see it when logged in = tell Claude: *"My Instagram test post is only visible to me."*
5. **After the slot time:** open `youtube.com/@PivendoTeam/shorts` in a private window. The Short is there. ✅
6. **Two evenings later at 21:00:** *"📈 Video numbers after 48 hours"*. ✅

---

## Settings you can change

n8n → the workflow → double-click **⚙️ Settings** → change → **Save** (and **Publish**).

**Workflow 02 · Telegram commands**

| Setting | Start value | Meaning |
|---|---|---|
| `post_times` | `12:30,20:30` | the posting slots, one video per slot |
| `post_timezone` | `America/New_York` | the clock those times belong to: your buyers' lunch and evening |
| `time_zone` | `Europe/Berlin` | your own clock. Every message shows times in it |
| `min_lead_hours` | `2` | a video is never slotted less than 2 hours ahead |
| `youtube_auto` | `no` | `yes` = the bot uploads to YouTube. `no` = you get a to-do list |
| `instagram_auto` | `no` | `yes` = the bot posts the Reel. `no` = you get a to-do list |
| `shop_url` | `pivendo.com` | added to every caption that does not name it |

12:30 and 20:30 in New York are 18:30 and 02:30 in Germany. For one week in autumn (25 Oct to 1 Nov 2026) and two weeks in spring it is 17:30 and 01:30, because the US and Europe change their clocks on different days. The bot handles that and always tells you the German time.

**Workflow 08 · Social publisher**

| Setting | Start value | Meaning |
|---|---|---|
| `ig_user_id` | `PASTE_YOUR_INSTAGRAM_ACCOUNT_ID` | your Instagram account ID, a long number (Part 3, step 2) |
| `ig_token_expires` | `never` | only if your Meta token has an end date: write it as `2026-12-31` |
| `max_late_hours` | `12` | a video that is more than 12 hours late is not posted. You get a message instead |
| `stuck_minutes` | `30` | after this time a post that did not finish is reported to you |
| `stats_after_hours` | `48` | when the bot reads the views |
| `graph_api` | `https://graph.facebook.com/v25.0` | Meta's address. Leave it |
| `time_zone` | `Europe/Berlin` | your own clock, for the messages |

---

## If something goes wrong

| What you see | Fix |
|---|---|
| Google: *"redirect_uri_mismatch"* when signing in | The URL in Google (Part 1, step 7) is not exactly the one n8n shows. Copy it again. If Google refuses the URL: left menu **Branding → Authorized domains** → add the part after `https://`. |
| n8n asks you to sign in to Google again after a PC restart | The n8n address changed. Copy the new **OAuth Redirect URL** from the credential, add it in Google (**Clients → n8n → Add URI**), sign in again. |
| *"🔑 YouTube did not answer the daily check"* two days in a row | n8n → **Credentials → YouTube (Pivendo) → Sign in with Google** again. Check that Part 1, step 5 says **In production**. |
| *"🔑 Instagram did not answer…"* with "token" or "expired" in it | Make a new token (Part 2, step 6) and paste it into **Instagram (Pivendo)**. |
| *"❌ Instagram: … could not use the video"* | The link must open in a private window without logging in. The video must be an upright MP4 (9:16), 3 seconds to 3 minutes long. |
| *"❌ YouTube: the upload of P… failed"* (for example *"exceeded your quota"*) | **Look in YouTube Studio → Content first:** a failed upload can still have left the video there. If it is there, do not retry (it is already scheduled; or delete it, then retry). If it is not there, wait until the next day when it says *quota*, then `/retry P…`. |
| *"⏰ … was NOT posted"* | The PC or n8n was off at the slot time. `/retry P…` posts it now. |
| The ✅ button does nothing | Send `/approve P…` instead and tell Claude. |
| You approved by mistake | `/reject P…`. The bot stops everything that has not happened yet, but it **cannot take back a video that YouTube already has** (it is uploaded within 10 minutes of your ✅). The message then gives the video link and the clicks: YouTube Studio → **Content** → move the mouse over the video → ⋮ → **Delete forever** → tick the box → **Delete forever**. The bot never deletes anything itself. |
| *"🚫 Instagram: P… was not posted: you rejected it"* | Good: you rejected it while Instagram was still preparing the video, and the bot stopped before posting. Nothing is on Instagram. |

---

## For Claude: how it works and what is not live-tested

- **Files:** `tools/build_workflows.py` (workflow 02: `/queue`, Approve/Reject, to-dos; workflow 08: publisher, stats), `templates/social_posts.csv`, tests in `tools/test_code_nodes.js`.
- **One Telegram trigger.** Buttons are inline callback buttons. Workflow 02's trigger listens to `message` and `callback_query`; "Parse command" turns a tap (`approve:P…`) into the same route as the typed `/approve P…`. The Coach (05) is different: its buttons are n8n "send and wait" links.
- **`social_posts` is append-only.** Every change is a new row holding only the changed columns; a post's state is all its rows merged (`foldPosts`). `post_at` is UTC, `slot` is the local slot time in `post_timezone`.
- **No double posts.** Workflow 08 only picks a platform while it is `queued`, and saves `uploading` / `publishing` before any API call. A crash leaves the mark; after `stuck_minutes` the owner is told, and only `/retry` (the owner) puts it back to `queued`. "Save marks" has no error setting on purpose (a run that cannot save its marks stops), every node that writes to YouTube or Instagram is reachable only through it, and every Telegram node in 08 continues on error, so a failed alert never blocks a posting branch. These three points are tested.
- **Reject races.** `/reject` only stops what has not started. Right before the Instagram publish call, "Reload post (Instagram)" + "Check post again (Instagram)" read the post again and publish only if it is still `approved` and still `publishing` (up to 10 minutes can lie between "Plan this run" and the publish call); a rejected post ends as `ig_status = cancelled`. A YouTube video is uploaded within 10 minutes of the approval and then waits for its slot, so Reject cannot take it back: its reply gives the Studio link and the clicks. There is no call that deletes a video or a Reel, on purpose (a test asserts it).
- **Failed uploads.** n8n sends a YouTube file in chunks, so an upload reported as failed can still have left a video. Only a failed download (`none: true`) is certain to leave nothing. `/retry` warns about a second copy for `stuck` and for a failed YouTube upload.
- **Music.** The owner chooses it himself and is reminded in the approval request, the approve message and the TikTok, YouTube and Instagram to-dos (`musicLine` in `JS_POSTS`). YouTube and Instagram APIs cannot add a sound, so for the platforms the bot posts the music must be inside the file. The Content and Post agents are told never to name or pick a song, and "Check post texts" refuses a text that credits one.
- **Table writes.** `social_posts` is append-only, so workflow 08 never rewrites it: an idle run writes nothing, and a busy run writes one small row per change.
- **Learning.** The evening run writes `feedback` rows in the `/video` shape (`ref` = `P…-yt`, `P…-ig`) plus one `content` row per video, because the Coach joins feedback with `content`. The Coach's prompt shows the content `format`, not the feedback `note`, so the format carries "views only" and "slot 12:30". Workflow 05 is unchanged.
- **Updating the live n8n:** `setup.ps1 -SkipInstall -ReplaceWorkflows -OnlyWorkflows 02,08` replaces only those two. The numbers also work quoted (`'02,08'`) or as `2,8`: PowerShell 5.1 turns an unquoted `02,08` into the numbers 2 and 8, and the script splits on commas and spaces and pads each number back to two digits. A number that matches no workflow file, a word that is not a number, or `-OnlyWorkflows` without `-ReplaceWorkflows` stops the script with a message before anything is touched.
- **Safe swap.** A replaced workflow is imported switched off, the old copy is switched off, the new copy is switched on, and only then is the old copy archived. If the new copy cannot be imported or switched on, the old copy stays (or is switched back on), the failed copy is archived and the script lists it under "Not replaced". Two copies are never on together: two Telegram triggers would fight over the bot's single webhook. The old and the new 02 even share one webhook address, and switching a copy off makes n8n remove that webhook at Telegram, so the old copy is switched off once, before the new one is switched on, and a copy that is already off is only archived. The script switches on every workflow it imports; there is no import-as-inactive option.
- **Settings are rebuilt on every re-import.** Workflow 02: the chat ID, support email and signature are filled in again, **everything else goes back to the start value**: `youtube_auto`, `instagram_auto`, `post_times`, `post_timezone`, `time_zone`, `min_lead_hours`, `shop_url`, `voice`, `cta_text`. Workflow 08: only the chat ID is filled in, so `ig_user_id` and the other Settings go back to the start values. Ask the owner for his values before a re-import and set them again afterwards (Step 0). Without `-OnlyWorkflows`, every workflow's Settings would be reset, including the money settings in 01 and 07. Workflow 08 is only imported once both credentials exist.

**Checked against the official docs (Oct 2026), not against live accounts:**

| Assumption | How Part 4 settles it |
|---|---|
| A new, unverified Google project can publish (Google's own pages disagree) | Step 3: "Scheduled" or "Private (locked)" |
| The built-in YouTube node (n8n 2.41.3) uploads private with `publishAt`; `videos.update` with `part=status` then sets `containsSyntheticMedia` | Step 3: Visibility and "Altered content" |
| A system-user token can create and publish a Reel for the own account without App Review, and the Reel is public while the Meta app is in development mode | Step 4, private window |
| `is_ai_generated=true` on the container shows the AI label | Step 4, in the app |
| `GET /me/accounts` returns the linked Instagram account for a system user | Part 3, step 2 |
| Meta and YouTube can fetch a video from a Shopify Files link | Steps 3 and 4 |
| Reel insights accept `views,reach,likes,comments,shares,saved` | Step 6 |
| Telegram delivers button taps to workflow 02 after its trigger is re-registered with `callback_query` | Step 2 |
| The workflows import and activate in n8n 2.41.3 (node parameters were checked against the node source in the n8n image, but nothing was imported or run) | Part 3, step 1 |
| The safe swap in `setup.ps1` works against n8n's REST API (deactivate the old workflow, activate the new one, archive the old one) and the bot's single Telegram webhook moves to the new workflow 02; its error handling was only tested with a fake n8n | Step 0: the script prints "replaced" and then "Telegram is connected to n8n", and `/posts` answers |
| A Reload of the post right before "Instagram: publish" sees a `/reject` from the last 10 minutes (the Data Table is read live, not cached) | Not covered by Part 4; to check, `/reject` a test post while its Reel is being prepared |
