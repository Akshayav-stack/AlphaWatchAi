import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Lock, Mail, User, ArrowRight, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { ErrorMessage, LoadingSpinner } from '../../components/UIState';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [consentGiven, setConsentGiven] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [generalError, setGeneralError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const { register, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    document.title = 'Create Account — AlphaWatch AI';
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) {
      metaDesc.setAttribute(
        'content',
        'Create a local researcher account with Argon2id encryption on AlphaWatch AI.'
      );
    }
    if (isAuthenticated) {
      navigate('/onboarding', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const validate = () => {
    const errors = {};
    if (!name.trim()) {
      errors.name = 'Full name is required.';
    }
    if (!email.trim()) {
      errors.email = 'Email address is required.';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      errors.email = 'Please enter a valid email address.';
    }
    if (!password) {
      errors.password = 'Password is required.';
    } else if (password.length < 10) {
      errors.password = 'Password must be at least 10 characters long.';
    }
    if (password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match.';
    }
    if (!consentGiven) {
      errors.consent = 'You must acknowledge the academic research terms.';
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setGeneralError(null);
    setSuccessMessage(null);

    if (!validate()) return;

    setSubmitting(true);
    try {
      const res = await register({
        name,
        email,
        password,
        consent_given: consentGiven,
      });
      if (res?.user) {
        setSuccessMessage('Account registered successfully! Redirecting to Onboarding...');
        setTimeout(() => {
          navigate('/onboarding');
        }, 700);
      }
    } catch (err) {
      setGeneralError(err.message || 'Registration failed. Please check inputs.');
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto pt-2 pb-8">
      <div className="p-8 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400 mx-auto flex items-center justify-center">
            <User className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Create Local Account
          </h2>
          <p className="text-xs text-slate-400">
            Set up your private, air-gapped quantitative research profile
          </p>
        </div>

        {generalError && (
          <ErrorMessage title="Registration Error" message={generalError} />
        )}
        {successMessage && (
          <div className="p-3 bg-emerald-950/50 border border-emerald-800/60 rounded-xl text-xs text-emerald-300 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span>{successMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          {/* Name Field */}
          <div className="space-y-1">
            <label className="block text-xs font-semibold text-slate-300">
              Full Name
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-500 absolute left-3 top-3 pointer-events-none" />
              <input
                type="text"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  if (fieldErrors.name) setFieldErrors({ ...fieldErrors, name: null });
                }}
                placeholder="Jane Doe"
                className={`w-full pl-9 pr-3 py-2 bg-slate-950 border rounded-lg text-xs text-white placeholder-slate-600 focus:outline-none focus:ring-1 ${
                  fieldErrors.name
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-slate-800 focus:ring-blue-500 focus:border-blue-500'
                }`}
                required
              />
            </div>
            {fieldErrors.name && (
              <p className="text-[11px] text-red-400 font-medium">{fieldErrors.name}</p>
            )}
          </div>

          {/* Email Field */}
          <div className="space-y-1">
            <label className="block text-xs font-semibold text-slate-300">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3 pointer-events-none" />
              <input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (fieldErrors.email) setFieldErrors({ ...fieldErrors, email: null });
                }}
                placeholder="researcher@alphawatch.local"
                className={`w-full pl-9 pr-3 py-2 bg-slate-950 border rounded-lg text-xs text-white placeholder-slate-600 focus:outline-none focus:ring-1 ${
                  fieldErrors.email
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-slate-800 focus:ring-blue-500 focus:border-blue-500'
                }`}
                autoComplete="email"
                required
              />
            </div>
            {fieldErrors.email && (
              <p className="text-[11px] text-red-400 font-medium">{fieldErrors.email}</p>
            )}
          </div>

          {/* Password Field */}
          <div className="space-y-1">
            <label className="block text-xs font-semibold text-slate-300">
              Password <span className="text-[10px] text-slate-500 font-normal">(Min 10 characters)</span>
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3 pointer-events-none" />
              <input
                type="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (fieldErrors.password) setFieldErrors({ ...fieldErrors, password: null });
                }}
                placeholder="At least 10 characters"
                className={`w-full pl-9 pr-3 py-2 bg-slate-950 border rounded-lg text-xs text-white placeholder-slate-600 focus:outline-none focus:ring-1 ${
                  fieldErrors.password
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-slate-800 focus:ring-blue-500 focus:border-blue-500'
                }`}
                autoComplete="new-password"
                required
              />
            </div>
            {fieldErrors.password && (
              <p className="text-[11px] text-red-400 font-medium">{fieldErrors.password}</p>
            )}
          </div>

          {/* Confirm Password Field */}
          <div className="space-y-1">
            <label className="block text-xs font-semibold text-slate-300">
              Confirm Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3 pointer-events-none" />
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  if (fieldErrors.confirmPassword)
                    setFieldErrors({ ...fieldErrors, confirmPassword: null });
                }}
                placeholder="Re-enter password"
                className={`w-full pl-9 pr-3 py-2 bg-slate-950 border rounded-lg text-xs text-white placeholder-slate-600 focus:outline-none focus:ring-1 ${
                  fieldErrors.confirmPassword
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-slate-800 focus:ring-blue-500 focus:border-blue-500'
                }`}
                autoComplete="new-password"
                required
              />
            </div>
            {fieldErrors.confirmPassword && (
              <p className="text-[11px] text-red-400 font-medium">{fieldErrors.confirmPassword}</p>
            )}
          </div>

          {/* Consent Checkbox */}
          <div className="pt-2">
            <label className="flex items-start gap-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={consentGiven}
                onChange={(e) => {
                  setConsentGiven(e.target.checked);
                  if (fieldErrors.consent) setFieldErrors({ ...fieldErrors, consent: null });
                }}
                className="mt-0.5 rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-[11px] text-slate-400 leading-snug">
                I understand that AlphaWatch AI is strictly an academic research platform and all outputs are educational models, not SEBI-registered financial advice.
              </span>
            </label>
            {fieldErrors.consent && (
              <p className="text-[11px] text-red-400 font-medium mt-1">{fieldErrors.consent}</p>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={submitting}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800/50 rounded-lg shadow-md transition-all focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {submitting ? (
              <LoadingSpinner size="small" text="" />
            ) : (
              <>
                <span>Create Researcher Account</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </form>

        <div className="pt-4 border-t border-slate-800 text-center text-xs text-slate-400">
          <span>Already registered? </span>
          <Link to="/login" className="font-semibold text-blue-400 hover:text-blue-300">
            Sign In here
          </Link>
        </div>
      </div>
    </div>
  );
}
