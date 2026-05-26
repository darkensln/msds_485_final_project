import React, { useEffect, useMemo, useState } from 'react';
import ReactFlow, { Background, Controls, MarkerType } from 'reactflow';
import { api } from '../api.js';

// Lay out nodes column-by-column based on tier.
const TIER_ORDER = ['external', 'raw', 'privacy', 'consumption', 'consumer'];

function layout(graph) {
  const byTier = {};
  graph.nodes.forEach(n => {
    const t = n.tier || 'raw';
    (byTier[t] = byTier[t] || []).push(n);
  });
  const COL_W = 260;
  const ROW_H = 84;
  const nodes = [];
  TIER_ORDER.forEach((tier, ci) => {
    (byTier[tier] || []).forEach((n, ri) => {
      nodes.push({
        id: n.id,
        position: { x: ci * COL_W, y: ri * ROW_H },
        data: { label: (
          <div className="text-center">
            <div className="text-[11px] font-medium leading-tight">{n.label}</div>
            {n.sub ? <div className="text-[9px] opacity-80">{n.sub}</div> : null}
          </div>
        )},
        className: 'tier-' + tier,
        style: { padding: 6, borderRadius: 8, border: 'none', width: 220 },
      });
    });
  });
  const edges = graph.edges.map((e, i) => ({
    id: 'e' + i,
    source: e.source,
    target: e.target,
    label: e.label,
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { stroke: '#94a3b8' },
    labelStyle: { fontSize: 10, fill: '#475569' },
  }));
  return { nodes, edges };
}

export default function LineageView() {
  const [view, setView] = useState('system'); // 'system' | 'columns'
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [tableFilter, setTableFilter] = useState('');

  useEffect(() => {
    if (view === 'system') {
      api.lineageSystem().then(setGraph);
    } else {
      api.lineageColumns(tableFilter || undefined).then(setGraph);
    }
  }, [view, tableFilter]);

  const flow = useMemo(() => layout(graph), [graph]);

  return (
    <div className="space-y-3">
      <div className="bg-white border border-slate-200 rounded-lg p-3 flex items-center gap-3 flex-wrap">
        <div className="text-sm font-medium">Lineage view:</div>
        <div className="inline-flex bg-slate-100 rounded">
          <button
            onClick={() => setView('system')}
            className={`px-3 py-1.5 text-sm rounded ${view === 'system' ? 'bg-finguard-navy text-white' : 'text-slate-700'}`}>
            System (sources → consumers)
          </button>
          <button
            onClick={() => setView('columns')}
            className={`px-3 py-1.5 text-sm rounded ${view === 'columns' ? 'bg-finguard-navy text-white' : 'text-slate-700'}`}>
            Column-level (PII flow)
          </button>
        </div>
        {view === 'columns' && (
          <select
            value={tableFilter}
            onChange={e => setTableFilter(e.target.value)}
            className="border border-slate-300 rounded px-2 py-1.5 text-sm"
          >
            <option value="">All PII fields</option>
            <option value="aml_transactions">aml_transactions</option>
            <option value="bank_marketing_customers">bank_marketing_customers</option>
            <option value="sec_edgar_filings">sec_edgar_filings</option>
            <option value="paysim_fraud_transactions">paysim_fraud_transactions</option>
          </select>
        )}
        <div className="ml-auto flex gap-3 text-xs">
          <Legend color="tier-external" label="External" />
          <Legend color="tier-raw" label="Raw" />
          <Legend color="tier-privacy" label="Privacy layer" />
          <Legend color="tier-consumption" label="Masked views" />
          <Legend color="tier-consumer" label="Consumers" />
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg" style={{ height: 620 }}>
        <ReactFlow nodes={flow.nodes} edges={flow.edges} fitView>
          <Background gap={20} color="#e2e8f0" />
          <Controls />
        </ReactFlow>
      </div>

      <div className="text-xs text-slate-500">
        {graph.nodes.length} nodes · {graph.edges.length} edges.
        {view === 'system'
          ? ' Tracks dataset-level flow from external feeds through the privacy layer into role-scoped consumption views.'
          : ' Shows each PII column\'s journey from source → masking method → masked destination → consuming roles.'}
      </div>
    </div>
  );
}

function Legend({ color, label }) {
  return (
    <div className="flex items-center gap-1">
      <span className={`inline-block w-3 h-3 rounded ${color}`}></span>
      <span>{label}</span>
    </div>
  );
}
