const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function api<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || res.statusText || 'Request failed');
  }
  return res.json();
}

export const auth = {
  register: (data: object) =>
    api('/api/v1/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  login: (data: object) =>
    api('/api/v1/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  logout: () => api('/api/v1/auth/logout', { method: 'POST' }),
  me: () => api('/api/v1/auth/me'),
};

export const wallet = {
  balance: () => api('/api/v1/wallet/balance'),
  deposit: (amount_kes: number, idempotency_key?: string) =>
    api('/api/v1/wallet/deposit', {
      method: 'POST',
      body: JSON.stringify({ amount_kes, idempotency_key }),
    }),
  transfer: (recipient: string, amount_kes: number, description?: string) =>
    api('/api/v1/wallet/transfer', {
      method: 'POST',
      body: JSON.stringify({ recipient, amount_kes, description }),
    }),
  history: () => api('/api/v1/wallet/history'),
};

export const tokens = {
  list: () => api('/api/v1/tokens'),
  create: (data: object) =>
    api('/api/v1/tokens', { method: 'POST', body: JSON.stringify(data) }),
  getByMint: (mint: string) => api(`/api/v1/tokens/mint/${mint}`),
  quote: (tokenId: string, body: object) =>
    api(`/api/v1/tokens/${tokenId}/quote`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  trade: (tokenId: string, body: object) =>
    api(`/api/v1/tokens/${tokenId}/trade`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  portfolio: () => api('/api/v1/tokens/portfolio/me'),
};
