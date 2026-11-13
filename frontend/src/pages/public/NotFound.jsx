import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, ArrowLeft, Home } from 'lucide-react';

export default function NotFound() {
  useEffect(() => {
    document.title = '404 Page Not Found — AlphaWatch AI';
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] text-center px-4">
      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-2xl max-w-md w-full space-y-4">
        <div className="w-12 h-12 rounded-xl bg-red-950/60 border border-red-700/60 text-red-400 mx-auto flex items-center justify-center">
          <AlertCircle className="w-6 h-6" />
        </div>
        <div className="space-y-1">
          <h1 className="text-xl font-bold text-white tracking-tight">404 — Page Not Found</h1>
          <p className="text-xs text-slate-400 leading-relaxed">
            The requested quantitative resource or dashboard view does not exist in this workstation.
          </p>
        </div>
        <div className="pt-2 flex justify-center gap-3">
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm transition-colors"
          >
            <Home className="w-3.5 h-3.5" />
            <span>Return Home</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
