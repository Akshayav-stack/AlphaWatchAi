/**
 * AlphaWatch AI — AI Decision Intelligence Client
 * ASTRAQUANT X 2026
 * Offline-compatible, CSP-compliant dynamic explainability client.
 */

document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('ai-decision-intelligence');
  if (!container) return;

  const stockPills = container.querySelectorAll('.xai-stock-pill');
  const profileSelect = container.getElementById ? container.getElementById('xai-profile-select') : document.getElementById('xai-profile-select');
  const explainButtons = document.querySelectorAll('.btn-explain-ai');

  let currentSymbol = container.getAttribute('data-initial-symbol') || 'RELIANCE';

  function fetchExplanation(symbol, profile) {
    const prof = profile || (profileSelect ? profileSelect.value : 'Moderate');
    const loadingEl = document.getElementById('xai-loading');
    const contentEl = document.getElementById('xai-content');
    const errorEl = document.getElementById('xai-error');

    if (loadingEl) loadingEl.style.display = 'block';
    if (contentEl) contentEl.style.opacity = '0.5';
    if (errorEl) errorEl.style.display = 'none';

    fetch(`/api/explain/${encodeURIComponent(symbol)}?profile=${encodeURIComponent(prof)}`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: Could not load explanation for ${symbol}`);
        }
        return res.json();
      })
      .then((data) => {
        renderExplanation(data);
        if (loadingEl) loadingEl.style.display = 'none';
        if (contentEl) contentEl.style.opacity = '1';
      })
      .catch((err) => {
        if (loadingEl) loadingEl.style.display = 'none';
        if (errorEl) {
          errorEl.textContent = err.message;
          errorEl.style.display = 'block';
        }
      });
  }

  function renderExplanation(data) {
    // Symbol & Name
    const symEl = document.getElementById('xai-symbol');
    if (symEl) symEl.textContent = data.symbol;
    const nameEl = document.getElementById('xai-name');
    if (nameEl) nameEl.textContent = data.name;
    const priceEl = document.getElementById('xai-price');
    if (priceEl) priceEl.textContent = `₹${Number(data.latest_close).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    const dateEl = document.getElementById('xai-date');
    if (dateEl) dateEl.textContent = data.as_of_date;

    // Signal Badge
    const sigBadge = document.getElementById('xai-signal-badge');
    if (sigBadge) {
      sigBadge.textContent = data.signal;
      sigBadge.className = `badge ${data.signal === 'BUY' ? 'badge-buy' : data.signal === 'SELL' ? 'badge-sell' : 'badge-neutral'}`;
    }

    // Probability & Gauge
    const probPct = data.probability_meter ? data.probability_meter.percentage : (data.calibrated_probability * 100).toFixed(1);
    const probEl = document.getElementById('xai-prob-pct');
    if (probEl) probEl.textContent = `${probPct}%`;
    const barEl = document.getElementById('xai-prob-bar');
    if (barEl) barEl.style.width = `${Math.min(100, Math.max(5, probPct))}%`;
    const bandEl = document.getElementById('xai-band-label');
    if (bandEl && data.probability_meter) bandEl.textContent = data.probability_meter.band_label;

    // Summary
    const sumEl = document.getElementById('xai-summary-text');
    if (sumEl) sumEl.textContent = `"${data.summary}"`;

    // Positive Factors
    const posList = document.getElementById('xai-pos-factors');
    if (posList) {
      posList.innerHTML = '';
      const factors = (data.factors && data.factors.positive) || [];
      if (factors.length === 0) {
        posList.innerHTML = '<li class="text-muted italic">No positive factors currently qualify under active criteria.</li>';
      } else {
        factors.forEach((f) => {
          const li = document.createElement('li');
          li.className = 'xai-factor-item xai-factor-pos';
          li.innerHTML = `<strong>+ ${f.label || f.feature}</strong> (Value: ${f.value_formatted || f.value}, +${f.shap_contribution} SHAP)<p class="text-xs">${f.reason}</p>`;
          posList.appendChild(li);
        });
      }
    }

    // Negative Factors
    const negList = document.getElementById('xai-neg-factors');
    if (negList) {
      negList.innerHTML = '';
      const factors = (data.factors && data.factors.negative) || [];
      if (factors.length === 0) {
        negList.innerHTML = '<li class="text-muted italic">No negative factors currently qualify under active criteria.</li>';
      } else {
        factors.forEach((f) => {
          const li = document.createElement('li');
          li.className = 'xai-factor-item xai-factor-neg';
          li.innerHTML = `<strong>- ${f.label || f.feature}</strong> (Value: ${f.value_formatted || f.value}, ${f.shap_contribution} SHAP)<p class="text-xs">${f.reason}</p>`;
          negList.appendChild(li);
        });
      }
    }

    // Risk Alerts
    const alertsContainer = document.getElementById('xai-risk-alerts');
    if (alertsContainer) {
      alertsContainer.innerHTML = '';
      const alerts = data.risk_alerts || [];
      if (alerts.length === 0) {
        alertsContainer.innerHTML = '<p class="text-xs text-muted">No risk alerts triggered by current data.</p>';
      } else {
        alerts.forEach((a) => {
          const div = document.createElement('div');
          div.className = 'xai-alert-card';
          div.innerHTML = `<strong>⚠️ ${a.trigger_metric || a.type} (Trigger: ${a.trigger_value}, Limit: ${a.threshold_value})</strong><p class="text-xs">${a.message}</p>`;
          alertsContainer.appendChild(div);
        });
      }
    }
  }

  // Stock Pill Clicks
  stockPills.forEach((btn) => {
    btn.addEventListener('click', () => {
      stockPills.forEach((p) => p.classList.remove('active'));
      btn.classList.add('active');
      currentSymbol = btn.getAttribute('data-symbol');
      fetchExplanation(currentSymbol);
    });
  });

  // Signal Row Explain Buttons
  explainButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const sym = btn.getAttribute('data-symbol');
      if (sym) {
        currentSymbol = sym;
        stockPills.forEach((p) => {
          if (p.getAttribute('data-symbol') === sym) p.classList.add('active');
          else p.classList.remove('active');
        });
        fetchExplanation(sym);
        container.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // Initial load
  if (currentSymbol) {
    fetchExplanation(currentSymbol);
  }
});
