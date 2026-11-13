import React, { useEffect } from 'react';
import { ShieldCheck, Lock, Trash2, Database, FileText, CheckCircle } from 'lucide-react';
import { DataProvenanceFooter } from '../../components/UIState';

export default function PrivacyTerms() {
  useEffect(() => {
    document.title = 'Privacy Policy & Terms — AlphaWatch AI';
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) {
      metaDesc.setAttribute(
        'content',
        'Data storage policies, consent requirements, and Right to Erasure under the Indian DPDP Act for AlphaWatch AI.'
      );
    }
  }, []);

  return (
    <div className="space-y-10 max-w-4xl mx-auto py-4">
      <div className="space-y-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold text-blue-400 bg-blue-950/60 border border-blue-700/50">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Data Governance & Privacy by Design</span>
        </div>
        <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
          Privacy Policy, Data Storage & Right to Erasure
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
          AlphaWatch AI complies with the Digital Personal Data Protection (DPDP) Act, 2023 and GDPR Article 17 standards. Here is how your data is protected.
        </p>
      </div>

      <div className="space-y-6">
        {/* 1. What Data is Stored */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-white font-bold text-sm">
            <Database className="w-4 h-4 text-blue-400" />
            <h3>1. What User Data is Stored Locally</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            The platform stores only the minimum data required to deliver personalized portfolio risk calculations:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1 text-xs text-slate-400">
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <strong className="text-white block mb-0.5">Account Credentials</strong>
              <span>Name, email address, and a salted Argon2id cryptographic password hash (passwords are never saved in plaintext).</span>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <strong className="text-white block mb-0.5">Portfolio Holdings</strong>
              <span>Stock ticker symbol, purchase quantity, buy price, and optional acquisition date.</span>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <strong className="text-white block mb-0.5">Profiling Answers</strong>
              <span>Investment goal, time horizon, experience level, trading frequency, and drawdown tolerance answers.</span>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <strong className="text-white block mb-0.5">Simulated Paper Trades</strong>
              <span>Virtual trade records, virtual cash balance, and simulated trade dates. Zero real bank or broker account information.</span>
            </div>
          </div>
        </div>

        {/* 2. Consent */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-white font-bold text-sm">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            <h3>2. User Consent & Processing Scope</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            During registration, every researcher explicitly acknowledges that AlphaWatch AI operates purely for academic analysis and educational modeling. No user data is ever sold, transferred to third parties, tracked by ad networks, or uploaded to external cloud APIs.
          </p>
        </div>

        {/* 3. Right to Erasure */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-white font-bold text-sm">
            <Trash2 className="w-4 h-4 text-rose-400" />
            <h3>3. Right to Erasure (Account Deletion)</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Under Indian DPDP Act rules and GDPR Article 17, users maintain unconditional ownership over their data. Clicking &ldquo;Delete Account Permanently&rdquo; in Researcher Settings issues an atomic SQL cascading deletion that permanently deletes:
          </p>
          <ul className="list-disc list-inside text-xs text-slate-400 space-y-1 pl-2">
            <li>The user account record in the SQLite database</li>
            <li>All associated portfolio holdings</li>
            <li>All questionnaire answers and calculated investor patterns</li>
            <li>All paper trading ledger transactions and active sessions</li>
          </ul>
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
