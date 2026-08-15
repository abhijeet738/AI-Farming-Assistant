import { createContext, useContext, useState, useCallback } from 'react';

const API_BASE = 'http://localhost:8000';
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('km_token'));
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('km_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // authFetch: automatically attaches Bearer token to every API call
  // and logs the user out if the token has expired (401 response)
  const authFetch = useCallback(
    async (url, options = {}) => {
      const currentToken = localStorage.getItem('km_token');
      const headers = { 'Content-Type': 'application/json', ...options.headers };
      if (currentToken) {
        headers['Authorization'] = `Bearer ${currentToken}`;
      }
      const response = await fetch(url, { ...options, headers });
      
      if (response.status === 401) {
        setToken(null);
        setUser(null);
        localStorage.removeItem('km_token');
        localStorage.removeItem('km_user');
      }
      
      return response;
    },
    []
  );

  const register = useCallback(async (email, password, name = '') => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Registration failed');

      if (data.access_token && data.access_token !== 'check-email-for-confirmation') {
        _persistAuth(data);
        return { success: true };
      }
      return { success: true, requiresConfirmation: true };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Invalid email or password');
      _persistAuth(data);
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('km_token');
    localStorage.removeItem('km_user');
  }, []);

  function _persistAuth(data) {
    const userInfo = { id: data.user_id, email: data.email };
    setToken(data.access_token);
    setUser(userInfo);
    localStorage.setItem('km_token', data.access_token);
    localStorage.setItem('km_user', JSON.stringify(userInfo));
  }

  return (
    <AuthContext.Provider value={{
      token, user, loading, error,
      isAuthenticated: Boolean(token && user),
      login, register, logout, authFetch
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
