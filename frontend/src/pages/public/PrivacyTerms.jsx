import React, { useEffect } from 'react';
import { Lock, Trash2, Eye, ShieldCheck, Database } from 'lucide-react';
import { DataProvenanceFooter } from '../../components/UIState';

export default function PrivacyTerms() {
  useEffect(() => {
    document.title = 'Privacy Policy & Terms of Use — AlphaWatch AI';
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) {
      metaDesc.setAttribute(
        'content',
        'Privacy policy, Indian DPDP Act compliance, Right to Erasure, and Terms of Use for AlphaWatch AI.'
      );
    }
  }, []);

  return (
    <div className="space-y-10 max-w-4xl mx-auto">
      <div className="space-y-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold text-blue-400 bg-blue-950/60 border border-blue-700/50">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Governance & Data Protection</span>
        </div>
        <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
          Privacy Policy, DPDP Compliance & Terms of Use
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
          AlphaWatch AI is built on privacy-by-design principles, complying with the Digital Personal Data Protection Act (DPDP Act, 2023) and GDPR data minimization standards.
        </p>
      </div>

      <div className="space-y-6">
        {/* Right to Erasure */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-white font-semibold text-sm">
            <Trash2 className="w-4 h-4 text-rose-400" />
            <h3>Right to Erasure (Complete Account Deletion)</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            In accordance with Indian DPDP Act guidelines and GDPR Article 17, users have the unconditional right to delete their account at any time. When you click &ldquo;Delete Account&rdquo; in Settings, the database executes an atomic cascading purge that irrevocably erases your user record, holdings, questionnaire answers, investor pattern, and simulated paper trade history from the SQLite database.
          </p>
        </div>

        {/* Data Minimization */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-white font-semibold text-sm">
            <Database className="w-4 h-4 text-blue-400" />
            <h3>Zero External Transmission & Data Minimization</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Your portfolio holdings, onboarding answers, and passwords never leave your local machine or server. We do not track users with Google Analytics, third-party cookies, tracking pixels, or external CDNs. All scripts, fonts, and stylesheets are self-hosted.
          </p>
        </div>

        {/* Password Security */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-white font-semibold text-sm">
            <Lock className="w-4 h-4 text-emerald-400" />
            <h3>Password Hashing & Session Cryptography</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Passwords are salted and hashed with Argon2id using memory-hard parameters. Sessions are authenticated via signed HttpOnly, SameSite=Lax cookies with automatic session rotation on login to prevent fixation attacks.
          </p>
        </div>

        {/* Terms of Academic Use */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-white font-semibold text-sm">
            <Eye className="w-4 h-4 text-amber-400" />
            <h3>Terms of Academic Research Use</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            By using AlphaWatch AI, you agree that this platform is provided strictly for academic and educational evaluation. The authors and developers accept zero liability for financial decisions or trading outcomes made on the basis of model signals, risk scores, or backtest results.
          </p>
        </div>
      </div>

      <DataProvenanceFooter
        source="Digital Personal Data Protection (DPDP) Act 2023"
        asOf="ASTRAQUANT X 2026"
        status="Privacy by Design"
      />
    </div>
  );
}
