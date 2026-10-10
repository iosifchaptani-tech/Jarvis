# Next up

## 0. For the next session (asked by the owner on 2 Oct 2026, ~01:00)
1. **DONE → `PLAN-30-DAYS.md` (repo root).** A 30-day master plan for EVERYTHING, day by day. The next session is **day 5**, so the plan covers days 5-34. The owner is doing many things at once and needs one plan that manages all of them. Each day gets a short task list (who does what, about how long), with one main focus per day so nothing is forgotten.

   It covers:
   - **Pivendo store** (`PLAN.md`):
     - setup is done and n8n is running
     - the order webhook and Telegram are tested
     - pivendo.com is bought and the permanent tunnel is being set up
     - next: first product, page copy, videos, posting, kill/scale checks
   - **Legal and admin:** Gewerbeanmeldung, Finanzamt (Kleinunternehmer), LUCID, Shopify Payments verification, shipping rates, cookie banner, connecting pivendo.com to Shopify.
   - **Wok Wang website:** the client has waited 3 months, so it should come early.
   - **Jarvis voice assistant:** only if the owner wants it.
   - **Money:** the moment to spend on things like the €6 server or Payoneer only comes after the first sales. Plus weekly reviews on days 7, 14, 21 and 28.

2. **Website for Wok Wang.** They have been waiting 3 months. Ask the owner before building:
   - what kind of business it is (restaurant?)
   - name, address, opening hours, phone
   - the menu with prices, and photos/logo
   - delivery or online ordering, and in which languages
   - which domain, and who pays for hosting
3. **Talk through the plan and how to make money.** Questions, priorities, what to do first.

## 1. PowerShell setup script: DONE (`setup.ps1`, `SETUP_DROPSHIPPING.bat`)

**When:** once the owner has created the accounts from `SETUP.md` Part 1 and has the keys ready.

**Build:** `dropshipping/setup.ps1`, a single script for Windows that:

1. **Checks and installs** what's missing, using `winget`:
   - Docker Desktop
   - cloudflared (Cloudflare's tunnel tool)
2. **Starts n8n** pinned to `docker.n8n.io/n8nio/n8n:2.41.3`, plus a cloudflared tunnel so n8n gets a public HTTPS address.
3. **Asks for each key on the PC itself.** Keys are typed into the script, never pasted into a chat:
   - Claude API key
   - Telegram bot token
   - CJ API key
   - JSON2Video key
   - support Gmail address + App password
4. **Sets up n8n through its REST API:**
   - creates the owner account (or logs in)
   - creates the 9 Data Tables from `templates/*.csv` and seeds `playbook`
   - creates the credentials
   - imports `n8n-workflows/*.json` and attaches the credentials to each node
   - sets the error workflow on every workflow
   - fills every ⚙️ Settings node: Telegram chat ID, support email, store name, policies
5. **Gets the Telegram chat ID** by activating workflow 02 and asking the owner to message the bot.
6. **Prints the steps that stay manual:**
   - the Shopify webhook URL, and where to paste it
   - Shopify Payments verification
   - Payoneer top-up
   - when to switch `auto_pay` to `yes`
7. **Re-running is safe:** it skips anything already done and never duplicates workflows or tables.

The REST calls used in testing already work: `/rest/owner/setup`, `/rest/projects/{id}/data-tables`, `/rest/credentials` and `/rest/workflows`. The test helpers from this session are a good starting point.
