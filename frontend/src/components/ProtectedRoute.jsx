import React from 'react';
import { Navigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LoadingSpinner } from './UIState';

export default function ProtectedRoute({ children, allowPendingOnboarding = false }) {
  const { user, loading, isAuthenticated } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner text="Checking authorization..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  // If user has not completed onboarding, force redirection to /onboarding
  if (user && !user.is_onboarded && !allowPendingOnboarding) {
    return <Navigate to="/onboarding" replace />;
  }

  return children ? children : <Outlet />;
}
