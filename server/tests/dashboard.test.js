process.env.NODE_ENV = 'test';
process.env.IN_TEST = '1';
process.env.DATABASE_PATH = './alphawatch_dashboard_test.db';

import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import app from '../src/index.js';

let server;
let baseUrl;

before(async () => {
  server = http.createServer(app);
  await new Promise((resolve) => {
    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port;
      baseUrl = `http://127.0.0.1:${port}`;
      resolve();
    });
  });
});

after(async () => {
  if (server) {
    await new Promise((resolve) => server.close(resolve));
  }
});

describe('AlphaWatch Onboarding & Dashboard Integration Tests', () => {
  const testEmail = `user_dash_${Date.now()}@alphawatch.local`;
  const testPassword = 'SecureDashboardPass2026!';
  let sessionCookie = '';
  let csrfToken = '';

  test('Register and authenticate user for dashboard', async () => {
    const regRes = await fetch(`${baseUrl}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'Dashboard Tester',
        email: testEmail,
        password: testPassword,
        consent_given: true,
      }),
    });
    assert.equal(regRes.status, 201);
    const regData = await regRes.json();
    assert.ok(regData.csrfToken);
    csrfToken = regData.csrfToken;

    const cookieHeader = regRes.headers.get('set-cookie');
    assert.ok(cookieHeader);
    sessionCookie = cookieHeader.split(';')[0];
  });

  test('GET /api/onboarding returns symbols and demo portfolios', async () => {
    const res = await fetch(`${baseUrl}/api/onboarding`, {
      headers: { Cookie: sessionCookie },
    });
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(Array.isArray(data.symbols));
    assert.ok(data.symbols.length > 0);
    assert.ok(data.demoPortfolios);
  });

  test('POST /api/onboarding saves holdings and assigns profile', async () => {
    const res = await fetch(`${baseUrl}/api/onboarding`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Cookie: sessionCookie,
        'X-CSRF-Token': csrfToken,
      },
      body: JSON.stringify({
        holdings: [
          { symbol: 'RELIANCE', quantity: 10, buy_price: 2500.0 },
          { symbol: 'TCS', quantity: 5, buy_price: 3600.0 },
        ],
        answers: {
          goal: 'Wealth Creation',
          horizon: '3-5 Years',
          experience: 'Intermediate',
          trading_frequency: 'Monthly',
          fall_reaction: 'Hold and observe',
          savings_share: '10-25%',
        },
      }),
    });
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.equal(data.success, true);
    assert.ok(data.evaluation);
    assert.ok(data.evaluation.suggested_profile);
    assert.ok(typeof data.evaluation.risk_score === 'number');
  });

  test('GET /api/dashboard/overview returns portfolio valuation and risk', async () => {
    const res = await fetch(`${baseUrl}/api/dashboard/overview`, {
      headers: { Cookie: sessionCookie },
    });
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(data.profile);
    assert.ok(data.valuation);
    assert.ok(data.risk_summary);
    assert.ok(data.as_of);
  });

  test('GET /api/dashboard/predictions returns signals', async () => {
    const res = await fetch(`${baseUrl}/api/dashboard/predictions`, {
      headers: { Cookie: sessionCookie },
    });
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(Array.isArray(data.predictions));
    assert.ok(data.as_of);
  });

  test('GET /api/dashboard/buy-candidates returns ranked opportunities', async () => {
    const res = await fetch(`${baseUrl}/api/dashboard/buy-candidates`, {
      headers: { Cookie: sessionCookie },
    });
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(Array.isArray(data.candidates));
  });

  test('GET /api/dashboard/risk returns VaR and CVaR', async () => {
    const res = await fetch(`${baseUrl}/api/dashboard/risk`, {
      headers: { Cookie: sessionCookie },
    });
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(typeof data.portfolio_vol_20d === 'number');
    assert.ok(typeof data.portfolio_var_95 === 'number');
    assert.ok(typeof data.portfolio_cvar_95 === 'number');
  });

  test('Paper trading: get ledger, place BUY order, verify balance and reset', async () => {
    // 1. Initial ledger
    const initialRes = await fetch(`${baseUrl}/api/dashboard/paper-trading`, {
      headers: { Cookie: sessionCookie },
    });
    assert.equal(initialRes.status, 200);
    const initialData = await initialRes.json();
    assert.equal(initialData.cash_balance, 1000000);

    // 2. Place simulated BUY order
    const orderRes = await fetch(`${baseUrl}/api/dashboard/paper-trading/order`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Cookie: sessionCookie,
        'X-CSRF-Token': csrfToken,
      },
      body: JSON.stringify({
        symbol: 'RELIANCE',
        action: 'BUY',
        quantity: 10,
        price: 2500,
        notes: 'Integration test buy',
      }),
    });
    assert.equal(orderRes.status, 200);
    const orderData = await orderRes.json();
    assert.equal(orderData.success, true);

    // 3. Verify ledger reflects trade
    const ledgerRes = await fetch(`${baseUrl}/api/dashboard/paper-trading`, {
      headers: { Cookie: sessionCookie },
    });
    assert.equal(ledgerRes.status, 200);
    const ledgerData = await ledgerRes.json();
    assert.ok(ledgerData.cash_balance < 1000000);
    assert.equal(ledgerData.trades.length, 1);

    // 4. Reset ledger
    const resetRes = await fetch(`${baseUrl}/api/dashboard/paper-trading/reset`, {
      method: 'POST',
      headers: {
        Cookie: sessionCookie,
        'X-CSRF-Token': csrfToken,
      },
    });
    assert.equal(resetRes.status, 200);
    const resetData = await resetRes.json();
    assert.equal(resetData.success, true);

    // 5. Verify reset back to 1000000
    const finalRes = await fetch(`${baseUrl}/api/dashboard/paper-trading`, {
      headers: { Cookie: sessionCookie },
    });
    const finalData = await finalRes.json();
    assert.equal(finalData.cash_balance, 1000000);
    assert.equal(finalData.trades.length, 0);
  });

  test('GET /api/dashboard/my-pattern returns transparent explanations', async () => {
    const res = await fetch(`${baseUrl}/api/dashboard/my-pattern`, {
      headers: { Cookie: sessionCookie },
    });
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(data.profile);
    assert.ok(data.profile.why_this_profile);
    assert.ok(data.answers);
  });

  test('GET /api/dashboard/holdings returns user holdings', async () => {
    const res = await fetch(`${baseUrl}/api/dashboard/holdings`, {
      headers: { Cookie: sessionCookie },
    });
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(Array.isArray(data.holdings));
    assert.equal(data.holdings.length, 2);
  });
});
