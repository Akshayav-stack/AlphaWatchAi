import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  CheckCircle,
  ShieldAlert,
  Sliders,
  Activity,
  DollarSign,
  FileText,
  PieChart,
  User,
  Settings,
  LogOut,
  X,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Sidebar({ isOpen, onClose }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
    if (onClose) onClose();
  };

  const navItems = [
    { name: 'Overview', path: '/dashboard/overview', icon: LayoutDashboard },
    { name: 'Predictions', path: '/dashboard/predictions', icon: TrendingUp },
    { name: 'Buy Candidates', path: '/dashboard/buy-candidates', icon: CheckCircle },
    { name: 'Risk Analytics', path: '/dashboard/risk', icon: ShieldAlert },
    { name: 'Backtest & Opt.', path: '/dashboard/backtest', icon: Sliders },
    { name: 'Model Performance', path: '/dashboard/model-performance', icon: Activity },
    { name: 'Paper Trading', path: '/dashboard/paper-trading', icon: DollarSign },
    { name: 'Claim Auditor', path: '/dashboard/auditor', icon: FileText },
    { name: 'Ripple Effect', path: '/dashboard/ripple', icon: PieChart },
    { name: 'My Pattern', path: '/dashboard/my-pattern', icon: User },
    { name: 'Settings', path: '/dashboard/settings', icon: Settings },
  ];

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-slate-900 border-r border-slate-800 flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Dashboard Navigation"
      >
        {/* Top Header */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-slate-800 bg-slate-950/40">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded bg-blue-600 flex items-center justify-center text-white font-bold text-xs">
              AW
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-bold text-white tracking-wide">
                ALPHAWATCH AI
              </span>
              <span className="text-[9px] text-blue-400 font-semibold tracking-wider">
                ASTRAQUANT X
              </span>
            </div>
          </div>
          {/* Mobile close button */}
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg lg:hidden"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* User Card */}
        <div className="p-3.5 mx-3 mt-3 bg-slate-800/60 border border-slate-700/60 rounded-xl">
          <div className="flex items-center justify-between">
            <div className="truncate">
              <p className="text-xs font-semibold text-slate-200 truncate">
                {user?.name || 'Local Researcher'}
              </p>
              <p className="text-[10px] text-slate-400 truncate">{user?.email || 'user@alphawatch.local'}</p>
            </div>
            <span className="px-2 py-0.5 text-[9px] font-bold text-blue-300 bg-blue-900/60 rounded border border-blue-700/60 uppercase">
              {user?.suggested_profile || 'Moderate'}
            </span>
          </div>
        </div>

        {/* Navigation List */}
        <nav className="flex-1 px-3 py-3 space-y-1 overflow-y-auto custom-scrollbar" aria-label="Sidebar modules">
          <div className="px-2 pb-1 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            Quant Modules
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => {
                  if (onClose && window.innerWidth < 1024) onClose();
                }}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2 text-xs font-medium rounded-lg transition-colors group ${
                    isActive
                      ? 'bg-blue-600 text-white font-semibold shadow-sm'
                      : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
                  }`
                }
              >
                <div className="flex items-center gap-2.5">
                  <Icon className="w-4 h-4 flex-shrink-0 text-slate-400 group-hover:text-white" />
                  <span className="truncate">{item.name}</span>
                </div>
                <ChevronRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
              </NavLink>
            );
          })}
        </nav>

        {/* Footer Actions */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/40">
          <button
            onClick={handleLogout}
            className="flex items-center justify-center gap-2 w-full px-3 py-2 text-xs font-medium text-slate-300 hover:text-red-400 hover:bg-slate-800/80 rounded-lg transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out Workstation</span>
          </button>
        </div>
      </aside>
    </>
  );
}
