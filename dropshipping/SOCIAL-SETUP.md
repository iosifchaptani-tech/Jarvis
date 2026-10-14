# Social posting setup: YouTube, Instagram and Facebook

This is your checklist to let the bot post on **YouTube**, **Instagram** and **Facebook** by itself.

**How it works (your plan, 14 Oct):** every day the agents on the PC show you 6 video plans and ask. After your OK they build all 6 and send them to the bot (workflow 09). The bot shows you each video in Telegram with a **❌ Stop** button and gives the 6 the next 6 slots (one every 4 hours). **About 10 minutes before each post you get the video again with ❌ Stop. No answer = it goes out** (workflow 08).

- **You don't need this to start.** Without the logins, everything still works as to-do lists: you post by hand.
- **TikTok and Pinterest stay by hand for now.** Both only allow posting apps after their own review (TikTok 2-6 weeks, Pinterest 10+ days, both can say no). Part 6 is the plan to apply. Until then you schedule them from the bot's to-do lists.
- **Nothing goes public without the 10-minute warning with ❌ Stop.** A video you send yourself with `/queue` also needs your ✅ first.
- **Time:** about 1 hour, once. You can do YouTube today and Instagram + Facebook another day.
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

## Part 2: Instagram and Facebook (about 40 minutes)

Instagram only lets apps post through Meta (Facebook). The same key also posts the Reels on your Facebook Page. There are two ways to get the key. We use the one with a **system user**:

> A system-user token **never runs out**, so there is no 60-day renewal that can be forgotten or fail quietly while the PC is off, and n8n has no built-in way to save a renewed token by itself. The price is a longer one-time setup (a Facebook Page and a business portfolio), but that fails loudly today instead of silently in two months.

You need a personal Facebook account for this. It is only the owner of the Page; nothing is posted on that personal account (the bot posts on the Page **Pivendo**).

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
   - Tick these permissions: `instagram_basic`, `instagram_content_publish`, `instagram_manage_insights`, `pages_show_list`, `pages_read_engagement`, **`pages_manage_posts`** (for the Facebook Reels), `business_management`
   - Already made a token without `pages_manage_posts`? Make a new one with it and paste it into the same n8n login (step 7). The old one keeps working for Instagram, but Facebook would say "no permission".
   - **Generate token** → copy it. It is shown only once.
7. **Put it into n8n.** n8n → **Credentials → Add credential** → search `Facebook Graph API` → **Continue**:
   - change the name at the top to exactly `Instagram (Pivendo)`
   - paste the token into **Access Token** → **Save**
   - it should say **Connection tested successfully**

If Meta only offers you a token for 60 days, take it. In Part 3 you then write its end date into `ig_token_expires`, and the bot warns you every evening, starting 14 days before.

---

## Part 3: Switch it on

**1. Let Claude load workflows 08 and 09.** n8n runs on the Oracle server, so PowerShell Claude does this against the server (the PC copy of `setup.ps1` still targets the PC). It also gives the table `social_posts` its 4 new columns (`fb_status`, `fb_video_id`, `warned`, `tg_file_id`) and makes the login **Video intake (Pivendo)**: a random key that only the PC and n8n know, so nobody else can send videos to your bot. The exact prompt is in Part 5.

Workflow 08 does nothing for a post until you switch a platform to `yes` in step 3.

**2. Tell the bot your Instagram account ID and your Facebook Page ID.**
- n8n → **Workflows → 08 · Social publisher**.
- Move the mouse over the node **Every evening 21:00** and click **Execute workflow**.
- Within a minute Telegram says: *"🆔 Your Facebook Page ID is 134… (Pivendo)"* and *"🆔 Your Instagram account ID is 1784…"*.
- Double-click **⚙️ Settings**, put the numbers into `fb_page_id` and `ig_user_id`, close the node, click **Save** (and **Publish** if n8n shows that button).
- No message? Then the Page or the Instagram account is not assigned to the system user: repeat Part 2, step 5.

**3. Hand over the posting.** Do this in **both** workflows: **09 · Video intake** (the 6 videos from the PC) and **02 · Telegram commands** (videos you send with `/queue`). n8n → **Workflows** → the workflow → double-click **⚙️ Settings**:
- `youtube_auto` → `yes`
- `instagram_auto` → `yes`
- `facebook_auto` → `yes`
- **Save** (and **Publish**).

You can also switch on only some of them. YouTube and Instagram then stay a to-do list; Facebook is simply left out.

---

## Part 4: The first test post

Use a video you want to post anyway. This one post answers the questions nobody can check without your logins.

1. **Choose the music first and put it inside the video.** The bot cannot add a sound to a YouTube or Instagram post, so the music must already be in the file. (For TikTok you pick the sound in TikTok Studio: **Sounds**, then **Save**.) The bot reminds you with *"Choose the music first."* in every approval message and every to-do list. The agents never pick or name a song. Then put the video online: Shopify admin → **Content → Files → Upload files** → click the link icon to copy the link. It must end with `.mp4`.
2. Send the bot: `/queue LINK SKU ai what the video shows` (leave out `ai` if there is no AI in it). Read the texts, tap **✅ Approve**.
3. **Within 10 minutes:** *"📺 YouTube: P… is uploaded as a private video"*. Open the link in that message (YouTube Studio) and look at **Visibility**:
   - **Private** = all good so far. ✅ The bot makes it public at the slot.
   - **Private (locked)** = Google locks uploads from new, unchecked apps. Set `youtube_auto` back to `no` (you get to-do lists again, nothing else changes) and tell Claude: *"YouTube locked my API upload."*
   - For an AI video, **Altered content** must say **Yes**.
4. **About 10 minutes before the slot:** *"⏰ In about 10 minutes P… goes out on …"* with the video and **❌ Stop**. Don't tap anything. ✅
5. **At the slot time:** *"📺 YouTube: P… is public now"*, *"📸 Instagram: P… is live"* and *"📘 Facebook: P… is posted on your Page"*. Open each link in a **private browser window** (not logged in):
   - You see it = all good. ✅ For an AI video, check in the Instagram app that the Reel shows the AI label.
   - You only see it when logged in = tell Claude which one: *"My test post is only visible to me on …"*
6. **Two evenings later at 21:00:** *"📈 Video numbers after 48 hours"* (YouTube and Instagram; Facebook numbers are not read yet). ✅

---

## Part 5: The PC sends the 6 videos (PowerShell Claude does this)

This connects the video factory on the PC to the bot. Paste this into PowerShell Claude (the same prompt cloud Claude gave you in chat):

> Owner's plan (14 Oct): every day the agents make 6 videos; they ask me first, then build all 6, and the bot posts them over 24 hours with a 10-minute warning. Cloud Claude built workflows 08 and 09 for it (repo Jarvis, branch `main`; if it is not merged yet, branch `claude/jolly-carson-nvnner`). Read `dropshipping/SOCIAL-SETUP.md` parts 3 and 5 and `PLAN-30-DAYS.md` first. Please:
> 1. **Server n8n (Oracle):** first add the columns `fb_status`, `fb_video_id`, `warned`, `tg_file_id` (text) to the table `social_posts`, **before** loading any new workflow (until they exist, every post action of the new 02 and 08 fails, even ❌ Stop). If the old workflow 08 was ever loaded, look for posts with `yt_status` = `scheduled` and tell me: YouTube makes those public by itself, ❌ Stop cannot hold them. Make the n8n login **Video intake (Pivendo)** (type Header Auth, name `X-Pivendo-Key`, value: a random 40-character key you generate). Save the same key in `%USERPROFILE%\.pivendo\video-intake.key`. Never print it, never put it in git or chat.
> 2. Load **09 · Video intake** into the server n8n: attach "Video intake (Pivendo)" to the node "Video in", the Telegram and Claude logins to their nodes, fill `telegram_chat_id`, switch it on. Load the new **02** with the safe swap (write down its Settings first and set them again after). Load the new **08** only once the login "Instagram (Pivendo)" exists; until then leave 08 out. Keep `youtube_auto`, `instagram_auto`, `facebook_auto` on `no` in 02 and 09 until I say the logins are done.
> 3. **Test** with one real video (the autos are still `no`, so nothing is posted by itself): send it to `https://n8n.pivendo.com/webhook/pivendo-video-in` (POST, form fields `video` = the MP4, `sku`, `ai` = yes/no, `shows`, `name`, header `X-Pivendo-Key` from the key file). Show me the answer. I check Telegram, open the video link from the to-do in a private browser window (it must play), then tap ❌ Stop.
> 4. **The daily video job** (change the scheduled task "Pivendo: make 2 new videos and prepare the uploads" in the Claude app, or make a new one, every day at 14:00 while the PC is on):
>    - First make **6 video plans** and **ask me** in the chat, and send me a short Telegram note through the same address (JSON `{"message": "6 video plans are ready: open the Claude app"}`). Each plan: product + SKU, what is seen in the **first second** (the product or the effect, never the AI person first), the recipe, which footage, AI yes/no, and the **Higgsfield credits** it costs. Build nothing and spend nothing before my OK.
>    - After my OK, build all 6 with the video factory: a music version (music inside, 9:16 MP4, 3-60 s, **under 19 MB**), a no-music TikTok version and a Pinterest picture. Check every video frame by frame as before. Never use other creators' CJ clips (`VIRAL-PLAYBOOK.md`), use `--xmas` from 18 Oct, AI label and "AI-made" for AI videos, no claims we can't prove.
>    - Send the 6 music versions to the bot **one at a time**, waiting for each answer. If an answer does not come (timeout), **do not send that video again**: wait 2 minutes, go on with the next, and tell me to check `/posts` in Telegram.
>    - Then tell me the 6 times and where the TikTok files are. Never post, schedule or upload anything on TikTok, Pinterest, YouTube, Instagram or Facebook yourself.
> 5. Update `PLAN-30-DAYS.md` and push only that file to `main`.

**Why a key:** the address `…/pivendo-video-in` is on the internet. Without the key, anybody could send videos to your bot.

---

## Part 6: TikTok and Pinterest (later, the free route)

Both let a posting app post publicly only after their own review. Until then you post from the bot's to-do lists. The steps, in order:

**TikTok** (review 2-6 weeks, can be refused)
1. 👤 You: open **developers.tiktok.com**, log in with the TikTok account **@pivendoteam**, accept the terms.
2. 👤 You: **Manage apps → Connect an app**: name `Pivendo posting`, category *Business*. Add the products **Login Kit** and **Content Posting API** (switch on **Direct Post**). Terms: `https://pivendo.com/policies/terms-of-service`, Privacy: `https://pivendo.com/policies/privacy-policy`.
3. 🤖 Claude builds the TikTok part of workflow 08. Before the review, TikTok only allows **private** test posts, so Claude tests with those.
4. 👤 You record the short demo video TikTok asks for (Claude tells you exactly what to show), then submit the app for review and the Direct Post audit.

**Pinterest** (review 10+ days, can be refused)
1. 👤 You: open **developers.pinterest.com** with the business account **PivendoTeam** → **My apps → Connect app**, name `Pivendo posting`. Pinterest first gives **Trial access** (a few days): pins made through it are only visible to you.
2. 🤖 Claude builds the Pinterest part of workflow 08 and tests it with Trial access.
3. 👤 You record the demo video Pinterest asks for (the login and one pin being made) and apply for **Standard access**.

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
| `facebook_auto` | `no` | `yes` = the bot posts the Reel on your Facebook Page. `no` = Facebook is left out |
| `shop_url` | `pivendo.com` | added to every caption that does not name it |

**Workflow 09 · Video intake** (the videos from the PC)

| Setting | Start value | Meaning |
|---|---|---|
| `post_times` | `00:30,04:30,08:30,12:30,16:30,20:30` | 6 slots a day, one every 4 hours, in `post_timezone`. 6 videos fill the next 24 hours |
| `post_timezone`, `time_zone`, `min_lead_hours` | `America/New_York`, `Europe/Berlin`, `1` | like in workflow 02 |
| `youtube_auto`, `instagram_auto`, `facebook_auto` | `no` | like in workflow 02. Set them here too |
| `pinterest_board` | `Christmas Decor & Gift Ideas` | named in the Pinterest to-do |
| `video_link_base` | `https://n8n.pivendo.com/webhook/pivendo-video` | the public link Instagram, Facebook and YouTube fetch the video from. Leave it |
| `max_mb` | `19` | biggest video. Telegram lets the bot fetch files only up to 20 MB |

12:30 and 20:30 in New York are 18:30 and 02:30 in Germany. For one week in autumn (25 Oct to 1 Nov 2026) and two weeks in spring it is 17:30 and 01:30, because the US and Europe change their clocks on different days. The bot handles that and always tells you the German time.

**Workflow 08 · Social publisher**

| Setting | Start value | Meaning |
|---|---|---|
| `ig_user_id` | `PASTE_YOUR_INSTAGRAM_ACCOUNT_ID` | your Instagram account ID, a long number (Part 3, step 2) |
| `fb_page_id` | `PASTE_YOUR_FACEBOOK_PAGE_ID` | your Facebook Page ID (Part 3, step 2) |
| `warn_minutes` | `5` | the least time between the ⏰ warning and the post. The warning comes 5-10 minutes before the slot |
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
| *"❌ Facebook: … Page key could not be read"* or *"(#200) … permission"* | The token has no `pages_manage_posts`, or the system user does not have the Page with **Content** (Part 2, steps 5-6). Fix it, then `/retry P…`. |
| *"❌ Facebook: … could not fetch the video"* or *"❌ Instagram: … could not use the video"* for a video from the PC | Open the video link from the bot's message in a private window. It must play. If not, tell Claude: workflow 09's video link does not work. |
| *"❌ A video from the PC was not queued: … MB. The limit is 19 MB"* | The video file is too big for Telegram. The agents on the PC make it smaller and send it again. |
| The ✅ button does nothing | Send `/approve P…` instead and tell Claude. |
| You approved by mistake | `/reject P…`. The bot stops everything that has not happened yet, but it **cannot take back a video that YouTube already has** (it is uploaded within 10 minutes of your ✅). The message then gives the video link and the clicks: YouTube Studio → **Content** → move the mouse over the video → ⋮ → **Delete forever** → tick the box → **Delete forever**. The bot never deletes anything itself. |
| *"🚫 Instagram: P… was not posted: you rejected it"* | Good: you rejected it while Instagram was still preparing the video, and the bot stopped before posting. Nothing is on Instagram. |

---

## For Claude: how it works and what is not live-tested

- **Files:** `tools/build_workflows.py` (workflow 02: `/queue`, Approve/Reject, to-dos; workflow 08: warning, publisher, stats; workflow 09: videos from the PC, the public video link), `templates/social_posts.csv`, tests in `tools/test_code_nodes.js`.
- **One Telegram trigger.** Buttons are inline callback buttons. Workflow 02's trigger listens to `message` and `callback_query`; "Parse command" turns a tap (`approve:P…`) into the same route as the typed `/approve P…`. The Coach (05) is different: its buttons are n8n "send and wait" links.
- **`social_posts` is append-only.** Every change is a new row holding only the changed columns; a post's state is all its rows merged (`foldPosts`). `post_at` is UTC, `slot` is the local slot time in `post_timezone`.
- **No double posts.** Workflow 08 only picks a platform while it is `queued` (YouTube's second step: `scheduled` = uploaded, still private), and saves `uploading` / `publishing` before any API call. A crash leaves the mark; after `stuck_minutes` the owner is told, and only `/retry` (the owner) puts it back to `queued`. "Save marks" has no error setting on purpose (a run that cannot save its marks stops), every node that writes to YouTube, Instagram or Facebook (and every warning) is reachable only through it, and every Telegram node in 08 continues on error, so a failed alert never blocks a posting branch. These three points are tested.
- **Reject races.** `/reject` only stops what has not started. Right before the Instagram publish call, "Reload post (Instagram)" + "Check post again (Instagram)" read the post again and publish only if it is still `approved` and still `publishing` (up to 10 minutes can lie between "Plan this run" and the publish call); a rejected post ends as `ig_status = cancelled`. Facebook does the same before its publish call (`fb_status = cancelled`). A YouTube video stays private until the bot makes it public at the slot, so Reject before the slot leaves it private; after that the reply gives the Studio link and the clicks. There is no call that deletes a video or a Reel, on purpose (a test asserts it).
- **Failed uploads.** n8n sends a YouTube file in chunks, so an upload reported as failed can still have left a video. Only a failed download (`none: true`) is certain to leave nothing. `/retry` warns about a second copy for `stuck` and for a failed YouTube upload (not when the video already has an id: then it is only made public again).
- **Music.** The owner chooses it himself and is reminded in the approval request, the approve message and the TikTok, YouTube and Instagram to-dos (`musicLine` in `JS_POSTS`). YouTube and Instagram APIs cannot add a sound, so for the platforms the bot posts the music must be inside the file. The Content and Post agents are told never to name or pick a song, and "Check post texts" refuses a text that credits one.
- **Table writes.** `social_posts` is append-only, so workflow 08 never rewrites it: an idle run writes nothing, and a busy run writes one small row per change.
- **Learning.** The evening run writes `feedback` rows in the `/video` shape (`ref` = `P…-yt`, `P…-ig`) plus one `content` row per video, because the Coach joins feedback with `content`. The Coach's prompt shows the content `format`, not the feedback `note`, so the format carries "views only" and "slot 12:30". Workflow 05 is unchanged.
- **Updating the live n8n:** `setup.ps1 -SkipInstall -ReplaceWorkflows -OnlyWorkflows 02,08` replaces only those two. The numbers also work quoted (`'02,08'`) or as `2,8`: PowerShell 5.1 turns an unquoted `02,08` into the numbers 2 and 8, and the script splits on commas and spaces and pads each number back to two digits. A number that matches no workflow file, a word that is not a number, or `-OnlyWorkflows` without `-ReplaceWorkflows` stops the script with a message before anything is touched.
- **Safe swap.** A replaced workflow is imported switched off, the old copy is switched off, the new copy is switched on, and only then is the old copy archived. If the new copy cannot be imported or switched on, the old copy stays (or is switched back on), the failed copy is archived and the script lists it under "Not replaced". Two copies are never on together: two Telegram triggers would fight over the bot's single webhook. The old and the new 02 even share one webhook address, and switching a copy off makes n8n remove that webhook at Telegram, so the old copy is switched off once, before the new one is switched on, and a copy that is already off is only archived. The script switches on every workflow it imports; there is no import-as-inactive option.
- **Settings are rebuilt on every re-import.** Workflow 02: the chat ID, support email and signature are filled in again, **everything else goes back to the start value**: `youtube_auto`, `instagram_auto`, `post_times`, `post_timezone`, `time_zone`, `min_lead_hours`, `shop_url`, `voice`, `cta_text`. Workflow 08: only the chat ID is filled in, so `ig_user_id`, `fb_page_id` and the other Settings go back to the start values. Workflow 09: the same (`youtube_auto`, `instagram_auto`, `facebook_auto` back to `no`). Ask the owner for his values before a re-import and set them again afterwards (Step 0). Without `-OnlyWorkflows`, every workflow's Settings would be reset, including the money settings in 01 and 07. Workflow 08 is only imported once both credentials exist, workflow 09 once "Video intake (Pivendo)" exists.

- **6 videos a day (owner, 14 Oct).** The PC sends finished videos to workflow 09 (`…/webhook/pivendo-video-in`, Header Auth login "Video intake (Pivendo)", attached by node name in `setup.ps1` because JSON2Video also uses Header Auth). 09 sends the file to the owner in Telegram (with ❌ Stop) and keeps only Telegram's `file_id` (`tg_file_id`): Telegram is the file store, so the PC can be off. The public link `…/webhook/pivendo-video?v=<20 random letters>.mp4` fetches the file from Telegram on every request (bots can download at most 20 MB, so 09 refuses more than `max_mb` = 19). The video gets the next free slot with no second OK (the owner approved its plan on the PC); 09 reads the table again right before "Plan intake" (the Post agent takes a while); a file name queued in the last 14 days and not rejected is refused (the PC may send again after a lost answer), and a post id that is already taken gets a letter (`P…b`). The PC sends one video at a time: Cloudflare ends a request after about 100 seconds, and the next slot is read from the table.
- **The warning (owner, 14 Oct: no answer = it goes out).** Workflow 08 runs every 5 minutes. A post the bot still has to make public gets one warning (`warned` = the moment) when its slot is at most `warn_minutes` + 5 minutes away, or right away if that was missed. No platform makes a post public before `ready()`: slot time reached AND the warning at least `warn_minutes` (minus one minute of slack) old. A late warning therefore moves the post; a failed warning (`warned = failed`) is sent again and nothing goes out meanwhile. The plan only marks `warned = sending`; the moment is written after Telegram confirmed a message (video or text), so a run that dies in between leaves the post unwarned and it is warned again. `/retry` writes `warned = again`: the owner gets a new warning. One warning per run. Slack: 30 seconds. Tested.
- **YouTube is uploaded private and made public at the slot** (`videos.update`, `part=status`, every status field sent again), after a last look at the post ("Reload post (YouTube)": the upload branch of the same run can take minutes). So ❌ Stop before the slot leaves only a private video (`yt_status = cancelled`); there is still no delete call. `/retry` of a YouTube post that has a video id goes back to `scheduled` (make public again), never to a second upload.
- **Facebook Reels** need a Page key: "Facebook: page key" reads it with the stored Meta login (`GET /{page}?fields=access_token`), then three calls without a stored login: start, upload (`rupload…`, header `file_url` = the video link), publish (`upload_phase=finish`, `video_state=PUBLISHED`). The last look at the post comes before publish. The key is never written to a row or a message (tested). It does pass through n8n's execution data, which stays on the owner's server.
- **AI-made line.** A video with AI in it gets "AI-made video." in the TikTok and Instagram captions and the YouTube description ("Check post texts"), because Facebook has no AI label the bot can set.

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
| n8n's Webhook node (v2) puts a multipart file under its field name in `binary`, and a Code node can hand that file on to the Telegram node | Part 5, step 3 |
| n8n's Telegram node sends a video by `file_id` (parameter `file`) with an inline ❌ Stop button, and returns `result.video.file_id` for an uploaded one | Part 5, step 3 and Part 4, step 4 |
| The public video link works: Telegram node "file get" with download, then Respond to Webhook (binary), reachable through the Cloudflare tunnel without a bot check, so Meta and n8n itself can fetch it | Part 5, step 3 (private window) and Part 4, step 5 |
| `GET /{page}?fields=access_token` with the system-user token gives a Page key, and start → rupload with `file_url` → finish posts a Reel | Part 4, step 5 |
| `videos.update` can make a private API upload public (a new, unchecked Google project may lock it private) | Part 4, steps 3 and 5 |
| n8n's REST call `POST …/data-tables/{id}/columns` adds the new columns (`setup.ps1`, for a table made by an older version) | `setup.ps1` prints "column … added" or says to add them by hand |
