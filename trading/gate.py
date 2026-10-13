"""Test gate: may a new or changed rule trade on the demo account?

Feed it the rule's back-test trades. Each trade needs its exit time and its
result in R (money won or lost, divided by the money risked), after spread and
commission. The gate looks only at the unseen windows: periods the rule was
never tuned on. A rule passes only if it made money in every unseen window,
with enough trades, and by more than luck explains, given how many ideas the
lab has tried so far. Each small tweak of an idea counts as a new idea.

    python gate.py trades.json --window 2024-01-01:2024-12-31 \
        --window 2025-01-01:2026-10-13 --ideas-tried 17

trades.json is a list like [{"time": "2024-03-05T14:30:00", "r": 1.8}, ...].
Prints the verdict as JSON. Exit code 0 = PASS, 1 = FAIL, 2 = bad input.
"""

import argparse
import json
import math
import sys
from datetime import date, datetime, timezone
from statistics import NormalDist, mean, stdev

DEFAULTS = {
    "min_trades_per_window": 30,   # fewer trades than this says nothing
    "min_mean_r": 0.05,            # each unseen window must earn at least this per trade
    "min_profit_factor": 1.15,     # money won / money lost, unseen windows together
    "max_drawdown_r": 10.0,        # worst losing streak, in R
    "alpha": 0.05,                 # allowed chance of passing a lucky rule, across ALL ideas tried
}


def _when(text):
    t = datetime.fromisoformat(str(text).strip().replace("Z", "+00:00"))
    if t.tzinfo is not None:
        t = t.astimezone(timezone.utc).replace(tzinfo=None)
    return t


def _day(text):
    return date.fromisoformat(str(text).strip()[:10])


def _num(x):
    return round(x, 3) if math.isfinite(x) else "inf"


def max_drawdown(results):
    """Largest drop from a high point of the running total, in R."""
    peak = total = worst = 0.0
    for r in results:
        total += r
        peak = max(peak, total)
        worst = max(worst, peak - total)
    return worst


def profit_factor(results):
    won = sum(r for r in results if r > 0)
    lost = -sum(r for r in results if r < 0)
    if lost == 0:
        return math.inf if won > 0 else 0.0
    return won / lost


def required_t(ideas_tried, alpha):
    """One-sided bar for the t-statistic, raised for every idea ever tested (Bonferroni)."""
    return NormalDist().inv_cdf(1 - alpha / max(1, int(ideas_tried)))


def check(trades, windows, ideas_tried, current_mean_r=None, settings=None):
    s = dict(DEFAULTS, **(settings or {}))
    spans = sorted((_day(a), _day(b)) for a, b in windows)
    if len(spans) < 2:
        raise ValueError("Give at least 2 unseen windows.")
    for a, b in spans:
        if b < a:
            raise ValueError(f"Window {a}:{b} ends before it starts.")
    for (a1, b1), (a2, b2) in zip(spans, spans[1:]):
        if a2 <= b1:
            raise ValueError(f"Windows {a1}:{b1} and {a2}:{b2} overlap.")

    rows = sorted((_when(t["time"]), float(t["r"])) for t in trades)
    reasons, per_window, unseen = [], [], []
    for a, b in spans:
        res = [r for t, r in rows if a <= t.date() <= b]
        unseen.extend(res)
        m = mean(res) if res else 0.0
        per_window.append({"window": f"{a}:{b}", "trades": len(res), "mean_r": _num(m)})
        if len(res) < s["min_trades_per_window"]:
            reasons.append(f"{a}:{b}: only {len(res)} trades, needs {s['min_trades_per_window']}")
        elif m < s["min_mean_r"]:
            reasons.append(f"{a}:{b}: {m:+.3f} R per trade, needs at least {s['min_mean_r']:+.3f}")

    n = len(unseen)
    m = mean(unseen) if unseen else 0.0
    sd = stdev(unseen) if n >= 2 else 0.0
    t_stat = m / (sd / math.sqrt(n)) if sd > 0 else (math.inf if m > 0 else 0.0)
    pf, dd = profit_factor(unseen), max_drawdown(unseen)
    need_t = required_t(ideas_tried, s["alpha"])

    if pf < s["min_profit_factor"]:
        reasons.append(f"profit factor {pf:.2f}, needs {s['min_profit_factor']:.2f}")
    if dd > s["max_drawdown_r"]:
        reasons.append(f"worst drop {dd:.1f} R, limit {s['max_drawdown_r']:.1f} R")
    if t_stat < need_t:
        reasons.append(f"could be luck: t = {t_stat:.2f}, needs {need_t:.2f} after {ideas_tried} ideas tried")
    if current_mean_r is not None and m < current_mean_r:
        reasons.append(f"worse than the version it replaces ({m:+.3f} vs {current_mean_r:+.3f} R per trade)")

    return {
        "passed": not reasons,
        "verdict": "PASS" if not reasons else "FAIL",
        "reasons": reasons,
        "windows": per_window,
        "unseen": {
            "trades": n, "mean_r": _num(m), "profit_factor": _num(pf),
            "max_drawdown_r": _num(dd), "t_stat": _num(t_stat),
            "t_needed": _num(need_t), "ideas_tried": int(ideas_tried),
        },
    }


def main(argv=None):
    p = argparse.ArgumentParser(description="Test gate for trading rules.")
    p.add_argument("trades", help="JSON file: list of {time, r}")
    p.add_argument("--window", action="append", required=True, help="unseen window START:END (YYYY-MM-DD)")
    p.add_argument("--ideas-tried", type=int, required=True, help="every idea ever sent to the gate, this one included")
    p.add_argument("--current-mean-r", type=float, help="mean R of the version this would replace")
    a = p.parse_args(argv)
    try:
        with open(a.trades, encoding="utf-8") as f:
            trades = json.load(f)
        windows = [w.split(":", 1) for w in a.window]
        result = check(trades, windows, a.ideas_tried, a.current_mean_r)
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(json.dumps({"verdict": "ERROR", "reason": str(e)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
