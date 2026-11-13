import React, { useEffect } from 'react';
import { ShieldAlert, AlertTriangle, Info, Scale, Lock, RefreshCw } from 'lucide-react';
import { DataProvenanceFooter } from '../../components/UIState';

export default function Limitations() {
  useEffect(() => {
    document.title = 'Limitations & Disclaimer — AlphaWatch AI';
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) {
      metaDesc.setAttribute(
        'content',
        'Academic limitations, regulatory notices, and data bias disclosures for AlphaWatch AI.'
      );
    }
  }, []);

  return (
    <div className="space-y-10 max-w-4xl mx-auto">
      <div className="space-y-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold text-amber-400 bg-amber-950/60 border border-amber-700/50">
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>Research Integrity & Compliance</span>
        </div>
        <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
          Platform Limitations, Disclaimers & Bias Audit
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
          In strict compliance with academic standards and quantitative ethics, AlphaWatch AI clearly discloses its data boundaries, technical limitations, and regulatory scope.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* SEBI Compliance */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-white font-semibold text-sm">
            <Scale className="w-4 h-4 text-blue-400" />
            <h3>SEBI Regulatory Boundary</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            AlphaWatch AI is NOT an investment advisor, research analyst entity, or registered broker-dealer under the Securities and Exchange Board of India (SEBI). All analytics, metrics, and probabilities are produced strictly for academic evaluation and quantitative research. Nothing on this website constitutes financial advice or an offer to buy or sell securities.
          </p>
        </div>

        {/* Corporate Actions */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-white font-semibold text-sm">
            <RefreshCw className="w-4 h-4 text-amber-400" />
            <h3>Corporate Action Adjustments</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Raw NSE Bhavcopy archives report transaction settlement prices without adjustments for stock splits, rights issues, or bonus shares. Consequently, large artificial price drops may reflect corporate actions rather than market declines. The system includes jump-detection flags but researchers must verify corporate action dates independently.
          </p>
        </div>

        {/* Survivorship Bias */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-white font-semibold text-sm">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <h3>Survivorship Bias</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            The dataset archive covers currently listed securities. Stocks that were suspended, acquired, or delisted during the historical window are not present in current bhavcopy archives. This can result in mild upward bias in historical backtests.
          </p>
        </div>

        {/* Zero Broker Code */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-white font-semibold text-sm">
            <Lock className="w-4 h-4 text-emerald-400" />
            <h3>Zero Broker Connectivity</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            AlphaWatch AI maintains zero connectivity to real broker APIs (Zerodha, Upstox, AngelOne, etc.). It contains zero order routing code and cannot execute live market transactions. Paper trading trades are logged strictly into an isolated virtual SQLite ledger.
          </p>
        </div>
      </div>

      {/* Account & Password Scope Note */}
      <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 text-xs text-slate-400 space-y-1">
        <h4 className="font-semibold text-slate-300">Authentication & Administrative Boundary</h4>
        <p>
          AlphaWatch AI is an air-gapped workstation designed for local deployment. It supports email and password authentication with Argon2 hashing. There is no automated email verification, no external password reset service (passwords are managed via user settings while authenticated), and no administrative superuser area. Every registered researcher owns and views strictly their own isolated portfolio records.
        </p>
      </div>

      <DataProvenanceFooter
        source="SEBI Compliance & Quant Ethics"
        asOf="ASTRAQUANT X 2026"
        status="Educational Only"
      />
    </div>
  );
}
