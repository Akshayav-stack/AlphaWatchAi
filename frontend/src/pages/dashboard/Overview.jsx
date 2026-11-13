import React, { useEffect, useState } from 'react';
import {
  LayoutDashboard,
  TrendingUp,
  AlertTriangle,
  ShieldCheck,
  Database,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
} from 'lucide-react';
import {
  Badge,
  DataProvenanceFooter,
  LoadingSpinner,
  EmptyState,
  ErrorMessage,
} from '../../components/UIState';
import { getDashboardOverviewApi } from '../../api/client';

export default function Overview() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    document.title = 'Portfolio Overview — AlphaWatch AI';
    fetchOverview();
  }, []);

  async function fetchOverview() {
    try {
      setLoading(true);
      setError(null);
      const res = await getDashboardOverviewApi();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to fetch portfolio overview data.');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <LoadingSpinner text="Loading portfolio valuation and risk summary..." />;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={fetchOverview} />;
  }

  const valuation = data?.valuation || {};
  const riskSummary = data?.risk_summary || {};
  const profile = data?.profile || {};
  const holdingsTable = valuation.holdings_table || [];
  const concentrationAlerts = valuation.concentration_alerts || [];
  const riskTiers = riskSummary.risk_tiers || { low: 0, medium: 0, high: 0 };
  const asOf = data?.as_of || {
    date: new Date().toISOString().split('T')[0],
    source: 'NSE Bhavcopy Official Archives (Offline Model Pipeline)',
  };

  const isProfitable = (valuation.unrealized_pnl || 0) >= 0;

  return (
    <div className="space-y-6">
      {/* Top Banner if in Demo Preview Mode */}
      {data?.is_demo_preview && (
        <div className="p-3 bg-blue-950/40 border border-blue-800/50 rounded-xl flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-blue-300">
            <Layers className="w-4 h-4 flex-shrink-0" />
            <span>
              <strong>DEMO PREVIEW:</strong> Showing verified Moderate Balanced sample portfolio. Visit Onboarding to configure your custom holdings.
            </span>
          </div>
          <Badge variant="primary" label="DEMO PORTFOLIO" />
        </div>
      )}

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Portfolio Value */}
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Total Portfolio Value
          </span>
          <div className="text-2xl font-black text-white font-mono">
            ₹{(valuation.total_value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <span className="text-[11px] text-slate-500 block">
            Cost basis: ₹{(valuation.total_cost || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
          </span>
        </div>

        {/* Unrealized P&L */}
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Unrealized P&L
          </span>
          <div className="flex items-center gap-2">
            <span
              className={`text-2xl font-black font-mono ${isProfitable ? 'text-emerald-400' : 'text-rose-400'
                }`}
            >
              {isProfitable ? '+' : ''}₹
              {(valuation.unrealized_pnl || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <Badge
              variant={isProfitable ? 'buy' : 'sell'}
              label={isProfitable ? 'GAIN' : 'LOSS'}
              sublabel={`${(valuation.unrealized_pnl_pct || 0) > 0 ? '+' : ''}${(valuation.unrealized_pnl_pct || 0).toFixed(2)}%`}
            />
          </div>
          <span className="text-[11px] text-slate-500 block">Relative to entry cost basis</span>
        </div>

        {/* Concentration Alert Card */}
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Concentration Status
          </span>
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-slate-200">
              {concentrationAlerts.length > 0 ? 'Concentration Alert' : 'Balanced (&le;30%)'}
            </span>
            <Badge
              variant={concentrationAlerts.length > 0 ? 'high' : 'low'}
              label={concentrationAlerts.length > 0 ? 'SKEWED' : 'SAFE'}
            />
          </div>
          <span className="text-[11px] text-slate-400 truncate block">
            {concentrationAlerts.length > 0
              ? concentrationAlerts[0]
              : 'No single holding exceeds 30% concentration limit'}
          </span>
        </div>

        {/* Risk Distribution Card (Low / Med / High) - Top Right */}
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Holdings by Risk Tier
          </span>
          <div className="flex items-center gap-2 pt-1 font-mono">
            <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-950 text-emerald-300 border border-emerald-700/60">
              {riskTiers.low || 0} Low
            </span>
            <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-950 text-amber-300 border border-amber-700/60">
              {riskTiers.medium || 0} Med
            </span>
            <span className="px-2 py-0.5 rounded text-xs font-bold bg-rose-950 text-rose-300 border border-rose-700/60">
              {riskTiers.high || 0} High
            </span>
          </div>
          <span className="text-[11px] text-slate-500 block">
            Profile: <strong className="text-slate-300">{profile.suggested_profile || 'Moderate'}</strong>
          </span>
        </div>
      </div>

      {/* Concentration Warnings Strip if triggered */}
      {concentrationAlerts.length > 0 && (
        <div className="p-4 bg-amber-950/40 border border-amber-800/60 rounded-xl space-y-1 text-xs">
          <div className="flex items-center gap-2 font-bold text-amber-300">
            <AlertTriangle className="w-4 h-4" />
            <span>Concentration Limit Alert Triggered (&gt; 30% Single Asset Weight)</span>
          </div>
          <ul className="list-disc list-inside text-slate-300 text-[11px] space-y-0.5">
            {concentrationAlerts.map((alert, idx) => (
              <li key={idx}>{alert}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Holdings Table with Internal Horizontal Scrollbar */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white">Current Portfolio Holdings</h3>
            <p className="text-xs text-slate-400">Position weights, valuation, and concentration monitors</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="primary" label={`${holdingsTable.length} ASSETS`} />
            <button
              onClick={fetchOverview}
              className="p-1 text-slate-400 hover:text-slate-200 transition-colors"
              title="Refresh Valuation"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {holdingsTable.length === 0 ? (
          <EmptyState
            title="No Active Holdings"
            description="You have not added any securities yet. Go to Onboarding to load sample portfolios or input your holdings."
          />
        ) : (
          <div className="overflow-x-auto border border-slate-800/80 rounded-xl bg-slate-950">
            <table className="w-full text-left text-xs whitespace-nowrap font-mono">
              <thead className="bg-slate-900/90 text-slate-400 font-semibold border-b border-slate-800 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">Symbol</th>
                  <th className="py-2.5 px-3">Quantity</th>
                  <th className="py-2.5 px-3">Avg Buy Price (₹)</th>
                  <th className="py-2.5 px-3">Saved Close (₹)</th>
                  <th className="py-2.5 px-3">Current Value (₹)</th>
                  <th className="py-2.5 px-3">Weight (%)</th>
                  <th className="py-2.5 px-3">P&L (₹)</th>
                  <th className="py-2.5 px-3">P&L (%)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {holdingsTable.map((h, idx) => {
                  const isPos = (h.pnl || 0) >= 0;
                  const isHighWeight = (h.weight_pct || 0) > 30.0;

                  return (
                    <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                      <td className="py-2.5 px-3 font-bold text-white">{h.symbol}</td>
                      <td className="py-2.5 px-3">{h.quantity}</td>
                      <td className="py-2.5 px-3">₹{Number(h.buy_price).toFixed(2)}</td>
                      <td className="py-2.5 px-3">₹{Number(h.current_price).toFixed(2)}</td>
                      <td className="py-2.5 px-3">₹{Number(h.current_value).toFixed(2)}</td>
                      <td className="py-2.5 px-3">
                        <span className={isHighWeight ? 'text-amber-400 font-bold' : 'text-slate-300'}>
                          {Number(h.weight_pct).toFixed(1)}%
                        </span>
                        {isHighWeight && <span className="ml-1 text-[10px] text-amber-400">&gt;30%</span>}
                      </td>
                      <td className={`py-2.5 px-3 font-semibold ${isPos ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {isPos ? '+' : ''}₹{Number(h.pnl).toFixed(2)}
                      </td>
                      <td className="py-2.5 px-3">
                        <Badge
                          variant={isPos ? 'buy' : 'sell'}
                          label={isPos ? 'UP' : 'DOWN'}
                          sublabel={`${isPos ? '+' : ''}${Number(h.pnl_pct).toFixed(2)}%`}
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <DataProvenanceFooter
        source={asOf.source}
        asOf={asOf.date}
        status="Daily Saved Bhavcopy (Offline)"
      />
    </div>
  );
}
