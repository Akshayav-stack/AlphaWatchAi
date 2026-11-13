import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  ShieldCheck,
  LayoutDashboard,
  Sliders,
  AlertTriangle,
  ArrowRight,
  Database,
  Layers,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { DataProvenanceFooter } from '../../components/UIState';

export default function Home() {
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    document.title = 'AlphaWatch AI — ASTRAQUANT X 2026';
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) {
      metaDesc.setAttribute(
        'content',
        'Offline-first algorithmic trading intelligence and quantitative risk workstation for the Indian equity market.'
      );
    }
  }, []);

  return (
    <div className="space-y-16 py-4">
      {/* Hero Section */}
      <section className="text-center space-y-6 pt-4 pb-4 max-w-4xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold text-blue-400 bg-blue-950/60 border border-blue-700/50 shadow-sm">
          <Layers className="w-3.5 h-3.5" />
          <span>ASTRAQUANT X 2026 &bull; Problem Statement 16</span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
          Risk-First Algorithmic Trading Intelligence for Indian Equities
        </h1>

        <p className="text-sm sm:text-base text-slate-300 max-w-2xl mx-auto leading-relaxed">
          A self-contained, 100% offline workstation turning historical NSE Bhavcopy archives into transparent machine learning signals, walk-forward risk diagnostics, and realistic backtests.
        </p>

        {/* Two Clear CTA Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          {isAuthenticated ? (
            <Link
              to="/dashboard/overview"
              className="inline-flex items-center gap-2 px-6 py-3 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-xl shadow-lg shadow-blue-500/20 transition-all"
            >
              <span>Enter Research Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          ) : (
            <>
              <Link
                to="/register"
                className="inline-flex items-center gap-2 px-6 py-3 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-xl shadow-lg shadow-blue-500/20 transition-all"
              >
                <span>Register</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/how-it-works"
                className="inline-flex items-center gap-2 px-6 py-3 text-sm font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl transition-all"
              >
                <span>How It Works</span>
              </Link>
            </>
          )}
        </div>
      </section>

      {/* 3 Feature Cards (Risk-First Signals, Personal Dashboard, Honest Backtests) */}
      <section className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Feature Card 1: Risk-First Signals */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors space-y-4">
            <div className="w-12 h-12 rounded-xl bg-blue-950/80 border border-blue-700/60 flex items-center justify-center text-blue-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div className="space-y-1.5">
              <h3 className="text-base font-bold text-white">Risk-First Signals</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Directional probabilities derived from past-only technical features, calibrated on validation data, and filtered through profile risk thresholds (Conservative, Moderate, Aggressive).
              </p>
            </div>
            <div className="text-[11px] font-semibold text-blue-400">
              &bull; 20d Volatility &bull; 95% Historical VaR &bull; CVaR
            </div>
          </div>

          {/* Feature Card 2: Personal Dashboard */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors space-y-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-950/80 border border-emerald-700/60 flex items-center justify-center text-emerald-400">
              <LayoutDashboard className="w-6 h-6" />
            </div>
            <div className="space-y-1.5">
              <h3 className="text-base font-bold text-white">Personal Dashboard</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Track your holdings marked against latest saved close prices, monitor single-stock concentration warnings above 30%, and inspect computed SHAP feature attributions.
              </p>
            </div>
            <div className="text-[11px] font-semibold text-emerald-400">
              &bull; Strict per-user isolation &bull; Real mark-to-market
            </div>
          </div>

          {/* Feature Card 3: Honest Backtests */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors space-y-4">
            <div className="w-12 h-12 rounded-xl bg-amber-950/80 border border-amber-700/60 flex items-center justify-center text-amber-400">
              <Sliders className="w-6 h-6" />
            </div>
            <div className="space-y-1.5">
              <h3 className="text-base font-bold text-white">Honest Backtests</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Realistic execution delay (Day t+1 market Open) with Indian statutory friction: 0.10% delivery STT, 0.03% brokerage, exchange charges, and 0.05% execution slippage.
              </p>
            </div>
            <div className="text-[11px] font-semibold text-amber-400">
              &bull; ~0.35% round-trip friction &bull; No lookahead bias
            </div>
          </div>
        </div>
      </section>

      {/* Short "Honest Limitations" Strip */}
      <section className="p-4 sm:p-5 rounded-xl bg-slate-900/40 border border-amber-900/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 text-xs text-slate-300">
          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <span>
            <strong className="text-amber-300">Honest Limitations:</strong> Bhavcopy prices are unadjusted for stock splits/bonus issues; historical survivorship bias applies; signals are educational models, not live investment advice.
          </span>
        </div>
        <Link
          to="/limitations"
          className="text-xs font-semibold text-blue-400 hover:text-blue-300 whitespace-nowrap pl-6 sm:pl-0"
        >
          View Full Audit &rarr;
        </Link>
      </section>

      {/* Provenance Stamp */}
      <DataProvenanceFooter
        source="NSE CM-UDiFF Archive"
        asOf="Verified Local Files"
        status="Deterministic Engine"
      />
    </div>
  );
}
