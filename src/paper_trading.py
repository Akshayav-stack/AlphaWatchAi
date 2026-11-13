"""
AlphaWatch AI — Simulated Paper Trading Engine
ASTRAQUANT X 2026

Simulated paper execution using latest saved NSE close prices:
  - Starting virtual capital: ₹1,000,000 (10 Lakhs INR)
  - Long-only execution (No margin shorting of cash equities)
  - Realistic Indian equity friction:
      * Brokerage: 0.03%
      * STT: 0.10% delivery turnover
      * SEBI / Exchange turnover / GST: ~0.02%
      * Total friction = 0.15% per trade
  - Strict order validation (sufficient cash for BUY, sufficient position for SELL)
  - Computes real-time mark-to-market valuations, unrealized/realized P&L, and portfolio returns
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from src.data_loader import load_prices

STARTING_VIRTUAL_CASH = 1000000.0  # ₹10,00,000
FRICTION_RATE = 0.0015             # 0.15% (Brokerage + STT + Taxes)


@dataclass
class PaperHoldingItem:
    symbol: str
    quantity: int
    avg_buy_price: float
    current_price: float
    invested_value: float
    current_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    weight_pct: float


@dataclass
class PaperPortfolioSummary:
    starting_cash: float
    available_cash: float
    invested_equity: float
    total_portfolio_value: float
    total_pnl: float
    total_return_pct: float
    realized_pnl: float
    unrealized_pnl: float
    total_fees_paid: float
    total_trades_count: int
    open_positions: List[PaperHoldingItem] = field(default_factory=list)
    recent_trades: List[Dict[str, Any]] = field(default_factory=list)


def calculate_order_friction(quantity: int, price: float) -> float:
    """Calculates realistic brokerage, STT and regulatory charges."""
    turnover = quantity * price
    return round(turnover * FRICTION_RATE, 2)


def validate_paper_order(
    action: str,
    symbol: str,
    quantity: int,
    price: float,
    current_cash: float,
    current_holding_qty: int,
) -> Tuple[bool, str, float]:
    """
    Validates trade logic before placement.
    Returns: (is_valid, error_or_success_message, friction_amount)
    """
    if quantity <= 0:
        return False, "Quantity must be a positive whole integer.", 0.0
    if price <= 0.0:
        return False, "Price must be positive.", 0.0

    action = action.upper().strip()
    friction = calculate_order_friction(quantity, price)

    if action == "BUY":
        total_required = (quantity * price) + friction
        if total_required > current_cash:
            return (
                False,
                f"Insufficient virtual cash. Required: ₹{total_required:,.2f}, Available: ₹{current_cash:,.2f}",
                friction,
            )
        return True, "Valid Buy Order", friction

    elif action == "SELL":
        if current_holding_qty < quantity:
            return (
                False,
                f"Insufficient shares to sell. Held: {current_holding_qty}, Requested: {quantity}",
                friction,
            )
        return True, "Valid Sell Order", friction

    return False, f"Invalid action: {action}. Must be BUY or SELL.", 0.0


def compute_paper_portfolio(trades: List[Any]) -> PaperPortfolioSummary:
    """
    Computes virtual portfolio state from a list of user paper trade database entities.
    """
    cash = STARTING_VIRTUAL_CASH
    total_fees = 0.0
    realized_pnl = 0.0

    # Bookkeeping per symbol
    # Dict[symbol, List[Tuple[qty, cost_per_share]]]
    inventory: Dict[str, List[List[float]]] = {}
    trade_dicts: List[Dict[str, Any]] = []

    # Sort trades chronologically
    sorted_trades = sorted(trades, key=lambda t: t.id if hasattr(t, "id") else 0)

    for tr in sorted_trades:
        sym = tr.symbol.upper()
        act = tr.action.upper()
        qty = int(tr.quantity)
        px = float(tr.price)
        fee = float(tr.brokerage_stt if tr.brokerage_stt is not None else calculate_order_friction(qty, px))
        total_fees += fee

        if sym not in inventory:
            inventory[sym] = []

        if act == "BUY":
            cash -= (qty * px + fee)
            inventory[sym].append([qty, px])

        elif act == "SELL":
            proceeds = (qty * px - fee)
            cash += proceeds

            # FIFO cost-basis matching
            qty_to_match = qty
            cost_basis = 0.0
            while qty_to_match > 0 and inventory[sym]:
                batch = inventory[sym][0]
                batch_qty = batch[0]
                batch_px = batch[1]

                if batch_qty <= qty_to_match:
                    cost_basis += batch_qty * batch_px
                    qty_to_match -= batch_qty
                    inventory[sym].pop(0)
                else:
                    cost_basis += qty_to_match * batch_px
                    batch[0] -= qty_to_match
                    qty_to_match = 0

            trade_realized = (qty * px) - cost_basis - fee
            realized_pnl += trade_realized

        trade_dicts.append(
            {
                "id": getattr(tr, "id", None),
                "symbol": sym,
                "action": act,
                "quantity": qty,
                "price": round(px, 2),
                "brokerage_stt": round(fee, 2),
                "net_amount": round(getattr(tr, "net_amount", qty * px), 2),
                "trade_date": getattr(tr, "trade_date", ""),
                "notes": getattr(tr, "notes", ""),
            }
        )

    # Compute current open positions
    open_items: List[PaperHoldingItem] = []
    total_open_equity = 0.0

    for sym, lots in inventory.items():
        total_qty = sum(lot[0] for lot in lots)
        if total_qty > 0:
            total_cost = sum(lot[0] * lot[1] for lot in lots)
            avg_px = total_cost / total_qty

            # Get latest saved close
            current_px = avg_px
            try:
                res = load_prices(sym)
                df = res[0] if isinstance(res, tuple) else res
                if not df.empty and "Close" in df.columns:
                    current_px = float(df["Close"].iloc[-1])
            except Exception:
                pass

            cur_val = total_qty * current_px
            unreal_pnl = cur_val - total_cost
            unreal_pct = (unreal_pnl / total_cost * 100.0) if total_cost > 0 else 0.0

            total_open_equity += cur_val
            open_items.append(
                PaperHoldingItem(
                    symbol=sym,
                    quantity=int(total_qty),
                    avg_buy_price=round(avg_px, 2),
                    current_price=round(current_px, 2),
                    invested_value=round(total_cost, 2),
                    current_value=round(cur_val, 2),
                    unrealized_pnl=round(unreal_pnl, 2),
                    unrealized_pnl_pct=round(unreal_pct, 2),
                    weight_pct=0.0,
                )
            )

    total_portfolio_val = cash + total_open_equity
    for item in open_items:
        item.weight_pct = round((item.current_value / total_portfolio_val * 100.0) if total_portfolio_val > 0 else 0.0, 2)

    unrealized_total = sum(item.unrealized_pnl for item in open_items)
    total_net_pnl = (total_portfolio_val - STARTING_VIRTUAL_CASH)
    total_ret_pct = (total_net_pnl / STARTING_VIRTUAL_CASH) * 100.0

    return PaperPortfolioSummary(
        starting_cash=round(STARTING_VIRTUAL_CASH, 2),
        available_cash=round(cash, 2),
        invested_equity=round(total_open_equity, 2),
        total_portfolio_value=round(total_portfolio_val, 2),
        total_pnl=round(total_net_pnl, 2),
        total_return_pct=round(total_ret_pct, 2),
        realized_pnl=round(realized_pnl, 2),
        unrealized_pnl=round(unrealized_total, 2),
        total_fees_paid=round(total_fees, 2),
        total_trades_count=len(trade_dicts),
        open_positions=open_items,
        recent_trades=list(reversed(trade_dicts)),
    )
