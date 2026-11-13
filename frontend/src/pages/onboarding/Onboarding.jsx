import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sliders, ShieldCheck, CheckCircle, Database, ArrowRight } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Badge, DataProvenanceFooter, EmptyState } from '../../components/UIState';

export default function Onboarding() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);

  useEffect(() => {
    document.title = 'Investor Profiler & Onboarding — AlphaWatch AI';
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-4">
      {/* Wizard Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold text-blue-400 bg-blue-950/60 border border-blue-700/50">
          <Sliders className="w-3.5 h-3.5" />
          <span>Rule-Based Investor Profiler</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Portfolio Input & Adaptive Risk Profiling
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 max-w-xl mx-auto">
          AlphaWatch uses deterministic rules (no LLM hallucinations) to compute your Investor Pattern and threshold profile.
        </p>
      </div>

      {/* Step Indicators */}
      <div className="grid grid-cols-3 gap-2 sm:gap-4 text-xs font-semibold">
        <button
          onClick={() => setStep(1)}
          className={`p-3 rounded-xl border text-left transition-all ${
            step === 1
              ? 'bg-blue-950/60 border-blue-600 text-white'
              : 'bg-slate-900/40 border-slate-800 text-slate-400'
          }`}
        >
          <span className="block text-[10px] text-blue-400 uppercase font-mono">Step 1</span>
          <span>Holdings Input</span>
        </button>
        <button
          onClick={() => setStep(2)}
          className={`p-3 rounded-xl border text-left transition-all ${
            step === 2
              ? 'bg-blue-950/60 border-blue-600 text-white'
              : 'bg-slate-900/40 border-slate-800 text-slate-400'
          }`}
        >
          <span className="block text-[10px] text-blue-400 uppercase font-mono">Step 2</span>
          <span>Fixed Questions</span>
        </button>
        <button
          onClick={() => setStep(3)}
          className={`p-3 rounded-xl border text-left transition-all ${
            step === 3
              ? 'bg-blue-950/60 border-blue-600 text-white'
              : 'bg-slate-900/40 border-slate-800 text-slate-400'
          }`}
        >
          <span className="block text-[10px] text-blue-400 uppercase font-mono">Step 3</span>
          <span>Investor Pattern</span>
        </button>
      </div>

      {/* Step Container Card */}
      <div className="p-6 sm:p-8 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
        {step === 1 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white">Enter Portfolio Holdings</h3>
                <p className="text-xs text-slate-400">Add supported NSE stocks or select a DEMO preset</p>
              </div>
              <div className="flex gap-2">
                <Badge variant="primary" label="DEMO PRESETS AVAILABLE" />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-white">Balanced Large-Cap</h4>
                  <Badge variant="low" label="DEMO" />
                </div>
                <p className="text-[11px] text-slate-400">RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-white">High-Beta Momentum</h4>
                  <Badge variant="high" label="DEMO" />
                </div>
                <p className="text-[11px] text-slate-400">TATASTEEL, SBIN, AXISBANK, MARUTI, LT</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-white">Dividend & Value</h4>
                  <Badge variant="medium" label="DEMO" />
                </div>
                <p className="text-[11px] text-slate-400">ITC, COALINDIA, POWERGRID, NTPC, ONGC</p>
              </div>
            </div>

            <div className="pt-4 flex justify-end">
              <button
                onClick={() => setStep(2)}
                className="inline-flex items-center gap-2 px-5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm"
              >
                <span>Continue to Fixed Questions</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <div className="border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white">Risk Profile Questions</h3>
              <p className="text-xs text-slate-400">Evaluate goal, horizon, and market reaction</p>
            </div>
            <div className="space-y-3 text-xs text-slate-300">
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                <p className="font-semibold text-white mb-1">1. Investment Goal</p>
                <p className="text-slate-400">Capital Wealth Creation &bull; Long-Term Compounding</p>
              </div>
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                <p className="font-semibold text-white mb-1">2. Market Reaction (10% Drawdown)</p>
                <p className="text-slate-400">Hold positions and systematically rebalance</p>
              </div>
            </div>
            <div className="pt-4 flex justify-between">
              <button
                onClick={() => setStep(1)}
                className="px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 rounded-lg"
              >
                Back
              </button>
              <button
                onClick={() => setStep(3)}
                className="inline-flex items-center gap-2 px-5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm"
              >
                <span>Derive Investor Pattern</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <div className="border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white">Calculated Investor Pattern</h3>
              <p className="text-xs text-slate-400">Transparent mathematical scoring with visible rule derivation</p>
            </div>

            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400 block">Suggested Profile</span>
                  <span className="text-base font-bold text-white">Moderate (0.60 BUY / 0.40 SELL)</span>
                </div>
                <Badge variant="medium" label="RISK SCORE: 54 / 100" />
              </div>
              <div className="p-3 bg-slate-900 rounded-lg text-xs text-slate-300 border border-slate-800/80">
                <p className="font-semibold text-blue-400 mb-0.5">Why this profile:</p>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Derived from long-term horizon (3-5 years) paired with balanced large-cap concentration (&lt;30% in single security) and disciplined drawdown tolerance.
                </p>
              </div>
            </div>

            <div className="pt-4 flex justify-between">
              <button
                onClick={() => setStep(2)}
                className="px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 rounded-lg"
              >
                Back
              </button>
              <button
                onClick={() => navigate('/dashboard/overview')}
                className="inline-flex items-center gap-2 px-5 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 rounded-lg shadow-sm"
              >
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Complete Onboarding & Enter Dashboard</span>
              </button>
            </div>
          </div>
        )}
      </div>

      <DataProvenanceFooter
        source="src/profiler.py (Deterministic Rules)"
        asOf="Current Session"
        status="Rule Engine Ready"
      />
    </div>
  );
}
