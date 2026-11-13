/**
 * AlphaWatch AI — Python ML Microservice Client
 * Communicates with the loopback Python FastAPI process (127.0.0.1:8001).
 * Safe timeout and fallback handling to ensure the Node gateway remains resilient.
 */

const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://127.0.0.1:8001';

export async function callMl(endpoint, options = {}) {
  const url = `${ML_SERVICE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  const method = (options.method || 'GET').toUpperCase();
  const headers = {
    'Accept': 'application/json',
    ...(options.headers || {}),
  };

  let body = options.body;
  if (body && typeof body === 'object' && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(body);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), options.timeoutMs || 15000);

  try {
    const res = await fetch(url, {
      method,
      headers,
      body,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      const errText = await res.text();
      let errJson;
      try { errJson = JSON.parse(errText); } catch { errJson = null; }
      const message = errJson?.detail || errJson?.error || `ML Service returned status ${res.status}`;
      const err = new Error(message);
      err.status = res.status;
      throw err;
    }

    return await res.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      const timeoutErr = new Error('ML microservice request timed out.');
      timeoutErr.status = 504;
      throw timeoutErr;
    }
    throw error;
  }
}
