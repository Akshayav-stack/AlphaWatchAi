import React, { useEffect, useState } from 'react';
import { TrendingUp, CheckCircle, Info, Sliders, RefreshCw, BarChart2 } from 'lucide-react';
import {
  Badge,
  DataProvenanceFooter,
  LoadingSpinner,
  ErrorMessage,
  EmptyState,
} from '../../components/UIState';
import { getPredictionsApi } from '../../api/client';

export default function Predictions() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    document.title = 'Predictions — AlphaWatch AI';
    fetchPredictions();
  }, []);

  async function fetchPredictions() {
    try {
      setLoading(true);
      setError(null);
      const res = await getPredictionsApi();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load model predictions.');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <LoadingSpinner text="Computing calibrated walk-forward probabilities..." />;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={fetchPredictions} />;
  }

  const predictions = data?.predictions || [];
  const profile = data?.profile || 'Moderate';
  const asOf = data?.as_of || {
    date: new Date().toISOString().split('T')[0],
    source: 'NSE Bhavcopy Official Archives (Offline Model Pipeline)',
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white">Algorithmic Directional Predictions</h2>
          <p className="text-xs text-slate-400">
            Calibrated forward probabilities with computed feature attributions for profile: <strong className="text-blue-400">{profile}</strong>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="primary" label="WALK-FORWARD RANDOM FOREST" sublabel="CALIBRATED" />
          <button
            onClick={fetchPredictions}
            className="p-1.5 text-slate-400 hover:text-slate-200 transition-colors"
            title="Refresh Predictions"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {predictions.length === 0 ? (
        <EmptyState
          title="No Predictions Found"
          description="No active signals calculated for the current securities. Check holdings or retry."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {predictions.map((p) => {
            const probPct = Number(p.prob_pct || (p.prob_up * 100)).toFixed(1);
            const sig = (p.signal || 'HOLD').toUpperCase();
            const riskTier = (p.risk_tier || 'medium').toLowerCase();

            return (
              <div
                key={p.symbol}
                className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <span className="text-base font-bold text-white">{p.symbol}</span>
                    <Badge
                      variant={sig === 'BUY' ? 'buy' : sig === 'SELL' ? 'sell' : 'hold'}
                      label={sig}
                    />
                    <Badge variant={riskTier} label={`${riskTier.toUpperCase()} RISK`} />
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400 mr-2">P(Direction = UP):</span>
                    <span className="text-sm font-mono font-bold text-blue-400">
                      {probPct}%
                    </span>
                  </div>
                </div>

                {/* Probability Progress Bar */}
                <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden border border-slate-800">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${sig === 'BUY'
                      ? 'bg-emerald-500'
                      : sig === 'SELL'
                        ? 'bg-rose-500'
                        : 'bg-amber-500'
                      }`}
                    style={{ width: `${Math.min(100, Math.max(5, probPct))}%` }}
                  />
                </div>

                {/* Plain-Language Reason String */}
                <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800/80 text-xs text-slate-300">
                  <span className="font-semibold text-slate-400 mr-1.5 font-mono text-[11px] uppercase">
                    Model Attribution:
                  </span>
                  <span>{p.reason}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <DataProvenanceFooter
        source={asOf.source}
        asOf={asOf.date}
        status="Chronological Split (Zero Future Leakage)"
      />
    </div>
  );
}
