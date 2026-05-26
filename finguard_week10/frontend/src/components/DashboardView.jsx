import React, { useEffect, useState } from 'react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend,
} from 'recharts';
import { api } from '../api.js';

const PIE_COLORS = ['#0B1D3A', '#028090', '#F4A261', '#E63946', '#02C39A'];

export default function DashboardView() {
  const [m, setM] = useState(null);
  const [audit, setAudit] = useState([]);
  const [erasures, setErasures] = useState([]);

  useEffect(() => {
    api.metrics().then(setM);
    api.audit(25).then(d => setAudit(d.entries));
    api.erasures().then(d => setErasures(d.erasures));
  }, []);

  if (!m) return <div className="text-slate-500">Loading…</div>;

  const classData = Object.entries(m.by_classification).map(([name, value]) => ({ name, value }));
  const piiData = Object.entries(m.by_pii_type).filter(([k]) => k !== 'None').map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <KPI label="PII columns masked" value={`${m.pii_masked_columns}/${m.pii_columns}`} sub="100% coverage" />
        <KPI label="Vault entries (AES-256)" value={m.vault_entries.toLocaleString()} sub="Reversible mapping" />
        <KPI label="GDPR erasures processed" value={m.erasures_processed} sub="Art. 17 cascade" color="text-finguard-mint" />
        <KPI label="RBAC denials (30d)" value={m.access_denials_30d} sub="From audit log" color="text-finguard-red" />
        <KPI label="Active SARs" value={m.active_sars} sub="AML reporting" color="text-finguard-accent" />
        <KPI label="Quality gate pass" value={`${(m.quality_gate_pass_rate * 100).toFixed(1)}%`} sub="ETL stages" />
        <KPI label="DQ columns flagged" value={m.dq_columns_with_issue} sub="6 dimensions" />
        <KPI label="Tables governed" value={m.tables_governed} sub={`${m.columns_governed} columns`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Panel title="Columns by classification">
          <div style={{ height: 240 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={classData} dataKey="value" nameKey="name" outerRadius={90} label>
                  {classData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel title="PII columns by type">
          <div style={{ height: 240 }}>
            <ResponsiveContainer>
              <BarChart data={piiData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#028090" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <Panel title="Regulators satisfied">
        <div className="flex flex-wrap gap-2">
          {m.regulators_satisfied.map(r => (
            <span key={r} className="px-3 py-1 text-xs rounded-full bg-finguard-mint/20 text-emerald-800 font-medium">
              ✓ {r}
            </span>
          ))}
        </div>
      </Panel>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Panel title={`Recent audit log (${audit.length})`}>
          <div className="overflow-auto" style={{ maxHeight: 280 }}>
            <table className="text-xs w-full">
              <thead className="text-slate-500">
                <tr>
                  <th className="text-left pb-1">Time (UTC)</th>
                  <th className="text-left pb-1">Role</th>
                  <th className="text-left pb-1">Decision</th>
                  <th className="text-left pb-1">Action</th>
                </tr>
              </thead>
              <tbody>
                {audit.map((e, i) => (
                  <tr key={i} className="border-t border-slate-100">
                    <td className="py-1 pr-2 text-slate-400">{e.ts.replace('T', ' ').replace('Z','')}</td>
                    <td className="py-1 pr-2">{e.role}</td>
                    <td className="py-1 pr-2">
                      <span className={e.decision === 'DENY' ? 'text-finguard-red font-medium' : 'text-emerald-700'}>
                        {e.decision}
                      </span>
                    </td>
                    <td className="py-1 pr-2 text-slate-600">{e.action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title={`GDPR erasure history (${erasures.length})`}>
          <div className="overflow-auto" style={{ maxHeight: 280 }}>
            <table className="text-xs w-full">
              <thead className="text-slate-500">
                <tr>
                  <th className="text-left pb-1">ID</th>
                  <th className="text-left pb-1">Time</th>
                  <th className="text-left pb-1">Customer</th>
                  <th className="text-left pb-1">By</th>
                  <th className="text-left pb-1">Status</th>
                </tr>
              </thead>
              <tbody>
                {erasures.map((e) => (
                  <tr key={e.id} className="border-t border-slate-100">
                    <td className="py-1 pr-2 font-mono">{e.id}</td>
                    <td className="py-1 pr-2 text-slate-400">{e.ts.slice(0, 10)}</td>
                    <td className="py-1 pr-2">{e.customer_id}</td>
                    <td className="py-1 pr-2">{e.requested_by}</td>
                    <td className="py-1 pr-2 text-emerald-700">{e.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </div>
  );
}

function Panel({ title, children }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4">
      <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-500 mb-3">{title}</h3>
      {children}
    </div>
  );
}
function KPI({ label, value, sub, color = 'text-finguard-navy' }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-3">
      <div className="text-[11px] uppercase tracking-widest text-slate-500">{label}</div>
      <div className={`text-2xl font-semibold ${color}`}>{value}</div>
      {sub && <div className="text-[11px] text-slate-400">{sub}</div>}
    </div>
  );
}
