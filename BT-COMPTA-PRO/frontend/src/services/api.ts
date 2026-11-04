import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';

/**
 * Gestion des jetons :
 * - le jeton d'accès (15 min) est conservé UNIQUEMENT en mémoire : un script malveillant ne peut pas le lire
 *   dans le stockage du navigateur ;
 * - le jeton de rafraîchissement est un cookie HttpOnly posé par le serveur (inaccessible au JavaScript),
 *   envoyé seulement vers /api/auth/ et jamais depuis un autre site.
 */
let accessToken: string | null = null;

export const session = {
  get access() {
    return accessToken;
  },
  set(access: string | null) {
    accessToken = access;
  },
};

// Nettoyage des jetons laissés par l'ancienne version de l'application.
try {
  localStorage.removeItem('btc.access');
  localStorage.removeItem('btc.refresh');
} catch {
  /* stockage indisponible */
}

const baseURL = import.meta.env.VITE_API_URL || '/api';

export const api = axios.create({ baseURL, timeout: 30000, withCredentials: true });

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
});

let refreshing: Promise<string | null> | null = null;

/** Demande un nouveau jeton d'accès à partir du cookie de session. Renvoie null si la session est expirée. */
export function refreshAccess(): Promise<string | null> {
  refreshing ??= axios
    .post(`${baseURL}/auth/refresh/`, {}, { withCredentials: true })
    .then((r) => {
      accessToken = r.data.access;
      return accessToken;
    })
    .catch(() => {
      accessToken = null;
      return null;
    })
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    const url = original?.url ?? '';
    const isAuthCall = /\/auth\/(login|refresh|logout|register|password-reset)/.test(url);
    if (error.response?.status === 401 && original && !original._retry && !isAuthCall) {
      original._retry = true;
      const access = await refreshAccess();
      if (access) {
        original.headers.Authorization = `Bearer ${access}`;
        return api(original);
      }
      window.dispatchEvent(new CustomEvent('btc:logout', { detail: 'expired' }));
    }
    return Promise.reject(error);
  },
);

/** Extrait un message d'erreur lisible depuis une réponse DRF. */
export function errorMessage(err: unknown, fallback = 'Une erreur est survenue.'): string {
  const e = err as AxiosError<unknown>;
  if (!e?.response) return e?.message === 'Network Error' ? 'Serveur injoignable. Vérifiez votre connexion.' : fallback;
  const data = e.response.data as Record<string, unknown> | string | undefined;
  if (e.response.status === 413) return 'Fichier trop volumineux pour être envoyé.';
  if (e.response.status === 429) return 'Trop de tentatives. Patientez avant de réessayer.';
  if (e.response.status >= 500) return 'Le serveur a rencontré un problème. Réessayez dans un instant.';
  if (!data || typeof data === 'string') return fallback;
  const flatten = (v: unknown): string[] => {
    if (v == null) return [];
    if (typeof v === 'string') return [v];
    if (Array.isArray(v)) return v.flatMap(flatten);
    if (typeof v === 'object') return Object.values(v as Record<string, unknown>).flatMap(flatten);
    return [String(v)];
  };
  const msgs = flatten(data.detail ?? data.non_field_errors ?? data);
  return msgs.length ? msgs.join(' ') : fallback;
}

/** Télécharge un fichier binaire (PDF / Excel) renvoyé par l'API. */
export async function download(url: string, filename: string, method: 'get' | 'post' = 'get', body?: unknown) {
  const response = await api.request({ url, method, data: body, responseType: 'blob' });
  const href = URL.createObjectURL(response.data as Blob);
  const a = document.createElement('a');
  a.href = href;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(href), 1000);
}

/**
 * Ouvre un fichier protégé (sujet, corrigé) dans un nouvel onglet.
 * Le fichier est récupéré avec le jeton d'accès puis affiché via une URL locale temporaire :
 * aucun lien public n'existe vers les documents.
 */
export async function openProtectedFile(url: string, filename: string) {
  const tab = window.open('', '_blank');
  try {
    const response = await api.get(url, { responseType: 'blob' });
    const blob = response.data as Blob;
    const href = URL.createObjectURL(blob);
    const viewable = blob.type === 'application/pdf' || blob.type.startsWith('image/');
    if (tab && viewable) {
      tab.location.href = href;
    } else {
      tab?.close();
      const a = document.createElement('a');
      a.href = href;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
    }
    setTimeout(() => URL.revokeObjectURL(href), 60_000);
  } catch (err) {
    tab?.close();
    throw err;
  }
}
