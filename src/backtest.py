"""
AlphaWatch AI — Backtesting & Strategy Execution Engine
ASTRAQUANT X 2026

Simulates long-only equity strategies with zero lookahead bias:
  - Signals generated at Day t Close
  - Executed at Day t+1 Open
  - Real-world Indian equity transaction friction:
      * Brokerage: 0.03% (₹20 or 0.03% capped)
      * STT (Securities Transaction Tax): 0.1% delivery buy & sell
      * Exchange turnover, SEBI charges, Stamp duty & GST: ~0.02%
      * Slippage: 0.05%
      * Total round-trip friction ~0.35% (0.175% to 0.20% per trade)
  - Strict long-only (no shorting of cash equities)
  - Comprehensive performance metrics: CAGR, Sharpe, Sortino, Max Drawdown, Win Rate, Profit Factor
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.data_loader import load_prices


@dataclass
class Trade:
    """Represents a simulated executed trade."""
    symbol: str
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    quantity: int
    gross_pnl: float
    net_pnl: float
    return_pct: float
    holding_days: int
    exit_reason: str


@dataclass
class BacktestResult:
    """Complete results and metrics of a backtest run."""
    symbol: str
    start_date: str
    end_date: str
    total_bars: int
    initial_capital: float
    final_equity: float
    total_return_pct: float
    cagr_pct: float
    benchmark_return_pct: float
    annualized_volatility_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    max_drawdown_duration_days: int
    win_rate_pct: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    exposure_pct: float
    total_fees_paid: float
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    trades: List[Dict[str, Any]] = field(default_factory=list)


def run_backtest(
    df: pd.DataFrame,
    symbol: str = "PORTFOLIO",
    initial_capital: float = 100000.0,
    fee_bps: float = 20.0,  # 20 basis points (0.20%) friction per trade
    risk_free_rate: float = 0.065,  # 6.5% Indian 91-day T-Bill rate
    signal_col: str = "Signal",
) -> BacktestResult:
    """
    Executes a long-only backtest on a DataFrame with 'Date', 'Open', 'Close' and a 'Signal' column.
    
    Signal definition:
      1: Long / Buy (hold equity)
      0: Cash / Neutral (hold cash)
    
    Execution logic:
      - Signal evaluated at Close(t)
      - Trade entered/exited at Open(t+1)
      - Cash earns 0% while out of market
    """
    if df.empty or len(df) < 5:
        return _empty_result(symbol, initial_capital)

    df_bt = df.copy().reset_index(drop=True)
    if "Date" not in df_bt.columns or "Open" not in df_bt.columns or "Close" not in df_bt.columns:
        raise ValueError("DataFrame must contain 'Date', 'Open', and 'Close' columns")

    if signal_col not in df_bt.columns:
        # Default simple strategy: Buy if 20-day SMA > 50-day SMA if not provided
        df_bt["sma20"] = df_bt["Close"].rolling(20).mean()
        df_bt["sma50"] = df_bt["Close"].rolling(50).mean()
        df_bt[signal_col] = (df_bt["sma20"] > df_bt["sma50"]).astype(int)

    n_bars = len(df_bt)
    cash = initial_capital
    position_qty = 0
    entry_price = 0.0
    entry_date = ""
    entry_bar = 0
    total_fees = 0.0

    completed_trades: List[Trade] = []
    equity_series: List[Dict[str, Any]] = []

    fee_multiplier = fee_bps / 10000.0  # e.g., 0.0020 for 20 bps

    # Benchmark Buy & Hold on Day 1 Open
    benchmark_start_price = float(df_bt["Open"].iloc[0])

    for i in range(n_bars):
        current_date = str(df_bt["Date"].iloc[i])
        current_open = float(df_bt["Open"].iloc[i])
        current_close = float(df_bt["Close"].iloc[i])

        # Execute pending orders based on signal from PREVIOUS bar (t-1)
        if i > 0:
            prev_signal = int(df_bt[signal_col].iloc[i - 1])
            
            # Need to enter Long position
            if prev_signal == 1 and position_qty == 0:
                # Buy at today's Open
                exec_price = current_open * (1.0 + fee_multiplier)  # Include slippage & fee
                affordable_qty = int(cash // exec_price)
                if affordable_qty > 0:
                    trade_cost = affordable_qty * exec_price
                    fee = affordable_qty * current_open * fee_multiplier
                    total_fees += fee
                    cash -= trade_cost
                    position_qty = affordable_qty
                    entry_price = current_open
                    entry_date = current_date
                    entry_bar = i

            # Need to exit Long position
            elif prev_signal == 0 and position_qty > 0:
                # Sell at today's Open
                exec_price = current_open * (1.0 - fee_multiplier)
                trade_proceeds = position_qty * exec_price
                fee = position_qty * current_open * fee_multiplier
                total_fees += fee
                cash += trade_proceeds

                gross_pnl = (current_open - entry_price) * position_qty
                net_pnl = trade_proceeds - (position_qty * entry_price * (1.0 + fee_multiplier))
                ret_pct = ((current_open - entry_price) / entry_price) * 100.0

                completed_trades.append(
                    Trade(
                        symbol=symbol,
                        entry_date=entry_date,
                        entry_price=round(entry_price, 2),
                        exit_date=current_date,
                        exit_price=round(current_open, 2),
                        quantity=position_qty,
                        gross_pnl=round(gross_pnl, 2),
                        net_pnl=round(net_pnl, 2),
                        return_pct=round(ret_pct, 2),
                        holding_days=i - entry_bar,
                        exit_reason="Signal Exit",
                    )
                )
                position_qty = 0
                entry_price = 0.0

        # Mark-to-market at today's Close
        current_equity = cash + (position_qty * current_close)
        benchmark_equity = initial_capital * (current_close / benchmark_start_price)

        equity_series.append(
            {
                "date": current_date,
                "equity": round(current_equity, 2),
                "benchmark_equity": round(benchmark_equity, 2),
                "in_position": position_qty > 0,
            }
        )

    # If still in position at the end, close it at final close
    if position_qty > 0:
        final_close = float(df_bt["Close"].iloc[-1])
        exec_price = final_close * (1.0 - fee_multiplier)
        proceeds = position_qty * exec_price
        gross_pnl = (final_close - entry_price) * position_qty
        net_pnl = proceeds - (position_qty * entry_price * (1.0 + fee_multiplier))
        ret_pct = ((final_close - entry_price) / entry_price) * 100.0
        total_fees += position_qty * final_close * fee_multiplier
        cash += proceeds

        completed_trades.append(
            Trade(
                symbol=symbol,
                entry_date=entry_date,
                entry_price=round(entry_price, 2),
                exit_date=str(df_bt["Date"].iloc[-1]),
                exit_price=round(final_close, 2),
                quantity=position_qty,
                gross_pnl=round(gross_pnl, 2),
                net_pnl=round(net_pnl, 2),
                return_pct=round(ret_pct, 2),
                holding_days=n_bars - 1 - entry_bar,
                exit_reason="End of Backtest Period",
            )
        )
        position_qty = 0

    final_equity = cash
    total_return_pct = ((final_equity - initial_capital) / initial_capital) * 100.0

    # Benchmark return
    final_benchmark_equity = equity_series[-1]["benchmark_equity"]
    benchmark_return_pct = ((final_benchmark_equity - initial_capital) / initial_capital) * 100.0

    # Calculate returns series for metrics
    equity_values = pd.Series([pt["equity"] for pt in equity_series])
    daily_returns = equity_values.pct_change().dropna()

    # Drawdown series
    cumulative_max = equity_values.cummax()
    drawdown_series = (equity_values - cumulative_max) / cumulative_max
    max_drawdown_pct = abs(float(drawdown_series.min())) * 100.0 if not drawdown_series.empty else 0.0

    for i, pt in enumerate(equity_series):
        pt["drawdown_pct"] = round(float(drawdown_series.iloc[i]) * 100.0, 2)

    # CAGR calculation (assuming 250 trading days per year)
    years = max(n_bars / 250.0, 0.01)
    if final_equity > 0:
        cagr_pct = (((final_equity / initial_capital) ** (1.0 / years)) - 1.0) * 100.0
    else:
        cagr_pct = -100.0

    # Volatility and Sharpe/Sortino
    if len(daily_returns) > 1 and daily_returns.std() > 0:
        ann_vol = float(daily_returns.std() * np.sqrt(250)) * 100.0
        daily_rf = (1.0 + risk_free_rate) ** (1.0 / 250.0) - 1.0
        excess_daily_returns = daily_returns - daily_rf
        sharpe = float(np.sqrt(250) * excess_daily_returns.mean() / (daily_returns.std() + 1e-9))

        downside_returns = daily_returns[daily_returns < daily_rf] - daily_rf
        downside_dev = float(downside_returns.std() * np.sqrt(250)) if len(downside_returns) > 1 else 1e-6
        sortino = float((cagr_pct / 100.0 - risk_free_rate) / (downside_dev + 1e-6))
    else:
        ann_vol = 0.0
        sharpe = 0.0
        sortino = 0.0

    # Trade stats
    total_trades = len(completed_trades)
    winning_trades = sum(1 for t in completed_trades if t.net_pnl > 0)
    losing_trades = sum(1 for t in completed_trades if t.net_pnl <= 0)
    win_rate = (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0

    gross_profit = sum(t.net_pnl for t in completed_trades if t.net_pnl > 0)
    gross_loss = abs(sum(t.net_pnl for t in completed_trades if t.net_pnl < 0))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)

    in_market_bars = sum(1 for pt in equity_series if pt["in_position"])
    exposure_pct = (in_market_bars / n_bars * 100.0) if n_bars > 0 else 0.0

    trades_list = [
        {
            "symbol": t.symbol,
            "entry_date": t.entry_date,
            "entry_price": t.entry_price,
            "exit_date": t.exit_date,
            "exit_price": t.exit_price,
            "quantity": t.quantity,
            "net_pnl": t.net_pnl,
            "return_pct": t.return_pct,
            "holding_days": t.holding_days,
            "exit_reason": t.exit_reason,
        }
        for t in completed_trades
    ]

    return BacktestResult(
        symbol=symbol,
        start_date=str(df_bt["Date"].iloc[0]),
        end_date=str(df_bt["Date"].iloc[-1]),
        total_bars=n_bars,
        initial_capital=round(initial_capital, 2),
        final_equity=round(final_equity, 2),
        total_return_pct=round(total_return_pct, 2),
        cagr_pct=round(cagr_pct, 2),
        benchmark_return_pct=round(benchmark_return_pct, 2),
        annualized_volatility_pct=round(ann_vol, 2),
        sharpe_ratio=round(sharpe, 2),
        sortino_ratio=round(sortino, 2),
        max_drawdown_pct=round(max_drawdown_pct, 2),
        max_drawdown_duration_days=0,
        win_rate_pct=round(win_rate, 2),
        profit_factor=round(min(profit_factor, 99.9), 2),
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        exposure_pct=round(exposure_pct, 2),
        total_fees_paid=round(total_fees, 2),
        equity_curve=equity_series,
        trades=trades_list,
    )


def _empty_result(symbol: str, capital: float) -> BacktestResult:
    return BacktestResult(
        symbol=symbol,
        start_date="N/A",
        end_date="N/A",
        total_bars=0,
        initial_capital=capital,
        final_equity=capital,
        total_return_pct=0.0,
        cagr_pct=0.0,
        benchmark_return_pct=0.0,
        annualized_volatility_pct=0.0,
        sharpe_ratio=0.0,
        sortino_ratio=0.0,
        max_drawdown_pct=0.0,
        max_drawdown_duration_days=0,
        win_rate_pct=0.0,
        profit_factor=0.0,
        total_trades=0,
        winning_trades=0,
        losing_trades=0,
        exposure_pct=0.0,
        total_fees_paid=0.0,
        equity_curve=[],
        trades=[],
    )
