import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import cookieParser from 'cookie-parser';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

import { authenticate } from './auth.js';
import authRouter from './routes/auth.js';
import onboardingRouter from './routes/onboarding.js';
import dashboardRouter from './routes/dashboard.js';

dotenv.config({ path: path.resolve(process.cwd(), '.env') });

const app = express();
const PORT = process.env.PORT || 5000;
const CLIENT_URL = process.env.CLIENT_URL || 'http://127.0.0.1:3000';
const SESSION_SECRET = process.env.SESSION_SECRET || 'alphawatch-super-secret-session-cookie-key-min-32-chars-hex';

// OWASP Security Headers via Helmet
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:"],
      connectSrc: ["'self'", CLIENT_URL],
      frameAncestors: ["'none'"],
    },
  },
  crossOriginEmbedderPolicy: false,
}));

// CORS Configuration
app.use(cors({
  origin: CLIENT_URL,
  credentials: true,
}));

// Cookie Parser with Secret for Signed Session Cookies
app.use(cookieParser(SESSION_SECRET));
app.use(express.json());

// Session & Authentication Middleware
app.use(authenticate);

// Public Health Check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'alphawatch-node-gateway',
    user: req.user ? { id: req.user.id, email: req.user.email } : null,
    timestamp: new Date().toISOString(),
  });
});

// Authentication Routes
app.use('/api/auth', authRouter);

// Onboarding Routes
app.use('/api/onboarding', onboardingRouter);

// Dashboard Routes
app.use('/api/dashboard', dashboardRouter);

// Centralized Error Handler (OWASP: Never leak stack traces to users)
app.use((err, req, res, next) => {
  console.error('[AlphaWatch Server Error]', err.message);
  const status = err.status || 500;
  const message = process.env.NODE_ENV === 'production' && status === 500
    ? 'An internal server error occurred.'
    : err.message || 'Server error';
  res.status(status).json({ error: message });
});

const isMain = process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1]);

if (isMain && process.env.NODE_ENV !== 'test') {
  app.listen(PORT, '127.0.0.1', () => {
    console.log(`[AlphaWatch Server] Listening on http://127.0.0.1:${PORT}`);
  });
}

export default app;
