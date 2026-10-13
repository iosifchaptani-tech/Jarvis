"""Run: python -m unittest test_trading.py  (no installs needed)"""

import unittest

from gate import check, max_drawdown
from guard import Account, Order, check_order, lots_for, status

W = [("2024-01-01", "2024-12-31"), ("2025-01-01", "2026-10-13")]


def trades(year, pattern, count):
    out = []
    for i in range(count):
        month, day = 1 + (i // 28) % 12, 1 + i % 28
        out.append({"time": f"{year}-{month:02d}-{day:02d}T10:00:00", "r": pattern[i % len(pattern)]})
    return out


class Gate(unittest.TestCase):
    def test_clear_edge_passes(self):
        t = trades(2024, [2, -1], 60) + trades(2025, [2, -1], 60)
        v = check(t, W, ideas_tried=10)
        self.assertTrue(v["passed"], v["reasons"])

    def test_too_few_trades_fails(self):
        v = check(trades(2024, [2, -1], 10) + trades(2025, [2, -1], 60), W, 10)
        self.assertFalse(v["passed"])
        self.assertIn("only 10 trades", v["reasons"][0])

    def test_one_losing_window_fails(self):
        v = check(trades(2024, [2, -1], 60) + trades(2025, [1, -1, -1], 60), W, 10)
        self.assertFalse(v["passed"])

    def test_small_edge_after_many_ideas_is_luck(self):
        v = check(trades(2024, [1.6, -1.4], 40) + trades(2025, [1.6, -1.4], 40), W, 200)
        self.assertFalse(v["passed"])
        self.assertTrue(any("luck" in r for r in v["reasons"]))

    def test_worse_than_current_fails(self):
        t = trades(2024, [2, -1], 60) + trades(2025, [2, -1], 60)
        self.assertFalse(check(t, W, 10, current_mean_r=0.9)["passed"])

    def test_trades_outside_windows_are_ignored(self):
        t = trades(2022, [-1], 200) + trades(2024, [2, -1], 60) + trades(2025, [2, -1], 60)
        self.assertTrue(check(t, W, 10)["passed"])

    def test_overlapping_windows_rejected(self):
        with self.assertRaises(ValueError):
            check([], [("2024-01-01", "2024-12-31"), ("2024-06-01", "2025-01-01")], 1)

    def test_utc_z_times(self):
        t = [{"time": "2024-05-01T10:00:00Z", "r": 1}]
        self.assertEqual(check(t, W, 1)["windows"][0]["trades"], 1)

    def test_drawdown(self):
        self.assertEqual(max_drawdown([1, -1, -1, -1, 2]), 3)


def acc(**kw):
    base = dict(is_demo=True, start_balance=10000, day_start_equity=10000, equity=10000)
    base.update(kw)
    return Account(**base)


BUY = Order("XAUUSD", "buy", entry=2000, stop_loss=1995)


class Guard(unittest.TestCase):
    def test_normal_order(self):
        d = check_order(acc(), BUY)
        self.assertTrue(d.allowed)
        self.assertEqual(d.risk_pct, 0.5)

    def test_live_account_refused(self):
        self.assertFalse(check_order(acc(is_demo=False), BUY).allowed)

    def test_stop_loss_required_and_on_right_side(self):
        self.assertFalse(check_order(acc(), Order("XAUUSD", "buy", 2000, None)).allowed)
        self.assertFalse(check_order(acc(), Order("XAUUSD", "buy", 2000, 2005)).allowed)
        self.assertTrue(check_order(acc(), Order("XAUUSD", "sell", 2000, 2005)).allowed)

    def test_daily_pause_and_full_stop(self):
        self.assertEqual(status(acc(day_start_equity=10100, equity=9898))[0], "PAUSED")
        self.assertEqual(status(acc(day_start_equity=9300, equity=9200))[0], "STOPPED")
        self.assertFalse(check_order(acc(equity=9200, day_start_equity=9200), BUY).allowed)

    def test_limits_on_count(self):
        self.assertFalse(check_order(acc(trades_today=6), BUY).allowed)
        three = [{"symbol": s, "side": "buy", "profit": 5} for s in ("EURUSD", "GBPUSD", "USDJPY")]
        self.assertFalse(check_order(acc(open_trades=three), BUY).allowed)

    def test_no_adding_to_a_loser(self):
        loser = [{"symbol": "XAUUSD", "side": "buy", "profit": -40}]
        self.assertFalse(check_order(acc(open_trades=loser), BUY).allowed)
        winner = [{"symbol": "XAUUSD", "side": "buy", "profit": 40}]
        self.assertTrue(check_order(acc(open_trades=winner), BUY).allowed)

    def test_profit_lock_and_new_rule_halve_risk(self):
        self.assertEqual(check_order(acc(equity=10300, day_start_equity=10300), BUY).risk_pct, 0.25)
        self.assertEqual(check_order(acc(), Order("XAUUSD", "buy", 2000, 1995, risk_factor=0.5)).risk_pct, 0.25)
        self.assertEqual(check_order(acc(), Order("XAUUSD", "buy", 2000, 1995, risk_factor=3)).risk_pct, 0.5)

    def test_lot_size(self):
        self.assertAlmostEqual(lots_for(10000, 0.5, 2000, 1995, 100), 0.1)
        self.assertAlmostEqual(lots_for(10000, 0.5, 2000, 1993, 100), 0.07)
        self.assertEqual(lots_for(1000, 0.5, 2000, 1900, 100), 0.0)


if __name__ == "__main__":
    unittest.main()
