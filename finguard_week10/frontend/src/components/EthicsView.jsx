import React, { useEffect, useState } from 'react';
import { api } from '../api.js';

export default function EthicsView() {
  const [data, setData] = useState(null);
  const [expanded, setExpanded] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    api.unesco()
      .then(setData)
      .catch(e => setErr(String(e)));
  }, []);

  if (err) return (
    <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-md p-3">
      Failed to load UNESCO crosswalk: {err}
    </div>
  );
  if (!data) return <div className="text-slate-500">Loading…</div>;

  return (
    <div className="space-y-5">

      {/* Header banner */}
      <div className="rounded-md border border-finguard-teal/30 bg-finguard-teal/5 px-5 py-4">
        <div className="text-xs uppercase tracking-widest text-finguard-mint font-medium">
          UNESCO AI Ethics — Compliance Crosswalk
        </div>
        <h2 className="text-xl font-semibold text-finguard-navy mt-1">{data.source}</h2>
        <div className="text-sm text-slate-600 mt-1">
          {data.adopted_by} ·
          <a href={data.url} target="_blank" rel="noreferrer"
             className="text-finguard-teal hover:underline ml-1">
            Read the recommendation ↗
          </a>
        </div>
      </div>

      {/* KPI tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <KPI label="UNESCO principles" value={data.principles.length}
             sub="Operational" />
        <KPI label="Foundational values" value={data.values.length}
             sub="Human-rights anchored" />
        <KPI label="FinGuard controls mapped" value={data.total_controls}
             sub="Across 10 principles" color="text-finguard-mint" />
        <KPI label="UNESCO member states" value="193" sub="Unanimously adopted" />
      </div>

      {/* Foundational values */}
      <Panel title="Foundational values (the 'why')">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {data.values.map(v => (
            <div key={v.id} className="border border-slate-200 rounded-md p-3 bg-white">
              <div className="text-sm font-medium text-finguard-navy">{v.name}</div>
              <div className="text-xs text-slate-600 mt-1">{v.summary}</div>
            </div>
          ))}
        </div>
      </Panel>

      {/* Principles table — expand to see FinGuard controls */}
      <Panel title="Principles → FinGuard controls (the 'how')">
        <div className="text-xs text-slate-500 mb-2">
          Click any principle to see exactly which FinGuard controls satisfy it.
        </div>
        <div className="divide-y divide-slate-200 border border-slate-200 rounded-md overflow-hidden">
          {data.principles.map((p, idx) => {
            const open = expanded === p.id;
            return (
              <div key={p.id} className="bg-white">
                <button
                  onClick={() => setExpanded(open ? null : p.id)}
                  className="w-full text-left px-4 py-3 hover:bg-slate-50 flex items-start justify-between gap-4"
                >
                  <div>
                    <div className="text-xs uppercase tracking-widest text-slate-400">
                      Principle {idx + 1}
                    </div>
                    <div className="text-sm font-semibold text-finguard-navy">
                      {p.name}
                    </div>
                    <div className="text-xs text-slate-600 mt-1">{p.summary}</div>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="inline-block text-[11px] font-medium bg-finguard-mint/15 text-finguard-mint rounded px-2 py-0.5">
                      {p.finguard_controls.length} controls
                    </span>
                    <div className="text-finguard-teal text-xs mt-1">
                      {open ? '▼ hide' : '▶ show'}
                    </div>
                  </div>
                </button>
                {open && (
                  <div className="px-4 pb-3 pt-1 bg-slate-50">
                    <div className="text-[11px] uppercase tracking-widest text-slate-500 mb-2">
                      FinGuard controls satisfying this principle
                    </div>
                    <ul className="space-y-1.5">
                      {p.finguard_controls.map((c, i) => (
                        <li key={i} className="text-sm text-slate-700 flex gap-2">
                          <span className="text-finguard-teal mt-0.5">✓</span>
                          <span>{c}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Panel>

      <div className="text-[11px] text-slate-500 italic">
        Crosswalk version: 1.0 · Generated from
        <code className="px-1 mx-1 bg-slate-100 rounded text-[10px]">/api/ethics/unesco</code>
        · Source: UNESCO Doc 386276 (2021)
      </div>
    </div>
  );
}

function KPI({ label, value, sub, color = 'text-finguard-navy' }) {
  return (
    <div className="bg-white border border-slate-200 rounded-md p-3">
      <div className="text-[11px] uppercase tracking-widest text-slate-500">{label}</div>
      <div className={`text-2xl font-semibold ${color}`}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
    </div>
  );
}

function Panel({ title, children }) {
  return (
    <div className="bg-white border border-slate-200 rounded-md p-4">
      <div className="text-sm font-semibold text-finguard-navy mb-3">{title}</div>
      {children}
    </div>
  );
}
