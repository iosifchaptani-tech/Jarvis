# Research 3: A cheap, self-improving n8n agent system

*Research agent report, 2026-09-29. Node versions were checked against the source of n8n **2.41.3**, the stable release (2026-09-25). "(unverified)" marks facts the agent could not confirm. The workflows in `../n8n-workflows/` were then imported into a real n8n 2.41.3 and test-run (see `../README.md`).*

**n8n 3.0 is due in October 2026:**
- Docker becomes the only self-hosting option.
- The legacy HTTP Request *Tool* is removed, and so is AI Agent v1.
- The Code node timeout drops to 60 s.

So **pin the version** and only upgrade on purpose ([breaking changes](https://docs.n8n.io/changelog/v30-breaking-changes.md)).

## 1. Hosting

| Host | Real monthly cost | Verdict |
|---|---|---|
| **Hetzner CX23** (2 vCPU, 4 GB) | €5.49 + €0.50 IPv4 = **€5.99** (about €7.10 with backups) | **Best pick.** Prices were raised in April and June 2026 ([Hetzner](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/)) |
| Oracle Cloud Always Free | €0 | Risky: the allowance was cut on 2026-06-15, and idle instances can be reclaimed ([InfoQ](https://www.infoq.com/news/2026/07/oracle-cloud-free-tier-limits/)) |
| Railway | about $8-15 (unverified) | – |
| Render | about $14-17 | The free tier sleeps, which breaks schedules and webhooks |
| Your Windows PC | €0 | Must stay on 24/7 and needs a public HTTPS tunnel. Fine for testing |

**License:** the Sustainable Use License FAQ explicitly allows "Use n8n community version to help run your business". It does not allow hosting n8n for others or white-labelling it ([FAQ](https://docs.n8n.io/n8n-community-license/community-license/license-faq.md)).

**Security and backups:**
- Create the owner account right after the first boot.
- Firewall: allow only 22, 80 and 443.
- Set `N8N_ENCRYPTION_KEY` and back it up. Without it, credentials can't be decrypted after a restore.
- A full backup is the `.n8n` folder **plus** a Postgres dump ([docs](https://docs.n8n.io/deploy/host-n8n/keep-n8n-running/backup-and-restore.md)).
- `N8N_WEBHOOK_URL` replaced `WEBHOOK_URL` in 2.35.

## 2. Nodes used (checked against the 2.41.3 source)

| Node | Latest version | Used here |
|---|---|---|
| scheduleTrigger | 1.4 | 1.2 |
| webhook | 2.1 | 2 |
| httpRequest | 4.5 | 4.2 |
| telegram / telegramTrigger | 1.2 / 1.5 | 1.2 / 1.1 |
| code | 2 | 2 |
| if / switch | 2.3 / – | 2.2 / 3.2 |
| set | 3.5 | 3.4 |
| wait | 1.1 | 1.1 |
| **dataTable** | 1.1 | 1.1 |
| errorTrigger | 1 | 1 |
| @n8n/n8n-nodes-langchain.agent | 3.1 | 3.1 |
| lmChatAnthropic | 1.6 | 1.6 |

- **Data Table operations** — row: insert, get, update, upsert, deleteRows, rowExists, rowNotExists; table: create, list, update, delete, clear.
- **Telegram `sendAndWait`** gives Approve/Decline buttons. The answer comes back in `$json.data.approved`, and it needs n8n on public HTTPS.
- **Shopify, 2026:** you can no longer create "legacy custom apps" (since 2026-01-01), and the REST Admin API is legacy. This project avoids both: it uses Shopify's built-in admin webhooks, and the CJ app handles fulfilment.

## 3. Agent design decisions

- **One workflow per agent,** with a deterministic scheduler and no LLM "supervisor". A supervisor adds cost and unpredictable routing. The Coach only makes *recommendations*.
- **Pricing, profit maths and KPIs are computed in Code nodes, never by the LLM.**
- **Order fulfilment has no LLM:** the CJ app plus the owner's payment click. That puts a human in the loop for every money action.

## 4. The "gets better every day" loop (the core design)

**Where memory lives:** n8n **Data Tables**.
- They're built in, need no credentials, are editable in the UI, and can be imported and exported as CSV.
- 200 MiB by default ([docs](https://docs.n8n.io/build/work-with-data/data-tables.md)).
- Google Sheets would be friendlier to read by hand, but needs OAuth.
- Postgres/pgvector only pays off above about 100k rows.

**Pattern:**
1. **Log outcomes.** Products tried, video stats and orders go to tables, with a 48-hour to 7-day delay so the results are real.
2. **Nightly reflection.**
   - Code computes the metrics.
   - The LLM compares them with past predictions and proposes at most 3 rule changes, each with evidence.
   - A validator enforces: allowed agents only, a length cap, dedupe, and no URLs, credentials, budgets, deceptive tactics or prompt-injection text.
3. **Human approval** via Telegram `sendAndWait`.
4. **Versioned, append-only rules.** The newest version of each `rule_id` wins, so rolling back means inserting an old version again. Rejected ideas are remembered so they aren't proposed again.
5. **Agents load the active rules at runtime** and put them in their system prompt. Self-modification is limited to these rule rows. Prompts, code, credentials, tools and spending never change automatically.

**Later additions:**
- **A/B prompt tests** only work at high volume (hooks, support replies).
- **n8n Evaluations** is free on Registered Community for one workflow.
- **Vector RAG** isn't worth it below about 1-2k items.

**Templates to learn from:** n8n.io/workflows 4197 (prompt improvement from feedback), 8802 (human feedback loop), 11495 (OPRO-style optimisation), 9472 (Telegram approval).

## 5. LLM cost

- **Prices:** Haiku 4.5 costs $1 / $5 per million tokens (input / output), Sonnet 5.5 costs $2 / $10, and Opus 5.5 costs $4 / $20.
- **Choice here:** these workflows use Opus 5.5 by default. It runs about twice a day, so the difference is only about $3/month. Change `MODEL` in `tools/build_workflows.py` to `claude-sonnet-5-5` to halve it.
- **Realistic bill:** about $3-15/month for this system. Set a hard spend limit in the Anthropic Console.
- **Gemini free tier:** data sent on it is used for training, so never send customer data through it.

## 6. Safety and failure modes

- **Runaway costs:** provider spend limits, `maxIterations` 3, and the execution timeout.
- **Wrong orders:** no automated ordering at all. The owner pays every CJ order.
- **Platform terms:**
  - TikTok and YouTube keep API posts from unaudited apps private, so the owner posts by hand.
  - Scraping TikTok, Amazon or AliExpress breaks their terms, so this project uses only the official CJ API.
- **Errors:** a global Error Trigger workflow sends a Telegram alert with the workflow, node, error and link.
