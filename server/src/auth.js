import { createRequire } from 'node:module';
import crypto from 'node:crypto';
import { db } from './db.js';

const require = createRequire(import.meta.url);
const argon2 = require('argon2');

const COMMON_PASSWORDS = new Set([
  'password123',
  'password1234',
  '1234567890',
  '12345678901',
  'qwerty12345',
  'alphawatch123',
  'admin123456',
  'welcome1234',
  'passcode1234',
]);

const LOCKOUT_THRESHOLD = Number(process.env.MAX_FAILED_LOGIN_ATTEMPTS || 5);
const LOCKOUT_MINUTES = Number(process.env.LOCKOUT_DURATION_MINUTES || 15);
const SESSION_MAX_AGE_MS = 24 * 60 * 60 * 1000; // 24 hours

export async function hashPassword(plainPassword) {
  if (plainPassword.length < 10) {
    throw new Error('Password must be at least 10 characters long.');
  }
  if (COMMON_PASSWORDS.has(plainPassword.toLowerCase())) {
    throw new Error('Password is too common or easily guessable. Please choose a stronger password.');
  }
  return argon2.hash(plainPassword, {
    type: argon2.argon2id,
    memoryCost: 65536, // 64 MB
    timeCost: 3,
    parallelism: 4,
  });
}

export async function verifyPassword(passwordHash, plainPassword) {
  try {
    return await argon2.verify(passwordHash, plainPassword);
  } catch {
    return false;
  }
}

export function generateToken() {
  return crypto.randomBytes(32).toString('hex');
}

export function createSession(userId) {
  const sessionToken = generateToken();
  const csrfToken = generateToken();
  const now = new Date();
  const expiresAt = new Date(now.getTime() + SESSION_MAX_AGE_MS).toISOString();

  const stmt = db.prepare(`
    INSERT INTO sessions (user_id, session_token, csrf_token, expires_at, created_at)
    VALUES (?, ?, ?, ?, ?)
  `);
  stmt.run(userId, sessionToken, csrfToken, expiresAt, now.toISOString());

  return { sessionToken, csrfToken };
}

export function deleteSession(sessionToken) {
  const stmt = db.prepare(`DELETE FROM sessions WHERE session_token = ?`);
  stmt.run(sessionToken);
}

export function deleteUserSessions(userId) {
  const stmt = db.prepare(`DELETE FROM sessions WHERE user_id = ?`);
  stmt.run(userId);
}

export function getSession(sessionToken) {
  if (!sessionToken) return null;
  const now = new Date().toISOString();
  const stmt = db.prepare(`
    SELECT s.id AS session_id, s.session_token, s.csrf_token, s.expires_at,
           u.id AS user_id, u.name, u.email, u.is_onboarded, u.consent_given
    FROM sessions s
    JOIN users u ON s.user_id = u.id
    WHERE s.session_token = ? AND s.expires_at > ?
  `);
  return stmt.get(sessionToken, now) || null;
}

// Authentication middleware
export function authenticate(req, res, next) {
  const sessionToken = req.signedCookies?.alphawatch_session || req.cookies?.alphawatch_session;
  if (!sessionToken) {
    req.user = null;
    req.session = null;
    return next();
  }

  const sessionData = getSession(sessionToken);
  if (!sessionData) {
    req.user = null;
    req.session = null;
    return next();
  }

  req.user = {
    id: sessionData.user_id,
    name: sessionData.name,
    email: sessionData.email,
    is_onboarded: Boolean(sessionData.is_onboarded),
    consent_given: Boolean(sessionData.consent_given),
  };
  req.session = {
    id: sessionData.session_id,
    sessionToken: sessionData.session_token,
    csrfToken: sessionData.csrf_token,
  };

  next();
}

export function requireAuth(req, res, next) {
  if (!req.user) {
    return res.status(401).json({ error: 'Authentication required. Please sign in.' });
  }
  next();
}

// CSRF verification middleware
export function verifyCsrf(req, res, next) {
  const method = req.method.toUpperCase();
  if (['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    return next();
  }

  if (!req.session) {
    return next(); // Unauthenticated requests (e.g. login/register) handle CSRF or validation separately
  }

  const clientCsrfToken = req.headers['x-csrf-token'];
  if (!clientCsrfToken || !req.session.csrfToken) {
    return res.status(403).json({ error: 'CSRF token missing or invalid.' });
  }

  try {
    const valid = crypto.timingSafeEqual(
      Buffer.from(clientCsrfToken),
      Buffer.from(req.session.csrfToken)
    );
    if (!valid) {
      return res.status(403).json({ error: 'CSRF verification failed.' });
    }
  } catch {
    return res.status(403).json({ error: 'CSRF verification error.' });
  }

  next();
}
