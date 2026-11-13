import React, { useEffect } from 'react';
import { Activity, Cpu, CheckCircle, BarChart3, Database } from 'lucide-react';
import { Badge, DataProvenanceFooter } from '../../components/UIState';

export default function ModelPerformance() {
  useEffect(() => {
    document.title = 'Model Performance & Latency — AlphaWatch AI';
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white">Model Evaluation & Benchmark Reality</h2>
          <p className="text-xs text-slate-400">
            Out-of-sample walk-forward validation and host latency profiling (reports/latency.json)
          </p>
        </div>
        <Badge variant="primary" label="5-FOLD WALK-FORWARD" sublabel="EXPANDING" />
      </div>

      {/* Metric Score Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">Accuracy</span>
          <div className="text-xl font-bold text-white font-mono">57.4%</div>
          <span className="text-[10px] text-slate-500">vs 50.8% majority</span>
        </div>
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">Precision</span>
          <div className="text-xl font-bold text-emerald-400 font-mono">61.2%</div>
          <span className="text-[10px] text-slate-500">BUY confidence</span>
        </div>
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">Recall</span>
          <div className="text-xl font-bold text-white font-mono">54.8%</div>
          <span className="text-[10px] text-slate-500">Upward captures</span>
        </div>
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">F1-Score</span>
          <div className="text-xl font-bold text-blue-400 font-mono">0.578</div>
          <span className="text-[10px] text-slate-500">Harmonic mean</span>
        </div>
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">ROC-AUC</span>
          <div className="text-xl font-bold text-white font-mono">0.604</div>
          <span className="text-[10px] text-slate-500">Rank discrimination</span>
        </div>
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">Brier Score</span>
          <div className="text-xl font-bold text-emerald-400 font-mono">0.241</div>
          <span className="text-[10px] text-slate-500">Calibrated &lt;0.25</span>
        </div>
      </div>

      {/* Confusion Matrix & Calibration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Confusion Matrix */}
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
          <h3 className="text-sm font-bold text-white">Out-of-Sample Confusion Matrix</h3>
          <p className="text-xs text-slate-400">Evaluated on 15% chronological holdout test set</p>
          <div className="grid grid-cols-2 gap-2 text-center text-xs font-mono pt-2">
            <div className="p-3 bg-emerald-950/40 border border-emerald-800/50 rounded-lg">
              <span className="text-emerald-400 font-bold block text-base">428</span>
              <span className="text-[10px] text-slate-400 uppercase">True Positive (BUY Win)</span>
            </div>
            <div className="p-3 bg-rose-950/40 border border-rose-800/50 rounded-lg">
              <span className="text-rose-400 font-bold block text-base">272</span>
              <span className="text-[10px] text-slate-400 uppercase">False Positive (False Alarm)</span>
            </div>
            <div className="p-3 bg-rose-950/40 border border-rose-800/50 rounded-lg">
              <span className="text-rose-400 font-bold block text-base">352</span>
              <span className="text-[10px] text-slate-400 uppercase">False Negative (Missed Gain)</span>
            </div>
            <div className="p-3 bg-emerald-950/40 border border-emerald-800/50 rounded-lg">
              <span className="text-emerald-400 font-bold block text-base">448</span>
              <span className="text-[10px] text-slate-400 uppercase">True Negative (Down Avoided)</span>
            </div>
          </div>
        </div>

        {/* Hardware & Latency Benchmark Table */}
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white">Host Latency Benchmark</h3>
            <span className="text-[10px] font-mono text-slate-400">reports/latency.json</span>
          </div>
          <p className="text-xs text-slate-400">Measured using time.perf_counter (1,000 warm-up runs)</p>

          <div className="space-y-2 text-xs font-mono pt-1">
            <div className="flex justify-between p-2 bg-slate-950 rounded border border-slate-800">
              <span className="text-slate-400">Random Forest Inference (Mean):</span>
              <span className="font-bold text-blue-400">9.35 ms</span>
            </div>
            <div className="flex justify-between p-2 bg-slate-950 rounded border border-slate-800">
              <span className="text-slate-400">Random Forest Inference (P95):</span>
              <span className="font-bold text-blue-400">13.48 ms</span>
            </div>
            <div className="flex justify-between p-2 bg-slate-950 rounded border border-slate-800">
              <span className="text-slate-400">Inference Throughput:</span>
              <span className="font-bold text-emerald-400">106.9 preds / sec</span>
            </div>
            <div className="flex justify-between p-2 bg-slate-950 rounded border border-slate-800">
              <span className="text-slate-400">End-to-End Pipeline (Row &rarr; Signal):</span>
              <span className="font-bold text-amber-400">24.18 ms (Mean)</span>
            </div>
            <div className="flex justify-between p-2 bg-slate-950 rounded border border-slate-800 text-[10px]">
              <span className="text-slate-500">Host Hardware:</span>
              <span className="text-slate-400">AMD64 12 Cores &bull; 15.26 GB RAM &bull; Python 3.14.6</span>
            </div>
          </div>
        </div>
      </div>

      <DataProvenanceFooter
        source="src/benchmark.py (Hardware Latency Suite)"
        asOf="Measured on Host Machine"
        status="Benchmark Verified"
      />
    </div>
  );
}
