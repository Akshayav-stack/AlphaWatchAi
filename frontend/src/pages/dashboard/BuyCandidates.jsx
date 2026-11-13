import React, { useEffect } from 'react';
import { CheckCircle, Sliders, ArrowUpRight } from 'lucide-react';
import { Badge, DataProvenanceFooter } from '../../components/UIState';

export default function BuyCandidates() {
  useEffect(() => {
    document.title = 'Buy Candidates — AlphaWatch AI';
  }, []);

  const candidates = [
    {
      symbol: 'RELIANCE',
      probUp: 0.68,
      sector: 'Energy & Conglomerate',
      volatility: '14.8%',
      maxPosition: '20%',
      stopLoss: '5.0%',
      profile: 'Moderate',
    },
    {
      symbol: 'TCS',
      probUp: 0.63,
      sector: 'Information Technology',
      volatility: '16.2%',
      maxPosition: '20%',
      stopLoss: '5.0%',
      profile: 'Moderate',
    },
    {
      symbol: 'BHARTIARTL',
      probUp: 0.62,
      sector: 'Telecommunications',
      volatility: '18.1%',
      maxPosition: '20%',
      stopLoss: '5.0%',
      profile: 'Moderate',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white">Profile-Ranked Buy Candidates</h2>
          <p className="text-xs text-slate-400">
            Equities with calibrated probability &ge; profile buy threshold (0.60 for Moderate)
          </p>
        </div>
        <Badge variant="primary" label="MODERATE PROFILE (BUY &ge; 0.60)" />
      </div>

      <div className="overflow-x-auto custom-scrollbar p-5 bg-slate-900/60 border border-slate-800 rounded-xl">
        <table className="w-full text-left text-xs whitespace-nowrap">
          <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800 uppercase text-[10px] tracking-wider">
            <tr>
              <th className="py-2.5 px-3">Rank</th>
              <th className="py-2.5 px-3">Symbol</th>
              <th className="py-2.5 px-3">Sector</th>
              <th className="py-2.5 px-3">P(Up Direction)</th>
              <th className="py-2.5 px-3">20d Volatility</th>
              <th className="py-2.5 px-3">Max Position Size</th>
              <th className="py-2.5 px-3">Trailing Stop-Loss</th>
              <th className="py-2.5 px-3">Signal Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-200">
            {candidates.map((c, idx) => (
              <tr key={c.symbol} className="hover:bg-slate-800/40">
                <td className="py-2.5 px-3 font-mono font-bold text-blue-400">#{idx + 1}</td>
                <td className="py-2.5 px-3 font-bold text-white">{c.symbol}</td>
                <td className="py-2.5 px-3 text-slate-400">{c.sector}</td>
                <td className="py-2.5 px-3 font-mono font-bold text-emerald-400">
                  {(c.probUp * 100).toFixed(1)}%
                </td>
                <td className="py-2.5 px-3 font-mono">{c.volatility}</td>
                <td className="py-2.5 px-3 font-mono">{c.maxPosition}</td>
                <td className="py-2.5 px-3 font-mono text-rose-400 font-semibold">-{c.stopLoss}</td>
                <td className="py-2.5 px-3">
                  <Badge variant="buy" label="BUY QUALIFIED" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <DataProvenanceFooter
        source="src/signals.py (PROFILES Config)"
        asOf="Latest Available Trading Day"
        status="Profile Filtered"
      />
    </div>
  );
}
