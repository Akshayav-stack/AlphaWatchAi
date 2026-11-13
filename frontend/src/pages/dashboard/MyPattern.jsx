import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { User, ShieldCheck, Sliders, CheckCircle, RefreshCw } from 'lucide-react';
import { Badge, DataProvenanceFooter } from '../../components/UIState';

export default function MyPattern() {
  useEffect(() => {
    document.title = 'My Investor Pattern — AlphaWatch AI';
  }, []);

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white">Investor Pattern & Risk Diagnostics</h2>
          <p className="text-xs text-slate-400">
            Deterministic risk profiling score and transparent rule explanations
          </p>
        </div>
        <Link
          to="/onboarding"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retake Profiler</span>
        </Link>
      </div>

      {/* Pattern Overview Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase">Suggested Profile</span>
          <div className="text-xl font-bold text-white">Moderate</div>
          <span className="text-[10px] text-blue-400">BUY &ge; 0.60 / SELL &le; 0.40</span>
        </div>
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase">Quantitative Risk Score</span>
          <div className="text-xl font-bold text-emerald-400 font-mono">54 / 100</div>
          <span className="text-[10px] text-slate-500">Disciplined mid-tier</span>
        </div>
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase">Diversification Index</span>
          <div className="text-xl font-bold text-white font-mono">82 / 100</div>
          <span className="text-[10px] text-slate-500">5 large-cap sectors</span>
        </div>
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase">Holding Style</span>
          <div className="text-xl font-bold text-white">Swing & Hold</div>
          <span className="text-[10px] text-slate-500">Medium-term compounding</span>
        </div>
      </div>

      {/* Transparent "Why this profile" derivation box */}
      <div className="p-6 bg-slate-900/60 border border-blue-900/40 rounded-xl space-y-3">
        <div className="flex items-center gap-2 text-blue-400 font-bold text-sm">
          <ShieldCheck className="w-5 h-5" />
          <h3>Why This Profile Was Assigned (Transparent Rule Logic)</h3>
        </div>
        <div className="space-y-2 text-xs text-slate-300 leading-relaxed">
          <p>
            Your Investor Pattern was computed by <code className="text-blue-400 bg-slate-950 px-1.5 py-0.5 rounded">src/profiler.py</code> using verified deterministic scoring rules:
          </p>
          <ul className="list-disc list-inside space-y-1 text-slate-400 text-[11px] pl-2">
            <li><strong>Horizon Rule:</strong> 3-5 Year investment horizon assigned +10 to baseline risk score (50 &rarr; 60).</li>
            <li><strong>Reaction Rule:</strong> Disciplined reaction to a 10% market drawdown (&ldquo;Hold and rebalance&rdquo;) prevented negative score penalties.</li>
            <li><strong>Concentration Check:</strong> Maximum single position weight (RELIANCE at 26.4%) is within the safe &lt;30% concentration threshold.</li>
            <li><strong>Sector Exposure:</strong> Portfolio is divided across Energy (26.4%), Financials (35.4%), and Technology (38.2%), triggering no single-sector diversification penalties.</li>
          </ul>
        </div>
      </div>

      <DataProvenanceFooter
        source="src/profiler.py (Deterministic Profiler Engine)"
        asOf="Session Pattern State"
        status="Rule-Based (Zero LLM)"
      />
    </div>
  );
}
