import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  apiFetch,
  getCurrentUserApi,
  getCsrfTokenApi,
  loginUserApi,
  registerUserApi,
  logoutUserApi,
  setCsrfToken as storeCsrfToken,
} from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [csrfToken, setLocalCsrfToken] = useState(null);

  // Initialize session on mount
  useEffect(() => {
    let isMounted = true;

    async function initAuth() {
      try {
        // Attempt to retrieve CSRF token if the endpoint is available
        try {
          const csrfRes = await getCsrfTokenApi();
          if (isMounted && csrfRes?.csrfToken) {
            setLocalCsrfToken(csrfRes.csrfToken);
            storeCsrfToken(csrfRes.csrfToken);
          }
        } catch {
          // Endpoint may not be ready in /server yet; proceed safely
        }

        // Attempt to check if an active signed session cookie exists
        const userRes = await getCurrentUserApi();
        if (isMounted && userRes?.user) {
          setUser(userRes.user);
        }
      } catch {
        // Unauthenticated or endpoint not yet mounted in /server
        if (isMounted) {
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    initAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  async function login(email, password) {
    setError(null);
    try {
      const res = await loginUserApi({ email, password });
      if (res?.user) {
        setUser(res.user);
        if (res.csrfToken) {
          setLocalCsrfToken(res.csrfToken);
          storeCsrfToken(res.csrfToken);
        }
        return { success: true, user: res.user };
      }
      throw new Error(res?.message || 'Login failed');
    } catch (err) {
      const msg = err.message || 'Invalid email or password';
      setError(msg);
      throw err;
    }
  }

  async function register(payload) {
    setError(null);
    try {
      const res = await registerUserApi(payload);
      if (res?.user) {
        setUser(res.user);
        if (res.csrfToken) {
          setLocalCsrfToken(res.csrfToken);
          storeCsrfToken(res.csrfToken);
        }
        return { success: true, user: res.user };
      }
      throw new Error(res?.message || 'Registration failed');
    } catch (err) {
      const msg = err.message || 'Registration failed';
      setError(msg);
      throw err;
    }
  }

  async function logout() {
    try {
      await logoutUserApi();
    } catch {
      // Ignore logout errors
    } finally {
      setUser(null);
      setLocalCsrfToken(null);
      storeCsrfToken(null);
    }
  }

  async function refreshUser() {
    try {
      const res = await getCurrentUserApi();
      if (res?.user) {
        setUser(res.user);
      }
    } catch {
      setUser(null);
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        csrfToken,
        login,
        register,
        logout,
        refreshUser,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
