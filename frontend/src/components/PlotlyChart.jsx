import React, { useEffect, useRef, useState } from 'react';
import { LoadingSpinner, ErrorMessage } from './UIState';

/**
 * PlotlyChart — Offline responsive wrapper for bundled local Plotly.js
 */
export default function PlotlyChart({
  data = [],
  layout = {},
  config = {},
  className = 'w-full h-80',
  title,
}) {
  const containerRef = useRef(null);
  const [error, setError] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Check if Plotly is loaded globally from /vendor/plotly.min.js
    if (!window.Plotly) {
      setError('Local Plotly bundle not found. Please ensure /vendor/plotly.min.js is present.');
      return;
    }
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready || !containerRef.current || !window.Plotly) return;

    const defaultLayout = {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: {
        color: '#94A3B8',
        family: 'ui-sans-serif, system-ui, -apple-system, sans-serif',
        size: 11,
      },
      margin: { l: 50, r: 20, t: 30, b: 40 },
      xaxis: {
        gridcolor: '#1E293B',
        zerolinecolor: '#334155',
        tickfont: { color: '#94A3B8' },
      },
      yaxis: {
        gridcolor: '#1E293B',
        zerolinecolor: '#334155',
        tickfont: { color: '#94A3B8' },
      },
      autosize: true,
      ...layout,
    };

    const defaultConfig = {
      responsive: true,
      displayModeBar: false, // Clean fintech UI without toolbar clutter
      ...config,
    };

    try {
      window.Plotly.newPlot(containerRef.current, data, defaultLayout, defaultConfig);
    } catch (err) {
      setError(`Failed to render chart: ${err.message}`);
    }

    const handleResize = () => {
      if (containerRef.current && window.Plotly) {
        window.Plotly.Plots.resize(containerRef.current);
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (containerRef.current && window.Plotly) {
        try {
          window.Plotly.purge(containerRef.current);
        } catch {
          // Ignore purge errors on unmount
        }
      }
    };
  }, [data, layout, config, ready]);

  if (error) {
    return <ErrorMessage title="Chart Error" message={error} />;
  }

  return (
    <div className="w-full">
      {title && (
        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
          {title}
        </h4>
      )}
      <div className="relative w-full overflow-hidden rounded-lg bg-slate-900/30 border border-slate-800">
        <div ref={containerRef} className={className} />
        {!ready && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-900/60">
            <LoadingSpinner text="Rendering chart..." />
          </div>
        )}
      </div>
    </div>
  );
}
