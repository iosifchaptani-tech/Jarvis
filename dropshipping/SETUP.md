# Setup guide: from zero to running agents

Do the parts in order. Plan on about 3-4 hours in total. Anything you have to type or paste is written `like this`.

---

## Part 1: Accounts (day 1)

| # | What | Where | Cost |
|---|---|---|---|
| 1 | **Shopify store** | shopify.com → start the free trial | 3 days free, then $1/month for 3 months, then $39/month |
| 2 | **CJ Dropshipping** | cjdropshipping.com → sign up | free |
| 3 | **CJ Shopify app** | Shopify admin → Apps → search "CJdropshipping" → install → connect your CJ account | free |
| 4 | **Telegram bot** | In Telegram, message **@BotFather** → `/newbot` → pick a name → copy the **bot token** | free |
| 5 | **Claude API key** | console.anthropic.com → API keys → create key. Add $10 credit and **set a monthly spend limit of $20** | pay per use, about $3-15/month for this system |
| 6 | **JSON2Video** (Video agent, optional at first) | json2video.com → sign up → copy the API key | free tier for testing (watermarked, not for commercial posts); prepaid $49.95 = 7,200 credits ≈ 240 videos when you start posting |

Then do these right away. They take days to clear, so don't leave them for later:

- **Shopify → Settings → Payments:** turn on Shopify Payments and finish identity and bank verification. Add PayPal too.
- **Shopify → Settings → Policies:** generate the refund, privacy, terms, shipping and contact policies.
  - EU customers: also turn on the withdrawal/cancellation button (a legal requirement since 19 June 2026).
- **CJ:** add a card or PayPal for paying orders. Then open the API page (under *Authorization → API* or *Developer*) and **generate an API key**. Copy it and keep it private.

---

## Part 2: Run n8n (pick one)

### Option A: Hetzner server (recommended once you're live, about €6/month)
1. Create a Hetzner Cloud server: **CX23**, Ubuntu 24.04, with an SSH key.
2. Buy a cheap domain (about $10/year, e.g. from Cloudflare). Add a DNS **A record** `n8n.your-domain.com` pointing to the server's IP.
3. On the server:
   ```bash
   curl -fsSL https://get.docker.com | sh
   git clone <this repo> && cd Jarvis/dropshipping/n8n-server
   cp .env.example .env && nano .env      # fill in the domain, timezone and 2 random secrets
   docker compose up -d
   ```
4. Open `https://n8n.your-domain.com` and create your owner account **immediately**. The first person to open it becomes the owner.
5. In the Hetzner firewall, allow only ports 22, 80 and 443.
6. Backups: `crontab -e` → add `15 3 * * * /root/Jarvis/dropshipping/n8n-server/backup.sh`.
7. **Save the `N8N_ENCRYPTION_KEY` from `.env` in a password manager.** Without it, your saved passwords can't be restored.

### Option B: free test on your Windows PC
The PC has to stay on, and the web address changes every restart. This is fine for testing, not for running the store.
1. Install **Docker Desktop** and **cloudflared** (Cloudflare's free tunnel).
2. In one terminal: `cloudflared tunnel --url http://localhost:5678`. Copy the `https://....trycloudflare.com` address it prints.
3. In a second terminal:
   ```
   docker volume create n8n_data
   docker run -it --rm --name n8n -p 5678:5678 -e N8N_WEBHOOK_URL=https://PASTE-THE-TRYCLOUDFLARE-URL/ -e GENERIC_TIMEZONE=Europe/London -v n8n_data:/home/node/.n8n docker.n8n.io/n8nio/n8n:2.41.3
   ```
4. Open http://localhost:5678 and create your account.

### Option C: n8n Cloud (easiest, €20/month on the annual plan)
Sign up at n8n.io. There's nothing to install. Skip to Part 3.

> n8n is pinned to version **2.41.3** on purpose. n8n 3.0 (October 2026) removes older node versions, so upgrade later, deliberately.

---

## Part 3: Create the agents' memory (Data Tables)

In n8n: **Overview → Data tables → Create data table**. Create these 7 tables with **exactly** these names and columns.

- If n8n offers "Import CSV", use the matching file in `templates/`.
- Otherwise add the columns by hand.
- Columns not listed as numbers are text/string.

| Table | Columns | Number columns |
|---|---|---|
| `playbook` | rule_id, agent, rule, status, version, evidence | version |
| `products` | day, pid, sku, name, image, cj_cost, ship_cost, ship_method, ship_days, sell_price, profit_per_order, score, why, angle, target_buyer, risks, prediction, status | cj_cost, ship_cost, sell_price, profit_per_order, score |
| `content` | day, content_id, sku, product, format, hook, shots, on_screen_text, voiceover, caption, rules_version | none |
| `feedback` | day, kind, ref, views, clicks, sales, status, note | views, clicks, sales |
| `orders` | day, order_name, order_id, revenue, currency, items, skus, country | revenue |
| `reports` | day, orders_today, revenue_today, orders_7d, revenue_7d, cj_cost_7d, est_profit_7d, report | every column except day and report |
| `clips` | day, sku, url | none |

**Important:** put the 6 starting rules from `templates/playbook.csv` into `playbook`, either by importing the CSV or by typing them in. These are the first things your agents "know". The coach adds to them every night.

---

## Part 4: Credentials in n8n

**Overview → Credentials → Create credential**:

| Credential type | Name it | What to paste |
|---|---|---|
| **Anthropic** | `Claude` | your Claude API key |
| **Telegram API** | `Telegram bot` | the BotFather token |
| **Custom Auth** | `CJ API key` | `{"body": {"apiKey": "PASTE_YOUR_CJ_API_KEY"}}` |
| **Header Auth** | `JSON2Video` | Name: `x-api-key` · Value: your JSON2Video API key |

The CJ key sits inside an n8n credential, so it's stored encrypted and never ends up in the workflow files.

---

## Part 5: Import the workflows

**Workflows → Import from file**, then import every file in `n8n-workflows/`:

| File | What it does | When it runs |
|---|---|---|
| `00-error-alerts.json` | Messages you on Telegram when any workflow breaks | on errors |
| `01-product-research.json` | Research agent: CJ trending products → AI picks 3 → priced → Telegram | every day at 07:00 |
| `02-telegram-commands.json` | Your remote control: `/content`, `/clips`, `/render` (Video agent), `/video`, `/product`, `/rules` | when you message the bot |
| `03-new-order-alert.json` | Shopify order → saved → "pay it in CJ" message | on every paid order |
| `04-cj-order-check.json` | Warns about unpaid CJ orders and missing tracking | every 3 hours, 9:00-21:00 |
| `05-daily-coach.json` | Daily report plus learning: proposes new playbook rules, which you approve | every day at 21:30 |

In **each** workflow:
1. Open every node with a red warning and pick the credential:
   - `Claude (...)` nodes → **Claude**
   - Telegram nodes → **Telegram bot**
   - `CJ: get token` → **CJ API key**
   - `JSON2Video: start render` and `JSON2Video: check` (in 02) → **JSON2Video**
2. If a Data Table node is red, pick the table from the dropdown.
3. Open the **⚙️ Settings** node. It holds everything you might change: prices, markup, warehouse country, and so on.
4. **Workflow menu → Settings → Error workflow → "00 · Error alerts"**.

### Get your Telegram chat ID
1. Activate workflow **02** (toggle top right).
2. Send your bot any message. It replies: *"Your chat ID is 123456789"*.
3. Paste that number into the **⚙️ Settings** node of **every** workflow (00-05) and save each one.

From then on the bot only obeys you. Messages from anyone else are ignored.

### Connect Shopify orders (no Shopify developer app needed)
1. Open workflow **03** → click the **Shopify: order paid** node.
2. Change the **Path** to something random, like `orders-k29x7q`. It works like a password.
3. Save and activate. Copy the **Production URL**.
4. Shopify admin → **Settings → Notifications → Webhooks → Create webhook**:
   - **Event:** Order payment
   - **Format:** JSON
   - **URL:** paste the Production URL
5. Save, then click **Send test notification**. You should get a Telegram message within seconds.

---

## Part 6: Test everything before your first real product

1. Open **01** → **Execute workflow**. You should get 3 product picks on Telegram in about a minute.
2. Send `/content <SKU from the picks>` to the bot. You get the page copy plus 5 video scripts.
3. Film 3 short vertical clips of anything, upload them to Google Drive (share: *anyone with the link*), then send `/clips <SKU> <link1> <link2> <link3>` and `/render <video id>`. After 1-3 minutes you get the MP4. On the free JSON2Video tier it has a watermark, so it's for testing only.
4. Send `/video <video id> 500 3 0` and `/product <SKU> testing`. The bot confirms both.
5. Open **05** → **Execute workflow**. You get the daily report, and possibly an approval request for new rules.
6. **Activate** 00, 01, 02, 03, 04 and 05.

Then order your sample in CJ.

---

## Troubleshooting

| What you see | Fix |
|---|---|
| CJ error `1600001` / "Invalid API key" | Re-copy the CJ API key into the **CJ API key** credential. |
| CJ error "apiKey cannot be empty" | In `CJ: get token`, set the JSON body to `{"apiKey": "YOUR_KEY"}` directly. It's less private, but it works. |
| CJ error `1600200` "Too much request" | The free CJ tier allows 1 request per second. Just run it again later. |
| Telegram trigger won't activate | n8n needs a public **https** address: Option A, Option C, or the cloudflared tunnel. |
| Data Table "column not found" | A column name in the table doesn't match Part 3 exactly. |
| Claude node error 400/401 | Check the API key and that you have credit. |
| No research message but no error | Every CJ trending product was filtered out. Raise `max_cj_price` in ⚙️ Settings. |
| "Render failed" | Open each clip link in a private browser window. It must download without logging in. Keep clips under about 50 MB. |
| Video arrives as a link but not as a file | The file was over Telegram's 50 MB bot limit. Use the link, or shoot shorter or lower-bitrate clips. |
