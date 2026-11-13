import React, { useEffect, useState } from 'react';
import { LayoutDashboard, TrendingUp, AlertTriangle, ShieldCheck, Database, Layers } from 'lucide-react';
import { Badge, DataProvenanceFooter, LoadingSpinner, EmptyState } from '../../components/UIState';

export default function Overview() {
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    document.title = 'Portfolio Overview — AlphaWatch AI';
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Value */}
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Total Portfolio Value
          </span>
          <div className="text-2xl font-black text-white">
            ₹10,48,250.00
          </div>
          <span className="text-[11px] text-slate-500 block">Marked to latest saved close</span>
        </div>

        {/* Total P&L */}
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Unrealized P&L
          </span>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-black text-emerald-400">
              +₹48,250.00
            </span>
            <Badge variant="buy" label="UP" sublabel="+4.82%" />
          </div>
          <span className="text-[11px] text-slate-500 block">Baseline vs cost basis</span>
        </div>

        {/* Concentration Alert Card */}
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Concentration Status
          </span>
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-slate-200">Max Weight: 26.4%</span>
            <Badge variant="low" label="SAFE" sublabel="&lt;30%" />
          </div>
          <span className="text-[11px] text-slate-500 block">Top single holding: RELIANCE</span>
        </div>

        {/* Risk Distribution Card (Low / Med / High) */}
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Holdings by Risk Tier
          </span>
          <div className="flex items-center gap-2 pt-1">
            <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-950 text-emerald-300 border border-emerald-700/60">
              3 Low
            </span>
            <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-950 text-amber-300 border border-amber-700/60">
              2 Med
            </span>
            <span className="px-2 py-0.5 rounded text-xs font-bold bg-rose-950 text-rose-300 border border-rose-700/60">
              0 High
            </span>
          </div>
          <span className="text-[11px] text-slate-500 block">Tercile ranking on 20d volatility</span>
        </div>
      </div>

      {/* Holdings Table with Internal Horizontal Scrollbar */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white">Current Portfolio Holdings</h3>
            <p className="text-xs text-slate-400">Position weights, valuation, and concentration monitors</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="primary" label="5 ACTIVE EQUITIES" />
          </div>
        </div>

        {/* Responsive internal scrolling table */}
        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full text-left text-xs whitespace-nowrap">
            <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-2.5 px-3">Symbol</th>
                <th className="py-2.5 px-3">Quantity</th>
                <th className="py-2.5 px-3">Avg Buy Price</th>
                <th className="py-2.5 px-3">Saved Close</th>
                <th className="py-2.5 px-3">Current Value</th>
                <th className="py-2.5 px-3">Weight</th>
                <th className="py-2.5 px-3">P&L</th>
                <th className="py-2.5 px-3">Risk Tier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              <tr className="hover:bg-slate-800/40">
                <td className="py-2.5 px-3 font-bold text-white">RELIANCE</td>
                <td className="py-2.5 px-3 font-mono">100</td>
                <td className="py-2.5 px-3 font-mono">₹2,650.00</td>
                <td className="py-2.5 px-3 font-mono">₹2,765.40</td>
                <td className="py-2.5 px-3 font-mono">₹2,76,540.00</td>
                <td className="py-2.5 px-3 font-mono font-bold text-blue-400">26.38%</td>
                <td className="py-2.5 px-3 font-mono text-emerald-400 font-semibold">+₹11,540.00</td>
                <td className="py-2.5 px-3"><Badge variant="low" label="LOW RISK" /></td>
              </tr>
              <tr className="hover:bg-slate-800/40">
                <td className="py-2.5 px-3 font-bold text-white">TCS</td>
                <td className="py-2.5 px-3 font-mono">60</td>
                <td className="py-2.5 px-3 font-mono">₹3,900.00</td>
                <td className="py-2.5 px-3 font-mono">₹4,080.00</td>
                <td className="py-2.5 px-3 font-mono">₹2,44,800.00</td>
                <td className="py-2.5 px-3 font-mono font-bold text-blue-400">23.35%</td>
                <td className="py-2.5 px-3 font-mono text-emerald-400 font-semibold">+₹10,800.00</td>
                <td className="py-2.5 px-3"><Badge variant="low" label="LOW RISK" /></td>
              </tr>
              <tr className="hover:bg-slate-800/40">
                <td className="py-2.5 px-3 font-bold text-white">HDFCBANK</td>
                <td className="py-2.5 px-3 font-mono">150</td>
                <td className="py-2.5 px-3 font-mono">₹1,580.00</td>
                <td className="py-2.5 px-3 font-mono">₹1,642.50</td>
                <td className="py-2.5 px-3 font-mono">₹2,46,375.00</td>
                <td className="py-2.5 px-3 font-mono font-bold text-blue-400">23.50%</td>
                <td className="py-2.5 px-3 font-mono text-emerald-400 font-semibold">+₹9,375.00</td>
                <td className="py-2.5 px-3"><Badge variant="low" label="LOW RISK" /></td>
              </tr>
              <tr className="hover:bg-slate-800/40">
                <td className="py-2.5 px-3 font-bold text-white">INFY</td>
                <td className="py-2.5 px-3 font-mono">100</td>
                <td className="py-2.5 px-3 font-mono">₹1,480.00</td>
                <td className="py-2.5 px-3 font-mono">₹1,560.20</td>
                <td className="py-2.5 px-3 font-mono">₹1,56,020.00</td>
                <td className="py-2.5 px-3 font-mono font-bold text-blue-400">14.88%</td>
                <td className="py-2.5 px-3 font-mono text-emerald-400 font-semibold">+₹8,020.00</td>
                <td className="py-2.5 px-3"><Badge variant="medium" label="MED RISK" /></td>
              </tr>
              <tr className="hover:bg-slate-800/40">
                <td className="py-2.5 px-3 font-bold text-white">ICICIBANK</td>
                <td className="py-2.5 px-3 font-mono">110</td>
                <td className="py-2.5 px-3 font-mono">₹1,090.00</td>
                <td className="py-2.5 px-3 font-mono">₹1,132.00</td>
                <td className="py-2.5 px-3 font-mono">₹1,24,520.00</td>
                <td className="py-2.5 px-3 font-mono font-bold text-blue-400">11.88%</td>
                <td className="py-2.5 px-3 font-mono text-emerald-400 font-semibold">+₹4,620.00</td>
                <td className="py-2.5 px-3"><Badge variant="medium" label="MED RISK" /></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <DataProvenanceFooter
        source="NSE CM-UDiFF Bhavcopy Archive"
        asOf="Latest Available Trading Day"
        status="Positive-Loss Convention"
      />
    </div>
  );
}
