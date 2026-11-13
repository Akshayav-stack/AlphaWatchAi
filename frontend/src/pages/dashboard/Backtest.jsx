import React, { useEffect, useState } from 'react';
import { Sliders, TrendingUp, AlertTriangle, CheckCircle, Percent, Play, RefreshCw } from 'lucide-react';
import {
  Badge,
  DataProvenanceFooter,
  LoadingSpinner,
  ErrorMessage,
  EmptyState,
} from '../../components/UIState';
import PlotlyChart from '../../components/PlotlyChart';
import { runBacktestApi } from '../../api/client';

export default function Backtest() {
  const [symbol, setSymbol] = useState('RELIANCE');
  const [initialCapital, setInitialCapital] = useState(100000);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    document.title = 'Backtest & Optimization — AlphaWatch AI';
    executeBacktest();
  }, []);

  async function executeBacktest() {
    try {
      setLoading(true);
      setError(null);
      const res = await runBacktestApi({
        symbol,
        initial_capital: Number(initialCapital),
      });
      setData(res);
    } catch (err) {
      setError(err.message || 'Backtest simulation failed.');
    } finally {
      setLoading(false);
    }
  }

  const equityCurve = data?.equity_curve || [];
  const trades = data?.trades || [];
  const asOf = data?.as_of || {
    date: new Date().toISOString().split('T')[0],
    source: 'Walk-Forward Chronological Backtest (Next-Day Open Settlement)',
  };

  // Build Plotly chart data from real backtest points
  const dates = equityCurve.map((pt) => pt.date);
  const portVals = equityCurve.map((pt) => pt.portfolio);
  const benchVals = equityCurve.map((pt) => pt.benchmark);

  const chartData = [
    {
      x: dates,
      y: portVals,
      type: 'scatter',
      mode: 'lines',
      name: `${symbol} RF Model (T+1 Open + Friction)`,
      line: { color: '#3B82F6', width: 2.5 },
    },
    {
      x: dates,
      y: benchVals,
      type: 'scatter',
      mode: 'lines',
      name: `${symbol} Buy & Hold Baseline`,
      line: { color: '#94A3B8', width: 1.5, dash: 'dot' },
    },
  ];

  const chartLayout = {
    yaxis: { title: 'Equity (₹)', gridcolor: '#1E293B' },
    xaxis: { gridcolor: '#1E293B' },
    legend: { orientation: 'h', y: -0.2, font: { color: '#94A3B8', size: 10 } },
    margin: { l: 60, r: 20, t: 30, b: 60 },
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white">Strategy Backtest & Execution Engine</h2>
          <p className="text-xs text-slate-400">
            Next-day Open fills (zero lookahead) with statutory Indian taxes, brokerage, and slippage
          </p>
        </div>
        <Badge variant="primary" label="ZERO LOOKAHEAD" sublabel="NEXT-DAY OPEN FILLS" />
      </div>

      {/* Control Bar */}
      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-slate-400 font-semibold">Security:</label>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-white font-semibold focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="RELIANCE">RELIANCE — Reliance Industries</option>
              <option value="TCS">TCS — Tata Consultancy Services</option>
              <option value="INFY">INFY — Infosys Ltd</option>
              <option value="HDFCBANK">HDFCBANK — HDFC Bank</option>
              <option value="ICICIBANK">ICICIBANK — ICICI Bank</option>
              <option value="ITC">ITC — ITC Ltd</option>
              <option value="SBIN">SBIN — State Bank of India</option>
              <option value="TATASTEEL">TATASTEEL — Tata Steel</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-slate-400 font-semibold">Capital (₹):</label>
            <input
              type="number"
              step="10000"
              value={initialCapital}
              onChange={(e) => setInitialCapital(e.target.value)}
              className="w-28 bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-white font-mono focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        <button
          onClick={executeBacktest}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm transition-all disabled:opacity-50"
        >
          {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
          <span>{loading ? 'Simulating...' : 'Run Simulation'}</span>
        </button>
      </div>

      {error && <ErrorMessage message={error} onRetry={executeBacktest} />}

      {loading ? (
        <LoadingSpinner text="Running historical walk-forward simulation with T+1 open fills..." />
      ) : data ? (
        <div className="space-y-6">
          {/* Top Performance Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Model CAGR
              </span>
              <div className="text-2xl font-black text-emerald-400 font-mono">
                +{(Number(data.cagr || 0) * 100).toFixed(2)}%
              </div>
              <span className="text-[11px] text-slate-500 block">
                Benchmark: +{(Number(data.benchmark_cagr || 0) * 100).toFixed(2)}%
              </span>
            </div>

            <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Sharpe Ratio
              </span>
              <div className="text-2xl font-black text-white font-mono">
                {Number(data.sharpe_ratio || 0).toFixed(2)}
              </div>
              <span className="text-[11px] text-slate-500 block">Risk-free rate: 6.5% (RBI repo)</span>
            </div>

            <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Max Drawdown
              </span>
              <div className="text-2xl font-black text-rose-400 font-mono">
                {(Number(data.max_drawdown || 0) * 100).toFixed(2)}%
              </div>
              <span className="text-[11px] text-slate-500 block">Positive peak-to-trough loss</span>
            </div>

            <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Trade Win Rate
              </span>
              <div className="text-2xl font-black text-blue-400 font-mono">
                {(Number(data.win_rate || 0) * 100).toFixed(1)}%
              </div>
              <span className="text-[11px] text-slate-500 block">
                Total completed trades: {data.total_trades || trades.length}
              </span>
            </div>
          </div>

          {/* Honest Verdict Card */}
          {data.honest_verdict && (
            <div className="p-4 bg-slate-900/60 border border-blue-900/40 rounded-xl space-y-1.5 text-xs">
              <div className="flex items-center gap-2 text-blue-400 font-bold uppercase tracking-wider">
                <CheckCircle className="w-4 h-4" />
                <span>Honest Quantitative Assessment (Zero Overfitting):</span>
              </div>
              <p className="text-slate-300 leading-relaxed font-sans">{data.honest_verdict}</p>
            </div>
          )}

          {/* Interactive Equity Curve Chart */}
          <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Equity Curve vs Buy & Hold Benchmark
            </h3>
            <div className="h-80">
              <PlotlyChart data={chartData} layout={chartLayout} />
            </div>
          </div>

          {/* Execution Trade Log */}
          {trades.length > 0 && (
            <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Historical Simulated Orders (First 10)
              </h3>
              <div className="overflow-x-auto border border-slate-800/80 rounded-xl bg-slate-950">
                <table className="w-full text-left text-xs whitespace-nowrap font-mono">
                  <thead className="bg-slate-900/90 text-slate-400 font-semibold border-b border-slate-800 uppercase text-[10px] tracking-wider">
                    <tr>
                      <th className="py-2.5 px-3">Date</th>
                      <th className="py-2.5 px-3">Action</th>
                      <th className="py-2.5 px-3">Fill Price (₹)</th>
                      <th className="py-2.5 px-3">Quantity</th>
                      <th className="py-2.5 px-3">P&L (₹)</th>
                      <th className="py-2.5 px-3">Friction (STT+Brokerage)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-200">
                    {trades.slice(0, 10).map((t, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                        <td className="py-2 px-3 text-slate-400">{t.date}</td>
                        <td className="py-2 px-3">
                          <Badge variant={t.action === 'BUY' ? 'buy' : 'sell'} label={t.action} />
                        </td>
                        <td className="py-2 px-3">₹{Number(t.price).toFixed(2)}</td>
                        <td className="py-2 px-3">{t.quantity}</td>
                        <td
                          className={`py-2 px-3 font-semibold ${
                            (t.pnl || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {(t.pnl || 0) >= 0 ? '+' : ''}₹{Number(t.pnl || 0).toFixed(2)}
                        </td>
                        <td className="py-2 px-3 text-slate-400">₹{Number(t.cost || 0).toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      ) : null}

      <DataProvenanceFooter
        source={asOf.source}
        asOf={asOf.date}
        status="Next-Day Open Settlement & Realized Transaction Friction"
      />
    </div>
  );
}
