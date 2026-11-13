import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sliders,
  ShieldCheck,
  CheckCircle,
  Plus,
  Trash2,
  ArrowRight,
  ArrowLeft,
  AlertTriangle,
  AlertCircle,
  RefreshCw,
  BarChart2,
  Layers,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import {
  Badge,
  DataProvenanceFooter,
  EmptyState,
  ErrorMessage,
  LoadingSpinner,
} from '../../components/UIState';
import {
  getOnboardingDataApi,
  submitOnboardingApi,
} from '../../api/client';

export default function Onboarding() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Metadata from backend
  const [supportedSymbols, setSupportedSymbols] = useState([]);
  const [demoPortfolios, setDemoPortfolios] = useState({});

  // Step 1: Holdings state
  const [holdings, setHoldings] = useState([]);

  // Step 2: Fixed Questions state
  const [answers, setAnswers] = useState({
    goal: 'Wealth Creation',
    horizon: '3-5 Years',
    experience: 'Intermediate',
    trading_frequency: 'Monthly',
    fall_reaction: 'Hold and observe',
    savings_share: '10-25%',
    preferred_sectors: ['Technology', 'Financials'],
  });

  // Step 3: Evaluation results from server profiler
  const [evaluation, setEvaluation] = useState(null);

  useEffect(() => {
    document.title = 'Investor Profiler & Onboarding — AlphaWatch AI';

    async function loadData() {
      try {
        setLoading(true);
        const data = await getOnboardingDataApi();
        if (data?.symbols) setSupportedSymbols(data.symbols);
        if (data?.demoPortfolios) setDemoPortfolios(data.demoPortfolios);

        if (data?.holdings && data.holdings.length > 0) {
          setHoldings(data.holdings);
        } else {
          // Pre-populate with Moderate Balanced demo preset for beginner convenience
          setHoldings([
            { symbol: 'RELIANCE', quantity: 15, buy_price: 2780.0, buy_date: '2024-01-15' },
            { symbol: 'ICICIBANK', quantity: 30, buy_price: 1080.0, buy_date: '2024-02-10' },
            { symbol: 'INFY', quantity: 25, buy_price: 1610.0, buy_date: '2024-03-01' },
            { symbol: 'LT', quantity: 10, buy_price: 3450.0, buy_date: '2024-04-12' },
          ]);
        }

        if (data?.profile?.answers) {
          setAnswers((prev) => ({ ...prev, ...data.profile.answers }));
        }
      } catch (err) {
        setError(err.message || 'Failed to load onboarding options.');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  // Preset Loaders
  function handleSelectPreset(presetKey) {
    const preset = demoPortfolios[presetKey];
    if (preset && preset.length > 0) {
      setHoldings(
        preset.map((h) => ({
          symbol: h.symbol,
          quantity: h.quantity,
          buy_price: h.buy_price,
          buy_date: '2024-01-10',
        }))
      );
      setError(null);
    }
  }

  // Holdings Management
  function handleAddRow() {
    const defaultSym = supportedSymbols[0]?.symbol || 'RELIANCE';
    setHoldings([
      ...holdings,
      { symbol: defaultSym, quantity: 10, buy_price: 1000.0, buy_date: new Date().toISOString().split('T')[0] },
    ]);
  }

  function handleRemoveRow(index) {
    setHoldings(holdings.filter((_, i) => i !== index));
  }

  function handleUpdateHolding(index, field, value) {
    const updated = [...holdings];
    updated[index] = { ...updated[index], [field]: value };
    setHoldings(updated);
  }

  // Step 1 Validation
  function validateStep1() {
    if (holdings.length === 0) {
      setError('Please add at least one holding or select a DEMO preset to continue.');
      return false;
    }
    for (let i = 0; i < holdings.length; i++) {
      const h = holdings[i];
      if (!h.symbol) {
        setError(`Holding row #${i + 1} is missing a stock symbol.`);
        return false;
      }
      if (Number(h.quantity) <= 0 || isNaN(Number(h.quantity))) {
        setError(`Invalid quantity for ${h.symbol}. Must be a positive integer.`);
        return false;
      }
      if (Number(h.buy_price) <= 0 || isNaN(Number(h.buy_price))) {
        setError(`Invalid buy price for ${h.symbol}. Must be greater than 0.`);
        return false;
      }
    }
    setError(null);
    return true;
  }

  function handleContinueToQuestions() {
    if (validateStep1()) {
      setStep(2);
    }
  }

  // Step 2 Submission to Server Profiler
  async function handleSubmitProfiler(e) {
    if (e) e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const payload = {
        holdings: holdings.map((h) => ({
          symbol: h.symbol.trim().toUpperCase(),
          quantity: Math.floor(Number(h.quantity)),
          buy_price: Number(h.buy_price),
          buy_date: h.buy_date || null,
        })),
        answers,
      };

      const res = await submitOnboardingApi(payload);
      if (res?.evaluation) {
        setEvaluation(res.evaluation);
        setStep(3);
      } else {
        throw new Error('Profiler returned incomplete evaluation.');
      }
    } catch (err) {
      setError(err.message || 'Profiler evaluation failed.');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleFinish() {
    try {
      await refreshUser();
      navigate('/dashboard/overview');
    } catch {
      navigate('/dashboard/overview');
    }
  }

  // Calculate live portfolio summary for Step 1
  const totalCost = holdings.reduce(
    (acc, h) => acc + (Number(h.quantity) || 0) * (Number(h.buy_price) || 0),
    0
  );

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-4 px-2 sm:px-0">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold text-blue-400 bg-blue-950/60 border border-blue-700/50">
          <Sliders className="w-3.5 h-3.5" />
          <span>Rule-Based Investor Profiler</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Portfolio Input & Adaptive Risk Profiling
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 max-w-xl mx-auto leading-relaxed">
          AlphaWatch uses documented mathematical rules (no LLM hallucination) to assign your personal signal thresholds and risk parameters.
        </p>
      </div>

      {/* Progress Bar & Tabs */}
      <div className="space-y-2">
        <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${(step / 3) * 100}%` }}
          />
        </div>
        <div className="grid grid-cols-3 gap-2 sm:gap-4 text-xs font-semibold">
          <button
            onClick={() => setStep(1)}
            className={`p-3 rounded-xl border text-left transition-all ${
              step === 1
                ? 'bg-blue-950/60 border-blue-600 text-white shadow-sm'
                : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            <span className="block text-[10px] text-blue-400 uppercase font-mono">Step 1</span>
            <span className="truncate block">Holdings Input</span>
          </button>
          <button
            onClick={() => {
              if (validateStep1()) setStep(2);
            }}
            className={`p-3 rounded-xl border text-left transition-all ${
              step === 2
                ? 'bg-blue-950/60 border-blue-600 text-white shadow-sm'
                : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            <span className="block text-[10px] text-blue-400 uppercase font-mono">Step 2</span>
            <span className="truncate block">Fixed Questions</span>
          </button>
          <button
            disabled={!evaluation}
            onClick={() => evaluation && setStep(3)}
            className={`p-3 rounded-xl border text-left transition-all ${
              step === 3
                ? 'bg-blue-950/60 border-blue-600 text-white shadow-sm'
                : 'bg-slate-900/40 border-slate-800 text-slate-500 disabled:opacity-50'
            }`}
          >
            <span className="block text-[10px] text-blue-400 uppercase font-mono">Step 3</span>
            <span className="truncate block">Investor Pattern</span>
          </button>
        </div>
      </div>

      {error && <ErrorMessage message={error} onRetry={() => setError(null)} />}

      {loading ? (
        <LoadingSpinner text="Loading onboarding engine and supported securities..." />
      ) : (
        <div className="p-4 sm:p-8 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
          {/* ================================================================ */}
          {/* STEP 1: HOLDINGS INPUT                                          */}
          {/* ================================================================ */}
          {step === 1 && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <h3 className="text-base font-bold text-white">Enter Your Portfolio Holdings</h3>
                  <p className="text-xs text-slate-400">
                    Add your actual stock holdings or choose an instant verified DEMO preset.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono text-slate-400">Total Basis:</span>
                  <span className="text-xs font-bold font-mono text-white">
                    ₹{totalCost.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </span>
                </div>
              </div>

              {/* Demo Preset Cards */}
              <div className="space-y-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Quick Load: Verified NSE Demo Portfolios
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <button
                    type="button"
                    onClick={() => handleSelectPreset('Conservative Income')}
                    className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 hover:border-emerald-600/60 text-left transition-all group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-white group-hover:text-emerald-400">
                        Conservative Income
                      </span>
                      <Badge variant="low" label="DEMO" />
                    </div>
                    <p className="text-[11px] text-slate-400">HDFCBANK, ITC, TCS</p>
                    <span className="text-[10px] text-emerald-400 block mt-1">Low volatility &bull; 10% max weight</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleSelectPreset('Moderate Balanced')}
                    className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 hover:border-blue-600/60 text-left transition-all group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-white group-hover:text-blue-400">
                        Moderate Balanced
                      </span>
                      <Badge variant="medium" label="DEMO" />
                    </div>
                    <p className="text-[11px] text-slate-400">RELIANCE, ICICIBANK, INFY, LT</p>
                    <span className="text-[10px] text-blue-400 block mt-1">Multi-sector &bull; 20% max weight</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleSelectPreset('Aggressive Growth')}
                    className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 hover:border-rose-600/60 text-left transition-all group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-white group-hover:text-rose-400">
                        Aggressive Growth
                      </span>
                      <Badge variant="high" label="DEMO" />
                    </div>
                    <p className="text-[11px] text-slate-400">TATASTEEL, BAJFINANCE, TITAN, MARUTI</p>
                    <span className="text-[10px] text-rose-400 block mt-1">High-beta momentum &bull; 30% max weight</span>
                  </button>
                </div>
              </div>

              {/* Holdings Table */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    Holdings Table ({holdings.length} securities)
                  </h4>
                  <button
                    type="button"
                    onClick={handleAddRow}
                    className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium text-blue-400 hover:text-blue-300 bg-blue-950/40 border border-blue-800/60 rounded-lg"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Security</span>
                  </button>
                </div>

                <div className="overflow-x-auto border border-slate-800 rounded-xl bg-slate-950">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-900/80 text-slate-400 font-mono text-[11px] uppercase border-b border-slate-800">
                      <tr>
                        <th className="py-2.5 px-3">Symbol</th>
                        <th className="py-2.5 px-3">Quantity</th>
                        <th className="py-2.5 px-3">Buy Price (₹)</th>
                        <th className="py-2.5 px-3">Weight (Est)</th>
                        <th className="py-2.5 px-3">Buy Date</th>
                        <th className="py-2.5 px-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {holdings.map((h, idx) => {
                        const cost = (Number(h.quantity) || 0) * (Number(h.buy_price) || 0);
                        const weight = totalCost > 0 ? (cost / totalCost) * 100 : 0;
                        const isConcentrated = weight > 30.0;

                        return (
                          <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                            <td className="py-2 px-3">
                              <select
                                value={h.symbol}
                                onChange={(e) => handleUpdateHolding(idx, 'symbol', e.target.value)}
                                className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-blue-500"
                              >
                                {supportedSymbols.map((s) => (
                                  <option key={s.symbol} value={s.symbol}>
                                    {s.symbol} — {s.name || s.symbol}
                                  </option>
                                ))}
                              </select>
                            </td>
                            <td className="py-2 px-3">
                              <input
                                type="number"
                                min="1"
                                step="1"
                                value={h.quantity}
                                onChange={(e) => handleUpdateHolding(idx, 'quantity', e.target.value)}
                                className="w-20 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                              />
                            </td>
                            <td className="py-2 px-3">
                              <input
                                type="number"
                                min="0.05"
                                step="0.05"
                                value={h.buy_price}
                                onChange={(e) => handleUpdateHolding(idx, 'buy_price', e.target.value)}
                                className="w-24 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                              />
                            </td>
                            <td className="py-2 px-3">
                              <span
                                className={`font-semibold ${
                                  isConcentrated ? 'text-amber-400 font-bold' : 'text-slate-300'
                                }`}
                              >
                                {weight.toFixed(1)}%
                              </span>
                              {isConcentrated && (
                                <span className="ml-1 text-[10px] text-amber-500">&gt;30%</span>
                              )}
                            </td>
                            <td className="py-2 px-3">
                              <input
                                type="date"
                                value={h.buy_date || ''}
                                onChange={(e) => handleUpdateHolding(idx, 'buy_date', e.target.value)}
                                className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-300 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                              />
                            </td>
                            <td className="py-2 px-3 text-right">
                              <button
                                type="button"
                                onClick={() => handleRemoveRow(idx)}
                                className="p-1 text-slate-400 hover:text-red-400 transition-colors"
                                title="Remove row"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Navigation Action */}
              <div className="pt-4 flex justify-end">
                <button
                  type="button"
                  onClick={handleContinueToQuestions}
                  className="inline-flex items-center gap-2 px-6 py-2.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-xl shadow-sm transition-all"
                >
                  <span>Continue to Fixed Questions</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* ================================================================ */}
          {/* STEP 2: FIXED QUESTIONS                                         */}
          {/* ================================================================ */}
          {step === 2 && (
            <form onSubmit={handleSubmitProfiler} className="space-y-6">
              <div className="border-b border-slate-800 pb-3">
                <h3 className="text-base font-bold text-white">Risk Profile & Behavioral Questions</h3>
                <p className="text-xs text-slate-400">
                  Fixed questions evaluated against deterministic rules defined in <code className="text-blue-400">src/profiler.py</code>.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                {/* 1. Goal */}
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <label className="font-semibold text-white block">
                    1. Primary Investment Objective
                  </label>
                  <select
                    value={answers.goal}
                    onChange={(e) => setAnswers({ ...answers, goal: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="Capital Preservation">Capital Preservation (Defensive focus)</option>
                    <option value="Income">Steady Dividend & Income Generation</option>
                    <option value="Wealth Creation">Long-Term Wealth Creation & Compounding</option>
                    <option value="Speculative Growth">Aggressive Capital Appreciation</option>
                  </select>
                  <p className="text-[10px] text-slate-500">Affects base risk allocation by +/-15 points.</p>
                </div>

                {/* 2. Horizon */}
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <label className="font-semibold text-white block">
                    2. Target Investment Horizon
                  </label>
                  <select
                    value={answers.horizon}
                    onChange={(e) => setAnswers({ ...answers, horizon: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="< 1 Year">&lt; 1 Year (Short term liquidity)</option>
                    <option value="1-3 Years">1 to 3 Years (Medium term)</option>
                    <option value="3-5 Years">3 to 5 Years (Standard equity cycle)</option>
                    <option value="> 5 Years">&gt; 5 Years (Multi-cycle compounding)</option>
                  </select>
                  <p className="text-[10px] text-slate-500">Short horizons dampen risk tolerance systematically.</p>
                </div>

                {/* 3. Market Experience */}
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <label className="font-semibold text-white block">
                    3. Market Experience in Indian Equities
                  </label>
                  <select
                    value={answers.experience}
                    onChange={(e) => setAnswers({ ...answers, experience: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="Beginner (&lt; 1 Year)">Beginner (&lt; 1 year in equities)</option>
                    <option value="Intermediate (1-3 Years)">Intermediate (1 to 3 years)</option>
                    <option value="Advanced (&gt; 3 Years)">Advanced (&gt; 3 years trading/investing)</option>
                  </select>
                </div>

                {/* 4. Reaction to 10% fall */}
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <label className="font-semibold text-white block">
                    4. Reaction to sudden -10% Portfolio Drawdown
                  </label>
                  <select
                    value={answers.fall_reaction}
                    onChange={(e) => setAnswers({ ...answers, fall_reaction: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="Panic sell everything">Panic sell everything (Preserve capital)</option>
                    <option value="Sell partial to reduce risk">Sell partial positions to cut risk</option>
                    <option value="Hold and observe">Hold and observe (Stay the course)</option>
                    <option value="Buy more aggressively">Buy more aggressively (Accumulate value)</option>
                  </select>
                  <p className="text-[10px] text-slate-500">Stress sensitivity trigger in mathematical scoring.</p>
                </div>

                {/* 5. Savings share */}
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <label className="font-semibold text-white block">
                    5. Share of Liquid Savings Allocated to Equities
                  </label>
                  <select
                    value={answers.savings_share}
                    onChange={(e) => setAnswers({ ...answers, savings_share: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="< 10%">&lt; 10% of total savings</option>
                    <option value="10-25%">10% to 25% of savings</option>
                    <option value="25-50%">25% to 50% of savings</option>
                    <option value="> 50%">&gt; 50% of total liquid net worth</option>
                  </select>
                </div>

                {/* 6. Trading frequency */}
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <label className="font-semibold text-white block">
                    6. Anticipated Rebalancing Frequency
                  </label>
                  <select
                    value={answers.trading_frequency}
                    onChange={(e) => setAnswers({ ...answers, trading_frequency: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="Daily">Daily / Swing Trading</option>
                    <option value="Weekly">Weekly Tactical Adjustments</option>
                    <option value="Monthly">Monthly Systematic Review</option>
                    <option value="Quarterly">Quarterly / Semi-annual Buy & Hold</option>
                  </select>
                </div>
              </div>

              {/* Navigation Action */}
              <div className="pt-4 flex justify-between items-center">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 rounded-xl transition-all"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Back to Holdings</span>
                </button>

                <button
                  type="submit"
                  disabled={submitting}
                  className="inline-flex items-center gap-2 px-6 py-2.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-xl shadow-sm transition-all disabled:opacity-50"
                >
                  {submitting ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4" />
                  )}
                  <span>{submitting ? 'Running Quantitative Profiler...' : 'Compute Investor Pattern'}</span>
                </button>
              </div>
            </form>
          )}

          {/* ================================================================ */}
          {/* STEP 3: INVESTOR PATTERN & ADAPTIVE FOLLOW-UPS                  */}
          {/* ================================================================ */}
          {step === 3 && evaluation && (
            <div className="space-y-6">
              <div className="border-b border-slate-800 pb-3">
                <h3 className="text-base font-bold text-white">Your Computed Investor Pattern</h3>
                <p className="text-xs text-slate-400">
                  Transparent mathematical evaluation with full rule provenance. No subjective AI assumptions.
                </p>
              </div>

              {/* Pattern Scorecard */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-[11px] uppercase tracking-wider text-slate-400 block font-mono">
                    Assigned Profile
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-bold text-white">
                      {evaluation.suggested_profile}
                    </span>
                    <Badge
                      variant={
                        evaluation.suggested_profile === 'Conservative'
                          ? 'low'
                          : evaluation.suggested_profile === 'Aggressive'
                          ? 'high'
                          : 'medium'
                      }
                      label={evaluation.suggested_profile.toUpperCase()}
                    />
                  </div>
                  <p className="text-[10px] text-slate-500 pt-1">
                    Thresholds: BUY &ge;{' '}
                    {evaluation.suggested_profile === 'Conservative'
                      ? '0.65'
                      : evaluation.suggested_profile === 'Aggressive'
                      ? '0.55'
                      : '0.60'}
                    , SELL &le;{' '}
                    {evaluation.suggested_profile === 'Conservative'
                      ? '0.35'
                      : evaluation.suggested_profile === 'Aggressive'
                      ? '0.45'
                      : '0.40'}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-[11px] uppercase tracking-wider text-slate-400 block font-mono">
                    Risk Score
                  </span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-2xl font-mono font-bold text-white">
                      {evaluation.risk_score}
                    </span>
                    <span className="text-xs text-slate-500 font-mono">/ 100</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mt-1">
                    <div
                      className={`h-full ${
                        evaluation.risk_score > 65
                          ? 'bg-rose-500'
                          : evaluation.risk_score < 40
                          ? 'bg-emerald-500'
                          : 'bg-amber-500'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(0, evaluation.risk_score))}%` }}
                    />
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-[11px] uppercase tracking-wider text-slate-400 block font-mono">
                    Diversification
                  </span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-2xl font-mono font-bold text-white">
                      {evaluation.diversification_score}
                    </span>
                    <span className="text-xs text-slate-500 font-mono">/ 100</span>
                  </div>
                  <span className="text-[11px] text-slate-400 block pt-1">
                    Status: <strong className="text-slate-200">{evaluation.concentration_status}</strong>
                  </span>
                </div>
              </div>

              {/* "Why this profile" Derivation Box */}
              <div className="p-4 rounded-xl bg-slate-950 border border-blue-900/40 space-y-2">
                <div className="flex items-center gap-2 text-blue-400 text-xs font-bold uppercase tracking-wider">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Rule Engine Derivation (Why This Profile):</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  {evaluation.why_this_profile}
                </p>
                <div className="pt-2 text-[11px] text-slate-500 flex items-center gap-4 border-t border-slate-900">
                  <span>Holding Style: <strong className="text-slate-300">{evaluation.holding_style}</strong></span>
                  <span>Evaluated at: <strong className="text-slate-300">{new Date().toLocaleTimeString()}</strong></span>
                </div>
              </div>

              {/* Adaptive Follow-ups triggered by holding concentration or drawdowns */}
              {evaluation.adaptive_followups && evaluation.adaptive_followups.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Adaptive Rule Follow-Ups & Mitigations</span>
                  </h4>
                  <div className="space-y-2">
                    {evaluation.adaptive_followups.map((af, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-amber-950/30 border border-amber-800/50 space-y-1 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-amber-200">{af.rule}</span>
                          <Badge variant="medium" label="ADAPTIVE RULE" />
                        </div>
                        <p className="text-slate-300">{af.message}</p>
                        {af.recommendation && (
                          <p className="text-[11px] text-amber-300 font-medium pt-1">
                            &bull; Recommendation: {af.recommendation}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Final Confirm Button */}
              <div className="pt-4 flex justify-between items-center">
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 rounded-xl transition-all"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Adjust Answers</span>
                </button>

                <button
                  type="button"
                  onClick={handleFinish}
                  className="inline-flex items-center gap-2 px-6 py-2.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 rounded-xl shadow-sm transition-all"
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>Complete Onboarding & Enter Dashboard</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      <DataProvenanceFooter
        source="src/profiler.py (Deterministic Rules Engine) & NSE Bhavcopy Archives"
        asOf={new Date().toISOString().split('T')[0]}
        status="Mathematical Scoring Active"
      />
    </div>
  );
}
