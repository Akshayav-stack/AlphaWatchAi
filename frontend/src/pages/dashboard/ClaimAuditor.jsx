import React, { useState, useEffect } from 'react';
import { FileText, CheckCircle, AlertTriangle, ShieldCheck, Search, RefreshCw } from 'lucide-react';
import {
  Badge,
  DataProvenanceFooter,
  LoadingSpinner,
  ErrorMessage,
  EmptyState,
} from '../../components/UIState';
import { runClaimAuditorApi } from '../../api/client';

export default function ClaimAuditor() {
  const [claimedWinRate, setClaimedWinRate] = useState(80);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    document.title = 'Claim Auditor & Verification — AlphaWatch AI';
    handleAudit();
  }, []);

  async function handleAudit(e) {
    if (e) e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const res = await runClaimAuditorApi({
        claimed_win_rate: Number(claimedWinRate),
      });
      setData(res);
    } catch (err) {
      setError(err.message || 'Audit execution failed.');
    } finally {
      setLoading(false);
    }
  }

  const asOf = data?.as_of || {
    date: new Date().toISOString().split('T')[0],
    source: '100 Historical Daily Signal Evaluations (EOD Settlement Audit)',
  };

  const auditTable = data?.audit_table || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white">Algorithmic Claim Auditor</h2>
          <p className="text-xs text-slate-400">
            Empirical verification of trading claims against realized forward returns with realistic transaction costs
          </p>
        </div>
        <Badge variant="primary" label="EMPIRICAL REPLAY" sublabel="BRIER CALIBRATED" />
      </div>

      {/* Audit Input Form */}
      <form onSubmit={handleAudit} className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4">
        <h3 className="text-sm font-bold text-white">Audit a Promotional Strategy Claim</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Claimed Strategy Win Rate</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="10"
                max="99"
                value={claimedWinRate}
                onChange={(e) => setClaimedWinRate(Number(e.target.value))}
                className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white font-mono focus:outline-none focus:ring-1 focus:ring-blue-500"
                required
              />
              <span className="text-xs text-slate-400 font-bold">%</span>
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Target Evaluation Benchmark</label>
            <select className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:ring-1 focus:ring-blue-500">
              <option>Walk-Forward Next-Day Open Fills (NSE EOD)</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 px-4 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              {loading ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Search className="w-3.5 h-3.5" />
              )}
              <span>{loading ? 'Auditing Records...' : 'Run Empirical Audit'}</span>
            </button>
          </div>
        </div>
      </form>

      {error && <ErrorMessage message={error} onRetry={handleAudit} />}

      {loading ? (
        <LoadingSpinner text="Replaying 100 historical walk-forward signals against bhavcopy settlement..." />
      ) : data ? (
        <div className="space-y-6">
          {/* Audit Verdict Banner */}
          <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 font-semibold uppercase">Audit Verdict:</span>
                <Badge
                  variant={data.verdict?.toLowerCase().includes('consistent') ? 'low' : 'medium'}
                  label={data.verdict?.split('(')[0]?.trim() || 'AUDITED'}
                />
              </div>
              <span className="text-xs text-slate-400 font-mono">
                Audited Sample: {data.total_audited || 100} Historical Signals
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs font-mono">
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
                <span className="text-slate-400 block text-[10px]">Claimed Win Rate</span>
                <span className="text-base font-bold text-slate-200">{data.claimed_win_rate}%</span>
              </div>
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
                <span className="text-slate-400 block text-[10px]">Realized Win Rate (Post-Costs)</span>
                <span className="text-base font-bold text-amber-400">{data.realized_win_rate}%</span>
              </div>
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
                <span className="text-slate-400 block text-[10px]">Statistical Brier Score</span>
                <span className="text-base font-bold text-emerald-400">
                  {data.brier_score} (Calibrated)
                </span>
              </div>
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
                <span className="text-slate-400 block text-[10px]">Alpha Over Random (50%)</span>
                <span className="text-base font-bold text-blue-400">
                  +{data.alpha_over_random}%
                </span>
              </div>
            </div>

            <div className="p-3 bg-slate-950/70 rounded-lg text-xs text-slate-300 border border-slate-800/80 leading-relaxed space-y-1">
              <p className="font-semibold text-slate-200 text-xs">Auditor Technical Assessment:</p>
              <p className="text-slate-400 text-xs">{data.verdict}</p>
            </div>
          </div>

          {/* Audited Signals Table */}
          {auditTable.length > 0 && (
            <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
              <h3 className="text-sm font-bold text-white">Audited Signals Verification Sample (Top 10)</h3>
              <div className="overflow-x-auto border border-slate-800/80 rounded-xl bg-slate-950">
                <table className="w-full text-left text-xs whitespace-nowrap font-mono">
                  <thead className="bg-slate-900/90 text-slate-400 font-semibold border-b border-slate-800 uppercase text-[10px] tracking-wider">
                    <tr>
                      <th className="py-2.5 px-3">Date</th>
                      <th className="py-2.5 px-3">Symbol</th>
                      <th className="py-2.5 px-3">Signal</th>
                      <th className="py-2.5 px-3">Model P(Up)</th>
                      <th className="py-2.5 px-3">Next-Day Return</th>
                      <th className="py-2.5 px-3">Net Return (Post-Friction)</th>
                      <th className="py-2.5 px-3">Audit Result</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-200">
                    {auditTable.map((row, idx) => {
                      const netRet = Number(row.realized_net_return || 0);
                      const isWin = netRet > 0;
                      return (
                        <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                          <td className="py-2 px-3 text-slate-400">{row.date}</td>
                          <td className="py-2 px-3 font-bold text-white">{row.symbol}</td>
                          <td className="py-2 px-3">
                            <Badge variant="buy" label={row.signal} />
                          </td>
                          <td className="py-2 px-3 text-blue-400">
                            {(Number(row.calibrated_prob || 0) * 100).toFixed(1)}%
                          </td>
                          <td className="py-2 px-3">
                            {(Number(row.next_day_return || 0) * 100).toFixed(2)}%
                          </td>
                          <td
                            className={`py-2 px-3 font-semibold ${
                              isWin ? 'text-emerald-400' : 'text-rose-400'
                            }`}
                          >
                            {isWin ? '+' : ''}{(netRet * 100).toFixed(2)}%
                          </td>
                          <td className="py-2 px-3">
                            <Badge
                              variant={isWin ? 'buy' : 'sell'}
                              label={isWin ? 'WIN' : 'LOSS'}
                            />
                          </td>
                        </tr>
                      );
                    })}
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
        status="Brier Score Decomposition & Friction Replay"
      />
    </div>
  );
}
