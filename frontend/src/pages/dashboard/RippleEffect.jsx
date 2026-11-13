import React, { useState, useEffect } from 'react';
import { PieChart, AlertTriangle, ShieldCheck, TrendingDown, ArrowDownRight } from 'lucide-react';
import { Badge, DataProvenanceFooter } from '../../components/UIState';

export default function RippleEffect() {
  const [scenario, setScenario] = useState('crude_spike');

  useEffect(() => {
    document.title = 'Ripple Effect Macro Stress Simulator — AlphaWatch AI';
  }, []);

  const scenarios = {
    crude_spike: {
      name: 'Crude Oil Surge (+20% Brent Spike)',
      mechanism: 'Higher crude elevates refining costs for chemical and paint manufacturers while benefiting upstream energy producers.',
      portfolioImpact: '-₹18,450.00 (-1.76%)',
      vulnerable: 'TCS (FX translation pressure) & Paints/Auto',
      items: [
        { symbol: 'RELIANCE', current: '₹2,765.40', sim: '₹2,848.36', impact: '+₹8,296.00', pct: '+3.0%', note: 'Upstream oil production gain' },
        { symbol: 'TCS', current: '₹4,080.00', sim: '₹3,998.40', impact: '-₹4,896.00', pct: '-2.0%', note: 'Global discretionary IT slowdown' },
        { symbol: 'HDFCBANK', current: '₹1,642.50', sim: '₹1,609.65', impact: '-₹4,927.50', pct: '-2.0%', note: 'Inflationary yield curve pressure' },
        { symbol: 'INFY', current: '₹1,560.20', sim: '₹1,529.00', impact: '-₹3,120.00', pct: '-2.0%', note: 'Client margin compression' },
        { symbol: 'ICICIBANK', current: '₹1,132.00', sim: '₹1,098.04', impact: '-₹3,735.60', pct: '-3.0%', note: 'Import inflation stress' },
      ],
    },
    repo_hike: {
      name: 'RBI Monetary Policy Tightening (+50 bps Repo Hike)',
      mechanism: 'Higher interest rates increase cost of capital and dampen credit growth while compressing banking valuation multiples.',
      portfolioImpact: '-₹24,120.00 (-2.30%)',
      vulnerable: 'Banking & Financials (HDFCBANK, ICICIBANK)',
      items: [
        { symbol: 'HDFCBANK', current: '₹1,642.50', sim: '₹1,585.00', impact: '-₹8,625.00', pct: '-3.5%', note: 'NIM compression & credit cost spike' },
        { symbol: 'ICICIBANK', current: '₹1,132.00', sim: '₹1,086.72', impact: '-₹4,980.80', pct: '-4.0%', note: 'Lending growth deceleration' },
        { symbol: 'RELIANCE', current: '₹2,765.40', sim: '₹2,737.75', impact: '-₹2,765.00', pct: '-1.0%', note: 'Higher interest expense on capex' },
        { symbol: 'TCS', current: '₹4,080.00', sim: '₹4,039.20', impact: '-₹2,448.00', pct: '-1.0%', note: 'Debt-free balance sheet defense' },
        { symbol: 'INFY', current: '₹1,560.20', sim: '₹1,544.60', impact: '-₹1,560.00', pct: '-1.0%', note: 'Cash surplus yield defense' },
      ],
    },
    tech_selloff: {
      name: 'Global Technology Correction (-8% Tech Selloff)',
      mechanism: 'Sharp valuation de-rating in US and European software customers dampens offshore IT outsourcing spending.',
      portfolioImpact: '-₹31,540.00 (-3.01%)',
      vulnerable: 'IT Sector (TCS, INFY)',
      items: [
        { symbol: 'TCS', current: '₹4,080.00', sim: '₹3,794.40', impact: '-₹17,136.00', pct: '-7.0%', note: 'Direct sector contagion' },
        { symbol: 'INFY', current: '₹1,560.20', sim: '₹1,450.99', impact: '-₹10,921.00', pct: '-7.0%', note: 'Direct sector contagion' },
        { symbol: 'RELIANCE', current: '₹2,765.40', sim: '₹2,737.75', impact: '-₹2,765.00', pct: '-1.0%', note: 'Minor broad market drag' },
        { symbol: 'HDFCBANK', current: '₹1,642.50', sim: '₹1,634.29', impact: '-₹1,231.50', pct: '-0.5%', note: 'Defensive domestic resilience' },
        { symbol: 'ICICIBANK', current: '₹1,132.00', sim: '₹1,126.34', impact: '-₹622.60', pct: '-0.5%', note: 'Domestic retail loan stability' },
      ],
    },
  };

  const currentScenario = scenarios[scenario];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white">Ripple Effect Macro Stress Simulator</h2>
          <p className="text-xs text-slate-400">
            Simulate multi-asset portfolio drawdowns under hypothetical macroeconomic shock scenarios
          </p>
        </div>
        <Badge variant="medium" label="HYPOTHETICAL SIMULATION" sublabel="CORRELATION != CAUSATION" />
      </div>

      {/* Scenario Selector Tabs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <button
          onClick={() => setScenario('crude_spike')}
          className={`p-3 text-left rounded-xl border text-xs font-semibold transition-all ${
            scenario === 'crude_spike'
              ? 'bg-blue-950/60 border-blue-600 text-white'
              : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:text-white'
          }`}
        >
          Crude Oil Surge (+20%)
        </button>
        <button
          onClick={() => setScenario('repo_hike')}
          className={`p-3 text-left rounded-xl border text-xs font-semibold transition-all ${
            scenario === 'repo_hike'
              ? 'bg-blue-950/60 border-blue-600 text-white'
              : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:text-white'
          }`}
        >
          RBI Rate Hike (+50 bps)
        </button>
        <button
          onClick={() => setScenario('tech_selloff')}
          className={`p-3 text-left rounded-xl border text-xs font-semibold transition-all ${
            scenario === 'tech_selloff'
              ? 'bg-blue-950/60 border-blue-600 text-white'
              : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:text-white'
          }`}
        >
          Global Tech Selloff (-8%)
        </button>
      </div>

      {/* Scenario Overview Card */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white">{currentScenario.name}</h3>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Simulated Net Impact:</span>
            <span className="text-sm font-bold font-mono text-rose-400">{currentScenario.portfolioImpact}</span>
          </div>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">{currentScenario.mechanism}</p>
        <div className="text-[11px] text-amber-400 font-semibold">
          Most Vulnerable Sector: {currentScenario.vulnerable}
        </div>
      </div>

      {/* Simulated Holding Impact Table */}
      <div className="overflow-x-auto custom-scrollbar p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
        <h4 className="text-xs font-bold text-white uppercase tracking-wider">Simulated Holding Breakdown</h4>
        <table className="w-full text-left text-xs whitespace-nowrap">
          <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800 uppercase text-[10px] tracking-wider">
            <tr>
              <th className="py-2.5 px-3">Symbol</th>
              <th className="py-2.5 px-3">Base Price</th>
              <th className="py-2.5 px-3">Simulated Price</th>
              <th className="py-2.5 px-3">Portfolio Impact</th>
              <th className="py-2.5 px-3">Shock Change</th>
              <th className="py-2.5 px-3">Economic Mechanism</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-200">
            {currentScenario.items.map((item) => (
              <tr key={item.symbol} className="hover:bg-slate-800/40">
                <td className="py-2.5 px-3 font-bold text-white">{item.symbol}</td>
                <td className="py-2.5 px-3 font-mono">{item.current}</td>
                <td className="py-2.5 px-3 font-mono">{item.sim}</td>
                <td className={`py-2.5 px-3 font-mono font-bold ${item.impact.startsWith('+') ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {item.impact}
                </td>
                <td className="py-2.5 px-3">
                  <Badge variant={item.pct.startsWith('+') ? 'buy' : 'sell'} label={item.pct} />
                </td>
                <td className="py-2.5 px-3 text-slate-400 text-[11px]">{item.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <DataProvenanceFooter
        source="src/ripple.py (Historical Asset Betas)"
        asOf="Hypothetical Educational Stress Model"
        status="Correlation != Causation"
      />
    </div>
  );
}
