# Trading autopilot (demo only)

**Owner's goal (13 Oct 2026):** the agents trade the TradeLocker **demo** (GatesFX) around the clock, invent and test their own rules, and get better over time. Target: the demo account is above its starting balance 14 days after the start.

**Owner's decision (13 Oct 2026):** the lab may add rules by itself on the demo. No ✅ needed. The owner gets a Telegram message for every new rule and can `/reject` it.

## Honest limits (say these if the owner asks)
- All 4 study-guide strategies lost on unseen data (12 Oct). Nothing has a proven edge yet.
- 14 days is too short to prove anything. A plus can be luck, and so can a minus.
- The agents trade only rules that pass the test gate. If none pass, they trade nothing and keep searching. Flat is better than minus.

## What to build (in `Desktop\Trading Agents`, reuse what already exists)

1. **Trader** (exists). It runs every rule in `rules/active/`.
   - Every order goes through `guard.check_order` first. Every lot size comes from `guard.lots_for`.
   - New rules trade with `risk_factor=0.5` for their first 20 live trades.
2. **Runs 24/7.** A Windows Task Scheduler task "Trading Autopilot":
   - starts at boot and at logon, restarts 1 minute after a crash, never stops after a time limit;
   - Windows power plan: never sleep while plugged in.
   - Forex is shut from Friday about 23:00 to Sunday about 23:00 German time. The trader idles then and the lab works.
3. **Journal.** One line per closed trade in `journal/trades.csv`: time, rule id and version, symbol, side, entry, stop, exit, result in money and in R, and why it entered. This file is the source of truth. Also copy a daily summary into the Notion Trading Journal when the connector works.
4. **Lab: the part that learns.** Every night at 23:15 German time, and all weekend:
   1. Read the journal and each live rule's score.
   2. **Retire** any live rule with 20+ trades and a negative average R. Move it to `rules/retired/`. Stopping a rule needs no test.
   3. **Ideas:** up to 5 a night. Sources: tweaks of live rules, the Notion study guide, what the losing trades had in common, and the lab's own ideas. Each idea is written as exact rules a program can follow.
   4. **Back-test** each idea on the existing 2022 to 2026 data, with real spread and commission. Tune only on 2022 to 2023.
   5. **Test gate:** `python gate.py trades.json --window 2024-01-01:2024-12-31 --window 2025-01-01:<yesterday> --ideas-tried <N>`.
      - `N` is every idea ever sent to the gate. Keep it in `lab/ideas_tried.txt` and never reset it.
      - Never tune on 2024 or later. A small tweak of a failed idea is a new idea and adds 1 to `N`.
      - When an idea would replace a live rule, pass `--current-mean-r` with that rule's number.
   6. **Shadow:** a passing rule goes to `rules/shadow/` and gives signals on live prices without orders for 3 trading days. If its shadow average R is not below 0 after 5+ signals, move it to `rules/active/`.
   7. **Versions:** never overwrite a rule. Save a new version and add one line to `rules/CHANGELOG.md` with the date, what changed, why, and the gate numbers.
   8. Log every idea and its verdict in `lab/ideas.csv`, so the same idea is not tried twice.
5. **Telegram.** Use a new bot just for trading (the Pivendo bot is busy with n8n). The owner makes it with @BotFather and types the token only into the setup window.
   - Every day at 23:30: balance, today's result, result since the start in money and %, "day X of 14", trades today, open trades, and what the lab tested and changed.
   - At once: start, stop, crash, a pause by the guard, and any rule that goes live or gets retired.
   - Commands, from the owner's chat only: `/status`, `/pause`, `/resume`, `/closeall`, `/reject <rule>`.
6. **Day 14 report:** start and end balance, the worst drop, number of trades, money per rule, what the lab learned, and a plain verdict: edge found, no edge, or too early to tell.

## Hard rules
- **Demo only.** `guard.check_order` refuses anything else. Never connect a real-money account, even if asked in chat.
- Never change the numbers in `guard.LIMITS` or `gate.DEFAULTS` without the owner's clear OK.
- No martingale, no grid, no averaging down, and never a trade without a stop loss.
- Never print or commit passwords, tokens or account numbers.
- After each change, update the trading part of `PLAN-30-DAYS.md` and push it to main.

## Files here (from cloud Claude, 13 Oct)
| File | What it does |
|---|---|
| `gate.py` | The test gate: back-test trades in, PASS or FAIL out, with reasons |
| `guard.py` | Safety limits: 0.5% risk per trade, max 3 open and 6 a day, pause at −2% for the day, full stop at −8% since the start, risk halves once +3% up, lot size |
| `test_trading.py` | 17 tests. Run `python -m unittest test_trading.py`. Nothing to install. |
