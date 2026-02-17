const API_URL = import.meta.env.VITE_API_URL ?? '/api';

const jsonHeaders = {
  'Content-Type': 'application/json',
};

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, options);
  const contentType = response.headers.get('content-type') ?? '';
  const payload = contentType.includes('application/json') ? await response.json() : null;

  if (!response.ok) {
    const detail = payload?.detail ?? 'Error de comunicación con el backend.';
    throw new Error(Array.isArray(detail) ? detail.join(', ') : detail);
  }

  return payload;
}

export const api = {
  getToken: (credentials) =>
    request('/auth/token', {
      method: 'POST',
      headers: jsonHeaders,
      body: JSON.stringify(credentials),
    }),

  getProducts: () => request('/products'),
  getClients: () => request('/clients'),
  getInventory: () => request('/inventory'),
  getSales: () => request('/sales'),

  createProduct: (token, data) =>
    request('/products', {
      method: 'POST',
      headers: { ...jsonHeaders, Authorization: `Bearer ${token}` },
      body: JSON.stringify(data),
    }),

  createClient: (token, data) =>
    request('/clients', {
      method: 'POST',
      headers: { ...jsonHeaders, Authorization: `Bearer ${token}` },
      body: JSON.stringify(data),
    }),

  createSale: (token, data) =>
    request('/sales', {
      method: 'POST',
      headers: { ...jsonHeaders, Authorization: `Bearer ${token}` },
      body: JSON.stringify(data),
    }),
};
