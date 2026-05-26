import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../api.js';

const CLASS_COLORS = {
  Public:       'bg-slate-200 text-slate-700',
  Internal:     'bg-finguard-teal/20 text-finguard-teal',
  Confidential: 'bg-finguard-accent/30 text-amber-800',
  Restricted:   'bg-finguard-red/20 text-finguard-red',
  'Highly Restricted': 'bg-finguard-red/30 text-finguard-red',
};

function Pill({ children, color = 'bg-slate-100 text-slate-700' }) {
  return <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-medium ${color}`}>{children}</span>;
}

export default function CatalogView({ role, onSelect }) {
  const [rows, setRows] = useState([]);
  const [summary, setSummary] = useState(null);
  const [filters, setFilters] = useState({
    search: '',
    table: '',
    classification: '',
    pii_only: false,
    dq_issues_only: false,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([api.catalog(filters), api.catalogSummary()])
      .then(([cat, sum]) => { setRows(cat.rows); setSummary(sum); })
      .finally(() => setLoading(false));
  }, [JSON.stringify(filters)]);

  const tables = summary ? Object.keys(summary.by_table) : [];

  return (
    <div className="space-y-4">
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <KPI label="Tables" value={summary.total_tables} />
          <KPI label="Columns" value={summary.total_columns} />
          <KPI label="PII columns" value={summary.pii_columns} color="text-finguard-accent" />
          <KPI label="Masked PII" value={summary.pii_masked_columns} color="text-finguard-mint" />
          <KPI label="DQ issues" value={summary.dq_columns_with_issue} color="text-finguard-red" />
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-lg p-3 flex flex-wrap gap-2 items-center">
        <input
          type="text"
          placeholder="Search column, table, owner, regulation…"
          className="flex-1 min-w-[240px] border border-slate-300 rounded px-3 py-1.5 text-sm"
          value={filters.search}
          onChange={e => setFilters(f => ({ ...f, search: e.target.value }))}
        />
        <select
          value={filters.table}
          onChange={e => setFilters(f => ({ ...f, table: e.target.value }))}
          className="border border-slate-300 rounded px-2 py-1.5 text-sm"
        >
          <option value="">All tables</option>
          {tables.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <select
          value={filters.classification}
          onChange={e => setFilters(f => ({ ...f, classification: e.target.value }))}
          className="border border-slate-300 rounded px-2 py-1.5 text-sm"
        >
          <option value="">All classifications</option>
          {['Public','Internal','Confidential','Restricted','Highly Restricted'].map(c =>
            <option key={c} value={c}>{c}</option>
          )}
        </select>
        <label className="text-sm flex items-center gap-1">
          <input type="checkbox" checked={filters.pii_only}
                 onChange={e => setFilters(f => ({ ...f, pii_only: e.target.checked }))}/>
          PII only
        </label>
        <label className="text-sm flex items-center gap-1">
          <input type="checkbox" checked={filters.dq_issues_only}
                 onChange={e => setFilters(f => ({ ...f, dq_issues_only: e.target.checked }))}/>
          DQ issues
        </label>
        <div className="text-xs text-slate-500 ml-auto">
          {loading ? 'Loading…' : `${rows.length} result${rows.length === 1 ? '' : 's'}`}
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-600 text-left">
            <tr>
              <th className="px-3 py-2">Table</th>
              <th className="px-3 py-2">Column</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Classification</th>
              <th className="px-3 py-2">PII</th>
              <th className="px-3 py-2">Mask</th>
              <th className="px-3 py-2">DQ</th>
              <th className="px-3 py-2">Steward</th>
              <th className="px-3 py-2 text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.table + '.' + r.column} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-3 py-2 text-slate-500">{r.table}</td>
                <td className="px-3 py-2 font-medium">{r.column}</td>
                <td className="px-3 py-2 text-slate-500">{r.data_type}</td>
                <td className="px-3 py-2"><Pill color={CLASS_COLORS[r.classification]}>{r.classification}</Pill></td>
                <td className="px-3 py-2">
                  {r.is_pii
                    ? <Pill color="bg-finguard-red/15 text-finguard-red">{r.pii_type} PII</Pill>
                    : <span className="text-slate-400 text-xs">—</span>}
                </td>
                <td className="px-3 py-2 text-xs text-slate-600">{r.masking_method}</td>
                <td className="px-3 py-2">
                  {r.dq_any_issue
                    ? <Pill color="bg-amber-100 text-amber-700">⚠ DQ</Pill>
                    : <span className="text-slate-300 text-xs">clean</span>}
                </td>
                <td className="px-3 py-2 text-xs text-slate-500">{r.steward}</td>
                <td className="px-3 py-2 text-right">
                  <button
                    onClick={() => onSelect(r.table, r.column)}
                    className="text-finguard-teal hover:underline text-xs"
                  >
                    Details →
                  </button>
                </td>
              </tr>
            ))}
            {!loading && rows.length === 0 && (
              <tr><td colSpan="9" className="px-3 py-6 text-center text-slate-400">
                No columns match those filters.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function KPI({ label, value, color = 'text-finguard-navy' }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-3">
      <div className="text-[11px] uppercase tracking-widest text-slate-500">{label}</div>
      <div className={`text-2xl font-semibold ${color}`}>{value}</div>
    </div>
  );
}
