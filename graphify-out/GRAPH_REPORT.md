# Graph Report - Jarvis  (2026-10-13)

## Corpus Check
- 27 files · ~63,245 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: .csv 9, (none) 3, .bat 2)

## Summary
- 260 nodes · 441 edges · 17 communities (16 shown, 1 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 36 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7d10dd97`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- setup.ps1
- build_workflows.py
- 30-day master plan (days 5-34 · 2-31 October 2026)
- jarvis.py
- 👤 2. Commands you send
- Setup guide: from zero to running agents
- test_code_nodes.js
- PART B: DEUTSCH
- The plan: CJ dropshipping with self-improving n8n agents
- Research 2: First sales and profit within 14 days (CJ, $100-300, late 2026)
- Research 1: Starting CJ dropshipping on a near-zero budget (late 2026)
- Research 3: A cheap, self-improving n8n agent system
- Research 4: Automatic product videos from n8n
- Jarvis
- Adding a new product
- Next up
- backup.sh

## God Nodes (most connected - your core abstractions)
1. `build_commands()` - 18 edges
2. `Workflow` - 16 edges
3. `build_coach()` - 16 edges
4. `build_research()` - 15 edges
5. `build_support()` - 15 edges
6. `build_autopay()` - 15 edges
7. `Step()` - 12 edges
8. `Ok()` - 12 edges
9. `Ensure-Credentials()` - 12 edges
10. `settings()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Keep the plan up to date (every session)` --references--> `main()`  [INFERRED]
  CLAUDE.md → jarvis.py

## Import Cycles
- None detected.

## Communities (17 total, 1 thin omitted)

### Community 0 - "setup.ps1"
Cohesion: 0.20
Nodes (31): Activate-Workflows(), ApiErrorText(), Ask(), AskSecret(), AsList(), Collect-Answers(), Ensure-Credentials(), Ensure-Docker() (+23 more)

### Community 1 - "build_workflows.py"
Cohesion: 0.27
Nodes (20): agent(), build_autopay(), build_cj_check(), build_coach(), build_commands(), build_error_alerts(), build_order_alert(), build_research() (+12 more)

### Community 2 - "30-day master plan (days 5-34 · 2-31 October 2026)"
Cohesion: 0.06
Nodes (30): 30-day master plan (days 5-34 · 2-31 October 2026), Day 10 · Wed 7 Oct · 🎯 Launch (if the Gewerbe is confirmed), Day 11 · Thu 8 Oct · 🎯 Wok Wang revisions, Day 12 · Fri 9 Oct · 🎯 Wok Wang goes live, Day 13 · Sat 10 Oct · 🎯 Learn from the first videos, Day 14 · Sun 11 Oct · 🎯 Weekly review #2 (first kill/scale check), Day 18 · Thu 15 Oct, Day 19 · Fri 16 Oct · 🎯 Check the numbers (+22 more)

### Community 3 - "jarvis.py"
Cohesion: 0.10
Nodes (15): Hard rules, Keep the plan up to date (every session), Notes for Claude, The owner, Things only the owner can do, What is in this repo, Brain, Ears (+7 more)

### Community 4 - "👤 2. Commands you send"
Cohesion: 0.11
Nodes (17): 🤖 1. Messages that come by themselves, 👤 2. Commands you send, 🔁 3. Your daily routine (about 20-30 minutes), `/clips SKU link1 link2 link3`: your own footage (later), `/content SKU`: product page + 5 video scripts, ⏰ Every 3 hours: order check (only if something's wrong), 📊 Every evening at 21:30: the coach report, 🔎 Every morning at 07:00: product research (+9 more)

### Community 5 - "Setup guide: from zero to running agents"
Cohesion: 0.12
Nodes (16): Connect Shopify orders (no Shopify developer app needed), Fast way on Windows: the setup script, Get your Telegram chat ID, How auto-pay decides (workflow 07), How the Support agent decides, Option A: Hetzner server (recommended once you're live, about €6/month), Option B: free test on your Windows PC, Option C: n8n Cloud (easiest, €20/month on the annual plan) (+8 more)

### Community 6 - "test_code_nodes.js"
Cohesion: 0.13
Nodes (10): cjList, { DateTime }, DIR, fs, load(), path, playbook, run() (+2 more)

### Community 7 - "PART B: DEUTSCH"
Cohesion: 0.13
Nodes (14): A1. Refund policy, A2. Shipping policy, A3. Privacy policy, A4. Terms of service, A5. Contact information / Legal notice, B1. Rückerstattungsrichtlinie, B2. Versandrichtlinie, B3. Datenschutzerklärung (+6 more)

### Community 8 - "The plan: CJ dropshipping with self-improving n8n agents"
Cohesion: 0.14
Nodes (12): 1. The honest answer first, 2. How the system works, 3. Budget, 4. Numbers for one product, 5. The 14 days, 6. Legal checklist, 7. After the first sales (phase 2), Sources (+4 more)

### Community 9 - "Research 2: First sales and profit within 14 days (CJ, $100-300, late 2026)"
Cohesion: 0.20
Nodes (9): 1. Product research with $0 tools, 2. Traffic at near-zero spend, 3. Unit economics: $29.99 product with free shipping (CJ costs assumed), 4. Conversion basics for a one-product store, 5. Cash flow: revenue vs cash profit, 6. Day-by-day plan, 7. Honest success rates, Bottom line (+1 more)

### Community 10 - "Research 1: Starting CJ dropshipping on a near-zero budget (late 2026)"
Cohesion: 0.25
Nodes (7): 1. Sales channels, 2. CJ Dropshipping specifics, 3. Payments, payouts, and the cash-flow gap, 4. Legal and admin minimum, 5. Budgets (first month, itemised), 6. Scams and failure data, Research 1: Starting CJ dropshipping on a near-zero budget (late 2026)

### Community 11 - "Research 3: A cheap, self-improving n8n agent system"
Cohesion: 0.25
Nodes (7): 1. Hosting, 2. Nodes used (checked against the 2.41.3 source), 3. Agent design decisions, 4. The "gets better every day" loop (the core design), 5. LLM cost, 6. Safety and failure modes, Research 3: A cheap, self-improving n8n agent system

### Community 12 - "Research 4: Automatic product videos from n8n"
Cohesion: 0.25
Nodes (7): 1. Render APIs (30 s, 1080×1920), 2. AI voice, 3. AI-generated video b-roll, 4. Captions, 5. Pipeline built into workflow 02, 6. Compliance when posting, Research 4: Automatic product videos from n8n

### Community 13 - "Jarvis"
Cohesion: 0.29
Nodes (6): How to start Jarvis, If something doesn't work, Jarvis, Let him answer any question (optional), Things he can do without anything extra, Your Pivendo store

### Community 14 - "Adding a new product"
Cohesion: 0.33
Nodes (5): 1. 👤 Find it, 2. 🤖 Paste this into PowerShell Claude, 3. 👤 Make videos, Adding a new product, When an order comes

### Community 15 - "Next up"
Cohesion: 0.50
Nodes (3): 0. For the next session (asked by the owner on 2 Oct 2026, ~01:00), 1. PowerShell setup script: DONE (`setup.ps1`, `SETUP_DROPSHIPPING.bat`), Next up

## Knowledge Gaps
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Are the 5 inferred relationships involving `build_commands()` (e.g. with `.add()` and `.chain()`) actually correct?**
  _`build_commands()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `30-day master plan (days 5-34 · 2-31 October 2026)` be split into smaller, more focused modules?**
  _Cohesion score 0.06451612903225806 - nodes in this community are weakly interconnected._
- **Are the 5 inferred relationships involving `build_coach()` (e.g. with `.add()` and `.chain()`) actually correct?**
  _`build_coach()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `jarvis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09655172413793103 - nodes in this community are weakly interconnected._
- **Are the 4 inferred relationships involving `build_research()` (e.g. with `.add()` and `.chain()`) actually correct?**
  _`build_research()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `👤 2. Commands you send` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._
- **Are the 4 inferred relationships involving `build_support()` (e.g. with `.add()` and `.chain()`) actually correct?**
  _`build_support()` has 4 INFERRED edges - model-reasoned connections that need verification._