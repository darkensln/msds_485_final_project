// Thin wrapper around the FastAPI backend.

const BASE = import.meta.env.VITE_API_BASE || '/api';

async function get(path) {
  const r = await fetch(BASE + path);
  if (!r.ok) throw new Error(`${path} ${r.status}`);
  return r.json();
}

async function post(path, body) {
  const r = await fetch(BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const j = await r.json().catch(() => ({}));
    throw new Error(j.detail || `${path} ${r.status}`);
  }
  return r.json();
}

export const api = {
  health:        () => get('/health'),
  roles:         () => get('/roles'),

  catalog:       (params = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== '' && v !== false && v !== null && v !== undefined)
    ).toString();
    return get('/catalog' + (qs ? '?' + qs : ''));
  },
  catalogSummary: () => get('/catalog/summary'),
  columnDetail:  (table, column) =>
    get(`/catalog/${encodeURIComponent(table)}/${encodeURIComponent(column)}`),

  sample: (table, role, limit = 25, offset = 0, search = '') => {
    const qs = new URLSearchParams({ role, limit, offset });
    if (search) qs.set('search', search);
    return get(`/tables/${encodeURIComponent(table)}/sample?` + qs.toString());
  },

  lineageSystem:  () => get('/lineage/system'),
  lineageColumns: (table, column) => {
    const qs = new URLSearchParams();
    if (table) qs.set('table', table);
    if (column) qs.set('column', column);
    return get('/lineage/columns' + (qs.toString() ? '?' + qs.toString() : ''));
  },

  metrics:        () => get('/compliance/metrics'),
  audit:          (limit = 100) => get('/compliance/audit?limit=' + limit),
  erasures:       () => get('/compliance/erasures'),
  submitErasure:  (body) => post('/compliance/erasure', body),
};
