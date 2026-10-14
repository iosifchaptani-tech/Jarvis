# Graph Report - Jarvis  (2026-10-14)

## Corpus Check
- 30 files · ~150,277 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: .csv 10, (none) 3, .bat 2)

## Summary
- 296 nodes · 522 edges · 16 communities (15 shown, 1 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 47 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ab1a6c64`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- setup.ps1
- build_workflows.py
- 30-day master plan (days 5-34 · 2-31 October 2026)
- jarvis.py
- 👤 2. Commands you send
- The plan: CJ dropshipping with self-improving n8n agents
- test_code_nodes.js
- PART B: DEUTSCH
- Research 2: First sales and profit within 14 days (CJ, $100-300, late 2026)
- Research 1: Starting CJ dropshipping on a near-zero budget (late 2026)
- Research 3: A cheap, self-improving n8n agent system
- Research 4: Automatic product videos from n8n
- Jarvis
- Adding a new product
- Next up
- backup.sh

## God Nodes (most connected - your core abstractions)
1. `Workflow` - 18 edges
2. `build_commands()` - 18 edges
3. `build_coach()` - 16 edges
4. `build_social()` - 16 edges
5. `build_intake()` - 16 edges
6. `build_research()` - 15 edges
7. `build_support()` - 15 edges
8. `build_autopay()` - 15 edges
9. `👤 2. Commands you send` - 14 edges
10. `Ok()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `Part 5: The PC sends the 6 videos (PowerShell Claude does this)` --references--> `main()`  [INFERRED]
  dropshipping/SOCIAL-SETUP.md → jarvis.py
- `📍 Status (updated Wed 14 Oct, day 17). New chats start here.` --references--> `main()`  [INFERRED]
  PLAN-30-DAYS.md → jarvis.py
- `Keep the plan up to date (every session)` --references--> `main()`  [INFERRED]
  CLAUDE.md → jarvis.py

## Import Cycles
- None detected.

## Communities (16 total, 1 thin omitted)

### Community 0 - "setup.ps1"
Cohesion: 0.17
Nodes (36): Activate-Workflows(), ApiErrorText(), Archive-Workflow(), Ask(), AskSecret(), AsList(), Collect-Answers(), Discard-NewWorkflow() (+28 more)

### Community 1 - "build_workflows.py"
Cohesion: 0.23
Nodes (25): agent(), api(), api_page(), build_autopay(), build_cj_check(), build_coach(), build_commands(), build_error_alerts() (+17 more)

### Community 2 - "30-day master plan (days 5-34 · 2-31 October 2026)"
Cohesion: 0.06
Nodes (30): 30-day master plan (days 5-34 · 2-31 October 2026), Day 10 · Wed 7 Oct · 🎯 Launch (if the Gewerbe is confirmed), Day 11 · Thu 8 Oct · 🎯 Wok Wang revisions, Day 12 · Fri 9 Oct · 🎯 Wok Wang goes live, Day 13 · Sat 10 Oct · 🎯 Learn from the first videos, Day 14 · Sun 11 Oct · 🎯 Weekly review #2 (first kill/scale check), Day 18 · Thu 15 Oct, Day 19 · Fri 16 Oct · 🎯 Check the numbers (+22 more)

### Community 3 - "jarvis.py"
Cohesion: 0.06
Nodes (26): Hard rules, Keep the plan up to date (every session), Notes for Claude, The owner, Things only the owner can do, What is in this repo, For Claude: how it works and what is not live-tested, If something goes wrong (+18 more)

### Community 4 - "👤 2. Commands you send"
Cohesion: 0.07
Nodes (29): 🤖 1. Messages that come by themselves, 👤 2. Commands you send, 🔁 3. Your daily routine (about 20-30 minutes), 🎬 A new video from the PC (6 a day), ⏰ About 10 minutes before a video goes out, After ✅: your to-do list, Better posting times, `/clips SKU link1 link2 link3`: your own footage (later) (+21 more)

### Community 5 - "The plan: CJ dropshipping with self-improving n8n agents"
Cohesion: 0.06
Nodes (28): 1. The honest answer first, 2. How the system works, 3. Budget, 4. Numbers for one product, 5. The 14 days, 6. Legal checklist, 7. After the first sales (phase 2), Sources (+20 more)

### Community 6 - "test_code_nodes.js"
Cohesion: 0.13
Nodes (10): cjList, { DateTime }, DIR, fs, load(), path, playbook, run() (+2 more)

### Community 7 - "PART B: DEUTSCH"
Cohesion: 0.13
Nodes (14): A1. Refund policy, A2. Shipping policy, A3. Privacy policy, A4. Terms of service, A5. Contact information / Legal notice, B1. Rückerstattungsrichtlinie, B2. Versandrichtlinie, B3. Datenschutzerklärung (+6 more)

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

- **Why does `main()` connect `jarvis.py` to `30-day master plan (days 5-34 · 2-31 October 2026)`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `build_commands()` (e.g. with `.add()` and `.chain()`) actually correct?**
  _`build_commands()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `30-day master plan (days 5-34 · 2-31 October 2026)` be split into smaller, more focused modules?**
  _Cohesion score 0.06451612903225806 - nodes in this community are weakly interconnected._
- **Why does `📍 Status (updated Wed 14 Oct, day 17). New chats start here.` connect `30-day master plan (days 5-34 · 2-31 October 2026)` to `jarvis.py`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `build_coach()` (e.g. with `.add()` and `.chain()`) actually correct?**
  _`build_coach()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `jarvis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0627177700348432 - nodes in this community are weakly interconnected._
- **Are the 4 inferred relationships involving `build_social()` (e.g. with `.add()` and `.chain()`) actually correct?**
  _`build_social()` has 4 INFERRED edges - model-reasoned connections that need verification._