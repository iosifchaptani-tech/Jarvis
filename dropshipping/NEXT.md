# Next up

## 1. PowerShell setup script (first thing next session)

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
