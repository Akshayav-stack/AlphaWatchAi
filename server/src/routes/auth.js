import { Router } from 'express';
import { z } from 'zod';
import rateLimit from 'express-rate-limit';
import { db } from '../db.js';
import {
  hashPassword,
  verifyPassword,
  createSession,
  deleteSession,
  deleteUserSessions,
  requireAuth,
  verifyCsrf,
} from '../auth.js';

const router = Router();

const isSecure = process.env.COOKIE_SECURE === 'true' || process.env.NODE_ENV === 'production';

// Dynamic rate limiting for auth routes (bypassed in test environment)
const rawLoginLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: Number(process.env.RATE_LIMIT_LOGIN_MAX || 5),
  message: { error: 'Too many login attempts. Please wait 1 minute before trying again.' },
  standardHeaders: true,
  legacyHeaders: false,
});

const rawRegisterLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: Number(process.env.RATE_LIMIT_REGISTER_MAX || 3),
  message: { error: 'Too many registration requests. Please wait a minute.' },
  standardHeaders: true,
  legacyHeaders: false,
});

const loginLimiter = (req, res, next) => {
  if (process.env.NODE_ENV === 'test' || process.env.IN_TEST === '1') return next();
  return rawLoginLimiter(req, res, next);
};

const registerLimiter = (req, res, next) => {
  if (process.env.NODE_ENV === 'test' || process.env.IN_TEST === '1') return next();
  return rawRegisterLimiter(req, res, next);
};

// Zod schemas
const registerSchema = z.object({
  name: z.string().min(1, 'Full name is required.').max(120),
  email: z.string().email('Please provide a valid email address.').max(255),
  password: z.string().min(10, 'Password must be at least 10 characters long.'),
  consent_given: z.boolean().refine((val) => val === true, {
    message: 'Academic research consent is required.',
  }),
});

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address.'),
  password: z.string().min(1, 'Password is required.'),
});

const changePasswordSchema = z.object({
  currentPassword: z.string().min(1, 'Current password is required.'),
  newPassword: z.string().min(10, 'New password must be at least 10 characters long.'),
});

// Cookie helper
function setSessionCookie(res, sessionToken) {
  res.cookie('alphawatch_session', sessionToken, {
    httpOnly: true,
    sameSite: 'lax',
    secure: isSecure,
    maxAge: 24 * 60 * 60 * 1000, // 24 hours
    signed: true,
    path: '/',
  });
}

function clearSessionCookie(res) {
  res.clearCookie('alphawatch_session', {
    httpOnly: true,
    sameSite: 'lax',
    secure: isSecure,
    path: '/',
  });
}

// ----------------------------------------------------------------------------
// POST /api/auth/register
// ----------------------------------------------------------------------------
router.post('/register', registerLimiter, async (req, res) => {
  const result = registerSchema.safeParse(req.body);
  if (!result.success) {
    const errorMsg = result.error.errors[0]?.message || 'Invalid input data.';
    return res.status(400).json({ error: errorMsg });
  }

  const { name, email, password, consent_given } = result.data;
  const normalizedEmail = email.trim().toLowerCase();

  // Check if email already registered
  const existingUser = db.prepare(`SELECT id FROM users WHERE email = ?`).get(normalizedEmail);
  if (existingUser) {
    return res.status(409).json({ error: 'An account with this email address already exists.' });
  }

  try {
    const passwordHash = await hashPassword(password);
    const now = new Date().toISOString();

    const insertStmt = db.prepare(`
      INSERT INTO users (name, email, password_hash, consent_given, is_onboarded, failed_login_attempts, created_at, updated_at)
      VALUES (?, ?, ?, ?, 0, 0, ?, ?)
    `);
    const info = insertStmt.run(name.trim(), normalizedEmail, passwordHash, consent_given ? 1 : 0, now, now);
    const userId = Number(info.lastInsertRowid);

    // Create session
    const { sessionToken, csrfToken } = createSession(userId);
    setSessionCookie(res, sessionToken);

    // Audit log
    db.prepare(`
      INSERT INTO audit_log (user_id, action, ip_address, details, created_at)
      VALUES (?, 'REGISTER', ?, 'User registered account', ?)
    `).run(userId, req.ip || '127.0.0.1', now);

    return res.status(201).json({
      success: true,
      user: {
        id: userId,
        name: name.trim(),
        email: normalizedEmail,
        is_onboarded: false,
        consent_given: true,
      },
      csrfToken,
    });
  } catch (err) {
    return res.status(400).json({ error: err.message || 'Registration failed.' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/auth/login
// ----------------------------------------------------------------------------
router.post('/login', loginLimiter, async (req, res) => {
  const result = loginSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(400).json({ error: 'Please enter a valid email and password.' });
  }

  const { email, password } = result.data;
  const normalizedEmail = email.trim().toLowerCase();
  const now = new Date();

  const user = db.prepare(`SELECT * FROM users WHERE email = ?`).get(normalizedEmail);
  if (!user) {
    // Generic error message to prevent enumeration
    return res.status(401).json({ error: 'Invalid email or password.' });
  }

  // Check lockout
  if (user.locked_until) {
    const lockTime = new Date(user.locked_until);
    if (lockTime > now) {
      const minutesRemaining = Math.ceil((lockTime.getTime() - now.getTime()) / 60000);
      return res.status(429).json({
        error: `Account is temporarily locked due to multiple failed login attempts. Please try again in ${minutesRemaining} minutes.`,
      });
    }
  }

  // Verify password
  const isValid = await verifyPassword(user.password_hash, password);
  if (!isValid) {
    const failedAttempts = (user.failed_login_attempts || 0) + 1;
    let lockedUntil = null;
    const lockoutThreshold = Number(process.env.MAX_FAILED_LOGIN_ATTEMPTS || 5);

    if (failedAttempts >= lockoutThreshold) {
      lockedUntil = new Date(now.getTime() + 15 * 60 * 1000).toISOString();
    }

    db.prepare(`
      UPDATE users
      SET failed_login_attempts = ?, locked_until = ?, updated_at = ?
      WHERE id = ?
    `).run(failedAttempts, lockedUntil, now.toISOString(), user.id);

    return res.status(401).json({ error: 'Invalid email or password.' });
  }

  // Password is correct: reset lockout and rotate sessions
  db.prepare(`
    UPDATE users
    SET failed_login_attempts = 0, locked_until = NULL, updated_at = ?
    WHERE id = ?
  `).run(now.toISOString(), user.id);

  // Session rotation: clear old sessions
  deleteUserSessions(user.id);
  const { sessionToken, csrfToken } = createSession(user.id);
  setSessionCookie(res, sessionToken);

  // Audit log
  db.prepare(`
    INSERT INTO audit_log (user_id, action, ip_address, details, created_at)
    VALUES (?, 'LOGIN', ?, 'Successful login with session rotation', ?)
  `).run(user.id, req.ip || '127.0.0.1', now.toISOString());

  return res.json({
    success: true,
    user: {
      id: user.id,
      name: user.name,
      email: user.email,
      is_onboarded: Boolean(user.is_onboarded),
      consent_given: Boolean(user.consent_given),
    },
    csrfToken,
  });
});

// ----------------------------------------------------------------------------
// POST /api/auth/logout
// ----------------------------------------------------------------------------
router.post('/logout', (req, res) => {
  const sessionToken = req.signedCookies?.alphawatch_session || req.cookies?.alphawatch_session;
  if (sessionToken) {
    deleteSession(sessionToken);
  }
  clearSessionCookie(res);
  return res.json({ success: true, message: 'Signed out successfully.' });
});

// ----------------------------------------------------------------------------
// GET /api/auth/me
// ----------------------------------------------------------------------------
router.get('/me', (req, res) => {
  if (!req.user) {
    return res.json({ user: null });
  }

  // Retrieve investor profile if exists
  const profile = db.prepare(`SELECT * FROM user_profiles WHERE user_id = ?`).get(req.user.id);

  return res.json({
    user: {
      ...req.user,
      suggested_profile: profile?.suggested_profile || 'Moderate',
      risk_score: profile?.risk_score ?? 50.0,
    },
    csrfToken: req.session?.csrfToken || null,
  });
});

// ----------------------------------------------------------------------------
// GET /api/auth/csrf
// ----------------------------------------------------------------------------
router.get('/csrf', (req, res) => {
  if (req.session) {
    return res.json({ csrfToken: req.session.csrfToken });
  }
  // Return a generic token if unauthenticated
  const tempToken = createSession(-1).csrfToken;
  return res.json({ csrfToken: tempToken });
});

// ----------------------------------------------------------------------------
// POST /api/auth/change-password
// ----------------------------------------------------------------------------
router.post('/change-password', requireAuth, verifyCsrf, async (req, res) => {
  const result = changePasswordSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(400).json({ error: result.error.errors[0]?.message || 'Invalid password input.' });
  }

  const { currentPassword, newPassword } = result.data;
  const user = db.prepare(`SELECT * FROM users WHERE id = ?`).get(req.user.id);

  const isValid = await verifyPassword(user.password_hash, currentPassword);
  if (!isValid) {
    return res.status(400).json({ error: 'Current password is incorrect.' });
  }

  try {
    const newHash = await hashPassword(newPassword);
    const now = new Date().toISOString();

    db.prepare(`UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?`).run(newHash, now, req.user.id);

    return res.json({ success: true, message: 'Password updated successfully.' });
  } catch (err) {
    return res.status(400).json({ error: err.message || 'Failed to update password.' });
  }
});

// ----------------------------------------------------------------------------
// DELETE /api/auth/account (Right to Erasure)
// ----------------------------------------------------------------------------
router.delete('/account', requireAuth, verifyCsrf, (req, res) => {
  const userId = req.user.id;
  const now = new Date().toISOString();

  // Audit log of erasure
  db.prepare(`
    INSERT INTO audit_log (user_id, action, ip_address, details, created_at)
    VALUES (?, 'ACCOUNT_DELETION', ?, 'Account and all data erased under Right to Erasure', ?)
  `).run(userId, req.ip || '127.0.0.1', now);

  // Cascading delete deletes user, sessions, profile, holdings, paper_trades
  db.prepare(`DELETE FROM users WHERE id = ?`).run(userId);
  clearSessionCookie(res);

  return res.json({ success: true, message: 'Your account and all associated data have been permanently erased.' });
});

export default router;
