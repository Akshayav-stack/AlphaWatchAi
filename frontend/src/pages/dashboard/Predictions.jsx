import React, { useEffect, useState } from 'react';
import {
  Sparkles,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  Info,
  RefreshCw,
  BarChart3,
  Sliders,
  ShieldAlert,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
} from 'lucide-react';
import {
  Badge,
  DataProvenanceFooter,
  LoadingSpinner,
  ErrorMessage,
  EmptyState,
} from '../../components/UIState';
import { getPredictionsApi, getExplainDecisionApi } from '../../api/client';

const SUPPORTED_EQUITIES = [
  'RELIANCE',
  'TCS',
  'HDFCBANK',
  'INFY',
  'ICICIBANK',
  'SBIN',
  'BHARTIARTL',
  'ITC',
  'LT',
  'HINDUNILVR',
];

export default function Predictions() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Explainable AI State
  const [selectedSymbol, setSelectedSymbol] = useState('RELIANCE');
  const [explanation, setExplanation] = useState(null);
  const [explainLoading, setExplainLoading] = useState(false);
  const [explainError, setExplainError] = useState(null);

  useEffect(() => {
    document.title = 'Predictions & AI Decision Intelligence — AlphaWatch AI';
    fetchPredictions();
  }, []);

  useEffect(() => {
    if (selectedSymbol) {
      fetchExplanation(selectedSymbol);
    }
  }, [selectedSymbol]);

  async function fetchPredictions() {
    try {
      setLoading(true);
      setError(null);
      const res = await getPredictionsApi();
      setData(res);
      if (res?.predictions?.length > 0 && !selectedSymbol) {
        setSelectedSymbol(res.predictions[0].symbol);
      }
    } catch (err) {
      setError(err.message || 'Failed to load model predictions.');
    } finally {
      setLoading(false);
    }
  }

  async function fetchExplanation(symbol) {
    try {
      setExplainLoading(true);
      setExplainError(null);
      const res = await getExplainDecisionApi(symbol);
      setExplanation(res);
    } catch (err) {
      setExplainError(err.message || `Failed to generate AI decision explanation for ${symbol}.`);
    } finally {
      setExplainLoading(false);
    }
  }

  function handleSelectSymbol(sym) {
    setSelectedSymbol(sym);
    // Smooth scroll to Decision Intelligence section
    const el = document.getElementById('ai-decision-intelligence');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  if (loading) {
    return <LoadingSpinner text="Computing walk-forward calibrated probabilities & SHAP attributions..." />;
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
    <div className="space-y-10">
      {/* ---------------------------------------------------------------------- */}
      {/* 1. Header Banner */}
      {/* ---------------------------------------------------------------------- */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Algorithmic Directional Predictions
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Calibrated walk-forward probabilities with model explanations for profile:{' '}
            <strong className="text-blue-400">{profile}</strong>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="primary" label="RANDOM FOREST" sublabel="TREEEXPLAINER SHAP" />
          <button
            onClick={() => {
              fetchPredictions();
              if (selectedSymbol) fetchExplanation(selectedSymbol);
            }}
            className="p-1.5 text-slate-400 hover:text-slate-200 transition-colors"
            title="Refresh All Predictions & Explanations"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* ---------------------------------------------------------------------- */}
      {/* 2. AI DECISION INTELLIGENCE (Feature Centerpiece) */}
      {/* ---------------------------------------------------------------------- */}
      <section
        id="ai-decision-intelligence"
        aria-label="AI Decision Intelligence"
        className="rounded-3xl bg-white text-slate-800 p-6 sm:p-10 shadow-2xl border border-purple-100/90 space-y-8 transition-all"
      >
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-purple-100 pb-6">
          <div className="space-y-1.5">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold text-purple-700 bg-purple-100/80 border border-purple-200 tracking-wide uppercase">
              <Sparkles className="w-3.5 h-3.5 text-purple-600" />
              <span>AI DECISION INTELLIGENCE</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Understand why your AI makes every trading decision.
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 max-w-2xl">
              Inspect the exact mathematical inputs, tree decision paths, and local SHAP feature attributions behind every single algorithmic trade signal.
            </p>
          </div>

          {/* Quick Stock Switcher Pills */}
          <div className="space-y-1.5">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Select Security for Deep XAI Audit:
            </span>
            <div className="flex flex-wrap gap-1.5 max-w-md">
              {SUPPORTED_EQUITIES.map((sym) => {
                const isSelected = selectedSymbol === sym;
                return (
                  <button
                    key={sym}
                    onClick={() => setSelectedSymbol(sym)}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                      isSelected
                        ? 'bg-purple-600 text-white shadow-md shadow-purple-500/20 scale-105'
                        : 'bg-slate-100 text-slate-600 hover:bg-purple-50 hover:text-purple-700 border border-slate-200'
                    }`}
                  >
                    {sym}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Explain Loading / Error / Content */}
        {explainLoading ? (
          <div className="py-16 text-center space-y-3">
            <div className="inline-block animate-spin text-purple-600">
              <RefreshCw className="w-8 h-8" />
            </div>
            <p className="text-sm font-semibold text-slate-600">
              Computing TreeExplainer SHAP values & risk factors for {selectedSymbol}...
            </p>
          </div>
        ) : explainError ? (
          <div className="p-6 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 space-y-2">
            <div className="flex items-center gap-2 font-bold text-sm">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              <span>Explanation Generation Notice</span>
            </div>
            <p className="text-xs text-rose-700">{explainError}</p>
            <button
              onClick={() => fetchExplanation(selectedSymbol)}
              className="text-xs font-semibold underline hover:text-rose-900 pt-1"
            >
              Retry Explanation Computation
            </button>
          </div>
        ) : explanation ? (
          <div className="space-y-8">
            {/* ------------------------------------------------------------------ */}
            {/* 2A. Security Dossier & AI Signal Banner */}
            {/* ------------------------------------------------------------------ */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
              {/* Left Quote & Signal Card */}
              <div className="lg:col-span-8 p-6 rounded-2xl bg-gradient-to-br from-purple-50/70 via-white to-sky-50/50 border border-purple-100 shadow-sm flex flex-col justify-between space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-2xl font-black text-slate-900 tracking-tight font-mono">
                        {explanation.symbol}
                      </span>
                      <span className="text-xs font-medium text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                        {explanation.company_name}
                      </span>
                    </div>
                    <div className="flex items-baseline gap-2 mt-1">
                      <span className="text-xl font-bold text-slate-800">
                        ₹{Number(explanation.current_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </span>
                      <span
                        className={`text-xs font-bold inline-flex items-center ${
                          explanation.change_1d_pct >= 0 ? 'text-emerald-600' : 'text-rose-600'
                        }`}
                      >
                        {explanation.change_1d_pct >= 0 ? (
                          <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
                        ) : (
                          <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />
                        )}
                        {explanation.change_1d_pct >= 0 ? '+' : ''}
                        {explanation.change_1d_pct.toFixed(2)}%
                      </span>
                    </div>
                  </div>

                  {/* AI Signal Pill */}
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                        AI Trading Signal
                      </span>
                      <span
                        className={`inline-block px-4 py-1.5 rounded-xl text-base font-black tracking-wider uppercase shadow-sm ${
                          explanation.signal === 'BUY'
                            ? 'bg-emerald-500 text-white shadow-emerald-500/20'
                            : explanation.signal === 'SELL'
                            ? 'bg-rose-500 text-white shadow-rose-500/20'
                            : 'bg-amber-400 text-slate-900 shadow-amber-400/20'
                        }`}
                      >
                        {explanation.signal}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Dynamic Natural Language Explanation */}
                <div className="p-4 rounded-xl bg-white border border-purple-100/80 shadow-sm space-y-1.5">
                  <span className="text-[11px] font-bold text-purple-700 uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                    <span>Dynamic AI Signal Rationale</span>
                  </span>
                  <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-medium">
                    "{explanation.dynamic_explanation}"
                  </p>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-[11px] text-slate-500 border-t border-purple-100/60">
                  <span>
                    Pipeline: <strong>{explanation.model_name}</strong>
                  </span>
                  <span>
                    As of: <strong>{explanation.as_of_date}</strong> (Offline NSE Bhavcopy)
                  </span>
                </div>
              </div>

              {/* Right Model Probability Gauge Card */}
              <div className="lg:col-span-4 p-6 rounded-2xl bg-gradient-to-br from-sky-50/80 via-white to-purple-50/50 border border-sky-100 shadow-sm flex flex-col justify-between space-y-4">
                <div className="flex items-center justify-between border-b border-sky-100 pb-2">
                  <span className="text-xs font-bold text-sky-900 uppercase tracking-wide flex items-center gap-1.5">
                    <Activity className="w-4 h-4 text-sky-600" />
                    <span>Probability Meter</span>
                  </span>
                  <span className="text-[10px] font-bold text-slate-500 bg-white px-2 py-0.5 rounded-full border border-sky-200">
                    Tier: {explanation.probability_meter?.tier}
                  </span>
                </div>

                {/* Visual Probability Indicator */}
                <div className="space-y-3 text-center my-auto">
                  <div className="inline-flex flex-col items-center justify-center w-28 h-28 rounded-full bg-white border-4 border-sky-400 shadow-inner p-2 mx-auto">
                    <span className="text-2xl font-black text-slate-900 font-mono tracking-tight">
                      {explanation.probability_up_pct}%
                    </span>
                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">
                      P(Direction = UP)
                    </span>
                  </div>

                  <div className="space-y-1">
                    <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden p-0.5">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          explanation.probability_up_pct >= 65
                            ? 'bg-emerald-500'
                            : explanation.probability_up_pct >= 50
                            ? 'bg-sky-500'
                            : 'bg-rose-500'
                        }`}
                        style={{ width: `${Math.min(100, Math.max(8, explanation.probability_up_pct))}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[10px] font-bold text-slate-400">
                      <span>0% (SELL)</span>
                      <span>50% (NEUTRAL)</span>
                      <span>100% (BUY)</span>
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-600 font-medium leading-snug">
                    {explanation.probability_meter?.tier_description}
                  </p>
                </div>

                <div className="p-2.5 rounded-lg bg-white/80 border border-sky-200/60 text-[10px] text-slate-500 leading-tight">
                  <span className="font-semibold text-slate-700">Calibration Disclosure: </span>
                  {explanation.probability_meter?.disclaimer}
                </div>
              </div>
            </div>

            {/* ------------------------------------------------------------------ */}
            {/* 2B. Positive and Negative Contributing Factors */}
            {/* ------------------------------------------------------------------ */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Positive Factors Card (Mint Green) */}
              <div className="p-6 rounded-2xl bg-emerald-50/60 border border-emerald-200/90 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-emerald-200/80 pb-3">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 bg-emerald-100 text-emerald-700 rounded-lg">
                      <CheckCircle2 className="w-4 h-4" />
                    </div>
                    <h3 className="text-sm sm:text-base font-bold text-emerald-950 uppercase tracking-wide">
                      POSITIVE FACTORS ({explanation.positive_factors?.length || 0})
                    </h3>
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-emerald-100/90 text-emerald-800 rounded-full border border-emerald-300/60">
                    Bullish Push
                  </span>
                </div>

                <div className="space-y-3">
                  {explanation.positive_factors?.map((f, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-white/95 border border-emerald-100 shadow-sm space-y-1.5"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-bold text-slate-900">{f.factor}</span>
                        <div className="flex items-center gap-1.5">
                          <span className="text-[11px] font-mono font-bold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                            {f.value}
                          </span>
                          <span className="text-[11px] font-mono font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">
                            {f.contribution} SHAP
                          </span>
                        </div>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">{f.detail}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Negative Factors Card (Light Red) */}
              <div className="p-6 rounded-2xl bg-rose-50/60 border border-rose-200/90 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-rose-200/80 pb-3">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 bg-rose-100 text-rose-700 rounded-lg">
                      <AlertTriangle className="w-4 h-4" />
                    </div>
                    <h3 className="text-sm sm:text-base font-bold text-rose-950 uppercase tracking-wide">
                      NEGATIVE FACTORS ({explanation.negative_factors?.length || 0})
                    </h3>
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-rose-100/90 text-rose-800 rounded-full border border-rose-300/60">
                    Downside Drag
                  </span>
                </div>

                <div className="space-y-3">
                  {explanation.negative_factors?.map((f, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-white/95 border border-rose-100 shadow-sm space-y-1.5"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-bold text-slate-900">{f.factor}</span>
                        <div className="flex items-center gap-1.5">
                          <span className="text-[11px] font-mono font-bold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                            {f.value}
                          </span>
                          <span className="text-[11px] font-mono font-bold text-rose-700 bg-rose-100 px-1.5 py-0.5 rounded">
                            {f.contribution} SHAP
                          </span>
                        </div>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">{f.detail}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* ------------------------------------------------------------------ */}
            {/* 2C. SHAP Feature Importance & Contribution Breakdown */}
            {/* ------------------------------------------------------------------ */}
            <div className="p-6 rounded-2xl bg-slate-50/80 border border-slate-200 shadow-sm space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-3">
                <div>
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-purple-600" />
                    <span>Top Five Influential Features (TreeExplainer SHAP)</span>
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Individual prediction local attributions calculated specifically for this prediction instance.
                  </p>
                </div>
                <span className="text-[11px] font-bold text-purple-700 bg-purple-100 px-2.5 py-1 rounded-md border border-purple-200 self-start sm:self-auto">
                  Local Tree SHAP Decomposition
                </span>
              </div>

              {/* Horizontal SHAP Contribution Bar Chart */}
              <div className="space-y-3.5">
                {explanation.top_features?.map((item, idx) => {
                  const isPos = item.direction === 'Positive';
                  return (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-white border border-slate-200/80 space-y-2 hover:border-purple-200 transition-colors"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[11px] font-bold text-slate-400">#{idx + 1}</span>
                          <span className="font-bold text-slate-800">{item.label}</span>
                          <span className="text-slate-500 font-mono text-[11px] bg-slate-100 px-1.5 py-0.5 rounded">
                            Input: {item.raw_value}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] font-bold font-mono ${
                              isPos ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                            }`}
                          >
                            {isPos ? '+' : ''}
                            {item.shap_value} SHAP ({item.direction})
                          </span>
                        </div>
                      </div>

                      {/* Visual Bar Indicator */}
                      <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden flex items-center">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${
                            isPos ? 'bg-emerald-500' : 'bg-rose-500'
                          }`}
                          style={{ width: `${Math.min(100, Math.max(10, item.relative_strength_pct))}%` }}
                        />
                      </div>

                      <p className="text-[11px] text-slate-600 leading-snug">{item.explanation}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* ------------------------------------------------------------------ */}
            {/* 2D. Smart Quantitative Risk Warnings */}
            {/* ------------------------------------------------------------------ */}
            {explanation.risk_warnings?.length > 0 && (
              <div className="p-6 rounded-2xl bg-amber-50/70 border border-amber-200/90 shadow-sm space-y-3">
                <div className="flex items-center gap-2 text-amber-900 border-b border-amber-200/60 pb-2">
                  <ShieldAlert className="w-5 h-5 text-amber-600 flex-shrink-0" />
                  <h3 className="text-sm sm:text-base font-bold uppercase tracking-wide">
                    SMART RISK WARNINGS & MARKET REGIME ALERTS ({explanation.risk_warnings.length})
                  </h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                  {explanation.risk_warnings.map((w, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-white border border-amber-200 shadow-sm space-y-1"
                    >
                      <div className="flex items-center justify-between text-xs font-bold text-amber-950">
                        <span>{w.type}</span>
                        <span className="uppercase text-[9px] px-1.5 py-0.5 rounded font-bold bg-amber-100 text-amber-800">
                          {w.level} priority
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">{w.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ------------------------------------------------------------------ */}
            {/* 2E. AI Explanation Summary Card */}
            {/* ------------------------------------------------------------------ */}
            <div className="p-6 rounded-2xl bg-gradient-to-r from-purple-100/60 via-sky-50/60 to-purple-50/60 border border-purple-200 shadow-sm space-y-2">
              <span className="text-xs font-bold text-purple-900 uppercase tracking-wide flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-purple-700" />
                <span>AI EXPLANATION SUMMARY & QUANTITATIVE VERDICT</span>
              </span>
              <p className="text-xs sm:text-sm text-slate-800 leading-relaxed font-medium">
                {explanation.final_summary}
              </p>
            </div>
          </div>
        ) : null}
      </section>

      {/* ---------------------------------------------------------------------- */}
      {/* 3. All Securities Predictions List (with Explain AI button) */}
      {/* ---------------------------------------------------------------------- */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider">
            All Monitored Equities & Signals ({predictions.length})
          </h2>
          <span className="text-xs text-slate-500">
            Click 'Explain AI' on any stock to inspect its full decision dossier
          </span>
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
              const isSelected = selectedSymbol === p.symbol;

              return (
                <div
                  key={p.symbol}
                  className={`p-5 rounded-2xl border transition-all space-y-3 ${
                    isSelected
                      ? 'bg-slate-900 border-purple-500/70 shadow-lg shadow-purple-900/10'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-3">
                      <span className="text-base font-bold text-white font-mono">{p.symbol}</span>
                      <Badge
                        variant={sig === 'BUY' ? 'buy' : sig === 'SELL' ? 'sell' : 'hold'}
                        label={sig}
                      />
                      <Badge variant={riskTier} label={`${riskTier.toUpperCase()} RISK`} />
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <span className="text-xs text-slate-400 mr-2">P(Direction = UP):</span>
                        <span className="text-sm font-mono font-bold text-blue-400">
                          {probPct}%
                        </span>
                      </div>

                      {/* Small Explain AI button beside signal */}
                      <button
                        onClick={() => handleSelectSymbol(p.symbol)}
                        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all shadow-sm ${
                          isSelected
                            ? 'bg-purple-600 text-white shadow-purple-600/30 ring-2 ring-purple-400/40'
                            : 'bg-purple-950/70 text-purple-300 hover:bg-purple-900/90 hover:text-white border border-purple-700/60'
                        }`}
                        title={`Open Deep Explainable AI Dossier for ${p.symbol}`}
                      >
                        <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                        <span>Explain AI</span>
                      </button>
                    </div>
                  </div>

                  {/* Probability Progress Bar */}
                  <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        sig === 'BUY'
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
      </div>

      <DataProvenanceFooter
        source={asOf.source}
        asOf={asOf.date}
        status="Chronological Split & TreeExplainer SHAP Attributions (Zero Lookahead Leakage)"
      />
    </div>
  );
}
