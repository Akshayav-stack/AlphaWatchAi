/**
 * AlphaWatch AI — Main Client Interaction Layer
 * ASTRAQUANT X 2026
 * 
 * 100% Offline Vanilla JS
 * - Mobile navigation menu toggle
 * - Expandable diagnostic accordion panels
 * - Local Plotly.js chart visualizers
 * - Accessible color schemes: Dark navy theme (#0A192F) with WCAG AA compliance
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Hamburger Navigation
    const navToggle = document.getElementById('nav-toggle');
    const navLinks = document.getElementById('nav-links');

    if (navToggle && navLinks) {
        navToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = navLinks.classList.toggle('nav-active');
            navToggle.setAttribute('aria-expanded', isOpen);
            navToggle.classList.toggle('is-active', isOpen);
        });

        // Close on navigation link click (smooth mobile routing)
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('nav-active');
                navToggle.setAttribute('aria-expanded', 'false');
                navToggle.classList.remove('is-active');
            });
        });

        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (!navLinks.contains(e.target) && !navToggle.contains(e.target)) {
                navLinks.classList.remove('nav-active');
                navToggle.setAttribute('aria-expanded', 'false');
                navToggle.classList.remove('is-active');
            }
        });

        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                navLinks.classList.remove('nav-active');
                navToggle.setAttribute('aria-expanded', 'false');
                navToggle.classList.remove('is-active');
            }
        });
    }

    // 2. Screener.in & Diagnostic Accordion Panels
    const accordionHeaders = document.querySelectorAll('.accordion-header');
    accordionHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const content = header.nextElementSibling;
            const icon = header.querySelector('.accordion-icon');
            if (content) {
                const isOpen = content.style.display === 'block';
                content.style.display = isOpen ? 'none' : 'block';
                if (icon) {
                    icon.textContent = isOpen ? '▼' : '▲';
                }
            }
        });
    });

    // 3. Tab Navigation (for pages with sub-views)
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const parent = btn.closest('.tab-container');
            if (!parent) return;

            parent.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            parent.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const targetPane = document.getElementById(targetId);
            if (targetPane) {
                targetPane.classList.add('active');
            }
        });
    });

    // 4. Dynamic Data-Fill Progress Bars
    document.querySelectorAll('.progress-bar-fill[data-fill]').forEach(bar => {
        bar.style.width = bar.getAttribute('data-fill');
    });
});

/**
 * Universal dark fintech Plotly layout configuration
 */
function getPlotlyDarkLayout(title, height = 380) {
    return {
        title: {
            text: title,
            font: { color: '#E2E8F0', size: 14, family: 'Inter, system-ui, sans-serif' },
            x: 0.05
        },
        paper_bgcolor: '#112240',
        plot_bgcolor: '#0B1528',
        margin: { l: 55, r: 25, t: 45, b: 45 },
        height: height,
        autosize: true,
        font: { color: '#94A3B8', family: 'Inter, system-ui, sans-serif' },
        xaxis: {
            gridcolor: '#1E293B',
            zerolinecolor: '#334155',
            tickfont: { color: '#94A3B8', size: 11 }
        },
        yaxis: {
            gridcolor: '#1E293B',
            zerolinecolor: '#334155',
            tickfont: { color: '#94A3B8', size: 11 }
        },
        legend: {
            orientation: 'h',
            y: -0.2,
            font: { color: '#CBD5E1', size: 11 }
        }
    };
}

const plotlyDefaultConfig = {
    responsive: true,
    displayModeBar: false,
};

/**
 * Renders NIFTY 50 Trend Chart with SMA 50 and SMA 200
 */
function renderNiftyTrendChart(elementId, dates, closes, sma50, sma200) {
    if (!window.Plotly || !document.getElementById(elementId)) return;

    const traces = [
        {
            x: dates,
            y: closes,
            type: 'scatter',
            mode: 'lines',
            name: 'NIFTY 50 Close',
            line: { color: '#64FFDA', width: 2 }
        },
        {
            x: dates,
            y: sma50,
            type: 'scatter',
            mode: 'lines',
            name: '50-Day SMA',
            line: { color: '#38BDF8', width: 1.5, dash: 'dot' }
        },
        {
            x: dates,
            y: sma200,
            type: 'scatter',
            mode: 'lines',
            name: '200-Day SMA',
            line: { color: '#F59E0B', width: 1.5, dash: 'dash' }
        }
    ];

    const layout = getPlotlyDarkLayout('NIFTY 50 Moving Average Trend', 400);
    layout.yaxis.title = 'Index Level';
    Plotly.newPlot(elementId, traces, layout, plotlyDefaultConfig);
}

/**
 * Renders Strategy vs Benchmark Cumulative Equity Curve
 */
function renderEquityCurveChart(elementId, dates, strategyEquity, benchmarkEquity) {
    if (!window.Plotly || !document.getElementById(elementId)) return;

    const traces = [
        {
            x: dates,
            y: strategyEquity,
            type: 'scatter',
            mode: 'lines',
            name: 'AlphaWatch Strategy (₹)',
            line: { color: '#10B981', width: 2.2 }
        },
        {
            x: dates,
            y: benchmarkEquity,
            type: 'scatter',
            mode: 'lines',
            name: 'Buy & Hold Benchmark (₹)',
            line: { color: '#94A3B8', width: 1.5, dash: 'dot' }
        }
    ];

    const layout = getPlotlyDarkLayout('Backtested Equity Growth (Zero-Lookahead Execution)', 380);
    layout.yaxis.title = 'Portfolio Value (₹)';
    Plotly.newPlot(elementId, traces, layout, plotlyDefaultConfig);
}

/**
 * Renders Efficient Frontier Plot for Modern Portfolio Optimization
 */
function renderEfficientFrontierChart(elementId, frontierPoints, currentPort, maxSharpe, minVar) {
    if (!window.Plotly || !document.getElementById(elementId)) return;

    const fVol = frontierPoints.map(p => p.volatility);
    const fRet = frontierPoints.map(p => p.return);

    const traces = [
        {
            x: fVol,
            y: fRet,
            type: 'scatter',
            mode: 'lines',
            name: 'Efficient Frontier',
            line: { color: '#38BDF8', width: 2 }
        }
    ];

    if (maxSharpe) {
        traces.push({
            x: [maxSharpe.expected_volatility_pct],
            y: [maxSharpe.expected_return_pct],
            type: 'scatter',
            mode: 'markers+text',
            name: 'Max Sharpe Portfolio',
            text: ['Max Sharpe'],
            textposition: 'top center',
            marker: { color: '#10B981', size: 12, symbol: 'star' }
        });
    }

    if (minVar) {
        traces.push({
            x: [minVar.expected_volatility_pct],
            y: [minVar.expected_return_pct],
            type: 'scatter',
            mode: 'markers+text',
            name: 'Minimum Variance',
            text: ['Min Var'],
            textposition: 'bottom center',
            marker: { color: '#F59E0B', size: 11, symbol: 'diamond' }
        });
    }

    if (currentPort) {
        traces.push({
            x: [currentPort.expected_volatility_pct],
            y: [currentPort.expected_return_pct],
            type: 'scatter',
            mode: 'markers+text',
            name: 'Current Portfolio',
            text: ['Current'],
            textposition: 'top left',
            marker: { color: '#64FFDA', size: 11, symbol: 'circle' }
        });
    }

    const layout = getPlotlyDarkLayout('Efficient Frontier & Risk-Return Tradeoff', 400);
    layout.xaxis.title = 'Annualized Volatility (%)';
    layout.yaxis.title = 'Expected Annual Return (%)';
    Plotly.newPlot(elementId, traces, layout, plotlyDefaultConfig);
}

/**
 * Renders Benchmark Relative Outperformance Chart
 */
function renderBenchmarkComparisonChart(elementId, dates, portRet, niftyRet) {
    if (!window.Plotly || !document.getElementById(elementId)) return;

    const traces = [
        {
            x: dates,
            y: portRet,
            type: 'scatter',
            mode: 'lines',
            name: 'Portfolio Cumulative %',
            line: { color: '#64FFDA', width: 2 }
        },
        {
            x: dates,
            y: niftyRet,
            type: 'scatter',
            mode: 'lines',
            name: 'NIFTY 50 %',
            line: { color: '#94A3B8', width: 1.5, dash: 'dot' }
        }
    ];

    const layout = getPlotlyDarkLayout('Cumulative Performance vs NIFTY 50', 360);
    layout.yaxis.title = 'Cumulative Return (%)';
    Plotly.newPlot(elementId, traces, layout, plotlyDefaultConfig);
}
