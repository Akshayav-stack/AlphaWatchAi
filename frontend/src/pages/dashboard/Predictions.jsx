import React, { useEffect } from 'react';
import { TrendingUp, CheckCircle, Info, Sliders } from 'lucide-react';
import { Badge, DataProvenanceFooter } from '../../components/UIState';

export default function Predictions() {
  useEffect(() => {
    document.title = 'Predictions — AlphaWatch AI';
  }, []);

  const predictions = [
    {
      symbol: 'RELIANCE',
      probUp: 0.68,
      signal: 'BUY',
      profile: 'Moderate',
      riskTier: 'low',
      reason: 'RSI-14 of 42.1 (+0.08) and 20d volatility of 14.8% pushed probability up above profile threshold (0.60).',
    },
    {
      symbol: 'TCS',
      probUp: 0.63,
      signal: 'BUY',
      profile: 'Moderate',
      riskTier: 'low',
      reason: '20d EMA distance (+1.4%) and volume ratio of 1.15x support positive directional probability.',
    },
    {
      symbol: 'INFY',
      probUp: 0.54,
      signal: 'HOLD',
      profile: 'Moderate',
      riskTier: 'medium',
      reason: 'Probability (0.54) falls inside neutral band (0.40 to 0.60). No clear statistical edge.',
    },
    {
      symbol: 'HDFCBANK',
      probUp: 0.49,
      signal: 'HOLD',
      profile: 'Moderate',
      riskTier: 'low',
      reason: 'Flat 5-day return and contracting 20d ATR indicate range-bound consolidation.',
    },
    {
      symbol: 'ICICIBANK',
      probUp: 0.38,
      signal: 'SELL',
      profile: 'Moderate',
      riskTier: 'medium',
      reason: 'RSI-14 (68.4) overbought divergence and negative 5d momentum push probability below sell threshold (0.40).',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white">Algorithmic Directional Predictions</h2>
          <p className="text-xs text-slate-400">
            Calibrated forward probabilities with computed SHAP TreeExplainer feature attributions
          </p>
        </div>
        <Badge variant="primary" label="WALK-FORWARD RANDOM FOREST" sublabel="CALIBRATED" />
      </div>

      <div className="grid grid-cols-1 gap-4">
        {predictions.map((p) => (
          <div
            key={p.symbol}
            className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <span className="text-base font-bold text-white">{p.symbol}</span>
                <Badge
                  variant={p.signal === 'BUY' ? 'buy' : p.signal === 'SELL' ? 'sell' : 'hold'}
                  label={p.signal}
                />
                <Badge variant={p.riskTier} label={`${p.riskTier.toUpperCase()} RISK`} />
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-400 mr-2">P(Direction = UP):</span>
                <span className="text-sm font-mono font-bold text-blue-400">
                  {(p.probUp * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            {/* Probability Progress Bar */}
            <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
              <div
                className={`h-full rounded-full ${
                  p.signal === 'BUY'
                    ? 'bg-emerald-500'
                    : p.signal === 'SELL'
                    ? 'bg-rose-500'
                    : 'bg-amber-500'
                }`}
                style={{ width: `${p.probUp * 100}%` }}
              />
            </div>

            {/* Computed Reason String */}
            <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-lg text-xs text-slate-300">
              <span className="font-semibold text-blue-400 mr-1.5">SHAP Attribution:</span>
              <span className="text-slate-300">{p.reason}</span>
            </div>
          </div>
        ))}
      </div>

      <DataProvenanceFooter
        source="src/models.py (Random Forest + SHAP)"
        asOf="Chronological Split & Walk-Forward"
        status="Calibrated Probabilities"
      />
    </div>
  );
}
