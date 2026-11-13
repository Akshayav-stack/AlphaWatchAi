import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Layouts
import PublicLayout from './layouts/PublicLayout';
import DashboardLayout from './layouts/DashboardLayout';

// Public Pages
import Home from './pages/public/Home';
import HowItWorks from './pages/public/HowItWorks';
import Limitations from './pages/public/Limitations';
import PrivacyTerms from './pages/public/PrivacyTerms';
import Login from './pages/public/Login';
import Register from './pages/public/Register';
import NotFound from './pages/public/NotFound';

// Onboarding
import Onboarding from './pages/onboarding/Onboarding';

// Dashboard Pages
import Overview from './pages/dashboard/Overview';
import Predictions from './pages/dashboard/Predictions';
import BuyCandidates from './pages/dashboard/BuyCandidates';
import Risk from './pages/dashboard/Risk';
import Backtest from './pages/dashboard/Backtest';
import ModelPerformance from './pages/dashboard/ModelPerformance';
import PaperTrading from './pages/dashboard/PaperTrading';
import ClaimAuditor from './pages/dashboard/ClaimAuditor';
import RippleEffect from './pages/dashboard/RippleEffect';
import MyPattern from './pages/dashboard/MyPattern';
import Settings from './pages/dashboard/Settings';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes with Top Navbar & Footer */}
          <Route element={<PublicLayout />}>
            <Route path="/" element={<Home />} />
            <Route path="/how-it-works" element={<HowItWorks />} />
            <Route path="/limitations" element={<Limitations />} />
            <Route path="/terms" element={<PrivacyTerms />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/onboarding"
              element={
                <ProtectedRoute allowPendingOnboarding={true}>
                  <Onboarding />
                </ProtectedRoute>
              }
            />
            {/* Catch-all 404 */}
            <Route path="*" element={<NotFound />} />
          </Route>

          {/* Authenticated Dashboard Routes with Sidebar Navigation */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard/overview" replace />} />
            <Route path="overview" element={<Overview />} />
            <Route path="predictions" element={<Predictions />} />
            <Route path="buy-candidates" element={<BuyCandidates />} />
            <Route path="risk" element={<Risk />} />
            <Route path="backtest" element={<Backtest />} />
            <Route path="model-performance" element={<ModelPerformance />} />
            <Route path="paper-trading" element={<PaperTrading />} />
            <Route path="auditor" element={<ClaimAuditor />} />
            <Route path="ripple" element={<RippleEffect />} />
            <Route path="my-pattern" element={<MyPattern />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
