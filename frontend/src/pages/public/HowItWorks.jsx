import React, { useEffect } from 'react';
import { Layers, Database, Cpu, Sliders, ShieldCheck, CheckCircle } from 'lucide-react';
import { DataProvenanceFooter } from '../../components/UIState';

export default function HowItWorks() {
  useEffect(() => {
    document.title = 'How It Works — AlphaWatch AI';
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) {
      metaDesc.setAttribute(
        'content',
        'Learn how AlphaWatch AI transforms raw NSE Bhavcopy archives into risk-first trading signals across five decoupled architectural layers.'
      );
    }
  }, []);

  const layers = [
    {
      num: '01',
      title: 'Data Layer: Offline Ingestion & Validation',
      desc: 'Local NSE Bhavcopy CSVs and Screener.in exports are ingested offline with manifest tracking. The validation engine enforces chronological ordering, deduplicates rows, verifies positive prices, and checks for market calendar gaps.',
      guarantees: ['Zero runtime network calls', 'Strict gap and duplicate detection', 'Manifest checksum verification'],
      icon: Database,
    },
    {
      num: '02',
      title: 'Feature Layer: Strictly Retrospective Indicators',
      desc: 'Computes past-only technical indicators (1d, 5d, 20d returns; SMA/EMA distances; RSI-14; 20d volatility; volume ratio). Drops initial warm-up rows. The target direction y(t) = 1 if Close(t+1) > Close(t) has zero lookahead bias into feature matrix X(t).',
      guarantees: ['Past data only in X(t)', 'No future price leakage', 'Standardized feature schema'],
      icon: Layers,
    },
    {
      num: '03',
      title: 'Model Layer: Walk-Forward Validation & Calibration',
      desc: 'Features are split chronologically (70% train, 15% validation, 15% holdout test). Scalers and probability calibrations fit strictly on past training data. Random Forest main model is benchmarked against Logistic Regression and a majority-class baseline.',
      guarantees: ['Expanding 5-fold walk-forward cross-validation', 'Isotonic calibration on validation data only', 'SHAP TreeExplainer feature attributions'],
      icon: Cpu,
    },
    {
      num: '04',
      title: 'Decision Layer: Dynamic Thresholds & Risk Labels',
      desc: 'Raw probabilities are mapped to signals based on investor risk profiles: Conservative (0.65/0.35), Moderate (0.60/0.40), Aggressive (0.55/0.45). Computes 20d volatility, 1y MaxDD, and 95% historical VaR/CVaR with positive-loss convention.',
      guarantees: ['Documented positive-loss convention', 'Tercile risk ranking', 'Configurable profile thresholds'],
      icon: Sliders,
    },
    {
      num: '05',
      title: 'Execution & Backtest: T+1 Open Friction Model',
      desc: 'Simulates long-only equity trades with realistic execution delay: Day t signal executes at Day t+1 market Open. Deducts 0.10% delivery STT, 0.03% brokerage, exchange turnover, and 0.05% slippage (~0.35% round-trip friction).',
      guarantees: ['Day t+1 market open fills', 'Explicit friction breakdown', 'No intraday lookahead execution'],
      icon: ShieldCheck,
    },
  ];

  return (
    <div className="space-y-12 max-w-4xl mx-auto">
      <div className="space-y-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold text-blue-400 bg-blue-950/60 border border-blue-700/50">
          <Layers className="w-3.5 h-3.5" />
          <span>System Architecture & Build Plan</span>
        </div>
        <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
          How Five Layers Turn Saved Data into a Personal, Risk-First Dashboard
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
          AlphaWatch AI is engineered to eliminate data leakage, overfitting, and imaginary backtest returns. Here is the exact mathematical and architectural journey from raw NSE bhavcopies to personal portfolio intelligence.
        </p>
      </div>

      {/* 12. System Architecture & Build Plan Diagram */}
      <div className="p-6 sm:p-8 rounded-2xl bg-[#0e1117] border border-slate-800 space-y-6">
        <div>
          <h2 className="text-xl sm:text-2xl font-serif text-slate-100 font-semibold tracking-tight">
            12. System architecture and build plan
          </h2>
          <p className="text-xs sm:text-sm font-bold text-slate-300 mt-1">
            Five layers turn saved data into a personal, risk-first dashboard
          </p>
        </div>

        <div className="space-y-3">
          {/* Layer 1: Data layer */}
          <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/40 space-y-2">
            <div className="text-xs text-slate-400 font-medium">Data layer</div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-3 bg-slate-950/90 rounded-lg border border-slate-800 text-center">
                <div className="text-sm font-bold text-slate-200">Saved NSE CSVs</div>
                <div className="text-xs text-slate-400 mt-0.5">Offline, with source and date</div>
              </div>
              <div className="p-3 bg-slate-950/90 rounded-lg border border-slate-800 text-center">
                <div className="text-sm font-bold text-slate-200">Validation</div>
                <div className="text-xs text-slate-400 mt-0.5">Sort, dedupe, check gaps</div>
              </div>
              <div className="p-3 bg-slate-950/90 rounded-lg border border-slate-800 text-center">
                <div className="text-sm font-bold text-slate-200">Features</div>
                <div className="text-xs text-slate-400 mt-0.5">Computed from past data only</div>
              </div>
            </div>
          </div>

          <div className="flex justify-center text-slate-500 text-sm py-0.5">↓</div>

          {/* Layer 2: Model layer */}
          <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/40 space-y-2">
            <div className="text-xs text-slate-400 font-medium">Model layer: chronological split, scaler fitted on training only</div>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <div className="p-3 bg-slate-950/90 rounded-lg border border-slate-800 text-center">
                <div className="text-sm font-bold text-slate-200">Logistic Reg.</div>
                <div className="text-xs text-slate-400 mt-0.5">Baseline</div>
              </div>
              <div className="p-3 bg-slate-950/90 rounded-lg border-2 border-blue-500 shadow-[0_0_16px_rgba(59,130,246,0.25)] text-center">
                <div className="text-sm font-bold text-blue-400">Random Forest</div>
                <div className="text-xs text-slate-300 mt-0.5 font-medium">Main model</div>
              </div>
              <div className="p-3 bg-slate-950/90 rounded-lg border border-slate-800 text-center">
                <div className="text-sm font-bold text-slate-200">XGBoost, LSTM</div>
                <div className="text-xs text-slate-400 mt-0.5">Optional comparison</div>
              </div>
              <div className="p-3 bg-slate-950/50 rounded-lg border border-dashed border-slate-700 text-center">
                <div className="text-sm font-bold text-slate-400">RL agent</div>
                <div className="text-xs text-slate-500 mt-0.5">Roadmap only</div>
              </div>
            </div>
          </div>

          <div className="flex justify-center text-slate-500 text-sm py-0.5">↓</div>

          {/* Layer 3: Decision layer */}
          <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/40 space-y-2">
            <div className="text-xs text-slate-400 font-medium">Decision layer</div>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <div className="p-3 bg-slate-950/90 rounded-lg border border-slate-800 text-center">
                <div className="text-sm font-bold text-slate-200">Probability</div>
                <div className="text-xs text-slate-400 mt-0.5">Calibrated, explained</div>
              </div>
              <div className="p-3 bg-slate-950/90 rounded-lg border border-slate-800 text-center">
                <div className="text-sm font-bold text-slate-200">Signals</div>
                <div className="text-xs text-slate-400 mt-0.5">Profile thresholds</div>
              </div>
              <div className="p-3 bg-slate-950/90 rounded-lg border border-slate-800 text-center">
                <div className="text-sm font-bold text-slate-200">Risk labels</div>
                <div className="text-xs text-slate-400 mt-0.5">Vol, drawdown, VaR</div>
              </div>
              <div className="p-3 bg-slate-950/90 rounded-lg border border-slate-800 text-center">
                <div className="text-sm font-bold text-slate-200">Backtest</div>
                <div className="text-xs text-slate-400 mt-0.5">Costs, next-day open</div>
              </div>
            </div>
          </div>

          <div className="flex justify-center text-slate-500 text-sm py-0.5">↓</div>

          {/* Layer 4: App layer */}
          <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/40 space-y-2">
            <div className="text-xs text-slate-400 font-medium">App layer: FastAPI and SQLite</div>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <div className="p-3 bg-slate-950/90 rounded-lg border border-slate-800 text-center">
                <div className="text-sm font-bold text-slate-200">Auth + SQLite</div>
                <div className="text-xs text-slate-400 mt-0.5">Private per-user data</div>
              </div>
              <div className="p-3 bg-slate-950/90 rounded-lg border border-slate-800 text-center">
                <div className="text-sm font-bold text-slate-200">Profiler</div>
                <div className="text-xs text-slate-400 mt-0.5">Rule-based pattern</div>
              </div>
              <div className="p-3 bg-slate-950/90 rounded-lg border border-slate-800 text-center">
                <div className="text-sm font-bold text-slate-200">Paper trading</div>
                <div className="text-xs text-slate-400 mt-0.5">Simulated orders only</div>
              </div>
              <div className="p-3 bg-slate-950/90 rounded-lg border border-slate-800 text-center">
                <div className="text-sm font-bold text-slate-200">Extras</div>
                <div className="text-xs text-slate-400 mt-0.5">Claim Auditor, Ripple</div>
              </div>
            </div>
          </div>

          <div className="flex justify-center text-slate-500 text-sm py-0.5">↓</div>

          {/* Layer 5: Presentation */}
          <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/40 space-y-2">
            <div className="text-xs text-slate-400 font-medium">Presentation</div>
            <div className="p-3.5 bg-slate-950/90 rounded-lg border border-slate-800 text-center">
              <div className="text-sm font-bold text-slate-200">Personal dashboard</div>
              <div className="text-xs text-slate-400 mt-0.5">Overview, predictions, buy candidates, risk, backtest, model performance</div>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {layers.map((layer) => {
          const Icon = layer.icon;
          return (
            <div
              key={layer.num}
              className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4"
            >
              <div className="flex items-start gap-4">
                <span className="text-xl font-black text-blue-500 font-mono">
                  {layer.num}
                </span>
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <Icon className="w-4 h-4 text-blue-400" />
                    <h3 className="text-base font-bold text-white">{layer.title}</h3>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">{layer.desc}</p>

                  <div className="pt-2 grid grid-cols-1 sm:grid-cols-3 gap-2">
                    {layer.guarantees.map((g, idx) => (
                      <div key={idx} className="flex items-center gap-1.5 text-[11px] text-emerald-400 font-medium">
                        <CheckCircle className="w-3.5 h-3.5 flex-shrink-0" />
                        <span>{g}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <DataProvenanceFooter
        source="NSE CM-UDiFF Archive"
        asOf="Chronological 70/15/15"
        status="Mathematical Pipeline"
      />
    </div>
  );
}
