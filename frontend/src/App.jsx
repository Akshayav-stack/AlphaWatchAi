import React from 'react';

export default function App() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 text-center">
      <div className="max-w-md p-8 bg-fintech-card border border-fintech-border rounded-xl shadow-2xl">
        <div className="inline-block px-3 py-1 mb-4 text-xs font-semibold text-blue-400 bg-blue-900/40 rounded-full border border-blue-700/50">
          ASTRAQUANT X 2026
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
          AlphaWatch AI
        </h1>
        <p className="mt-3 text-sm text-fintech-textMuted leading-relaxed">
          Offline Algorithmic Trading Intelligence Workstation for the Indian Stock Market.
        </p>
      </div>
    </div>
  );
}
