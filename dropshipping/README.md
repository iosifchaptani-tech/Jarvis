# Dropshipping + self-improving n8n agents

Start with **[PLAN.md](PLAN.md)**, then follow **[SETUP.md](SETUP.md)**.

| Folder | What's inside |
|---|---|
| `PLAN.md` | Honest odds, how the system works, budget, 14-day plan, kill/scale rules, legal checklist |
| `SETUP.md` | Step-by-step: accounts → n8n → Data Tables → credentials → import → test |
| `setup.ps1` / `SETUP_DROPSHIPPING.bat` | Windows: does Parts 2-5 of SETUP.md automatically (install, n8n, keys, tables, workflows); safe to run again |
| `POLICIES.md` | Ready-to-paste Shopify policies: refund, shipping, privacy, terms, contact |
| `n8n-workflows/` | 8 workflows to import into n8n (research, Telegram commands with the content and video agents, order alert, CJ order check, daily coach, customer support, CJ auto-pay, error alerts) |
| `templates/` | CSV templates for the 9 Data Tables. `playbook.csv` holds the 7 starting rules |
| `n8n-server/` | Docker Compose (n8n 2.41.3 + Postgres + automatic HTTPS) and a backup script for a €6/month server |
| `research/` | The 4 research reports, with sources |
| `tools/` | `build_workflows.py` generates the workflow files; `test_code_nodes.js` tests their logic |

## Changing the workflows
Edit `tools/build_workflows.py` (not the JSON files), then run:

```bash
python3 dropshipping/tools/build_workflows.py        # regenerate n8n-workflows/*.json
cd dropshipping/tools && npm install luxon@3 && node test_code_nodes.js   # 31 logic tests
```

## How the workflows were tested
- **In a real n8n 2.41.3 (Docker):**
  - All 8 workflows pass n8n's activation check. The only issues reported were the missing credentials you add during setup.
  - Every path was run against real Data Tables, with CJ, Claude, Telegram, Shopify and JSON2Video replaced by fake responses: research; all Telegram commands; video render success and timeout; order alert; CJ check; coach approve and reject; error alert; support emails with auto-send off and on; `/send` (including a double send), `/reply` and `/skip`; the coach learning a support rule from an owner's rewrite; a video with no clips (CJ photos); auto-pay off, on, and a second run (nothing paid twice, no repeat alerts).
  - The CJ credential was confirmed to send the API key in the request body.
- **Not tested with live accounts** (no keys were used): the real CJ API, Claude's answers, Telegram delivery, JSON2Video rendering, and a real mailbox over IMAP/SMTP. Part 6 of `SETUP.md` is the first live test.
