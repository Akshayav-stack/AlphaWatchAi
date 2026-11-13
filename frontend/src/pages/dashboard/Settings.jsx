import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Settings as SettingsIcon, Lock, Trash2, ShieldAlert, CheckCircle, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { ErrorMessage, DataProvenanceFooter } from '../../components/UIState';
import { changePasswordApi, deleteAccountApi } from '../../api/client';

export default function Settings() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordStatus, setPasswordStatus] = useState(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

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
      await changePasswordApi({ currentPassword, newPassword });
      setPasswordStatus({ type: 'success', message: 'Password updated successfully.' });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setPasswordStatus({ type: 'error', message: err.message || 'Failed to update password.' });
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
          Manage local authentication credentials and execute complete account erasure
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
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-300 font-medium"
            />
          </div>
          <div>
            <label className="block text-slate-400 font-semibold mb-1">Email Address</label>
            <input
              type="text"
              readOnly
              value={user?.email || 'user@alphawatch.local'}
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-300 font-medium"
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
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white"
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
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white"
              required
            />
          </div>
          <div className="space-y-1">
            <label className="block text-xs font-semibold text-slate-300">Confirm New Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white"
              required
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm"
          >
            Update Password
          </button>
        </form>
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
              <ShieldAlert className="w-5 h-5" />
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
