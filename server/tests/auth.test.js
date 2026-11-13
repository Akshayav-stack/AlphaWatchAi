process.env.NODE_ENV = 'test';
process.env.IN_TEST = '1';
process.env.DATABASE_PATH = './alphawatch_test.db';

import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import app from '../src/index.js';
import { db } from '../src/db.js';

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

describe('AlphaWatch Authentication & Right to Erasure Tests', () => {
  const testEmail = `test_${Date.now()}@alphawatch.local`;
  const testPassword = 'StrongPassword2026!';
  let sessionCookie = '';
  let csrfToken = '';

  test('POST /api/auth/register fails with short password (< 10 chars)', async () => {
    const res = await fetch(`${baseUrl}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'Short Pass User',
        email: `short_${Date.now()}@alphawatch.local`,
        password: 'short',
        consent_given: true,
      }),
    });
    assert.equal(res.status, 400);
    const data = await res.json();
    assert.match(data.error, /10 characters/);
  });

  test('POST /api/auth/register fails without consent checkbox', async () => {
    const res = await fetch(`${baseUrl}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'No Consent User',
        email: `noconsent_${Date.now()}@alphawatch.local`,
        password: testPassword,
        consent_given: false,
      }),
    });
    assert.equal(res.status, 400);
    const data = await res.json();
    assert.match(data.error, /consent/i);
  });

  test('POST /api/auth/register succeeds with valid details', async () => {
    const res = await fetch(`${baseUrl}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'Dr. Jane Quant',
        email: testEmail,
        password: testPassword,
        consent_given: true,
      }),
    });
    assert.equal(res.status, 201);
    const data = await res.json();
    assert.equal(data.success, true);
    assert.equal(data.user.email, testEmail);
    assert.ok(data.csrfToken);
    csrfToken = data.csrfToken;

    // Capture set-cookie header
    const rawCookie = res.headers.get('set-cookie');
    assert.ok(rawCookie);
    assert.match(rawCookie, /alphawatch_session/);
    assert.match(rawCookie, /HttpOnly/i);
    assert.match(rawCookie, /SameSite=Lax/i);
    sessionCookie = rawCookie.split(';')[0];
  });

  test('POST /api/auth/register fails on duplicate email', async () => {
    const res = await fetch(`${baseUrl}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'Duplicate User',
        email: testEmail,
        password: testPassword,
        consent_given: true,
      }),
    });
    assert.equal(res.status, 409);
    const data = await res.json();
    assert.match(data.error, /already exists/i);
  });

  test('POST /api/auth/login fails with wrong password (generic error)', async () => {
    const res = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: testEmail,
        password: 'WrongPassword123!',
      }),
    });
    assert.equal(res.status, 401);
    const data = await res.json();
    assert.equal(data.error, 'Invalid email or password.');
  });

  test('POST /api/auth/login succeeds with correct password & rotates session', async () => {
    const res = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: testEmail,
        password: testPassword,
      }),
    });
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.equal(data.success, true);
    assert.equal(data.user.email, testEmail);
    assert.ok(data.csrfToken);
    csrfToken = data.csrfToken;

    const rawCookie = res.headers.get('set-cookie');
    sessionCookie = rawCookie.split(';')[0];
  });

  test('GET /api/auth/me returns authenticated user with session cookie', async () => {
    const res = await fetch(`${baseUrl}/api/auth/me`, {
      headers: { Cookie: sessionCookie },
    });
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(data.user);
    assert.equal(data.user.email, testEmail);
  });

  test('POST /api/auth/logout clears session', async () => {
    const res = await fetch(`${baseUrl}/api/auth/logout`, {
      method: 'POST',
      headers: { Cookie: sessionCookie },
    });
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.equal(data.success, true);

    // Verify /api/auth/me is now null
    const checkRes = await fetch(`${baseUrl}/api/auth/me`, {
      headers: { Cookie: sessionCookie },
    });
    const checkData = await checkRes.json();
    assert.equal(checkData.user, null);
  });

  test('DELETE /api/auth/account permanently purges user (Right to Erasure)', async () => {
    // Log back in first
    const loginRes = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: testEmail, password: testPassword }),
    });
    const loginData = await loginRes.json();
    const newCookie = loginRes.headers.get('set-cookie').split(';')[0];

    // Attempt deletion without CSRF -> 403
    const noCsrfRes = await fetch(`${baseUrl}/api/auth/account`, {
      method: 'DELETE',
      headers: { Cookie: newCookie },
    });
    assert.equal(noCsrfRes.status, 403);

    // Delete with valid CSRF
    const deleteRes = await fetch(`${baseUrl}/api/auth/account`, {
      method: 'DELETE',
      headers: {
        Cookie: newCookie,
        'X-CSRF-Token': loginData.csrfToken,
      },
    });
    assert.equal(deleteRes.status, 200);

    // Verify user no longer exists in DB
    const userInDb = db.prepare(`SELECT id FROM users WHERE email = ?`).get(testEmail);
    assert.equal(userInDb, undefined);
  });
});
