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

### `/rules`: what the agents have learned
Shows the current rule list (the "playbook").

### `/help`: the command list

---

## 🔁 3. Your daily routine (about 20-30 minutes)

1. **Morning:** read the 07:00 research (2 minutes).
2. **Daytime:**
   - post your videos
   - pay CJ for any new orders
   - answer support tickets with `/send` or `/reply`
3. **48 hours after each video:** send `/video` with its numbers.
4. **Evening:** read the 21:30 report and tap ✅/❌.

**The more you report (`/video`, `/product`, ✅/❌), the smarter the agents get.**
