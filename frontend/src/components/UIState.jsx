import React from 'react';
import { AlertTriangle, AlertCircle, Info, Database } from 'lucide-react';

/**
 * LoadingSpinner — Accessible loading state
 */
export function LoadingSpinner({ text = 'Loading data...', size = 'default' }) {
  const spinnerSize = size === 'small' ? 'w-5 h-5' : size === 'large' ? 'w-10 h-10' : 'w-8 h-8';
  return (
    <div className="flex flex-col items-center justify-center p-8 space-y-3" role="status" aria-live="polite">
      <div
        className={`${spinnerSize} border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin`}
        aria-hidden="true"
      />
      {text && <p className="text-xs text-slate-400 font-medium tracking-wide">{text}</p>}
      <span className="sr-only">Loading</span>
    </div>
  );
}

/**
 * EmptyState — Honest empty state when data is missing or empty
 */
export function EmptyState({
  title = 'No Data Available',
  description = 'No computed records match the current criteria.',
  icon: Icon = Info,
  action,
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-slate-900/40 border border-slate-800 rounded-xl">
      <div className="p-3 bg-slate-800/80 rounded-full text-slate-400 mb-3">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
      <p className="mt-1 text-xs text-slate-400 max-w-sm leading-relaxed">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

/**
 * ErrorMessage — Field or container level error box
 */
export function ErrorMessage({
  title = 'Error',
  message,
  onRetry,
}) {
  if (!message) return null;
  return (
    <div
      className="p-4 bg-red-950/40 border border-red-800/60 rounded-xl text-left"
      role="alert"
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          {title && <h4 className="text-xs font-semibold text-red-200 uppercase tracking-wider">{title}</h4>}
          <p className="text-xs text-red-300 mt-0.5 leading-relaxed">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-2 text-xs font-medium text-red-400 hover:text-red-300 underline underline-offset-2"
            >
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Badge — Accessible signal / status pill
 * Rule: Green and red are ALWAYS paired with clear text labels.
 */
export function Badge({ variant = 'neutral', label, sublabel }) {
  const styles = {
    buy: 'bg-emerald-950/60 text-emerald-300 border-emerald-700/60',
    sell: 'bg-rose-950/60 text-rose-300 border-rose-700/60',
    hold: 'bg-amber-950/60 text-amber-300 border-amber-700/60',
    primary: 'bg-blue-950/60 text-blue-300 border-blue-700/60',
    neutral: 'bg-slate-800 text-slate-300 border-slate-700',
    low: 'bg-emerald-950/50 text-emerald-300 border-emerald-700/50',
    medium: 'bg-amber-950/50 text-amber-300 border-amber-700/50',
    high: 'bg-rose-950/50 text-rose-300 border-rose-700/50',
  };

  const currentStyle = styles[variant] || styles.neutral;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-semibold rounded-full border ${currentStyle}`}
    >
      <span>{label}</span>
      {sublabel && (
        <span className="text-[10px] opacity-75 font-normal tracking-wide">
          ({sublabel})
        </span>
      )}
    </span>
  );
}

/**
 * DataProvenanceFooter — Data source and as-of date metadata stamp
 */
export function DataProvenanceFooter({
  source = 'NSE CM-UDiFF Archive',
  asOf = 'Latest Saved Bhavcopy',
  status = 'Offline Verified',
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 pt-3 mt-4 text-[11px] text-slate-500 border-t border-slate-800/80">
      <div className="flex items-center gap-1.5">
        <Database className="w-3.5 h-3.5 text-slate-400" />
        <span>Source: <strong className="text-slate-400 font-medium">{source}</strong></span>
      </div>
      <div>
        <span>As-of: <strong className="text-slate-400 font-medium">{asOf}</strong></span>
      </div>
      <div className="flex items-center gap-1">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block"></span>
        <span className="text-slate-400 font-medium">{status}</span>
      </div>
    </div>
  );
}
