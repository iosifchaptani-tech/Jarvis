# Your Telegram bot, simply explained

The bot is your **remote control** for the store's AI agents. They work on your PC (inside n8n) and talk to you through Telegram.

**Only you can use it.** It ignores messages from anyone else.

There are two kinds of messages:
- **🤖 Messages the bot sends you by itself**, at fixed times or when something happens.
- **👤 Commands you send it**, starting with `/`.

---

## 🤖 1. Messages that come by themselves

### 🔎 Every morning at 07:00: product research
The research agent looks through CJ's trending products and sends you **3 product ideas**. For each one you get:

| Line | Meaning |
|---|---|
| **CJ SKU** + "Open in CJ" | the product number, plus a link to its page on CJ |
| **Cost** | what CJ charges you: the product + shipping |
| **Sell at** | your shop price, set by a fixed rule (1.5× your cost, at least $7 above it) |
| **By country** | your profit in the US / Germany / Canada / Australia. ✅ = worth selling there, ❌ = don't sell there |
| **Score** | how good the agent thinks it is (0-100) |
| **Video idea** | what to show in the first seconds of a video |
| **Risks** | what could go wrong (competition, season, returns...) |

**👉 What you do:** usually nothing. When you like one, send `/product SKU testing`, then list it in Shopify and send `/content SKU`.

### 🛒 When a customer pays: order alert
*"🛒 New paid order #1001…"*
**👉 What you do:** open the CJ app or website and **pay that order at CJ**. CJ then ships it to the customer. While auto-pay is off, you do this step yourself.

### ⏰ Every 3 hours: order check (only if something's wrong)
It warns you when a CJ order is **not paid yet**, or has had **no tracking number for 48 hours**.
**👉 What you do:** pay it, or ask CJ support about the tracking.

### ✉️ When a customer emails: support draft
The support agent reads the email, looks up the customer's order and tracking, and **writes a reply for you**. The message shows a ticket number like **T123**.
**👉 What you do (pick one):**
- `/send T123`: send the agent's reply as it is
- `/reply T123 your text`: send your own text instead. The agent **learns from your version**.
- `/skip T123`: close it without replying

### 🎬 A new video from the PC (6 a day)
Every day the agents on the PC first show you **6 video plans and ask you**. After your OK they build all 6 and send them to the bot. For each one you get:
- *"🎬 P… · product · Goes out Thu 15 Oct at 18:30 …"*: the finished video, its time, and a **❌ Stop** button.
- a **TikTok to-do** and a **Pinterest to-do** (you post those two yourself for now).

The 6 videos get the next 6 slots: **one every 4 hours** (06:30, 10:30, 14:30, 18:30, 22:30 and 02:30 German time).

**👉 What you do:** watch it. Don't like it? Tap **❌ Stop**. Then do the TikTok and Pinterest to-dos.

### ⏰ About 10 minutes before a video goes out
*"⏰ In about 10 minutes P… goes out on YouTube, Instagram, Facebook."* with the video and a **❌ Stop** button.

**👉 What you do:** nothing, if you like it. **No answer = it goes out.** Tap **❌ Stop** if you don't want it. The bot never makes anything public without sending you this warning first (if Telegram fails, it tries again and waits).

### 📺 📸 📘 When a video goes out
- *"📺 YouTube: P… is uploaded as a private video"*: nobody can see it yet. The bot makes it public at its slot, after your warning.
- *"📺 YouTube: P… is public now"*, *"📸 Instagram: P… is live"*, *"📘 Facebook: P… is posted on your Page"*: it is out, with its link.

**👉 What you do:** nothing. If the video has AI in it, open it once and check the AI label (Facebook has none: its text says "AI-made video." instead).

These only come when the bot posts on that platform itself (see `SOCIAL-SETUP.md`). Until then you get a to-do list instead. **TikTok and Pinterest are to-do lists for now:** you post them yourself.

### ⏰ ❓ ❌ When a video did NOT go out
| Message | Meaning | 👉 What you do |
|---|---|---|
| **⏰ was NOT posted** | the slot passed more than 12 hours ago, for example because the PC was off | `/retry P…` posts it now, `/reject P…` drops it |
| **❌ was not posted / the upload failed / could not be made public** | YouTube, Instagram or Facebook said no. The reason is in the message | fix it (or send the message to Claude), then `/retry P…`. For a failed YouTube upload, **look in YouTube Studio first**: it can still have left the video there |
| **❓ may not have been posted** | the bot is not sure | look on Instagram, Facebook or YouTube. Not there? `/retry P…` |
| **🚫 was not posted: you stopped it** | you tapped ❌ while Instagram or Facebook was still preparing the video, so the bot stopped before posting | nothing. Nothing is public there |

The bot never tries again by itself, so nothing is ever posted twice.

### 📈 Every evening at 21:00: video numbers
For every video that has been out for 48 hours, the bot reads the views on YouTube and Instagram and saves them. The coach uses them half an hour later. The last line (🏆) shows your **best and weakest video of the last 7 days**, with the platform and the time slot.

**👉 What you do:** send the TikTok numbers yourself, the message shows the exact command: `/video P…-tt views clicks sales`.

**🔑** in this message means a login stopped working. The message says which one and how to fix it.

### 📊 Every evening at 21:30: the coach report
Today's numbers, 3 things to do tomorrow, and sometimes a **rule idea**, like *"Start videos with the result: those got 3× more views"*, with **✅ / ❌ buttons**.
**👉 What you do:** tap ✅ if the idea makes sense, ❌ if not. Approved rules become part of every agent's instructions. **That's how the agents get better every day.**

### ⚠️ "Workflow failed"
Something broke, for example CJ was down or there's no API credit left.
**👉 What you do:** send that message to Claude.

---

## 👤 2. Commands you send

### `/content SKU`: product page + 5 video scripts
Example: `/content CJJJJTJT02140-4X22`

You get:
1. **Product page text:** title, description, bullet points. Paste it into Shopify.
2. **5 video scripts**, each with an **ID** (like `V100314295`) and these parts:
   - **HOOK:** the first 1-2 seconds that make people stop scrolling
   - **SHOTS:** what to film or show, scene by scene
   - **ON-SCREEN TEXT:** the words on the video
   - **VOICEOVER:** what you or an AI voice say
   - **CAPTION:** the text and hashtags under your TikTok or Reel

It only works for products the agents know: from the research, or added by PowerShell Claude.

### `/render ID`: automatic video (⚠️ currently off)
It would turn a script into a finished video from the CJ photos. It needs **JSON2Video**, which you **skipped**, so it won't work for now.
**👉 Instead:** make the video yourself in **CapCut**, following the script. That's free.

### `/clips SKU link1 link2 link3`: your own footage (later)
When you film your own clips, upload them to Google Drive (shared with "anyone with the link") and send the links. Real footage gets more views than photos.

### `/video ID views clicks sales`: report a video's results ⭐ important
**48 hours after posting**, send e.g. `/video V100314295 2400 31 1` (2,400 views, 31 link clicks, 1 sale).
The agents use this to learn **which hooks and styles work**, and write better scripts next time.

### `/product SKU testing|winner|killed note`: report how a product is doing
- `/product CJJJJTJT02140-4X22 testing`: you started selling it
- `… winner good sales from video 2`: it's working
- `… killed 30 videos no sales`: you stopped it, and the research avoids similar products

### `/queue LINK SKU ai`: send a finished video to TikTok, Instagram and YouTube ⭐
Example: `/queue https://cdn.shopify.com/videos/star-lamp-1.mp4 CJYS315715002BY ai presenter holds the lamp, stars on the wall`

- **LINK:** a public link to the video that ends with `.mp4`. Easiest way: Shopify admin → **Content → Files → Upload files**, then click the link icon to copy the link. **Choose the music first:** if the bot posts the video on YouTube or Instagram, the music must already be inside the file (see 🎵 below).
- **SKU:** the product in the video.
- **ai:** write `ai` if the video has an AI presenter or an AI voice. Leave it out if not.
- **After that:** a few words about what the video shows. The agent cannot watch the video, so this keeps the text honest.

The agent writes a TikTok caption, an Instagram caption, and a YouTube title and description. You get one message with all texts and two buttons:

- **✅ Approve:** the video gets the next free slot. There are two slots a day: **12:30 and 20:30 New York time** (lunch and evening for US buyers). The bot always tells you the time in **German time**.
- **❌ Reject:** the video is dropped.

**A video you send with `/queue` is never posted without your ✅.** If the buttons don't react, send `/approve P…` or `/reject P…`. (Videos from the PC need no ✅ here: you already said yes to their plans. You still get the 10-minute warning with ❌ Stop.)

If the agent's text breaks an honesty rule (a discount, a countdown, a delivery promise, a fake review, a "whole ceiling" claim, a price), the bot says *"Not queued"*. Send the same `/queue` again to get new texts.

### After ✅: your to-do list
You get a **TikTok to-do** every time: the download link, the music reminder, the caption (tap it to copy), the time to schedule, and what to switch on (**"Your brand"**, and **"AI-generated content"** for AI videos). When you've scheduled it in TikTok Studio, send `/tiktok P… done`.

If the bot doesn't post on YouTube or Instagram itself yet, you get the same kind of list for them. Then send `/youtube P… done` or `/instagram P… done`.

### 🎵 The music: you choose it, every time
You pick the music for every video yourself, **before it is posted**. The bot reminds you each time with **"Choose the music first."**: in the message with the texts, in the ✅ message, and in every to-do list.

- **TikTok:** in TikTok Studio tap **Sounds**, pick one, then **Save**.
- **YouTube and Instagram, when the bot posts them:** the bot **cannot add a sound**. The music must already be **inside the video file**. So put the music in first, then send the link with `/queue`.
- **YouTube and Instagram, when you post by hand:** the to-do list tells you where to pick it.

The agents never choose or name a song for you.

### `/posts`: your posting plan
Shows the videos waiting for your OK, the ones coming up with their times, and the last 5 that went out.

### `/retry P…`: try a failed post again
Only works after the bot told you that YouTube, Instagram or Facebook failed. Check first that the video is not already there. This matters most for YouTube: a failed upload can still have left the video in YouTube Studio, and a retry would make a second copy.

### `/reject P…` or ❌ Stop: stop a video
The bot posts nothing more for it. What is already out (or what you scheduled on TikTok), you delete yourself. The message tells you where.

**YouTube:** the bot uploads your video as a **private** video soon after it is queued and only makes it public at its slot. If you stop it before the slot, it **stays private**: nobody sees it. After the slot it is public, and the bot never deletes anything for you. The message gives you its link and these clicks:
1. Open YouTube Studio → **Content** (left menu).
2. Move the mouse over the video and click the three dots **⋮** (Options) → **Delete forever**.
3. Tick the box and click **Delete forever**.

### `/rules`: what the agents have learned
Shows the current rule list (the "playbook").

### `/help`: the command list

---

## 🔁 3. Your daily routine (about 20-30 minutes)

1. **Morning:** read the 07:00 research (2 minutes).
2. **Daytime:**
   - answer the agents on the PC when they show you the 6 video plans (say OK, or what to change)
   - watch the 6 videos when they arrive in Telegram; tap ❌ Stop on any you don't like
   - schedule the 6 on TikTok and Pinterest from the to-do lists
   - pay CJ for any new orders
   - answer support tickets with `/send` or `/reply`
3. **48 hours after each video:** send `/video` with its TikTok numbers. The bot reads YouTube and Instagram itself.
4. **Evening:** read the 21:00 video numbers and the 21:30 report, and tap ✅/❌.

**The more you report (`/video`, `/product`, ✅/❌), the smarter the agents get.**

### Better posting times
The coach sees the time slot of every video next to its views. When one slot clearly works better, it can propose that as a **rule idea** with ✅/❌. The bot **never changes the posting times by itself**. If you approve such an idea, tell Claude: *"Change the posting times to …"*.
