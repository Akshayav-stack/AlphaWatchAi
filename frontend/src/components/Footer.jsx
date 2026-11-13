import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Activity, Database, Lock } from 'lucide-react';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="w-full border-t border-slate-800 bg-fintech-surface mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand Info */}
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-md bg-blue-600 flex items-center justify-center text-white">
                <Activity className="w-4 h-4" />
              </div>
              <span className="text-sm font-bold text-white tracking-tight">
                AlphaWatch <span className="text-blue-400">AI</span>
              </span>
              <span className="text-[10px] px-2 py-0.5 font-semibold text-blue-300 bg-blue-900/40 rounded-full border border-blue-700/40">
                ASTRAQUANT X 2026
              </span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed max-w-md">
              Self-contained, offline-first algorithmic trading intelligence workstation for the Indian equity market (NSE). Developed for academic research and quantitative risk evaluation.
            </p>
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 pt-1">
              <div className="flex items-center gap-1">
                <Database className="w-3.5 h-3.5 text-slate-400" />
                <span>100% Offline-Capable</span>
              </div>
              <div className="flex items-center gap-1">
                <Lock className="w-3.5 h-3.5 text-slate-400" />
                <span>Zero Broker Connectivity</span>
              </div>
            </div>
          </div>

          {/* Quick Links */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
              Navigation
            </h4>
            <ul className="space-y-1.5 text-xs text-slate-400">
              <li>
                <Link to="/" className="hover:text-white transition-colors">
                  Home Overview
                </Link>
              </li>
              <li>
                <Link to="/how-it-works" className="hover:text-white transition-colors">
                  How It Works (5-Layer Pipeline)
                </Link>
              </li>
              <li>
                <Link to="/limitations" className="hover:text-white transition-colors">
                  Limitations & Bias Audit
                </Link>
              </li>
              <li>
                <Link to="/terms" className="hover:text-white transition-colors">
                  Privacy Policy & DPDP Terms
                </Link>
              </li>
            </ul>
          </div>

          {/* Access */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
              Researcher Portal
            </h4>
            <ul className="space-y-1.5 text-xs text-slate-400">
              <li>
                <Link to="/login" className="hover:text-white transition-colors">
                  Sign In to Workstation
                </Link>
              </li>
              <li>
                <Link to="/register" className="hover:text-white transition-colors">
                  Create Local Account
                </Link>
              </li>
              <li>
                <Link to="/dashboard/overview" className="hover:text-white transition-colors">
                  Live Portfolio Overview
                </Link>
              </li>
              <li>
                <Link to="/dashboard/model-performance" className="hover:text-white transition-colors">
                  Model Latency Benchmarks
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Mandatory Educational Disclaimer */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400 leading-relaxed mb-6">
          <div className="flex items-center gap-1.5 font-semibold text-slate-300 mb-1">
            <ShieldCheck className="w-4 h-4 text-amber-400" />
            <span>Academic & Educational Disclaimer (SEBI Compliance Notice)</span>
          </div>
          <p>
            AlphaWatch AI is strictly an academic quantitative research platform developed for ASTRAQUANT X 2026. It is not an investment advisory service, research analyst entity, or registered broker-dealer. It is not registered with the Securities and Exchange Board of India (SEBI). All predictions, probabilities, and signals are educational models computed mathematically from local saved historical Bhavcopy files. Contains zero live broker connectivity, zero automated order routing, and zero real money execution. Equities and derivatives involve substantial risk of loss.
          </p>
        </div>

        {/* Copyright and Metadata */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500 pt-4 border-t border-slate-800/80">
          <p>&copy; {currentYear} AlphaWatch AI (ASTRAQUANT X 2026). All rights reserved.</p>
          <p className="text-[11px]">Mode: Offline Deterministic &bull; Zero External CDN Reliance</p>
        </div>
      </div>
    </footer>
  );
}
