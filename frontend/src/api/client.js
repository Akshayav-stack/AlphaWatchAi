/**
 * AlphaWatch AI — API Client
 * Centralized fetch wrapper that sends cookies, attaches CSRF tokens, and handles error normalization.
 * 
 * SERVER ENDPOINT AUDIT NOTE:
 * The only endpoint currently running on /server is:
 *   - GET /api/health
 * 
 * The following required endpoints are pending implementation in /server:
 *   - POST /api/auth/register
 *   - POST /api/auth/login
 *   - POST /api/auth/logout
 *   - GET  /api/auth/me
 *   - GET  /api/auth/csrf
 *   - POST /api/auth/change-password
 *   - DELETE /api/auth/account
 *   - GET  /api/onboarding
 *   - POST /api/onboarding
 *   - GET  /api/holdings
 *   - POST /api/holdings
 *   - POST /api/holdings/demo
 *   - GET  /api/dashboard/overview
 *   - GET  /api/dashboard/predictions
 *   - GET  /api/dashboard/buy-candidates
 *   - GET  /api/dashboard/risk
 *   - POST /api/dashboard/backtest
 *   - GET  /api/dashboard/model-performance
 *   - GET  /api/dashboard/paper-trading
 *   - POST /api/dashboard/paper-trading/order
 *   - POST /api/dashboard/paper-trading/reset
 *   - POST /api/dashboard/auditor
 *   - POST /api/dashboard/ripple
 */

let storedCsrfToken = null;

export function setCsrfToken(token) {
  storedCsrfToken = token;
}

export function getCsrfToken() {
  return storedCsrfToken;
}

export class ApiError extends Error {
  constructor(message, status = 500, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Universal fetch wrapper for AlphaWatch backend
 */
export async function apiFetch(endpoint, options = {}) {
  const url = endpoint.startsWith('/') ? `/api${endpoint}` : `/api/${endpoint}`;
  
  const headers = {
    'Accept': 'application/json',
    ...(options.headers || {}),
  };

  const method = (options.method || 'GET').toUpperCase();

  // Attach CSRF token on state-changing requests
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method) && storedCsrfToken) {
    headers['X-CSRF-Token'] = storedCsrfToken;
  }

  // Handle JSON bodies
  let body = options.body;
  if (body && typeof body === 'object' && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(body);
  }

  try {
    const response = await fetch(url, {
      ...options,
      method,
      headers,
      body,
      credentials: 'include', // Ensure signed session cookies are included
    });

    let data = null;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      const text = await response.text();
      try {
        data = JSON.parse(text);
      } catch {
        data = { message: text };
      }
    }

    if (!response.ok) {
      const errorMessage = data?.error || data?.message || `Request failed with status ${response.status}`;
      throw new ApiError(errorMessage, response.status, data);
    }

    return data;
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    // Network or connection failure
    throw new ApiError(
      err.message || 'Network error connecting to AlphaWatch server',
      0,
      null
    );
  }
}

// ----------------------------------------------------------------------------
// Existing Server Endpoints
// ----------------------------------------------------------------------------

export async function checkServerHealth() {
  return apiFetch('/health');
}

// ----------------------------------------------------------------------------
// Authentication Endpoints (Prepared for Step 3 implementation in /server)
// ----------------------------------------------------------------------------

export async function getCsrfTokenApi() {
  const data = await apiFetch('/auth/csrf');
  if (data?.csrfToken) {
    setCsrfToken(data.csrfToken);
  }
  return data;
}

export async function getCurrentUserApi() {
  return apiFetch('/auth/me');
}

export async function registerUserApi(payload) {
  return apiFetch('/auth/register', {
    method: 'POST',
    body: payload,
  });
}

export async function loginUserApi(payload) {
  return apiFetch('/auth/login', {
    method: 'POST',
    body: payload,
  });
}

export async function logoutUserApi() {
  return apiFetch('/auth/logout', {
    method: 'POST',
  });
}

export async function changePasswordApi(payload) {
  return apiFetch('/auth/change-password', {
    method: 'POST',
    body: payload,
  });
}

export async function deleteAccountApi() {
  return apiFetch('/auth/account', {
    method: 'DELETE',
  });
}

// ----------------------------------------------------------------------------
// Onboarding API Methods
// ----------------------------------------------------------------------------

export async function getOnboardingDataApi() {
  return apiFetch('/onboarding');
}

export async function submitOnboardingApi(payload) {
  return apiFetch('/onboarding', {
    method: 'POST',
    body: payload,
  });
}

// ----------------------------------------------------------------------------
// Dashboard API Methods
// ----------------------------------------------------------------------------

export async function getDashboardOverviewApi() {
  return apiFetch('/dashboard/overview');
}

export async function getPredictionsApi() {
  return apiFetch('/dashboard/predictions');
}

export async function getBuyCandidatesApi() {
  return apiFetch('/dashboard/buy-candidates');
}

export async function getRiskAnalysisApi() {
  return apiFetch('/dashboard/risk');
}

export async function runBacktestApi(payload) {
  return apiFetch('/dashboard/backtest', {
    method: 'POST',
    body: payload,
  });
}

export async function getModelPerformanceApi() {
  return apiFetch('/dashboard/model-performance');
}

export async function getPaperTradingApi() {
  return apiFetch('/dashboard/paper-trading');
}

export async function executePaperOrderApi(payload) {
  return apiFetch('/dashboard/paper-trading/order', {
    method: 'POST',
    body: payload,
  });
}

export async function resetPaperTradingApi() {
  return apiFetch('/dashboard/paper-trading/reset', {
    method: 'POST',
  });
}

export async function runClaimAuditorApi(payload) {
  return apiFetch('/dashboard/auditor', {
    method: 'POST',
    body: payload,
  });
}

export async function getRippleScenariosApi() {
  return apiFetch('/dashboard/ripple/scenarios');
}

export async function runRippleSimulationApi(payload) {
  return apiFetch('/dashboard/ripple', {
    method: 'POST',
    body: payload,
  });
}

export async function getMyPatternApi() {
  return apiFetch('/dashboard/my-pattern');
}

export async function getUserHoldingsApi() {
  return apiFetch('/dashboard/holdings');
}
