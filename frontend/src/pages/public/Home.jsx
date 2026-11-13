import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  ShieldCheck,
  Cpu,
  Database,
  ArrowRight,
  Sliders,
  AlertTriangle,
  Lock,
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
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="text-center space-y-6 pt-4 pb-8 max-w-4xl mx-auto">
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
                <span>Launch Workstation</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/how-it-works"
                className="inline-flex items-center gap-2 px-6 py-3 text-sm font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl transition-all"
              >
                <span>Explore 5-Layer Build</span>
              </Link>
            </>
          )}
        </div>

        {/* Feature Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-6 text-xs text-slate-400">
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
            <span className="font-semibold text-slate-200 block">100% Offline</span>
            <span>Zero external network calls</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
            <span className="font-semibold text-slate-200 block">Zero Lookahead</span>
            <span>Past-only feature matrix</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
            <span className="font-semibold text-slate-200 block">Realistic T+1 Open</span>
            <span>STT, brokerage & slippage</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
            <span className="font-semibold text-slate-200 block">Positive-Loss VaR</span>
            <span>Reported strictly as L &ge; 0</span>
          </div>
        </div>
      </section>

      {/* 3 Core Architecture Pillars */}
      <section className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Transparent Quantitative Engineering
          </h2>
          <p className="text-xs sm:text-sm text-slate-400">
            Three mathematically grounded pillars replace black-box promotional claims.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors space-y-3">
            <div className="w-10 h-10 rounded-lg bg-blue-950/80 border border-blue-700/60 flex items-center justify-center text-blue-400">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-white">
              Walk-Forward Machine Learning
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Random Forest main model trained with 5-fold expanding walk-forward splits. Calibrated with isotonic/sigmoid regression on validation data only. Predictions explained via SHAP TreeExplainer feature attributions.
            </p>
            <div className="pt-2 text-[11px] text-blue-400 font-medium">
              &bull; Strict 70/15/15 chronological split
            </div>
          </div>

          {/* Card 2 */}
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors space-y-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-950/80 border border-emerald-700/60 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-white">
              Positive-Loss Risk Analytics
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Computes 20-day annualized volatility ($\text{ddof}=1$), 1-year rolling max drawdown, and 95% 1-day historical Value at Risk (VaR) & Expected Shortfall (CVaR). Adheres strictly to positive-loss convention ($L = -R$).
            </p>
            <div className="pt-2 text-[11px] text-emerald-400 font-medium">
              &bull; Tercile cross-sectional ranking
            </div>
          </div>

          {/* Card 3 */}
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors space-y-3">
            <div className="w-10 h-10 rounded-lg bg-amber-950/80 border border-amber-700/60 flex items-center justify-center text-amber-400">
              <Sliders className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-white">
              Realistic T+1 Friction Backtest
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Signals generated at Day $t$ Close execute at Day $t+1$ Open. Automatically deducts Indian statutory friction: 0.10% delivery STT, 0.03% brokerage, exchange & SEBI charges, and 0.05% slippage.
            </p>
            <div className="pt-2 text-[11px] text-amber-400 font-medium">
              &bull; ~0.35% round-trip friction model
            </div>
          </div>
        </div>
      </section>

      {/* Honest Limitations Section */}
      <section className="p-6 rounded-xl bg-slate-900/40 border border-amber-900/40 space-y-3">
        <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
          <AlertTriangle className="w-4 h-4" />
          <span>Transparent Platform Limitations</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          In strict compliance with academic research standards, AlphaWatch AI makes no guaranteed return claims. Bhavcopy data is unadjusted for stock splits and bonus issues (corporate actions may introduce artificial jumps). Historical survivorship bias applies since delisted stocks are not present in current archives. All signals are educational models, not registered investment advice.
        </p>
        <div className="pt-1">
          <Link
            to="/limitations"
            className="text-xs font-semibold text-blue-400 hover:text-blue-300 inline-flex items-center gap-1"
          >
            Read the full Limitations and Bias Audit &rarr;
          </Link>
        </div>
      </section>

      {/* Data Provenance Stamp */}
      <DataProvenanceFooter
        source="NSE CM-UDiFF Archive (Offline CSVs)"
        asOf="Verified Local Bhavcopy"
        status="Deterministic Engine"
      />
    </div>
  );
}
