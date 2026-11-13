import React, { useEffect, useState } from 'react';
import { ShieldAlert, AlertTriangle, Info, TrendingDown, RefreshCw } from 'lucide-react';
import {
  Badge,
  DataProvenanceFooter,
  LoadingSpinner,
  ErrorMessage,
  EmptyState,
} from '../../components/UIState';
import PlotlyChart from '../../components/PlotlyChart';
import { getRiskAnalysisApi } from '../../api/client';

export default function Risk() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    document.title = 'Quantitative Risk & VaR — AlphaWatch AI';
    fetchRisk();
  }, []);

  async function fetchRisk() {
    try {
      setLoading(true);
      setError(null);
      const res = await getRiskAnalysisApi();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to compute portfolio risk.');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <LoadingSpinner text="Computing volatility, max drawdown, and positive-loss VaR..." />;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={fetchRisk} />;
  }

  const assetTable = data?.asset_risk_table || [];
  const asOf = data?.as_of || {
    date: new Date().toISOString().split('T')[0],
    source: 'Historical Close Return Distribution (Positive-Loss Convention)',
  };

  // Prepare Plotly Chart data: comparative bar chart of asset risk metrics
  const symbols = assetTable.map((a) => a.symbol);
  const vols = assetTable.map((a) => Number((a.volatility_20d * 100).toFixed(1)));
  const dds = assetTable.map((a) => Number((a.max_drawdown_1y * 100).toFixed(1)));
  const vars = assetTable.map((a) => Number((a.var_95_1d * 100).toFixed(2)));

  const chartData = [
    {
      x: symbols,
      y: vols,
      name: '20d Volatility (%)',
      type: 'bar',
      marker: { color: '#3B82F6' },
    },
    {
      x: symbols,
      y: dds,
      name: '1y Max Drawdown (%)',
      type: 'bar',
      marker: { color: '#F43F5E' },
    },
    {
      x: symbols,
      y: vars,
      name: '95% 1d VaR (%)',
      type: 'bar',
      marker: { color: '#F59E0B' },
    },
  ];

  const chartLayout = {
    barmode: 'group',
    title: {
      text: 'Comparative Asset Risk Breakdown (% Annualized & 1d Loss)',
      font: { color: '#E2E8F0', size: 12 },
    },
    legend: { font: { color: '#94A3B8' }, orientation: 'h', y: -0.2 },
    margin: { l: 40, r: 20, t: 30, b: 60 },
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white">Quantitative Risk & Tail Loss (VaR / CVaR)</h2>
          <p className="text-xs text-slate-400">
            Historical distribution analysis with tercile risk labeling and positive-loss conventions
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="primary" label="POSITIVE-LOSS CONVENTION" sublabel="L = -R &ge; 0" />
          <button
            onClick={fetchRisk}
            className="p-1.5 text-slate-400 hover:text-slate-200 transition-colors"
            title="Refresh Risk"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Portfolio Level Risk Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            20d Annualized Volatility
          </span>
          <div className="text-2xl font-black text-white font-mono">
            {Number(data?.portfolio_vol_20d || 0).toFixed(2)}%
          </div>
          <span className="text-[11px] text-slate-500 block">Weighted asset covariance</span>
        </div>

        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            1-Year Maximum Drawdown
          </span>
          <div className="text-2xl font-black text-rose-400 font-mono">
            {Number(data?.portfolio_max_dd_1y || 0).toFixed(2)}%
          </div>
          <span className="text-[11px] text-slate-500 block">Peak-to-trough positive loss</span>
        </div>

        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            95% 1-Day Historical VaR
          </span>
          <div className="text-2xl font-black text-amber-400 font-mono">
            {Number(data?.portfolio_var_95 || 0).toFixed(2)}%
          </div>
          <span className="text-[11px] text-slate-500 block">95% confidence 1-day threshold</span>
        </div>

        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            95% 1-Day CVaR (Expected Shortfall)
          </span>
          <div className="text-2xl font-black text-rose-400 font-mono">
            {Number(data?.portfolio_cvar_95 || 0).toFixed(2)}%
          </div>
          <span className="text-[11px] text-slate-500 block">Average loss in 5% worst tail</span>
        </div>
      </div>

      {/* Positive-Loss Convention Box */}
      <div className="p-4 bg-slate-900/40 border border-blue-900/40 rounded-xl text-xs text-slate-300 space-y-1">
        <div className="flex items-center gap-1.5 font-semibold text-blue-400">
          <Info className="w-4 h-4" />
          <span>Documented Positive-Loss Convention (ASTRAQUANT Standard)</span>
        </div>
        <p className="leading-relaxed text-[11px] text-slate-400">
          In standard quantitative risk reporting, loss distributions are framed positively: a VaR of {Number(data?.portfolio_var_95 || 1.5).toFixed(2)}% means there is a 95% statistical confidence that daily losses will not exceed {Number(data?.portfolio_var_95 || 1.5).toFixed(2)}% (where loss \(L = -R \ge 0\)). CVaR reflects the expected average loss in the 5% worst tail outcomes.
        </p>
      </div>

      {/* Plotly Chart Container */}
      {assetTable.length > 0 && (
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Risk Distribution by Asset
          </h3>
          <div className="h-72">
            <PlotlyChart data={chartData} layout={chartLayout} />
          </div>
        </div>
      )}

      {/* Asset-by-Asset Risk Breakdown Table */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4">
        <div className="border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white">Cross-Sectional Asset Risk Breakdown</h3>
          <p className="text-xs text-slate-400">Tercile ranking on 20-day historical volatility</p>
        </div>

        {assetTable.length === 0 ? (
          <EmptyState
            title="No Risk Breakdown"
            description="Add holdings to view cross-sectional asset risk metrics."
          />
        ) : (
          <div className="overflow-x-auto border border-slate-800/80 rounded-xl bg-slate-950">
            <table className="w-full text-left text-xs whitespace-nowrap font-mono">
              <thead className="bg-slate-900/90 text-slate-400 font-semibold border-b border-slate-800 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">Symbol</th>
                  <th className="py-2.5 px-3">Weight (%)</th>
                  <th className="py-2.5 px-3">20d Volatility</th>
                  <th className="py-2.5 px-3">1y Max Drawdown</th>
                  <th className="py-2.5 px-3">95% 1d VaR</th>
                  <th className="py-2.5 px-3">95% 1d CVaR</th>
                  <th className="py-2.5 px-3">Tercile Risk Tier</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {assetTable.map((r) => {
                  const label = (r.risk_label || 'Medium').toLowerCase();
                  return (
                    <tr key={r.symbol} className="hover:bg-slate-900/40 transition-colors">
                      <td className="py-2.5 px-3 font-bold text-white">{r.symbol}</td>
                      <td className="py-2.5 px-3">{Number(r.weight_pct || 0).toFixed(1)}%</td>
                      <td className="py-2.5 px-3">{(Number(r.volatility_20d || 0) * 100).toFixed(1)}%</td>
                      <td className="py-2.5 px-3 text-rose-400">
                        {(Number(r.max_drawdown_1y || 0) * 100).toFixed(1)}%
                      </td>
                      <td className="py-2.5 px-3 text-amber-400">
                        {(Number(r.var_95_1d || 0) * 100).toFixed(2)}%
                      </td>
                      <td className="py-2.5 px-3 text-rose-400">
                        {(Number(r.cvar_95_1d || 0) * 100).toFixed(2)}%
                      </td>
                      <td className="py-2.5 px-3">
                        <Badge
                          variant={label === 'low' ? 'low' : label === 'high' ? 'high' : 'medium'}
                          label={`${label.toUpperCase()} RISK`}
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
        status="ddof=1 Sample Volatility & Rolling Peak Max Drawdown"
      />
    </div>
  );
}
