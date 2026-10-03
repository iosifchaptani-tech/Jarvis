# Notes for Claude

## The owner
- Explain things in **short, simple words**, but include every step they need.
- They're a beginner on Windows. Give exact clicks and commands.

## What is in this repo
- `jarvis.py`, `START_JARVIS.bat`: a simple voice assistant (see `README.md`).
- `dropshipping/`: the Pivendo store's automation.
  - The store runs on Shopify + CJ Dropshipping, with n8n workflows and Claude agents.
  - Start with `dropshipping/README.md`, then `PLAN.md` and `SETUP.md`.
  - `setup.ps1` / `SETUP_DROPSHIPPING.bat`: the Windows setup. It installs Docker and cloudflared, starts n8n, creates the tables, imports the workflows and attaches the credentials. It is safe to run again.
  - `n8n-workflows/*.json` are **generated**. Edit `tools/build_workflows.py`, then run `python tools/build_workflows.py`.
  - Tests: `cd dropshipping/tools && npm install luxon@3 && node test_code_nodes.js`. They must all pass before every commit.
  - `POLICIES.md`: the store's legal texts in English and German, with blanks instead of the owner's name, address and email.

## Hard rules
- **Keys and passwords:**
  - Never ask for API keys, tokens or passwords in chat.
  - Never read, print or commit `keys.txt`, `api_key.txt` or `.env`.
  - The owner types keys only into the setup script window.
- **Money:**
  - Never turn on `auto_pay`, and never change prices, `markup`, `min_profit_usd`, `max_order_usd` or `daily_limit_usd` without the owner's clear OK.
  - Never pay, top up or buy anything.
- **Personal data:** never commit the owner's name, home address or email.
- **Honesty:** no fake reviews, discounts, countdowns or delivery times, and no brand copies. Germany/EU law applies: the owner lives in Germany.
- **Ask first** before anything outside this PC: pushing, deleting, or changing Shopify, CJ or Telegram settings.

## Things only the owner can do
- Create accounts and pass ID or bank checks.
- The Gewerbeanmeldung, Finanzamt and LUCID registrations.
- Top up money.
- Post videos.
- Tap ✅/❌ on rule proposals in Telegram.
