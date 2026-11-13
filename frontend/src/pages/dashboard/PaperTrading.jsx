import React, { useState, useEffect } from 'react';
import { DollarSign, RefreshCw, AlertCircle, CheckCircle, ArrowRight, Trash2 } from 'lucide-react';
import {
  Badge,
  DataProvenanceFooter,
  LoadingSpinner,
  ErrorMessage,
  EmptyState,
} from '../../components/UIState';
import {
  getPaperTradingApi,
  executePaperOrderApi,
  resetPaperTradingApi,
  getOnboardingDataApi,
} from '../../api/client';

export default function PaperTrading() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [orderLoading, setOrderLoading] = useState(false);
  const [error, setError] = useState(null);
  const [orderSuccess, setOrderSuccess] = useState(null);

  // Form State
  const [symbol, setSymbol] = useState('RELIANCE');
  const [action, setAction] = useState('BUY');
  const [quantity, setQuantity] = useState(10);
  const [price, setPrice] = useState(2500.0);
  const [supportedSymbols, setSupportedSymbols] = useState([]);

  useEffect(() => {
    document.title = 'Simulated Paper Trading — AlphaWatch AI';
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);
      const [paperRes, onbRes] = await Promise.all([
        getPaperTradingApi(),
        getOnboardingDataApi().catch(() => null),
      ]);
      setData(paperRes);
      if (onbRes?.symbols) {
        setSupportedSymbols(onbRes.symbols);
      }
    } catch (err) {
      setError(err.message || 'Failed to load paper trading account.');
    } finally {
      setLoading(false);
    }
  }

  async function handleOrder(e) {
    if (e) e.preventDefault();
    setOrderLoading(true);
    setError(null);
    setOrderSuccess(null);

    try {
      const res = await executePaperOrderApi({
        symbol,
        action,
        quantity: Math.floor(Number(quantity)),
        price: Number(price),
        notes: `Simulated ${action} via UI`,
      });
      setOrderSuccess(res.message || 'Order executed successfully.');
      // Refresh balances and positions
      const updated = await getPaperTradingApi();
      setData(updated);
    } catch (err) {
      setError(err.message || 'Order execution failed.');
    } finally {
      setOrderLoading(false);
    }
  }

  async function handleReset() {
    if (!window.confirm('Reset virtual paper trading ledger back to ₹10,00,000 initial cash?')) {
      return;
    }
    try {
      setLoading(true);
      setError(null);
      await resetPaperTradingApi();
      setOrderSuccess('Paper balance reset to ₹10,00,000 cash.');
      const updated = await getPaperTradingApi();
      setData(updated);
    } catch (err) {
      setError(err.message || 'Failed to reset paper account.');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <LoadingSpinner text="Loading paper ledger and open positions..." />;
  }

  const positions = data?.positions || [];
  const trades = data?.trades || [];
  const cashBalance = data?.cash_balance ?? 1000000;
  const investedValue = data?.invested_value ?? 0;
  const totalPnl = data?.total_pnl ?? 0;
  const totalPnlPct = data?.total_pnl_pct ?? 0;
  const asOf = data?.as_of || {
    date: new Date().toISOString().split('T')[0],
    source: 'Paper Trading Engine (Simulated Orders with 0.1% Friction)',
  };

  const isProfitable = totalPnl >= 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white">Simulated Paper Trading Workstation</h2>
          <p className="text-xs text-slate-400">
            Execute virtual simulated orders against latest saved NSE closing data (zero broker code)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="primary" label="VIRTUAL SIMULATION" sublabel="NO REAL MONEY" />
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-rose-300 hover:text-white bg-rose-950/60 hover:bg-rose-900/60 border border-rose-800/60 rounded-lg transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Reset Ledger</span>
          </button>
        </div>
      </div>

      {error && <ErrorMessage message={error} onRetry={() => setError(null)} />}
      {orderSuccess && (
        <div className="p-3 bg-emerald-950/40 border border-emerald-800/60 rounded-xl text-xs text-emerald-300 flex items-center gap-2">
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          <span>{orderSuccess}</span>
        </div>
      )}

      {/* Ledger Balances */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Available Virtual Cash
          </span>
          <div className="text-2xl font-black text-white font-mono">
            ₹{cashBalance.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <span className="text-[10px] text-slate-500">Starting capital: ₹10,00,000.00</span>
        </div>
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Invested Paper Equity
          </span>
          <div className="text-2xl font-black text-blue-400 font-mono">
            ₹{investedValue.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <span className="text-[10px] text-slate-500">{positions.length} open position(s)</span>
        </div>
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Total Paper P&L
          </span>
          <div
            className={`text-2xl font-black font-mono ${
              isProfitable ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {isProfitable ? '+' : ''}₹{totalPnl.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <span className="text-[10px] text-slate-400">
            {isProfitable ? '+' : ''}{totalPnlPct.toFixed(2)}% net virtual return
          </span>
        </div>
      </div>

      {/* Order Placement Form */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4">
        <h3 className="text-sm font-bold text-white">Place Simulated Order</h3>
        <form onSubmit={handleOrder} className="grid grid-cols-1 sm:grid-cols-5 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Symbol</label>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:ring-1 focus:ring-blue-500 font-semibold"
            >
              {supportedSymbols.length > 0 ? (
                supportedSymbols.map((s) => (
                  <option key={s.symbol} value={s.symbol}>
                    {s.symbol}
                  </option>
                ))
              ) : (
                <>
                  <option value="RELIANCE">RELIANCE</option>
                  <option value="TCS">TCS</option>
                  <option value="HDFCBANK">HDFCBANK</option>
                  <option value="INFY">INFY</option>
                  <option value="ICICIBANK">ICICIBANK</option>
                </>
              )}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Action</label>
            <select
              value={action}
              onChange={(e) => setAction(e.target.value)}
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:ring-1 focus:ring-blue-500 font-semibold"
            >
              <option value="BUY">BUY (Long Position)</option>
              <option value="SELL">SELL (Reduce Position)</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Quantity</label>
            <input
              type="number"
              min="1"
              step="1"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white font-mono focus:outline-none focus:ring-1 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Price (₹)</label>
            <input
              type="number"
              min="0.05"
              step="0.05"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white font-mono focus:outline-none focus:ring-1 focus:ring-blue-500"
              required
            />
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={orderLoading}
              className="w-full py-2 px-4 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm transition-all disabled:opacity-50"
            >
              {orderLoading ? 'Executing...' : 'Execute Order'}
            </button>
          </div>
        </form>
        <span className="text-[10px] text-slate-500 block">
          * 0.1% statutory friction (Brokerage + STT + Turnover Tax) is automatically factored into net cash debits/credits.
        </span>
      </div>

      {/* Open Positions Table */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
        <h3 className="text-sm font-bold text-white">Open Paper Positions ({positions.length})</h3>
        {positions.length === 0 ? (
          <EmptyState
            title="No Open Positions"
            description="Your paper portfolio currently holds 100% cash. Place a simulated BUY order above to begin."
          />
        ) : (
          <div className="overflow-x-auto border border-slate-800/80 rounded-xl bg-slate-950">
            <table className="w-full text-left text-xs whitespace-nowrap font-mono">
              <thead className="bg-slate-900/90 text-slate-400 font-semibold border-b border-slate-800 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">Symbol</th>
                  <th className="py-2.5 px-3">Shares</th>
                  <th className="py-2.5 px-3">Avg Cost (₹)</th>
                  <th className="py-2.5 px-3">Saved Close (₹)</th>
                  <th className="py-2.5 px-3">Position Value (₹)</th>
                  <th className="py-2.5 px-3">Unrealized P&L</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {positions.map((p, idx) => {
                  const pnl = Number(p.pnl || 0);
                  const isPos = pnl >= 0;
                  return (
                    <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                      <td className="py-2.5 px-3 font-bold text-white">{p.symbol}</td>
                      <td className="py-2.5 px-3">{p.quantity}</td>
                      <td className="py-2.5 px-3">₹{Number(p.buy_price || 0).toFixed(2)}</td>
                      <td className="py-2.5 px-3">₹{Number(p.current_price || p.buy_price || 0).toFixed(2)}</td>
                      <td className="py-2.5 px-3">₹{Number(p.current_value || 0).toFixed(2)}</td>
                      <td className={`py-2.5 px-3 font-semibold ${isPos ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {isPos ? '+' : ''}₹{pnl.toFixed(2)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Execution Trade History Table */}
      {trades.length > 0 && (
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
          <h3 className="text-sm font-bold text-white">Execution Ledger History ({trades.length} orders)</h3>
          <div className="overflow-x-auto border border-slate-800/80 rounded-xl bg-slate-950">
            <table className="w-full text-left text-xs whitespace-nowrap font-mono">
              <thead className="bg-slate-900/90 text-slate-400 font-semibold border-b border-slate-800 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">Order ID</th>
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Symbol</th>
                  <th className="py-2.5 px-3">Action</th>
                  <th className="py-2.5 px-3">Quantity</th>
                  <th className="py-2.5 px-3">Fill Price</th>
                  <th className="py-2.5 px-3">Friction (₹)</th>
                  <th className="py-2.5 px-3">Net Cash Flow</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {trades.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-2 px-3 text-slate-400">#{t.id}</td>
                    <td className="py-2 px-3 text-slate-300">{t.trade_date}</td>
                    <td className="py-2 px-3 font-bold text-white">{t.symbol}</td>
                    <td className="py-2 px-3">
                      <Badge variant={t.action === 'BUY' ? 'buy' : 'sell'} label={t.action} />
                    </td>
                    <td className="py-2 px-3">{t.quantity}</td>
                    <td className="py-2 px-3">₹{Number(t.price).toFixed(2)}</td>
                    <td className="py-2 px-3 text-slate-400">₹{Number(t.brokerage_stt).toFixed(2)}</td>
                    <td
                      className={`py-2 px-3 font-semibold ${
                        t.action === 'BUY' ? 'text-rose-400' : 'text-emerald-400'
                      }`}
                    >
                      {t.action === 'BUY' ? '-' : '+'}₹{Number(t.net_amount).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <DataProvenanceFooter
        source={asOf.source}
        asOf={asOf.date}
        status="Virtual SQLite Ledger (Isolated Session)"
      />
    </div>
  );
}
