import React, { useEffect, useState } from 'react';
import { CheckCircle, Sliders, ArrowUpRight, RefreshCw, BarChart2 } from 'lucide-react';
import {
  Badge,
  DataProvenanceFooter,
  LoadingSpinner,
  ErrorMessage,
  EmptyState,
} from '../../components/UIState';
import { getBuyCandidatesApi } from '../../api/client';

export default function BuyCandidates() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    document.title = 'Buy Candidates — AlphaWatch AI';
    fetchCandidates();
  }, []);

  async function fetchCandidates() {
    try {
      setLoading(true);
      setError(null);
      const res = await getBuyCandidatesApi();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load buy candidates.');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <LoadingSpinner text="Screening universe for calibrated buy candidates..." />;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={fetchCandidates} />;
  }

  const candidates = data?.candidates || [];
  const profile = data?.profile || 'Moderate';
  const asOf = data?.as_of || {
    date: new Date().toISOString().split('T')[0],
    source: 'Filtered by calibrated walk-forward threshold',
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white">Profile-Ranked Buy Candidates</h2>
          <p className="text-xs text-slate-400">
            Equities meeting profile BUY threshold parameters (ranked by descending forward probability)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant="primary"
            label={`${profile.toUpperCase()} PROFILE`}
            sublabel={
              profile === 'Conservative'
                ? 'BUY &ge; 0.65'
                : profile === 'Aggressive'
                ? 'BUY &ge; 0.55'
                : 'BUY &ge; 0.60'
            }
          />
          <button
            onClick={fetchCandidates}
            className="p-1.5 text-slate-400 hover:text-slate-200 transition-colors"
            title="Refresh Candidates"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {candidates.length === 0 ? (
        <EmptyState
          title="No BUY Candidates Found"
          description={`No securities in the current NSE bhavcopy universe meet the ${profile} BUY probability threshold. The model maintains discipline and recommends HOLD / cash.`}
        />
      ) : (
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300">
              Ranked Screening Universe ({candidates.length} opportunities)
            </span>
            <span className="text-[11px] font-mono text-slate-500">
              Stop-losses and position caps enforced
            </span>
          </div>

          <div className="overflow-x-auto border border-slate-800/80 rounded-xl bg-slate-950">
            <table className="w-full text-left text-xs whitespace-nowrap font-mono">
              <thead className="bg-slate-900/90 text-slate-400 font-semibold border-b border-slate-800 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">Rank</th>
                  <th className="py-2.5 px-3">Symbol</th>
                  <th className="py-2.5 px-3">Company Name</th>
                  <th className="py-2.5 px-3">Sector</th>
                  <th className="py-2.5 px-3">P(Up Direction)</th>
                  <th className="py-2.5 px-3">20d Volatility</th>
                  <th className="py-2.5 px-3">Max Position Size</th>
                  <th className="py-2.5 px-3">Stop-Loss</th>
                  <th className="py-2.5 px-3">Signal Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {candidates.map((c, idx) => (
                  <tr key={c.symbol} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-2.5 px-3 font-bold text-blue-400">#{idx + 1}</td>
                    <td className="py-2.5 px-3 font-bold text-white">{c.symbol}</td>
                    <td className="py-2.5 px-3 font-sans text-slate-300 text-xs">{c.name || c.symbol}</td>
                    <td className="py-2.5 px-3 font-sans text-slate-400 text-xs">{c.sector}</td>
                    <td className="py-2.5 px-3 font-bold text-emerald-400">
                      {Number(c.prob_pct || c.prob_up * 100).toFixed(1)}%
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">{c.volatility}</td>
                    <td className="py-2.5 px-3 text-slate-300">{c.max_position}</td>
                    <td className="py-2.5 px-3 text-rose-400 font-semibold">-{c.stop_loss}</td>
                    <td className="py-2.5 px-3">
                      <Badge variant="buy" label="BUY QUALIFIED" />
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
        status="Configured via PROFILES Dict"
      />
    </div>
  );
}
