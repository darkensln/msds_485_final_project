import React, { useEffect, useState } from 'react';
import { api } from './api.js';
import CatalogView from './components/CatalogView.jsx';
import ColumnDetail from './components/ColumnDetail.jsx';
import LineageView from './components/LineageView.jsx';
import DashboardView from './components/DashboardView.jsx';
import ErasureView from './components/ErasureView.jsx';

const TABS = [
  { id: 'catalog',   label: 'Data Catalog' },
  { id: 'lineage',   label: 'Lineage' },
  { id: 'dashboard', label: 'Compliance Dashboard' },
  { id: 'erasure',   label: 'GDPR Erasure' },
];

export default function App() {
  const [tab, setTab] = useState('catalog');
  const [role, setRole] = useState('data_analyst');
  const [roles, setRoles] = useState([]);
  const [selected, setSelected] = useState(null); // {table, column}

  useEffect(() => {
    api.roles().then(d => setRoles(d.roles)).catch(() => {});
  }, []);

  const currentRole = roles.find(r => r.id === role);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      {/* Header */}
      <header className="bg-finguard-navy text-white">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <div className="text-xs uppercase tracking-widest text-finguard-mint">
              FinGuard — Borderless Banking
            </div>
            <h1 className="text-2xl font-semibold">Data Catalog & Compliance Console</h1>
            <div className="text-xs text-slate-300 mt-1">
              Week 10 deliverable · Governance First, Growth Always
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-[11px] uppercase tracking-widest text-slate-300">
                Logged in as
              </div>
              <div className="text-sm font-medium">{currentRole?.label ?? role}</div>
              <div className="text-[11px] text-slate-300">
                Tier: {currentRole?.tier ?? '—'}
                {currentRole?.see_raw ? ' · sees raw PII' : ' · masked'}
              </div>
            </div>
            <select
              className="bg-finguard-teal/80 text-white text-sm rounded-md px-2 py-1.5 border border-finguard-teal"
              value={role}
              onChange={e => setRole(e.target.value)}
            >
              {roles.map(r => (
                <option key={r.id} value={r.id}>{r.label}</option>
              ))}
            </select>
          </div>
        </div>

        <nav className="max-w-7xl mx-auto px-6">
          <div className="flex gap-1">
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => { setTab(t.id); setSelected(null); }}
                className={
                  'px-4 py-2 text-sm rounded-t-md ' +
                  (tab === t.id
                    ? 'bg-slate-50 text-finguard-navy font-medium'
                    : 'text-slate-200 hover:text-white hover:bg-finguard-teal/60')
                }
              >
                {t.label}
              </button>
            ))}
          </div>
        </nav>
      </header>

      {/* Body */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {tab === 'catalog' && (
          selected
            ? <ColumnDetail
                table={selected.table}
                column={selected.column}
                role={role}
                onBack={() => setSelected(null)}
                onJumpLineage={() => setTab('lineage')}
              />
            : <CatalogView
                role={role}
                onSelect={(table, column) => setSelected({ table, column })}
              />
        )}
        {tab === 'lineage'   && <LineageView />}
        {tab === 'dashboard' && <DashboardView />}
        {tab === 'erasure'   && <ErasureView role={role} />}
      </main>

      <footer className="max-w-7xl mx-auto px-6 py-6 text-xs text-slate-500">
        FinGuard · 7 datasets · 33,197 records · 98 columns · 24 PII fields ·
        28,893 vault entries · 7 roles enforced
      </footer>
    </div>
  );
}
