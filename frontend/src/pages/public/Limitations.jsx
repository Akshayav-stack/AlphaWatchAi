import React, { useEffect } from 'react';
import { ShieldAlert, AlertTriangle, Scale, Lock, RefreshCw, Mail, Database, UserCheck } from 'lucide-react';
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
    <div className="space-y-10 max-w-4xl mx-auto py-4">
      <div className="space-y-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold text-amber-400 bg-amber-950/60 border border-amber-700/50">
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>Research Integrity & Transparency</span>
        </div>
        <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
          Platform Limitations, Regulatory Scope & Bias Audit
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
          In strict compliance with quantitative finance ethics and academic guidelines, AlphaWatch AI details every operational limitation, dataset boundary, and administrative constraint.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Educational Only & Not Investment Advice */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-white font-bold text-sm">
            <Scale className="w-4 h-4 text-blue-400" />
            <h3>Educational-Only Research (Not Investment Advice)</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            AlphaWatch AI is an educational algorithmic trading research workstation developed for ASTRAQUANT X 2026. All probabilities, risk scores, and directional classifications represent academic models. Nothing on this platform constitutes an investment recommendation, financial advice, or solicitation to trade securities.
          </p>
        </div>

        {/* SEBI Compliance Notice */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-white font-bold text-sm">
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            <h3>SEBI Regulatory Note</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            The platform and its developers are not registered with the Securities and Exchange Board of India (SEBI) as Investment Advisers (RIA) or Research Analysts (RA). The tool is designed strictly for classroom, hackathon, and quantitative engineering demonstration.
          </p>
        </div>

        {/* Survivorship Bias */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-white font-bold text-sm">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <h3>Survivorship Bias Disclosure</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            The dataset archive is restricted to currently listed securities on the National Stock Exchange of India. Companies that were delisted, liquidated, or suspended during historical observation periods are excluded, which may introduce a mild upward survivorship bias into historical backtest statistics.
          </p>
        </div>

        {/* Daily Saved Data (Not Live) */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-white font-bold text-sm">
            <Database className="w-4 h-4 text-emerald-400" />
            <h3>Daily Saved Data (Not Live Real-Time)</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            AlphaWatch AI operates entirely offline from saved end-of-day (EOD) Bhavcopy CSV archives. The running website makes zero live network calls to the NSE website. Data is stamped with an explicit &ldquo;As-of&rdquo; date and is never misrepresented as a live streaming ticker.
          </p>
        </div>
      </div>

      {/* Scope of Authentication: No email verification, password reset, or admin area */}
      <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-3">
        <div className="flex items-center gap-2 text-white font-bold text-sm">
          <UserCheck className="w-4 h-4 text-blue-400" />
          <h3>System Scope: No Email Verification, Password Reset, or Admin Area</h3>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          AlphaWatch AI is an air-gapped, privacy-centric application. To guarantee 100% offline operation without third-party mailer daemon dependencies (e.g. SendGrid or SMTP servers):
        </p>
        <ul className="list-disc list-inside space-y-1 text-xs text-slate-400 pl-2">
          <li><strong>No Email Verification:</strong> Accounts activate immediately upon registration.</li>
          <li><strong>No Password Reset via Email:</strong> Password updates are performed while logged in via the Researcher Settings page. Researchers must safeguard their credentials.</li>
          <li><strong>No Superuser Admin Area:</strong> To prevent unauthorized cross-tenant inspection, there is no administrative dashboard. Every researcher views strictly their own isolated portfolio records.</li>
        </ul>
      </div>

      <DataProvenanceFooter
        source="SEBI Compliance & Quant Ethics"
        asOf="ASTRAQUANT X 2026"
        status="Educational Only"
      />
    </div>
  );
}
