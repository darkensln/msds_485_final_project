import React, { useEffect, useState } from 'react';
import { api } from '../api.js';

export default function ErasureView({ role }) {
  const [customerId, setCustomerId] = useState('CUST-00099');
  const [reason, setReason] = useState('Customer email request (Art. 17)');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const [busy, setBusy] = useState(false);

  const refresh = () => api.erasures().then(d => setHistory(d.erasures));
  useEffect(() => { refresh(); }, []);

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError(null); setResult(null);
    try {
      const r = await api.submitErasure({ customer_id: customerId, role, reason });
      setResult(r.request);
      refresh();
    } catch (err) {
      setError(err.message || 'Erasure failed');
    } finally {
      setBusy(false);
    }
  }

  const authorized = role === 'cdo' || role === 'dpo';

  return (
    <div className="space-y-4">
      <div className="bg-white border border-slate-200 rounded-lg p-5">
        <h2 className="text-lg font-semibold text-finguard-navy mb-1">GDPR Article 17 — Right to Erasure</h2>
        <p className="text-sm text-slate-500">
          Submit a customer-erasure request. The platform cascades the deletion across
          every table containing that customer, unmaps their entries in the AES-256
          vault, and records the event in the audit log within the 72-hour window.
        </p>
        {!authorized && (
          <div className="mt-3 text-sm text-finguard-red bg-finguard-red/10 border border-finguard-red/30 rounded px-3 py-2">
            Role <span className="font-mono">{role}</span> is not authorized to submit erasure requests.
            Switch to <span className="font-mono">dpo</span> or <span className="font-mono">cdo</span> in the header dropdown.
          </div>
        )}
        <form onSubmit={submit} className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1">Customer ID</label>
            <input
              value={customerId}
              onChange={e => setCustomerId(e.target.value)}
              className="border border-slate-300 rounded px-3 py-1.5 text-sm w-full font-mono"
            />
            <div className="text-[11px] text-slate-400 mt-1">e.g. CUST-00052, CUST-00099</div>
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs text-slate-500 mb-1">Reason</label>
            <input
              value={reason}
              onChange={e => setReason(e.target.value)}
              className="border border-slate-300 rounded px-3 py-1.5 text-sm w-full"
            />
          </div>
          <div className="md:col-span-3">
            <button
              type="submit"
              disabled={!authorized || busy}
              className="px-4 py-2 text-sm font-medium bg-finguard-red text-white rounded disabled:opacity-50"
            >
              {busy ? 'Processing…' : 'Submit erasure request'}
            </button>
          </div>
        </form>
        {error && <div className="mt-3 text-sm text-finguard-red">{error}</div>}
        {result && (
          <div className="mt-4 border-l-4 border-finguard-mint bg-finguard-mint/10 rounded p-3 text-sm">
            <div className="font-semibold">✅ {result.id} — {result.status}</div>
            <div className="text-slate-600">Customer {result.customer_id} · requested by {result.requested_by} · {result.ts}</div>
            <div className="text-slate-600">Tables impacted: {Object.entries(result.tables_impacted).map(([t,n]) => `${t} (${n})`).join(', ') || '—'}</div>
          </div>
        )}
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-5">
        <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-500 mb-3">Erasure log</h3>
        <table className="text-sm w-full">
          <thead className="text-left text-slate-500 text-xs">
            <tr>
              <th className="py-1">ID</th>
              <th className="py-1">Time</th>
              <th className="py-1">Customer</th>
              <th className="py-1">By</th>
              <th className="py-1">Impact</th>
              <th className="py-1">Reason</th>
              <th className="py-1">Status</th>
            </tr>
          </thead>
          <tbody>
            {history.map(h => (
              <tr key={h.id} className="border-t border-slate-100">
                <td className="py-1 font-mono">{h.id}</td>
                <td className="py-1 text-slate-400 text-xs">{h.ts.replace('T',' ').replace('Z','')}</td>
                <td className="py-1">{h.customer_id}</td>
                <td className="py-1">{h.requested_by}</td>
                <td className="py-1 text-xs">{Object.entries(h.tables_impacted).map(([t,n]) => `${t}(${n})`).join(', ') || '—'}</td>
                <td className="py-1 text-slate-500 text-xs">{h.reason}</td>
                <td className="py-1 text-emerald-700 text-xs">{h.status}</td>
              </tr>
            ))}
            {history.length === 0 && (
              <tr><td colSpan="7" className="py-3 text-center text-slate-400">No erasures yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
