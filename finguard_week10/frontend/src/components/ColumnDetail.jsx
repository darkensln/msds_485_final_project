import React, { useEffect, useState } from 'react';
import { api } from '../api.js';

export default function ColumnDetail({ table, column, role, onBack, onJumpLineage }) {
  const [detail, setDetail] = useState(null);
  const [sample, setSample] = useState(null);

  useEffect(() => {
    api.columnDetail(table, column).then(setDetail);
    api.sample(table, role, 5).then(setSample);
  }, [table, column, role]);

  if (!detail) return <div className="text-slate-500">Loading…</div>;

  return (
    <div className="space-y-4">
      <button onClick={onBack} className="text-sm text-finguard-teal hover:underline">← Back to catalog</button>

      <div className="bg-white border border-slate-200 rounded-lg p-5">
        <div className="text-xs uppercase tracking-widest text-slate-500">{detail.table}</div>
        <h2 className="text-2xl font-semibold text-finguard-navy">{detail.column}</h2>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          <Tag>Type: {detail.data_type}</Tag>
          <Tag>Classification: {detail.classification}</Tag>
          <Tag>Access: {detail.access_tier}</Tag>
          {detail.is_pii ? <Tag color="bg-finguard-red/15 text-finguard-red">{detail.pii_type} PII</Tag> : null}
          {detail.masking_required ? <Tag color="bg-finguard-mint/20 text-emerald-700">Mask: {detail.masking_method}</Tag> : null}
          {detail.dq_any_issue ? <Tag color="bg-amber-100 text-amber-700">⚠ DQ issues</Tag> : null}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Section title="Governance">
          <Row k="Owner" v={detail.owner} />
          <Row k="Steward" v={detail.steward} />
          <Row k="Retention" v={detail.retention} />
          <Row k="Regulation" v={detail.regulation} />
          <Row k="Sample value" v={String(detail.sample_value)} />
        </Section>

        <Section title="Data Quality flags">
          {Object.entries(detail.dq).map(([k, v]) => (
            <Row key={k} k={k} v={v ? '⚠ flagged' : 'clean'}
                 color={v ? 'text-amber-700' : 'text-slate-400'} />
          ))}
        </Section>
      </div>

      <Section title="Column lineage">
        <div className="text-sm text-slate-600">
          {detail.lineage.rows.length === 0 ? (
            <div>This column does not flow through the masking layer (non-PII).</div>
          ) : (
            detail.lineage.rows.map((row, i) => (
              <div key={i} className="flex flex-wrap items-center gap-2 mb-2 text-xs">
                <span className="px-2 py-1 rounded tier-raw">{row.source_column}</span>
                <span>→</span>
                <span className="px-2 py-1 rounded tier-privacy">{row.method}</span>
                <span>→</span>
                <span className="px-2 py-1 rounded tier-consumption">{row.dest_column}</span>
                <span>→</span>
                <span className="text-slate-500">{row.consumers.join(', ')}</span>
                <span className="ml-auto text-slate-400">{row.regulation}</span>
              </div>
            ))
          )}
        </div>
        <button onClick={onJumpLineage} className="mt-2 text-sm text-finguard-teal hover:underline">
          Open full lineage graph →
        </button>
      </Section>

      {sample && !sample.denied && (
        <Section title={`Sample data (5 rows, as ${role}${sample.masked_for_role ? ', masked' : ', raw'})`}>
          <div className="overflow-x-auto">
            <table className="text-xs w-full">
              <thead>
                <tr className="text-left">
                  {sample.columns.map(c => (
                    <th key={c} className={'px-2 py-1 ' + (c === column ? 'bg-finguard-accent/20' : 'bg-slate-100')}>{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sample.rows.map((r, i) => (
                  <tr key={i} className="border-t">
                    {sample.columns.map(c => (
                      <td key={c} className={'px-2 py-1 ' + (c === column ? 'bg-finguard-accent/10 font-mono' : '')}>{String(r[c] ?? '')}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}
      {sample && sample.denied && (
        <Section title="Sample data">
          <div className="text-finguard-red text-sm">{sample.reason}</div>
        </Section>
      )}
    </div>
  );
}

function Tag({ children, color = 'bg-slate-100 text-slate-700' }) {
  return <span className={`px-2 py-1 rounded ${color}`}>{children}</span>;
}
function Section({ title, children }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5">
      <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-500 mb-3">{title}</h3>
      {children}
    </div>
  );
}
function Row({ k, v, color = 'text-slate-700' }) {
  return (
    <div className="flex justify-between py-1 border-b border-slate-100 last:border-0 text-sm">
      <span className="text-slate-500 capitalize">{k.replace(/_/g, ' ')}</span>
      <span className={color}>{String(v)}</span>
    </div>
  );
}
