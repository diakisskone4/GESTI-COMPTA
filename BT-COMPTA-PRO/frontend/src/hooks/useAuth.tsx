import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { api, refreshAccess, session } from '../services/api';
import type { Role, User } from '../types';

/** Déconnexion automatique après une période d'inactivité (poste partagé, cybercafé, salle de classe). */
const IDLE_MINUTES = Number(import.meta.env.VITE_IDLE_MINUTES ?? 30);

export type LogoutReason = 'expired' | 'idle' | null;

interface AuthState {
  user: User | null;
  loading: boolean;
  logoutReason: LogoutReason;
  login: (identifier: string, password: string) => Promise<User>;
  register: (data: Record<string, string>) => Promise<User>;
  logout: (reason?: LogoutReason) => Promise<void>;
  refreshUser: () => Promise<void>;
  hasRole: (...roles: Role[]) => boolean;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [logoutReason, setLogoutReason] = useState<LogoutReason>(null);
  const lastActivity = useRef(Date.now());

  const refreshUser = useCallback(async () => {
    const { data } = await api.get<User>('/auth/me/');
    setUser(data);
  }, []);

  // Au chargement : reprise silencieuse de la session grâce au cookie HttpOnly.
  useEffect(() => {
    refreshAccess()
      .then(async (access) => {
        if (access) await refreshUser();
      })
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, [refreshUser]);

  const logout = useCallback(async (reason: LogoutReason = null) => {
    try {
      await api.post('/auth/logout/');
    } catch {
      /* la session locale est fermée même si le serveur est injoignable */
    }
    session.set(null);
    setLogoutReason(reason);
    setUser(null);
  }, []);

  useEffect(() => {
    const onExpired = () => {
      session.set(null);
      setLogoutReason('expired');
      setUser(null);
    };
    window.addEventListener('btc:logout', onExpired);
    return () => window.removeEventListener('btc:logout', onExpired);
  }, []);

  // Surveillance de l'inactivité
  useEffect(() => {
    if (!user) return;
    const touch = () => {
      lastActivity.current = Date.now();
    };
    const events = ['mousemove', 'keydown', 'pointerdown', 'scroll', 'touchstart'] as const;
    events.forEach((e) => window.addEventListener(e, touch, { passive: true }));
    const timer = setInterval(() => {
      if (Date.now() - lastActivity.current > IDLE_MINUTES * 60_000) logout('idle');
    }, 30_000);
    return () => {
      events.forEach((e) => window.removeEventListener(e, touch));
      clearInterval(timer);
    };
  }, [user, logout]);

  const login = useCallback(async (identifier: string, password: string) => {
    const { data } = await api.post('/auth/login/', { identifier, password });
    session.set(data.access);
    lastActivity.current = Date.now();
    setLogoutReason(null);
    setUser(data.user);
    return data.user as User;
  }, []);

  const register = useCallback(async (payload: Record<string, string>) => {
    const { data } = await api.post('/auth/register/', payload);
    session.set(data.access);
    setLogoutReason(null);
    setUser(data.user);
    return data.user as User;
  }, []);

  const hasRole = useCallback((...roles: Role[]) => !!user && roles.includes(user.role), [user]);

  const value = useMemo(
    () => ({ user, loading, logoutReason, login, register, logout, refreshUser, hasRole }),
    [user, loading, logoutReason, login, register, logout, refreshUser, hasRole],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth doit être utilisé dans <AuthProvider>');
  return ctx;
}
