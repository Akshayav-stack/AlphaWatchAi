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
  Plus,
  Minus,
  Check,
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

const PROFILES = ['Conservative', 'Moderate', 'Aggressive'];

export default function Predictions() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Explainable AI State
  const [selectedSymbol, setSelectedSymbol] = useState('RELIANCE');
  const [selectedProfile, setSelectedProfile] = useState('Moderate');
  const [explanation, setExplanation] = useState(null);
  const [explainLoading, setExplainLoading] = useState(false);
  const [explainError, setExplainError] = useState(null);
  const [showAllFeatures, setShowAllFeatures] = useState(false);

  useEffect(() => {
    document.title = 'Predictions & AI Decision Intelligence — AlphaWatch AI';
    fetchPredictions();
  }, []);

  useEffect(() => {
    if (selectedSymbol) {
      fetchExplanation(selectedSymbol, selectedProfile);
    }
  }, [selectedSymbol, selectedProfile]);

  async function fetchPredictions() {
    try {
      setLoading(true);
      setError(null);
      const res = await getPredictionsApi();
      setData(res);
      if (res?.profile) {
        setSelectedProfile(res.profile);
      }
      if (res?.predictions?.length > 0 && !selectedSymbol) {
        setSelectedSymbol(res.predictions[0].symbol);
      }
    } catch (err) {
      setError(err.message || 'Failed to load model predictions.');
    } finally {
      setLoading(false);
    }
  }

  async function fetchExplanation(symbol, profile) {
    try {
      setExplainLoading(true);
      setExplainError(null);
      const res = await getExplainDecisionApi(symbol, profile);
      setExplanation(res);
    } catch (err) {
      setExplainError(err.message || `Failed to generate AI decision explanation for ${symbol}.`);
    } finally {
      setExplainLoading(false);
    }
  }

  function handleSelectSymbol(sym) {
    setSelectedSymbol(sym);
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
  const asOf = data?.as_of || {
    date: new Date().toISOString().split('T')[0],
    source: 'NSE Bhavcopy Official Archives (Offline Model Pipeline)',
  };

  // Helper values from explanation
  const probMeter = explanation?.probability_meter || {};
  const probPct = Number(probMeter.percentage || (explanation?.calibrated_probability ? explanation.calibrated_probability * 100 : 50)).toFixed(1);
  const buyThresh = (probMeter.buy_threshold ? probMeter.buy_threshold * 100 : 60).toFixed(0);
  const sellThresh = (probMeter.sell_threshold ? probMeter.sell_threshold * 100 : 40).toFixed(0);
  const bandLabel = probMeter.band_label || (Number(probPct) >= buyThresh ? 'At or above BUY threshold' : Number(probPct) <= sellThresh ? 'At or below SELL threshold' : 'Between thresholds (HOLD zone)');

  const posFactors = explanation?.factors?.positive || explanation?.positive_factors || [];
  const negFactors = explanation?.factors?.negative || explanation?.negative_factors || [];

  const shapBlock = explanation?.shap || {};
  const shapTopFive = shapBlock.top_five || explanation?.top_features || [];
  const shapAll = shapBlock.contributions || [];
  const displayedShap = showAllFeatures && shapAll.length > 0 ? shapAll : shapTopFive;
  const globalImportance = shapBlock.global_importance || [];
  const riskAlerts = explanation?.risk_alerts || explanation?.risk_warnings || [];

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
            <strong className="text-blue-400">{selectedProfile}</strong>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="primary" label="RANDOM FOREST" sublabel="TREEEXPLAINER SHAP" />
          <button
            onClick={() => {
              fetchPredictions();
              if (selectedSymbol) fetchExplanation(selectedSymbol, selectedProfile);
            }}
            className="p-1.5 text-slate-400 hover:text-slate-200 transition-colors"
            title="Refresh All Predictions & Explanations"
            aria-label="Refresh All Predictions"
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
        className="rounded-3xl bg-white text-slate-800 p-6 sm:p-10 shadow-2xl border border-purple-100 space-y-8 transition-all"
      >
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-purple-100 pb-6">
          <div className="space-y-1.5">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold text-purple-700 bg-purple-100 border border-purple-200 tracking-wide uppercase">
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

          {/* Profile & Stock Selectors */}
          <div className="space-y-3">
            <div>
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                Active Investor Profile:
              </span>
              <div className="flex gap-1.5">
                {PROFILES.map((p) => {
                  const isActive = selectedProfile === p;
                  return (
                    <button
                      key={p}
                      onClick={() => setSelectedProfile(p)}
                      className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                        isActive
                          ? 'bg-purple-700 text-white shadow-sm'
                          : 'bg-slate-100 text-slate-600 hover:bg-purple-50 hover:text-purple-700 border border-slate-200'
                      }`}
                    >
                      {p}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                Select Security for Deep XAI Audit:
              </span>
              <div className="flex flex-wrap gap-1.5 max-w-md">
                {SUPPORTED_EQUITIES.map((sym) => {
                  const isSelected = selectedSymbol === sym;
                  return (
                    <button
                      key={sym}
                      onClick={() => setSelectedSymbol(sym)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
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
              onClick={() => fetchExplanation(selectedSymbol, selectedProfile)}
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
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
              {/* Left Quote & Meta Card */}
              <div className="lg:col-span-8 p-6 rounded-2xl bg-gradient-to-br from-purple-50/70 via-white to-sky-50/50 border border-purple-100 shadow-sm flex flex-col justify-between space-y-4">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-2xl font-black text-slate-900 font-mono tracking-tight">
                        {explanation.symbol}
                      </span>
                      <span className="text-xs font-medium text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                        {explanation.name || explanation.company_name}
                      </span>
                    </div>
                    <div className="flex items-baseline gap-2 mt-1">
                      <span className="text-xl font-bold text-slate-800">
                        ₹{Number(explanation.latest_close || explanation.current_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </span>
                      <span className="text-xs text-slate-500">
                        Close on {explanation.as_of_date}
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

                {/* Dynamic Summary / Rationale */}
                <div className="p-4 rounded-xl bg-white border border-purple-100 shadow-sm space-y-1.5">
                  <span className="text-[11px] font-bold text-purple-700 uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                    <span>Dynamic AI Signal Rationale</span>
                  </span>
                  <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-medium">
                    "{explanation.summary || explanation.dynamic_explanation}"
                  </p>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-[11px] text-slate-500 border-t border-purple-100">
                  <span>
                    Model Version: <strong>{explanation.model_version || '1.0.0'}</strong> ({explanation.method || 'TreeExplainer'})
                  </span>
                  <span>
                    Data Source: <strong>{explanation.data_source || 'Offline Local NSE Bhavcopy'}</strong>
                  </span>
                </div>
              </div>

              {/* Right Model Probability Gauge Card */}
              <div className="lg:col-span-4 p-6 rounded-2xl bg-gradient-to-br from-sky-50 via-white to-purple-50/50 border border-sky-100 shadow-sm flex flex-col justify-between space-y-4">
                <div className="flex items-center justify-between border-b border-sky-100 pb-2">
                  <span className="text-xs font-bold text-sky-900 uppercase tracking-wide flex items-center gap-1.5">
                    <Activity className="w-4 h-4 text-sky-600" />
                    <span>Probability Meter</span>
                  </span>
                  <span className="text-[10px] font-bold text-slate-600 bg-white px-2 py-0.5 rounded-full border border-sky-200">
                    {bandLabel}
                  </span>
                </div>

                {/* Gauge Display with Thresholds */}
                <div className="space-y-3 text-center my-auto">
                  <div className="inline-flex flex-col items-center justify-center w-28 h-28 rounded-full bg-white border-4 border-sky-400 shadow-inner p-2 mx-auto">
                    <span className="text-2xl font-black text-slate-900 font-mono tracking-tight">
                      {probPct}%
                    </span>
                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">
                      Calibrated Prob
                    </span>
                  </div>

                  {/* Horizontal Threshold Gauge */}
                  <div className="space-y-1">
                    <div className="relative w-full bg-slate-200 h-3 rounded-full overflow-hidden p-0.5">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          Number(probPct) >= buyThresh
                            ? 'bg-emerald-500'
                            : Number(probPct) <= sellThresh
                            ? 'bg-rose-500'
                            : 'bg-amber-400'
                        }`}
                        style={{ width: `${Math.min(100, Math.max(6, Number(probPct)))}%` }}
                      />
                    </div>
                    {/* Markers for Profile Thresholds */}
                    <div className="flex justify-between text-[10px] font-bold text-slate-500 pt-0.5">
                      <span>0% (SELL ≤ {sellThresh}%)</span>
                      <span className="text-amber-700">HOLD Zone</span>
                      <span>(BUY ≥ {buyThresh}%) 100%</span>
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-600 font-medium">
                    Calibration: <strong>{probMeter.calibration_method || 'Validation-set calibration'}</strong>
                    {probMeter.validation_brier_score !== undefined && (
                      <span className="block text-[10px] text-slate-500">
                        Validation Brier: {probMeter.validation_brier_score} | ROC-AUC: {probMeter.validation_roc_auc}
                      </span>
                    )}
                  </p>
                </div>

                {/* Explicit Profit Disclaimer */}
                <div className="p-2.5 rounded-lg bg-white border border-sky-200 text-[10px] text-slate-600 leading-tight">
                  <span className="font-semibold text-slate-800">Mandatory Risk Disclosure: </span>
                  {probMeter.disclaimer || 'This is the model estimated probability of a higher next-day close. It is not the probability of making a profit and not a guarantee.'}
                </div>
              </div>
            </div>

            {/* ------------------------------------------------------------------ */}
            {/* 2B. Positive and Negative Contributing Factors */}
            {/* ------------------------------------------------------------------ */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Positive Factors Card (Mint Green) */}
              <div className="p-6 rounded-2xl bg-emerald-50 border border-emerald-200 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-emerald-200 pb-3">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 bg-emerald-100 text-emerald-700 rounded-lg">
                      <Plus className="w-4 h-4 stroke-[3]" />
                    </div>
                    <div>
                      <h3 className="text-sm sm:text-base font-bold text-emerald-950 uppercase tracking-wide">
                        POSITIVE FACTORS ({posFactors.length})
                      </h3>
                      <span className="text-[11px] font-semibold text-emerald-800">Positive Bullish Momentum & SHAP Attributions</span>
                    </div>
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded-full border border-emerald-300">
                    Positive
                  </span>
                </div>

                <div className="space-y-3">
                  {posFactors.length === 0 ? (
                    <div className="p-4 rounded-xl bg-white border border-emerald-100 text-xs text-slate-500 italic">
                      No positive factors currently qualify under active criteria.
                    </div>
                  ) : (
                    posFactors.map((f, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-white border border-emerald-100 shadow-sm space-y-1.5"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-xs font-bold text-slate-900">{f.label || f.factor}</span>
                          <div className="flex items-center gap-1.5">
                            <span className="text-[11px] font-mono font-bold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                              Value: {f.value_formatted || f.value}
                            </span>
                            <span className="text-[11px] font-mono font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">
                              +{Math.abs(Number(f.shap_contribution || f.contribution || 0)).toFixed(4)} SHAP
                            </span>
                          </div>
                        </div>
                        <p className="text-xs text-slate-600 leading-relaxed">{f.reason || f.detail}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Negative Factors Card (Soft Red) */}
              <div className="p-6 rounded-2xl bg-rose-50 border border-rose-200 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-rose-200 pb-3">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 bg-rose-100 text-rose-700 rounded-lg">
                      <Minus className="w-4 h-4 stroke-[3]" />
                    </div>
                    <div>
                      <h3 className="text-sm sm:text-base font-bold text-rose-950 uppercase tracking-wide">
                        NEGATIVE FACTORS ({negFactors.length})
                      </h3>
                      <span className="text-[11px] font-semibold text-rose-800">Negative Downside Drag & SHAP Penalties</span>
                    </div>
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-rose-100 text-rose-800 rounded-full border border-rose-300">
                    Negative
                  </span>
                </div>

                <div className="space-y-3">
                  {negFactors.length === 0 ? (
                    <div className="p-4 rounded-xl bg-white border border-rose-100 text-xs text-slate-500 italic">
                      No negative factors currently qualify under active criteria.
                    </div>
                  ) : (
                    negFactors.map((f, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-white border border-rose-100 shadow-sm space-y-1.5"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-xs font-bold text-slate-900">{f.label || f.factor}</span>
                          <div className="flex items-center gap-1.5">
                            <span className="text-[11px] font-mono font-bold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                              Value: {f.value_formatted || f.value}
                            </span>
                            <span className="text-[11px] font-mono font-bold text-rose-700 bg-rose-100 px-1.5 py-0.5 rounded">
                              -{Math.abs(Number(f.shap_contribution || f.contribution || 0)).toFixed(4)} SHAP
                            </span>
                          </div>
                        </div>
                        <p className="text-xs text-slate-600 leading-relaxed">{f.reason || f.detail}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* ------------------------------------------------------------------ */}
            {/* 2C. SHAP Feature Importance & Contribution Breakdown */}
            {/* ------------------------------------------------------------------ */}
            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 shadow-sm space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-3">
                <div>
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-purple-600" />
                    <span>
                      {showAllFeatures ? 'All 20 Features' : 'Top 5 Influential Features'} (SHAP TreeExplainer)
                    </span>
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Individual prediction (SHAP), explains the raw model probability before calibration.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setShowAllFeatures(!showAllFeatures)}
                    className="text-xs font-bold px-3 py-1 rounded-lg bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 transition-colors"
                  >
                    {showAllFeatures ? 'Show Top 5 Only' : 'Show All Features (20)'}
                  </button>
                  <span className="text-[11px] font-bold text-purple-700 bg-purple-100 px-2.5 py-1 rounded-md border border-purple-200">
                    Method: {explanation.method || 'TreeExplainer'}
                  </span>
                </div>
              </div>

              {/* Horizontal SHAP Contribution Bar Chart (Signed) */}
              <div className="space-y-3">
                {displayedShap.map((item, idx) => {
                  const contribVal = Number(item.shap_contribution || item.shap_value || 0);
                  const isPos = contribVal >= 0;
                  const absVal = Math.abs(contribVal);
                  // Normalize width relative to 0.15 max expected SHAP
                  const barWidthPct = Math.min(100, Math.max(8, (absVal / 0.15) * 100));

                  return (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-white border border-slate-200 space-y-2 hover:border-purple-200 transition-colors"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[11px] font-bold text-slate-400">#{idx + 1}</span>
                          <span className="font-bold text-slate-800">{item.label || item.feature}</span>
                          <span className="text-slate-500 font-mono text-[11px] bg-slate-100 px-1.5 py-0.5 rounded">
                            Value: {item.value_formatted || item.raw_value || String(item.value)}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] font-bold font-mono ${
                              isPos ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                            }`}
                          >
                            {isPos ? '+' : ''}
                            {contribVal.toFixed(4)} SHAP ({isPos ? 'Positive' : 'Negative'})
                          </span>
                        </div>
                      </div>

                      {/* Diverging Horizontal Bar Chart */}
                      <div className="grid grid-cols-2 gap-1 items-center bg-slate-100 h-3 rounded-full overflow-hidden px-1">
                        {/* Negative side (left) */}
                        <div className="flex justify-end h-full">
                          {!isPos && (
                            <div
                              className="h-full bg-rose-500 rounded-full"
                              style={{ width: `${barWidthPct}%` }}
                            />
                          )}
                        </div>
                        {/* Positive side (right) */}
                        <div className="flex justify-start h-full">
                          {isPos && (
                            <div
                              className="h-full bg-emerald-500 rounded-full"
                              style={{ width: `${barWidthPct}%` }}
                            />
                          )}
                        </div>
                      </div>

                      {item.explanation && (
                        <p className="text-[11px] text-slate-600 leading-snug">{item.explanation}</p>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Separate Global Feature Importance Panel */}
              {globalImportance.length > 0 && (
                <div className="mt-6 pt-4 border-t border-slate-200 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                      Global importance (whole model)
                    </h4>
                    <span className="text-[10px] text-slate-500">
                      Ensemble aggregate importance across all training folds
                    </span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                    {globalImportance.slice(0, 6).map((g, i) => (
                      <div
                        key={i}
                        className="p-2.5 rounded-lg bg-white border border-slate-200 text-xs flex justify-between items-center"
                      >
                        <span className="font-medium text-slate-800 truncate mr-2">{g.label || g.feature}</span>
                        <span className="font-mono text-purple-700 font-bold bg-purple-50 px-1.5 py-0.5 rounded">
                          {(g.importance * 100).toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* ------------------------------------------------------------------ */}
            {/* 2D. Smart Quantitative Risk Warnings */}
            {/* ------------------------------------------------------------------ */}
            <div className="p-6 rounded-2xl bg-amber-50 border border-amber-200 shadow-sm space-y-3">
              <div className="flex items-center justify-between border-b border-amber-200 pb-2">
                <div className="flex items-center gap-2 text-amber-900">
                  <ShieldAlert className="w-5 h-5 text-amber-600 flex-shrink-0" />
                  <h3 className="text-sm sm:text-base font-bold uppercase tracking-wide">
                    SMART RISK WARNINGS & VOLATILITY ALERTS ({riskAlerts.length})
                  </h3>
                </div>
                <span className="text-[10px] font-bold text-amber-800 bg-amber-100 px-2 py-0.5 rounded">
                  Cautionary Checks
                </span>
              </div>

              {riskAlerts.length === 0 ? (
                <div className="p-4 rounded-xl bg-white border border-amber-100 text-xs text-slate-600">
                  No risk alerts triggered by current data.
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                  {riskAlerts.map((w, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-white border border-amber-200 shadow-sm space-y-1"
                    >
                      <div className="flex items-center justify-between text-xs font-bold text-amber-950">
                        <span>{w.trigger_metric || w.type}</span>
                        <span className="uppercase text-[9px] px-1.5 py-0.5 rounded font-bold bg-amber-100 text-amber-800">
                          Trigger: {w.trigger_value} (Limit: {w.threshold_value})
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">{w.message}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* ------------------------------------------------------------------ */}
            {/* 2E. AI Explanation Summary & Limitations Box */}
            {/* ------------------------------------------------------------------ */}
            <div className="p-6 rounded-2xl bg-gradient-to-r from-purple-100/70 via-sky-50 to-purple-50 border border-purple-200 shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-purple-900">
                <Sparkles className="w-4 h-4 text-purple-700" />
                <h3 className="text-xs font-bold uppercase tracking-wide">
                  AI EXPLANATION SUMMARY & QUANTITATIVE VERDICT
                </h3>
              </div>
              <p className="text-xs sm:text-sm text-slate-800 leading-relaxed font-medium">
                {explanation.summary || explanation.final_summary}
              </p>

              {explanation.limitations && (
                <div className="pt-2 border-t border-purple-200/60 text-[11px] text-slate-500 space-y-1">
                  <span className="font-semibold text-slate-700">Methodological Disclosures:</span>
                  <ul className="list-disc pl-4 space-y-0.5">
                    {explanation.limitations.map((lim, i) => (
                      <li key={i}>{lim}</li>
                    ))}
                  </ul>
                </div>
              )}
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
                        aria-label={`Explain AI trading decision for ${p.symbol}`}
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
