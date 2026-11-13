import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Menu, Activity, ShieldCheck, Database } from 'lucide-react';
import Sidebar from '../components/Sidebar';

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  // Map route path to human-readable title
  const routeTitles = {
    '/dashboard/overview': 'Portfolio Overview & Concentration',
    '/dashboard/predictions': 'Algorithmic Directional Predictions',
    '/dashboard/buy-candidates': 'Profile-Ranked Buy Candidates',
    '/dashboard/risk': 'Quantitative Risk Analytics & VaR',
    '/dashboard/backtest': 'T+1 Backtest & Strategy Execution',
    '/dashboard/model-performance': 'Walk-Forward Model Performance & Latency',
    '/dashboard/paper-trading': 'Simulated Paper Trading Workstation',
    '/dashboard/auditor': 'Claim Auditor & Empirical Calibration',
    '/dashboard/ripple': 'Ripple Effect Macro Stress Simulator',
    '/dashboard/my-pattern': 'Investor Pattern & Adaptive Rules',
    '/dashboard/settings': 'Researcher Settings & Account Security',
  };

  const pageTitle = routeTitles[location.pathname] || 'Algorithmic Intelligence Workstation';

  return (
    <div className="min-h-screen bg-fintech-bg text-slate-100 flex flex-col">
      {/* Sidebar Navigation */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content Area */}
      <div className="lg:pl-64 flex flex-col flex-1">
        {/* Top Bar Header */}
        <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-4 sm:px-6 bg-slate-900/90 backdrop-blur border-b border-slate-800">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 text-slate-400 hover:text-white rounded-lg lg:hidden focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Open navigation sidebar"
            >
              <Menu className="w-5 h-5" />
            </button>
            <h1 className="text-sm font-bold text-white tracking-tight sm:text-base truncate max-w-[200px] sm:max-w-md">
              {pageTitle}
            </h1>
          </div>

          <div className="flex items-center gap-2 sm:gap-4 text-xs">
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 bg-slate-800/80 rounded-md border border-slate-700/60 text-slate-300">
              <Database className="w-3.5 h-3.5 text-blue-400" />
              <span>Offline Verified</span>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-950/40 border border-emerald-700/40 rounded-md text-emerald-300 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Local Engine</span>
            </div>
          </div>
        </header>

        {/* Dynamic Page Outlet */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>

        {/* Bottom Disclaimer Bar */}
        <footer className="p-3 text-center text-[10px] text-slate-500 border-t border-slate-800/80 bg-slate-950/40">
          AlphaWatch AI &bull; Academic & Educational Platform (ASTRAQUANT X 2026) &bull; Zero Broker Code &bull; Positive-Loss Reporting Convention
        </footer>
      </div>
    </div>
  );
}
