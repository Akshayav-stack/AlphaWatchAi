import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Lock, Mail, ArrowRight, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { ErrorMessage, LoadingSpinner } from '../../components/UIState';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [generalError, setGeneralError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const { login, isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    document.title = 'Sign In — AlphaWatch AI';
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) {
      metaDesc.setAttribute(
        'content',
        'Sign in to your private AlphaWatch AI quantitative trading research dashboard.'
      );
    }
    if (isAuthenticated) {
      if (user && !user.is_onboarded) {
        navigate('/onboarding', { replace: true });
      } else {
        const from = location.state?.from?.pathname || '/dashboard/overview';
        navigate(from, { replace: true });
      }
    }
  }, [isAuthenticated, user, navigate, location]);

  const validate = () => {
    const errors = {};
    if (!email.trim()) {
      errors.email = 'Email address is required.';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      errors.email = 'Please enter a valid email address.';
    }
    if (!password) {
      errors.password = 'Password is required.';
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
      const res = await login(email, password);
      if (res?.user) {
        setSuccessMessage('Signed in successfully! Loading workstation...');
        setTimeout(() => {
          if (!res.user.is_onboarded) {
            navigate('/onboarding');
          } else {
            navigate('/dashboard/overview');
          }
        }, 600);
      }
    } catch (err) {
      // Security rule: Generic error message to prevent account enumeration
      setGeneralError(err.message || 'Invalid email or password.');
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto pt-4 pb-8">
      <div className="p-8 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400 mx-auto flex items-center justify-center">
            <Lock className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Sign In to AlphaWatch AI
          </h2>
          <p className="text-xs text-slate-400">
            Access your isolated local portfolio analytics & model signals
          </p>
        </div>

        {generalError && (
          <ErrorMessage title="Authentication Failed" message={generalError} />
        )}
        {successMessage && (
          <div className="p-3 bg-emerald-950/50 border border-emerald-800/60 rounded-xl text-xs text-emerald-300 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span>{successMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
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
              Password
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
                placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;"
                className={`w-full pl-9 pr-3 py-2 bg-slate-950 border rounded-lg text-xs text-white placeholder-slate-600 focus:outline-none focus:ring-1 ${
                  fieldErrors.password
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-slate-800 focus:ring-blue-500 focus:border-blue-500'
                }`}
                autoComplete="current-password"
                required
              />
            </div>
            {fieldErrors.password && (
              <p className="text-[11px] text-red-400 font-medium">{fieldErrors.password}</p>
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
                <span>Sign In to Workstation</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </form>

        <div className="pt-4 border-t border-slate-800 text-center text-xs text-slate-400">
          <span>New researcher? </span>
          <Link to="/register" className="font-semibold text-blue-400 hover:text-blue-300">
            Create a local account
          </Link>
        </div>
      </div>
    </div>
  );
}
