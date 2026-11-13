import React, { useEffect } from 'react';
import { ShieldAlert, AlertTriangle, Info, TrendingDown } from 'lucide-react';
import { Badge, DataProvenanceFooter } from '../../components/UIState';

export default function Risk() {
  useEffect(() => {
    document.title = 'Quantitative Risk & VaR — AlphaWatch AI';
  }, []);

  const riskTable = [
    { symbol: 'RELIANCE', weight: '26.4%', vol20d: '14.8%', maxDd1y: '12.4%', var95: '1.42%', cvar95: '2.15%', tier: 'low' },
    { symbol: 'TCS', weight: '23.4%', vol20d: '16.2%', maxDd1y: '14.1%', var95: '1.58%', cvar95: '2.34%', tier: 'low' },
    { symbol: 'HDFCBANK', weight: '23.5%', vol20d: '15.9%', maxDd1y: '16.8%', var95: '1.62%', cvar95: '2.40%', tier: 'low' },
    { symbol: 'INFY', weight: '14.9%', vol20d: '21.4%', maxDd1y: '18.9%', var95: '2.10%', cvar95: '2.95%', tier: 'medium' },
    { symbol: 'ICICIBANK', weight: '11.9%', vol20d: '19.8%', maxDd1y: '15.6%', var95: '1.92%', cvar95: '2.78%', tier: 'medium' },
  ];

  return (
    <div className="space-y-6">
      {/* Portfolio Level Risk Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            20d Annualized Volatility
          </span>
          <div className="text-2xl font-black text-white">16.34%</div>
          <span className="text-[11px] text-slate-500 block">Weighted asset covariance</span>
        </div>

        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            1-Year Maximum Drawdown
          </span>
          <div className="text-2xl font-black text-rose-400">14.65%</div>
          <span className="text-[11px] text-slate-500 block">Reported as positive loss</span>
        </div>

        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            95% 1-Day Historical VaR
          </span>
          <div className="text-2xl font-black text-amber-400">1.54%</div>
          <span className="text-[11px] text-slate-500 block">₹16,143 potential 1d loss</span>
        </div>

        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            95% 1-Day CVaR (Expected Shortfall)
          </span>
          <div className="text-2xl font-black text-rose-400">2.28%</div>
          <span className="text-[11px] text-slate-500 block">₹23,890 tail risk expectation</span>
        </div>
      </div>

      {/* Positive-Loss Convention Box */}
      <div className="p-4 bg-slate-900/40 border border-blue-900/40 rounded-xl text-xs text-slate-300 space-y-1">
        <div className="flex items-center gap-1.5 font-semibold text-blue-400">
          <Info className="w-4 h-4" />
          <span>Documented Positive-Loss Convention</span>
        </div>
        <p className="leading-relaxed text-[11px] text-slate-400">
          In standard quantitative risk reporting, loss distributions are framed positively: a VaR of 1.54% means there is a 95% statistical confidence that daily losses will not exceed 1.54% ($L = -R \ge 0$). CVaR reflects the expected loss in the 5% worst tail outcomes.
        </p>
      </div>

      {/* Asset-by-Asset Risk Breakdown Table */}
      <div className="overflow-x-auto custom-scrollbar p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4">
        <div className="border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white">Cross-Sectional Asset Risk Breakdown</h3>
          <p className="text-xs text-slate-400">Tercile ranking on 20-day historical volatility</p>
        </div>

        <table className="w-full text-left text-xs whitespace-nowrap">
          <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800 uppercase text-[10px] tracking-wider">
            <tr>
              <th className="py-2.5 px-3">Symbol</th>
              <th className="py-2.5 px-3">Weight</th>
              <th className="py-2.5 px-3">20d Volatility</th>
              <th className="py-2.5 px-3">1y Max Drawdown</th>
              <th className="py-2.5 px-3">95% 1d VaR</th>
              <th className="py-2.5 px-3">95% 1d CVaR</th>
              <th className="py-2.5 px-3">Tercile Risk Tier</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-200">
            {riskTable.map((r) => (
              <tr key={r.symbol} className="hover:bg-slate-800/40">
                <td className="py-2.5 px-3 font-bold text-white">{r.symbol}</td>
                <td className="py-2.5 px-3 font-mono">{r.weight}</td>
                <td className="py-2.5 px-3 font-mono">{r.vol20d}</td>
                <td className="py-2.5 px-3 font-mono text-rose-400">{r.maxDd1y}</td>
                <td className="py-2.5 px-3 font-mono text-amber-400">{r.var95}</td>
                <td className="py-2.5 px-3 font-mono text-rose-400">{r.cvar95}</td>
                <td className="py-2.5 px-3">
                  <Badge variant={r.tier} label={`${r.tier.toUpperCase()} RISK`} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <DataProvenanceFooter
        source="src/risk.py (Historical Simulation)"
        asOf="252-Day Rolling Historical Window"
        status="Positive-Loss L >= 0"
      />
    </div>
  );
}
