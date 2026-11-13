import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Settings as SettingsIcon,
  Lock,
  Trash2,
  ShieldAlert,
  CheckCircle,
  AlertCircle,
  Download,
  FileSpreadsheet,
  FileCode,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { ErrorMessage, DataProvenanceFooter } from '../../components/UIState';
import {
  changePasswordApi,
  deleteAccountApi,
  getMyPatternApi,
  getUserHoldingsApi,
} from '../../api/client';

export default function Settings() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordStatus, setPasswordStatus] = useState(null);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteError, setDeleteError] = useState(null);
  const [exportStatus, setExportStatus] = useState(null);

  useEffect(() => {
    document.title = 'Researcher Settings — AlphaWatch AI';
  }, []);

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPasswordStatus(null);

    if (newPassword.length < 10) {
      setPasswordStatus({ type: 'error', message: 'New password must be at least 10 characters long.' });
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordStatus({ type: 'error', message: 'Passwords do not match.' });
      return;
    }

    try {
      setPasswordLoading(true);
      await changePasswordApi({ currentPassword, newPassword });
      setPasswordStatus({ type: 'success', message: 'Password updated successfully with Argon2id.' });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setPasswordStatus({ type: 'error', message: err.message || 'Failed to update password.' });
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleExportJson = async () => {
    try {
      setExportStatus('Generating JSON export...');
      const [patternRes, holdingsRes] = await Promise.all([
        getMyPatternApi().catch(() => null),
        getUserHoldingsApi().catch(() => null),
      ]);

      const exportData = {
        exported_at: new Date().toISOString(),
        user: { name: user?.name, email: user?.email },
        profile: patternRes?.profile || null,
        answers: patternRes?.answers || null,
        holdings: holdingsRes?.holdings || [],
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `alphawatch_user_export_${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setExportStatus('JSON export downloaded.');
    } catch (err) {
      setExportStatus('Export failed: ' + err.message);
    }
  };

  const handleExportCsv = async () => {
    try {
      setExportStatus('Generating CSV export...');
      const holdingsRes = await getUserHoldingsApi().catch(() => null);
      const holdings = holdingsRes?.holdings || [];

      if (holdings.length === 0) {
        setExportStatus('No holdings to export.');
        return;
      }

      const headers = ['Symbol', 'Quantity', 'Buy Price', 'Buy Date'];
      const rows = holdings.map((h) => [
        h.symbol,
        h.quantity,
        h.buy_price,
        h.buy_date || '',
      ]);

      const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `alphawatch_holdings_${Date.now()}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setExportStatus('Holdings CSV downloaded.');
    } catch (err) {
      setExportStatus('CSV export failed: ' + err.message);
    }
  };

  const handleDeleteAccount = async () => {
    try {
      await deleteAccountApi();
      await logout();
      navigate('/');
    } catch (err) {
      setDeleteError(err.message || 'Failed to delete account.');
    }
  };

  return (
    <div className="space-y-8 max-w-4xl">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-base font-bold text-white">Researcher Profile & Account Security</h2>
        <p className="text-xs text-slate-400">
          Manage local authentication credentials, export personal data, and execute complete account erasure
        </p>
      </div>

      {/* Profile Details */}
      <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4">
        <h3 className="text-sm font-bold text-white">Researcher Profile</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="block text-slate-400 font-semibold mb-1">Full Name</label>
            <input
              type="text"
              readOnly
              value={user?.name || 'Local Researcher'}
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-300 font-medium focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-slate-400 font-semibold mb-1">Email Address</label>
            <input
              type="text"
              readOnly
              value={user?.email || 'user@alphawatch.local'}
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-300 font-medium focus:outline-none"
            />
          </div>
        </div>
      </div>

      {/* Change Password Form */}
      <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4">
        <div className="flex items-center gap-2 text-white font-bold text-sm">
          <Lock className="w-4 h-4 text-blue-400" />
          <h3>Update Password (Argon2id Hashed)</h3>
        </div>

        {passwordStatus?.type === 'error' && (
          <ErrorMessage title="Password Error" message={passwordStatus.message} />
        )}

        {passwordStatus?.type === 'success' && (
          <div className="p-3 bg-emerald-950/40 border border-emerald-800/60 rounded-xl text-xs text-emerald-300 flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span>{passwordStatus.message}</span>
          </div>
        )}

        <form onSubmit={handlePasswordChange} className="space-y-4 max-w-md">
          <div className="space-y-1">
            <label className="block text-xs font-semibold text-slate-300">Current Password</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              required
            />
          </div>
          <div className="space-y-1">
            <label className="block text-xs font-semibold text-slate-300">
              New Password <span className="text-[10px] text-slate-500 font-normal">(Min 10 characters)</span>
            </label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              required
            />
          </div>
          <div className="space-y-1">
            <label className="block text-xs font-semibold text-slate-300">Confirm New Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              required
            />
          </div>
          <button
            type="submit"
            disabled={passwordLoading}
            className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm transition-all disabled:opacity-50"
          >
            {passwordLoading ? 'Updating...' : 'Update Password'}
          </button>
        </form>
      </div>

      {/* Data Export (JSON / CSV) */}
      <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
        <div className="flex items-center gap-2 text-white font-bold text-sm">
          <Download className="w-4 h-4 text-emerald-400" />
          <h3>Data Portability & Export</h3>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          Download your personal research data, holdings portfolio, and profiling answers in standard formats.
        </p>
        <div className="flex flex-wrap items-center gap-3 pt-1">
          <button
            type="button"
            onClick={handleExportJson}
            className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors"
          >
            <FileCode className="w-4 h-4 text-blue-400" />
            <span>Export Complete Profile (JSON)</span>
          </button>
          <button
            type="button"
            onClick={handleExportCsv}
            className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
            <span>Export Holdings (CSV)</span>
          </button>
        </div>
        {exportStatus && (
          <p className="text-[11px] text-slate-400 pt-1 font-mono">{exportStatus}</p>
        )}
      </div>

      {/* Right to Erasure / Delete Account */}
      <div className="p-6 bg-rose-950/20 border border-rose-900/40 rounded-xl space-y-3">
        <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
          <Trash2 className="w-4 h-4" />
          <h3>Danger Zone: Right to Erasure (Account Deletion)</h3>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          Under the Digital Personal Data Protection (DPDP) Act, clicking delete will permanently and irrevocably purge your account record, all portfolio holdings, risk profiling answers, and paper trades from the SQLite database.
        </p>
        <button
          onClick={() => setDeleteModalOpen(true)}
          className="px-4 py-2 text-xs font-semibold text-rose-300 hover:text-white bg-rose-950 border border-rose-800/80 rounded-lg hover:bg-rose-900/60 transition-colors"
        >
          Delete Account Permanently
        </button>
      </div>

      {/* Confirmation Modal for Deletion */}
      {deleteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="p-6 bg-slate-900 border border-slate-700 rounded-2xl max-w-sm w-full space-y-4">
            <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
              <ShieldAlert className="w-5 h-5 flex-shrink-0" />
              <span>Confirm Irreversible Erasure</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Are you absolutely sure? All portfolio holdings, risk metrics, and order history will be deleted immediately with cascading deletes. This action cannot be undone.
            </p>
            {deleteError && (
              <ErrorMessage title="Deletion Error" message={deleteError} />
            )}
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setDeleteModalOpen(false)}
                className="px-3 py-1.5 text-xs text-slate-300 bg-slate-800 rounded-lg hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 rounded-lg"
              >
                Yes, Delete Everything
              </button>
            </div>
          </div>
        </div>
      )}

      <DataProvenanceFooter
        source="SQLite Cascading Constraints"
        asOf="Indian DPDP Act & GDPR Article 17"
        status="Right to Erasure"
      />
    </div>
  );
}
