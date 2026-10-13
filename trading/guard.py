"""Safety limits for the demo trader. Every order goes through check_order first,
and every lot size comes from lots_for. Change LIMITS only with the owner's
clear OK (see CLAUDE.md in the Jarvis repo).
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional

LIMITS = {
    "risk_per_trade_pct": 0.5,    # of current equity, per trade
    "max_open_trades": 3,
    "max_trades_per_day": 6,
    "daily_loss_stop_pct": 2.0,   # down this much today: no new trades until tomorrow
    "total_loss_stop_pct": 8.0,   # down this much since the start: everything stops, owner restarts
    "lock_profit_at_pct": 3.0,    # up this much since the start: risk per trade halves to protect the lead
}


@dataclass
class Account:
    is_demo: bool
    start_balance: float          # balance on day 1 of the 2-week run
    day_start_equity: float       # equity at 00:00 German time today
    equity: float
    trades_today: int = 0
    open_trades: List[dict] = field(default_factory=list)   # {"symbol", "side", "profit"}


@dataclass
class Order:
    symbol: str
    side: str                     # "buy" or "sell"
    entry: float
    stop_loss: Optional[float]
    risk_factor: float = 1.0      # 0.5 while a rule is in its first 20 live trades


@dataclass
class Decision:
    allowed: bool
    risk_pct: float
    reason: str


def status(acc, limits=None):
    """'STOPPED', 'PAUSED' or 'OK', with a reason."""
    L = dict(LIMITS, **(limits or {}))
    if acc.equity <= acc.start_balance * (1 - L["total_loss_stop_pct"] / 100):
        return "STOPPED", f"Down {L['total_loss_stop_pct']}% since the start. Stopped until the owner restarts it."
    if acc.equity <= acc.day_start_equity * (1 - L["daily_loss_stop_pct"] / 100):
        return "PAUSED", f"Down {L['daily_loss_stop_pct']}% today. No new trades until tomorrow."
    return "OK", "Running."


def check_order(acc, order, limits=None):
    L = dict(LIMITS, **(limits or {}))
    no = lambda why: Decision(False, 0.0, why)
    if not acc.is_demo:
        return no("Not a demo account. The agents only trade the demo.")
    state, why = status(acc, L)
    if state != "OK":
        return no(why)
    side = order.side.lower()
    if side not in ("buy", "sell"):
        return no(f"Unknown side '{order.side}'.")
    if order.stop_loss is None:
        return no("Every trade needs a stop loss.")
    if (side == "buy" and order.stop_loss >= order.entry) or (side == "sell" and order.stop_loss <= order.entry):
        return no("The stop loss is on the wrong side of the entry.")
    if acc.trades_today >= L["max_trades_per_day"]:
        return no(f"Already {acc.trades_today} trades today (max {L['max_trades_per_day']}).")
    if len(acc.open_trades) >= L["max_open_trades"]:
        return no(f"Already {len(acc.open_trades)} open trades (max {L['max_open_trades']}).")
    for t in acc.open_trades:
        if t.get("symbol") == order.symbol and str(t.get("side", "")).lower() == side and float(t.get("profit", 0)) < 0:
            return no("No adding to a losing trade.")
    risk = L["risk_per_trade_pct"] * min(1.0, max(0.0, order.risk_factor))
    note = "OK."
    if acc.equity >= acc.start_balance * (1 + L["lock_profit_at_pct"] / 100):
        risk /= 2
        note = f"OK. Up {L['lock_profit_at_pct']}%+ since the start, so risk is halved."
    return Decision(True, risk, note)


def lots_for(equity, risk_pct, entry, stop_loss, money_per_unit_per_lot, lot_step=0.01, min_lot=0.01):
    """Lot size that loses about risk_pct of equity if the stop is hit. Rounded down.

    money_per_unit_per_lot: money won or lost per 1.0 price move per 1 lot
    (for example 100 for gold at 100 ounces per lot, in the account currency).
    Returns 0 when even the smallest lot would risk too much: skip that trade.
    """
    distance = abs(entry - stop_loss)
    if distance <= 0 or money_per_unit_per_lot <= 0 or risk_pct <= 0:
        return 0.0
    raw = equity * risk_pct / 100 / (distance * money_per_unit_per_lot)
    lots = math.floor(raw / lot_step + 1e-9) * lot_step
    return round(lots, 8) if lots >= min_lot - 1e-12 else 0.0
