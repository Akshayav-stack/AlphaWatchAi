import express from 'express';
import { db } from '../db.js';
import { requireAuth, verifyCsrf } from '../auth.js';
import { callMl } from '../mlClient.js';

const router = express.Router();

// Fallback supported symbols in case ML service is starting up
const FALLBACK_SYMBOLS = [
  { symbol: 'RELIANCE', name: 'Reliance Industries Ltd', sector: 'Energy' },
  { symbol: 'TCS', name: 'Tata Consultancy Services', sector: 'Technology' },
  { symbol: 'HDFCBANK', name: 'HDFC Bank Ltd', sector: 'Financials' },
  { symbol: 'INFY', name: 'Infosys Ltd', sector: 'Technology' },
  { symbol: 'ICICIBANK', name: 'ICICI Bank Ltd', sector: 'Financials' },
  { symbol: 'HINDUNILVR', name: 'Hindustan Unilever Ltd', sector: 'FMCG' },
  { symbol: 'ITC', name: 'ITC Ltd', sector: 'FMCG' },
  { symbol: 'SBIN', name: 'State Bank of India', sector: 'Financials' },
  { symbol: 'BHARTIARTL', name: 'Bharti Airtel Ltd', sector: 'Telecom' },
  { symbol: 'KOTAKBANK', name: 'Kotak Mahindra Bank', sector: 'Financials' },
  { symbol: 'LT', name: 'Larsen & Toubro Ltd', sector: 'Capital Goods' },
  { symbol: 'AXISBANK', name: 'Axis Bank Ltd', sector: 'Financials' },
  { symbol: 'ASIANPAINT', name: 'Asian Paints Ltd', sector: 'Consumer Discretionary' },
  { symbol: 'MARUTI', name: 'Maruti Suzuki India Ltd', sector: 'Automobile' },
  { symbol: 'SUNPHARMA', name: 'Sun Pharmaceutical Ltd', sector: 'Healthcare' },
  { symbol: 'TITAN', name: 'Titan Company Ltd', sector: 'Consumer Discretionary' },
  { symbol: 'BAJFINANCE', name: 'Bajaj Finance Ltd', sector: 'Financials' },
  { symbol: 'WIPRO', name: 'Wipro Ltd', sector: 'Technology' },
  { symbol: 'HCLTECH', name: 'HCL Technologies Ltd', sector: 'Technology' },
  { symbol: 'TATASTEEL', name: 'Tata Steel Ltd', sector: 'Metals' },
];

const FALLBACK_DEMO_PORTFOLIOS = {
  'Conservative Income': [
    { symbol: 'HDFCBANK', quantity: 20, buy_price: 1540.0, sector: 'Financials' },
    { symbol: 'ITC', quantity: 80, buy_price: 430.0, sector: 'FMCG' },
    { symbol: 'TCS', quantity: 10, buy_price: 3650.0, sector: 'Technology' },
  ],
  'Moderate Balanced': [
    { symbol: 'RELIANCE', quantity: 15, buy_price: 2780.0, sector: 'Energy' },
    { symbol: 'ICICIBANK', quantity: 30, buy_price: 1080.0, sector: 'Financials' },
    { symbol: 'INFY', quantity: 25, buy_price: 1610.0, sector: 'Technology' },
    { symbol: 'LT', quantity: 10, buy_price: 3450.0, sector: 'Capital Goods' },
  ],
  'Aggressive Growth': [
    { symbol: 'TATASTEEL', quantity: 120, buy_price: 142.0, sector: 'Metals' },
    { symbol: 'BAJFINANCE', quantity: 6, buy_price: 6850.0, sector: 'Financials' },
    { symbol: 'TITAN', quantity: 12, buy_price: 3290.0, sector: 'Consumer Discretionary' },
    { symbol: 'MARUTI', quantity: 4, buy_price: 11200.0, sector: 'Automobile' },
  ],
};

/**
 * GET /api/onboarding
 * Retrieves the current onboarding metadata, user holdings, and profile.
 */
router.get('/', requireAuth, async (req, res, next) => {
  try {
    let symbols = FALLBACK_SYMBOLS;
    let demoPortfolios = FALLBACK_DEMO_PORTFOLIOS;

    try {
      const symRes = await callMl('/api/ml/supported-symbols', { timeoutMs: 3000 });
      if (symRes?.symbols && symRes.symbols.length > 0) {
        symbols = symRes.symbols;
      }
    } catch {
      // Use fallback if ML service offline
    }

    try {
      const demoRes = await callMl('/api/ml/demo-portfolios', { timeoutMs: 3000 });
      if (demoRes?.portfolios) {
        demoPortfolios = demoRes.portfolios;
      }
    } catch {
      // Use fallback
    }

    const holdings = db.prepare(
      'SELECT id, symbol, quantity, buy_price, buy_date FROM holdings WHERE user_id = ? ORDER BY id ASC'
    ).all(req.user.id);

    const profile = db.prepare(
      'SELECT * FROM user_profiles WHERE user_id = ?'
    ).get(req.user.id);

    let parsedAnswers = {};
    if (profile?.answers_json) {
      try {
        parsedAnswers = JSON.parse(profile.answers_json);
      } catch {
        parsedAnswers = {};
      }
    }

    res.json({
      symbols,
      demoPortfolios,
      holdings,
      profile: profile ? { ...profile, answers: parsedAnswers } : null,
      is_onboarded: Boolean(req.user.is_onboarded),
    });
  } catch (err) {
    next(err);
  }
});

/**
 * POST /api/onboarding
 * Saves holdings and answers, calls the deterministic ML profiler,
 * and updates user profile and onboarding status.
 */
router.post('/', requireAuth, verifyCsrf, async (req, res, next) => {
  try {
    const { holdings = [], answers = {} } = req.body;

    if (!Array.isArray(holdings)) {
      return res.status(400).json({ error: 'Holdings must be provided as an array.' });
    }

    // Validate each holding
    for (const h of holdings) {
      if (!h.symbol || typeof h.symbol !== 'string') {
        return res.status(400).json({ error: 'Each holding must have a valid stock symbol.' });
      }
      const qty = Number(h.quantity);
      if (isNaN(qty) || qty <= 0) {
        return res.status(400).json({ error: `Invalid quantity for ${h.symbol}. Must be > 0.` });
      }
      const price = Number(h.buy_price);
      if (isNaN(price) || price <= 0) {
        return res.status(400).json({ error: `Invalid buy price for ${h.symbol}. Must be > 0.` });
      }
    }

    // Call ML Profiler to determine investor risk profile deterministically
    let evaluation = {
      risk_score: 50.0,
      suggested_profile: 'Moderate',
      diversification_score: 50.0,
      concentration_status: 'Balanced',
      holding_style: 'Swing / Medium Term',
      why_this_profile: 'Calculated using balanced allocation across multi-asset sectors.',
      adaptive_followups: [],
    };

    try {
      evaluation = await callMl('/api/ml/profiler', {
        method: 'POST',
        body: {
          answers,
          holdings_summary: holdings,
        },
      });
    } catch (mlErr) {
      console.warn('[Onboarding] ML profiler fallback:', mlErr.message);
      // Fallback deterministic evaluation based on fixed questions
      const horizon = answers.horizon || '3-5 Years';
      const fall = answers.fall_reaction || 'Hold and observe';
      if (fall === 'Panic sell everything' || horizon === '< 1 Year') {
        evaluation.suggested_profile = 'Conservative';
        evaluation.risk_score = 30.0;
        evaluation.why_this_profile = 'Conservative profile assigned due to short time horizon and high sensitivity to market drawdowns.';
      } else if (fall === 'Buy more aggressively' || horizon === '> 5 Years') {
        evaluation.suggested_profile = 'Aggressive';
        evaluation.risk_score = 75.0;
        evaluation.why_this_profile = 'Aggressive profile assigned due to multi-year investment horizon and opportunistic reaction to market volatility.';
      }
    }

    const now = new Date().toISOString();

    // Sanitize and normalize all answers and evaluation values to primitive SQLite types
    const goalVal = String(answers.goal || 'Wealth Creation');
    const horizonVal = String(answers.horizon || '3-5 Years');
    const experienceVal = String(answers.experience || 'Intermediate');
    const frequencyVal = String(answers.trading_frequency || 'Monthly');
    const reactionVal = String(answers.fall_reaction || 'Hold and observe');
    const savingsVal = String(answers.savings_share || '10-25%');
    const preferredSectorsVal = Array.isArray(answers.preferred_sectors)
      ? answers.preferred_sectors.join(', ')
      : String(answers.preferred_sectors || 'Technology, Financials');
    const riskScoreVal = Number(evaluation.risk_score != null ? evaluation.risk_score : 50.0);
    const suggestedProfileVal = String(evaluation.suggested_profile || 'Moderate');
    const divScoreVal = Number(evaluation.diversification_score != null ? evaluation.diversification_score : 50.0);
    const concentrationStatusVal = String(evaluation.concentration_status || 'Balanced');
    const holdingStyleVal = String(evaluation.holding_style || 'Balanced Growth & Value');
    const whyThisProfileVal = String(evaluation.why_this_profile || '');
    const answersJsonVal = typeof answers === 'string' ? answers : JSON.stringify(answers);

    // Database updates in transaction
    const updateTransaction = () => {
      // 1. Replace holdings
      db.prepare('DELETE FROM holdings WHERE user_id = ?').run(req.user.id);
      const insertHolding = db.prepare(
        'INSERT INTO holdings (user_id, symbol, quantity, buy_price, buy_date, created_at) VALUES (?, ?, ?, ?, ?, ?)'
      );
      for (const h of holdings) {
        insertHolding.run(
          req.user.id,
          h.symbol.toUpperCase().trim(),
          Math.floor(Number(h.quantity)),
          Number(h.buy_price),
          h.buy_date || now.split('T')[0],
          now
        );
      }

      // 2. Insert or update user_profiles
      const existingProfile = db.prepare('SELECT id FROM user_profiles WHERE user_id = ?').get(req.user.id);
      if (existingProfile) {
        db.prepare(`
          UPDATE user_profiles
          SET goal = ?, horizon = ?, experience = ?, trading_frequency = ?, fall_reaction = ?,
              savings_share = ?, preferred_sectors = ?, risk_score = ?, suggested_profile = ?,
              diversification_score = ?, concentration_status = ?, holding_style = ?,
              why_this_profile = ?, answers_json = ?, updated_at = ?
          WHERE user_id = ?
        `).run(
          goalVal,
          horizonVal,
          experienceVal,
          frequencyVal,
          reactionVal,
          savingsVal,
          preferredSectorsVal,
          riskScoreVal,
          suggestedProfileVal,
          divScoreVal,
          concentrationStatusVal,
          holdingStyleVal,
          whyThisProfileVal,
          answersJsonVal,
          now,
          req.user.id
        );
      } else {
        db.prepare(`
          INSERT INTO user_profiles (
            user_id, goal, horizon, experience, trading_frequency, fall_reaction,
            savings_share, preferred_sectors, risk_score, suggested_profile,
            diversification_score, concentration_status, holding_style,
            why_this_profile, answers_json, updated_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).run(
          req.user.id,
          goalVal,
          horizonVal,
          experienceVal,
          frequencyVal,
          reactionVal,
          savingsVal,
          preferredSectorsVal,
          riskScoreVal,
          suggestedProfileVal,
          divScoreVal,
          concentrationStatusVal,
          holdingStyleVal,
          whyThisProfileVal,
          answersJsonVal,
          now
        );
      }

      // 3. Update user onboarding status
      db.prepare('UPDATE users SET is_onboarded = 1, updated_at = ? WHERE id = ?').run(now, req.user.id);

      // 4. Log to audit trail
      db.prepare(
        'INSERT INTO audit_log (user_id, action, ip_address, details, created_at) VALUES (?, ?, ?, ?, ?)'
      ).run(
        req.user.id,
        'ONBOARDING_COMPLETED',
        req.ip,
        `Assigned Profile: ${evaluation.suggested_profile}, Risk Score: ${evaluation.risk_score}`,
        now
      );
    };

    updateTransaction();

    res.json({
      success: true,
      message: 'Onboarding completed successfully.',
      evaluation: {
        risk_score: evaluation.risk_score,
        suggested_profile: evaluation.suggested_profile,
        diversification_score: evaluation.diversification_score,
        concentration_status: evaluation.concentration_status,
        holding_style: evaluation.holding_style,
        why_this_profile: evaluation.why_this_profile,
        adaptive_followups: evaluation.adaptive_followups || [],
      },
    });
  } catch (err) {
    next(err);
  }
});

export default router;
