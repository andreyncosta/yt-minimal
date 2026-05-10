import { useCallback, useEffect, useRef, useState } from 'react';

import * as SecureStore from 'expo-secure-store';
import * as WebBrowser from 'expo-web-browser';

import { API_BASE_URL } from '../constants/api';

const SECURE_STORE_KEY = 'yt_minimal_jwt';
const APP_SCHEME = 'ytminimal://auth';
const REFRESH_MARGIN_MS = 5 * 60 * 1_000; // renew 5 min before expiry

export interface AuthState {
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
}

/**
 * Decode the `exp` claim from a JWT payload.
 * Returns milliseconds since epoch, or null if unparseable.
 * No signature verification — we trust our own backend's tokens.
 */
function jwtExpiryMs(token: string): number | null {
  try {
    const raw = token.split('.')[1];
    // JWT uses base64url; atob requires standard base64
    const b64 = raw.replace(/-/g, '+').replace(/_/g, '/');
    const padded = b64 + '==='.slice((b64.length + 3) % 4);
    const { exp } = JSON.parse(atob(padded)) as { exp?: number };
    return typeof exp === 'number' ? exp * 1_000 : null;
  } catch {
    return null;
  }
}

/** Extract `?token=` from the deep-link URL returned by openAuthSessionAsync. */
function extractToken(url: string): string | null {
  const match = url.match(/[?&]token=([^&]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

export function useAuth(): AuthState {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Refs hold stable, always-current values for use inside timer callbacks.
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const tokenRef = useRef<string | null>(null);
  // Forward ref breaks the persist → scheduleRenewal → refresh → persist cycle.
  const refreshRef = useRef<() => Promise<void>>();

  const clearTimer = (): void => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  // scheduleRenewal has no deps: refs are stable, no state reads.
  const scheduleRenewal = useCallback((jwt: string): void => {
    clearTimer();
    const expMs = jwtExpiryMs(jwt);
    if (expMs === null) return;
    const delay = expMs - Date.now() - REFRESH_MARGIN_MS;
    timerRef.current = setTimeout(
      () => void refreshRef.current?.(),
      delay > 0 ? delay : 0,
    );
  }, []);

  // logout has no deps: only touches refs and SecureStore.
  const logout = useCallback(async (): Promise<void> => {
    clearTimer();
    tokenRef.current = null;
    setToken(null);
    await SecureStore.deleteItemAsync(SECURE_STORE_KEY);
  }, []);

  const persist = useCallback(
    async (jwt: string): Promise<void> => {
      tokenRef.current = jwt;
      setToken(jwt);
      await SecureStore.setItemAsync(SECURE_STORE_KEY, jwt);
      scheduleRenewal(jwt);
    },
    [scheduleRenewal],
  );

  const refresh = useCallback(async (): Promise<void> => {
    const current = tokenRef.current;
    if (!current) return;
    try {
      const resp = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${current}` },
      });
      if (!resp.ok) throw new Error('refresh_failed');
      const { session_token } = (await resp.json()) as { session_token: string };
      await persist(session_token);
    } catch {
      // Refresh failed (revoked session, network error) — force re-login.
      await logout();
    }
  }, [persist, logout]);

  // Keep the forward ref pointing to the latest refresh closure.
  useEffect(() => {
    refreshRef.current = refresh;
  }, [refresh]);

  // On mount: restore any persisted token and arm the renewal timer.
  // If the stored token is already expired, attempt a silent refresh first so
  // the app never surfaces an expired token as authenticated.
  useEffect(() => {
    SecureStore.getItemAsync(SECURE_STORE_KEY)
      .then(async stored => {
        if (!stored) return;
        const expMs = jwtExpiryMs(stored);
        const isExpired = expMs !== null && Date.now() >= expMs;
        if (isExpired) {
          tokenRef.current = stored; // refresh() reads this ref
          await refreshRef.current?.();
        } else {
          tokenRef.current = stored;
          setToken(stored);
          scheduleRenewal(stored);
        }
      })
      .catch(() => {
        // Any error during restore leaves the user on the login screen.
      })
      .finally(() => setIsLoading(false));
    return clearTimer;
  }, [scheduleRenewal]);

  const login = useCallback(async (): Promise<void> => {
    const result = await WebBrowser.openAuthSessionAsync(
      `${API_BASE_URL}/auth/login`,
      APP_SCHEME,
    );
    if (result.type !== 'success') return;
    const jwt = extractToken(result.url);
    if (!jwt) return;
    await persist(jwt);
  }, [persist]);

  return {
    token,
    isLoading,
    isAuthenticated: token !== null,
    login,
    logout,
  };
}
