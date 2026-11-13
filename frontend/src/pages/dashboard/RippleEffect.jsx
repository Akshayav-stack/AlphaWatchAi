import React, { useState, useEffect } from 'react';
import { PieChart, AlertTriangle, ShieldCheck, TrendingDown, ArrowDownRight, RefreshCw, Layers } from 'lucide-react';
import {
  Badge,
  DataProvenanceFooter,
  LoadingSpinner,
  ErrorMessage,
  EmptyState,
} from '../../components/UIState';
import { getRippleScenariosApi, runRippleSimulationApi } from '../../api/client';

export default function RippleEffect() {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState('crude_oil_spike');
  const [simData, setSimData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    document.title = 'Ripple Effect Macro Stress Simulator — AlphaWatch AI';
    loadScenarios();
  }, []);

  async function loadScenarios() {
    try {
      setLoading(true);
      setError(null);
      const res = await getRippleScenariosApi();
      const list = res?.scenarios || [];
      setScenarios(list);
      const initialId = list[0]?.id || 'crude_oil_spike';
      setSelectedScenario(initialId);
      // Run simulation for default scenario
      const simRes = await runRippleSimulationApi({ scenario_id: initialId });
      setSimData(simRes);
    } catch (err) {
      setError(err.message || 'Failed to load macro scenarios.');
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectScenario(id) {
    setSelectedScenario(id);
    try {
      setLoading(true);
      setError(null);
      const simRes = await runRippleSimulationApi({ scenario_id: id });
      setSimData(simRes);
    } catch (err) {
      setError(err.message || 'Scenario simulation failed.');
    } finally {
      setLoading(false);
    }
  }

  const holdingImpacts = simData?.holding_impacts || [];
  const isLoss = (simData?.impact_amount || 0) < 0;
  const asOf = simData?.as_of || {
    date: new Date().toISOString().split('T')[0],
    source: 'Historical Sector Betas & Sensitivity Transmission Models',
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white">Ripple Effect Macro Stress Simulator</h2>
          <p className="text-xs text-slate-400">
            Simulate multi-asset portfolio drawdowns under hypothetical macroeconomic shock scenarios
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="medium" label="HYPOTHETICAL SIMULATION" sublabel="NOT A FORECAST" />
          <button
            onClick={() => handleSelectScenario(selectedScenario)}
            className="p-1.5 text-slate-400 hover:text-slate-200 transition-colors"
            title="Re-run Simulation"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Scenario Selector Pills */}
      <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
        {scenarios.map((s) => (
          <button
            key={s.id}
            onClick={() => handleSelectScenario(s.id)}
            className={`p-3 text-left rounded-xl border text-xs font-semibold transition-all ${
              selectedScenario === s.id
                ? 'bg-blue-950/60 border-blue-600 text-white shadow-sm'
                : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <span className="block truncate">{s.name}</span>
          </button>
        ))}
      </div>

      {error && <ErrorMessage message={error} onRetry={() => handleSelectScenario(selectedScenario)} />}

      {loading ? (
        <LoadingSpinner text="Computing multi-asset macroeconomic sensitivity shocks..." />
      ) : simData ? (
        <div className="space-y-6">
          {/* Simulation Impact Banner */}
          <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white">{simData.scenario_name}</h3>
                <p className="text-xs text-slate-400">{simData.scenario_description}</p>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`text-base font-black font-mono ${
                    isLoss ? 'text-rose-400' : 'text-emerald-400'
                  }`}
                >
                  {isLoss ? '' : '+'}₹
                  {Number(simData.impact_amount || 0).toLocaleString('en-IN', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}{' '}
                  ({isLoss ? '' : '+'}{Number(simData.impact_pct || 0).toFixed(2)}%)
                </span>
                <Badge
                  variant={isLoss ? 'sell' : 'buy'}
                  label={isLoss ? 'PORTFOLIO DRAG' : 'PORTFOLIO GAIN'}
                />
              </div>
            </div>

            {/* Economic Mechanism */}
            <div className="p-3 bg-slate-950 rounded-lg text-xs text-slate-300 border border-slate-800/80 space-y-1">
              <span className="font-semibold text-blue-400 block font-mono text-[11px] uppercase">
                Transmission Channel & Economic Mechanism:
              </span>
              <p className="text-slate-400 leading-relaxed text-xs">{simData.economic_mechanism}</p>
            </div>

            {/* High-level vulnerability highlights */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
              <div className="p-3 bg-rose-950/30 border border-rose-900/50 rounded-lg space-y-1">
                <span className="text-rose-400 text-[10px] uppercase font-bold block">
                  Most Vulnerable Asset
                </span>
                <div className="flex items-baseline justify-between">
                  <span className="text-base font-bold text-white">{simData.most_vulnerable_symbol}</span>
                  <span className="text-sm font-bold text-rose-400">
                    {Number(simData.most_vulnerable_impact_pct || 0).toFixed(2)}% Shock
                  </span>
                </div>
              </div>

              <div className="p-3 bg-emerald-950/30 border border-emerald-900/50 rounded-lg space-y-1">
                <span className="text-emerald-400 text-[10px] uppercase font-bold block">
                  Most Resilient Asset
                </span>
                <div className="flex items-baseline justify-between">
                  <span className="text-base font-bold text-white">{simData.most_resilient_symbol}</span>
                  <span className="text-sm font-bold text-emerald-400">
                    {Number(simData.most_resilient_impact_pct || 0) > 0 ? '+' : ''}
                    {Number(simData.most_resilient_impact_pct || 0).toFixed(2)}% Shock
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Holding Impact Breakdown Table */}
          <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
            <h3 className="text-sm font-bold text-white">Holdings Sensitivity Breakdown</h3>
            <div className="overflow-x-auto border border-slate-800/80 rounded-xl bg-slate-950">
              <table className="w-full text-left text-xs whitespace-nowrap font-mono">
                <thead className="bg-slate-900/90 text-slate-400 font-semibold border-b border-slate-800 uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="py-2.5 px-3">Symbol</th>
                    <th className="py-2.5 px-3">Sector</th>
                    <th className="py-2.5 px-3">Baseline Price (₹)</th>
                    <th className="py-2.5 px-3">Simulated Price (₹)</th>
                    <th className="py-2.5 px-3">Shock (%)</th>
                    <th className="py-2.5 px-3">Portfolio Impact (₹)</th>
                    <th className="py-2.5 px-3">Transmission Mechanism</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-200">
                  {holdingImpacts.map((h, idx) => {
                    const isPos = (h.shock_pct || 0) >= 0;
                    return (
                      <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                        <td className="py-2.5 px-3 font-bold text-white">{h.symbol}</td>
                        <td className="py-2.5 px-3 font-sans text-slate-400">{h.sector}</td>
                        <td className="py-2.5 px-3">₹{Number(h.current_price).toFixed(2)}</td>
                        <td className="py-2.5 px-3 font-semibold text-slate-100">
                          ₹{Number(h.simulated_price).toFixed(2)}
                        </td>
                        <td
                          className={`py-2.5 px-3 font-bold ${
                            isPos ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {isPos ? '+' : ''}{Number(h.shock_pct).toFixed(2)}%
                        </td>
                        <td
                          className={`py-2.5 px-3 font-semibold ${
                            (h.impact_amount || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {(h.impact_amount || 0) >= 0 ? '+' : ''}₹{Number(h.impact_amount).toFixed(2)}
                        </td>
                        <td className="py-2.5 px-3 font-sans text-[11px] text-slate-300">
                          {h.sensitivity_mechanism}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}

      <DataProvenanceFooter
        source={asOf.source}
        asOf={asOf.date}
        status="Macro Stress Engine (Academic Simulation)"
      />
    </div>
  );
}
