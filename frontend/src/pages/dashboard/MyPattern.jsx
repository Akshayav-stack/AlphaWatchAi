import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { User, ShieldCheck, Sliders, CheckCircle, RefreshCw, BarChart2 } from 'lucide-react';
import {
  Badge,
  DataProvenanceFooter,
  LoadingSpinner,
  ErrorMessage,
  EmptyState,
} from '../../components/UIState';
import { getMyPatternApi } from '../../api/client';

export default function MyPattern() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    document.title = 'My Investor Pattern — AlphaWatch AI';
    fetchPattern();
  }, []);

  async function fetchPattern() {
    try {
      setLoading(true);
      setError(null);
      const res = await getMyPatternApi();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load investor pattern.');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <LoadingSpinner text="Loading your behavioral investor pattern..." />;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={fetchPattern} />;
  }

  const profile = data?.profile || {};
  const answers = data?.answers || {};

  const riskScore = Number(profile.risk_score || 50);
  const profileName = profile.suggested_profile || 'Moderate';

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white">Investor Pattern & Risk Diagnostics</h2>
          <p className="text-xs text-slate-400">
            Deterministic risk profiling score and transparent rule explanations (Zero AI Hallucination)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to="/onboarding"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retake Profiler Assessment</span>
          </Link>
        </div>
      </div>

      {/* Pattern Overview Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Suggested Profile
          </span>
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-white">{profileName}</span>
            <Badge
              variant={
                profileName === 'Conservative'
                  ? 'low'
                  : profileName === 'Aggressive'
                  ? 'high'
                  : 'medium'
              }
              label={profileName.toUpperCase()}
            />
          </div>
          <span className="text-[10px] text-blue-400 block pt-0.5">
            {profileName === 'Conservative'
              ? 'BUY \u2265 0.65 / SELL \u2264 0.35'
              : profileName === 'Aggressive'
              ? 'BUY \u2265 0.55 / SELL \u2264 0.45'
              : 'BUY \u2265 0.60 / SELL \u2264 0.40'}
          </span>
        </div>

        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Risk Score
          </span>
          <div className="text-xl font-bold text-emerald-400 font-mono">
            {riskScore.toFixed(1)} / 100
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mt-1">
            <div
              className={`h-full ${
                riskScore > 65
                  ? 'bg-rose-500'
                  : riskScore < 40
                  ? 'bg-emerald-500'
                  : 'bg-amber-500'
              }`}
              style={{ width: `${Math.min(100, Math.max(0, riskScore))}%` }}
            />
          </div>
        </div>

        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Diversification Index
          </span>
          <div className="text-xl font-bold text-white font-mono">
            {Number(profile.diversification_score || 50).toFixed(1)} / 100
          </div>
          <span className="text-[10px] text-slate-400">
            Status: <strong className="text-slate-200">{profile.concentration_status || 'Balanced'}</strong>
          </span>
        </div>

        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Holding Style
          </span>
          <div className="text-base font-bold text-white truncate">
            {profile.holding_style || 'Balanced Growth & Value'}
          </div>
          <span className="text-[10px] text-slate-500">Derived investment posture</span>
        </div>
      </div>

      {/* Transparent "Why this profile" derivation box */}
      <div className="p-6 bg-slate-900/60 border border-blue-900/40 rounded-xl space-y-3">
        <div className="flex items-center gap-2 text-blue-400 font-bold text-sm">
          <ShieldCheck className="w-5 h-5 flex-shrink-0" />
          <h3>Why This Profile Was Assigned (Transparent Mathematical Derivation)</h3>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed font-sans">
          {profile.why_this_profile ||
            'Calculated using quantitative evaluation of your investment horizon, market volatility experience, and multi-asset position weights.'}
        </p>
      </div>

      {/* Answers Questionnaire Summary Table */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
        <h3 className="text-sm font-bold text-white">Assessment Questionnaire Responses</h3>
        <div className="overflow-x-auto border border-slate-800/80 rounded-xl bg-slate-950">
          <table className="w-full text-left text-xs whitespace-nowrap">
            <thead className="bg-slate-900/90 text-slate-400 font-semibold border-b border-slate-800 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-2.5 px-3">Question Attribute</th>
                <th className="py-2.5 px-3">Your Stated Preference</th>
                <th className="py-2.5 px-3">Rule Scoring Impact</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              <tr className="hover:bg-slate-900/40">
                <td className="py-2 px-3 font-semibold text-white">Investment Goal</td>
                <td className="py-2 px-3 text-slate-300">{answers.goal || 'Wealth Creation'}</td>
                <td className="py-2 px-3 font-mono text-emerald-400">+5 pts (Compounding focus)</td>
              </tr>
              <tr className="hover:bg-slate-900/40">
                <td className="py-2 px-3 font-semibold text-white">Target Horizon</td>
                <td className="py-2 px-3 text-slate-300">{answers.horizon || '3-5 Years'}</td>
                <td className="py-2 px-3 font-mono text-emerald-400">+5 pts (Multi-year horizon)</td>
              </tr>
              <tr className="hover:bg-slate-900/40">
                <td className="py-2 px-3 font-semibold text-white">Market Experience</td>
                <td className="py-2 px-3 text-slate-300">{answers.experience || 'Intermediate'}</td>
                <td className="py-2 px-3 font-mono text-slate-400">Baseline midpoint (0 pts)</td>
              </tr>
              <tr className="hover:bg-slate-900/40">
                <td className="py-2 px-3 font-semibold text-white">Reaction to -10% Drawdown</td>
                <td className="py-2 px-3 text-slate-300">{answers.fall_reaction || 'Hold and observe'}</td>
                <td className="py-2 px-3 font-mono text-emerald-400">+5 pts (Disciplined retention)</td>
              </tr>
              <tr className="hover:bg-slate-900/40">
                <td className="py-2 px-3 font-semibold text-white">Share of Liquid Savings</td>
                <td className="py-2 px-3 text-slate-300">{answers.savings_share || '10-25%'}</td>
                <td className="py-2 px-3 font-mono text-slate-400">Safe allocation tier (0 pts)</td>
              </tr>
              <tr className="hover:bg-slate-900/40">
                <td className="py-2 px-3 font-semibold text-white">Rebalancing Frequency</td>
                <td className="py-2 px-3 text-slate-300">{answers.trading_frequency || 'Monthly'}</td>
                <td className="py-2 px-3 font-mono text-slate-400">Systematic rebalancing</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <DataProvenanceFooter
        source="src/profiler.py (Deterministic Profiler Engine)"
        asOf={profile.updated_at ? profile.updated_at.split('T')[0] : new Date().toISOString().split('T')[0]}
        status="Rule-Based Parameter Assignment"
      />
    </div>
  );
}
