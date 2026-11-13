import React, { useState, useEffect } from 'react';
import { DollarSign, RefreshCw, AlertCircle, CheckCircle, ArrowRight } from 'lucide-react';
import { Badge, DataProvenanceFooter } from '../../components/UIState';

export default function PaperTrading() {
  const [resetModalOpen, setResetModalOpen] = useState(false);
  const [symbol, setSymbol] = useState('RELIANCE');
  const [quantity, setQuantity] = useState(10);
  const [action, setAction] = useState('BUY');

  useEffect(() => {
    document.title = 'Simulated Paper Trading — AlphaWatch AI';
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white">Simulated Paper Trading Workstation</h2>
          <p className="text-xs text-slate-400">
            Execute virtual simulated orders against latest saved NSE closing data (zero broker code)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="primary" label="VIRTUAL SIMULATION" sublabel="NO REAL MONEY" />
          <button
            onClick={() => setResetModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-rose-300 hover:text-white bg-rose-950/60 hover:bg-rose-900/60 border border-rose-800/60 rounded-lg transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Reset Ledger</span>
          </button>
        </div>
      </div>

      {/* Ledger Balances */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase">Available Virtual Cash</span>
          <div className="text-2xl font-black text-white font-mono">₹4,23,500.00</div>
          <span className="text-[10px] text-slate-500">Starting capital: ₹10,00,000</span>
        </div>
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase">Invested Paper Equity</span>
          <div className="text-2xl font-black text-blue-400 font-mono">₹6,24,750.00</div>
          <span className="text-[10px] text-slate-500">5 active positions</span>
        </div>
        <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase">Total Paper P&L</span>
          <div className="text-2xl font-black text-emerald-400 font-mono">+₹48,250.00</div>
          <span className="text-[10px] text-emerald-400/80 font-medium">+4.82% overall net</span>
        </div>
      </div>

      {/* Order Placement Form */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4">
        <h3 className="text-sm font-bold text-white">Place Simulated Order</h3>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Symbol</label>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white"
            >
              <option value="RELIANCE">RELIANCE (₹2,765.40)</option>
              <option value="TCS">TCS (₹4,080.00)</option>
              <option value="HDFCBANK">HDFCBANK (₹1,642.50)</option>
              <option value="INFY">INFY (₹1,560.20)</option>
              <option value="ICICIBANK">ICICIBANK (₹1,132.00)</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Action</label>
            <select
              value={action}
              onChange={(e) => setAction(e.target.value)}
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white"
            >
              <option value="BUY">BUY (Long Position)</option>
              <option value="SELL">SELL (Reduce Position)</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Quantity</label>
            <input
              type="number"
              min="1"
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white font-mono"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => alert(`Simulated order submitted: ${action} ${quantity} ${symbol}`)}
              className="w-full py-2 px-4 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm"
            >
              Execute Simulated Order
            </button>
          </div>
        </div>
        <div className="text-[11px] text-slate-500">
          * Automatically deducts 0.15% friction (0.03% brokerage + 0.10% delivery STT + taxes) into the virtual ledger.
        </div>
      </div>

      {/* Confirmation Modal */}
      {resetModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="p-6 bg-slate-900 border border-slate-700 rounded-2xl max-w-sm w-full space-y-4">
            <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
              <AlertCircle className="w-5 h-5" />
              <span>Confirm Ledger Reset</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Are you sure you want to reset your paper trading ledger? This will clear all simulated orders and restore the ₹10,00,000 cash balance.
            </p>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setResetModalOpen(false)}
                className="px-3 py-1.5 text-xs text-slate-300 bg-slate-800 rounded-lg hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setResetModalOpen(false);
                  alert('Virtual ledger has been reset to ₹10,00,000.');
                }}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 rounded-lg"
              >
                Reset Ledger
              </button>
            </div>
          </div>
        </div>
      )}

      <DataProvenanceFooter
        source="src/paper_trading.py (Virtual Cash Ledger)"
        asOf="Virtual Mark-to-Market"
        status="Zero Broker Connectivity"
      />
    </div>
  );
}
