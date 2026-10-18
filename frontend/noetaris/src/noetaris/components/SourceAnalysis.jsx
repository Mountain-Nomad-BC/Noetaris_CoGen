import React, { useEffect, useRef, useState } from 'react';
import { apiRequest } from '../services/api';
import { analysisRequest, analysisResult } from '../services/sourceControls';

export default function SourceAnalysis({ source }) {
  const evidence = source.manifest?.documents?.[0]?.metadata?.structured_data;
  const sheets = evidence?.schema === 'nsai.xlsx-evidence/1' ? evidence.sheets : null;
  const supported = ['text/csv','text/tab-separated-values','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'].includes(source.media_type);
  const [input, setInput] = useState({ value: '1', group: '', skip: '0', operation: 'sum', unit: '', sheet: '' });
  const [state, setState] = useState({ running: false, result: null, error: null });
  const pending = useRef(null); const epoch = useRef(0);
  useEffect(() => () => { epoch.current++; pending.current?.abort(); }, []);
  if (!supported) return null;
  const change = (key, value) => {
    epoch.current++; pending.current?.abort(); setInput(previous => ({ ...previous, [key]: value }));
    setState({ running: false, result: null, error: null });
  };
  async function calculate(event) {
    event.preventDefault(); const version = ++epoch.current; pending.current?.abort();
    const controller = new AbortController(); pending.current = controller;
    setState({ running: true, result: null, error: null });
    try {
      if (sheets && !input.sheet) throw new Error('Select the exact worksheet before calculating.');
      const request = analysisRequest(input);
      const result = analysisResult(await apiRequest(`/v1/sources/${source.id}/analysis`, { method: 'POST', body: request, signal: controller.signal }), source, request);
      if (version === epoch.current && !controller.signal.aborted) setState({ running: false, result, error: null });
    } catch (error) { if (version === epoch.current && error.name !== 'AbortError') setState({ running: false, result: null, error: error.message }); }
  }
  const result = state.result;
  const numeric = result?.groups.map(row => Number(row.value));
  const scale = numeric?.length ? Math.max(...numeric.map(Math.abs)) : 0;
  const chart = result && numeric.every(Number.isFinite) && scale > 0;
  return <section className="n-panel rounded-xl p-4 space-y-3 min-w-0" data-testid="source-analysis">
    <h3 className="font-display text-xl">Calculate from source cells</h3>
    <p>No AI generation. Decimal results cite the retained source; units and header skips are your explicit choices. Formulas are never executed.</p>
    <form className="grid grid-cols-1 sm:grid-cols-2 gap-3" onSubmit={calculate}>
      {sheets && <label>Worksheet<select aria-label="Analysis worksheet" value={input.sheet} onChange={event => change('sheet',event.target.value)} className="block w-full n-glass p-2">
        <option value="">Select exact worksheet</option>{sheets.map(sheet => <option key={sheet.sheet_id} value={sheet.name}>{sheet.name} ({sheet.state})</option>)}
      </select></label>}
      <label>Value column (1–100)<input aria-label="Analysis value column" type="number" min="1" max="100" step="1" value={input.value} onChange={event => change('value',event.target.value)} className="block w-full n-glass p-2" /></label>
      <label>Group column (optional)<input aria-label="Analysis group column" type="number" min="1" max="100" step="1" value={input.group} onChange={event => change('group',event.target.value)} className="block w-full n-glass p-2" /></label>
      <label>Explicit rows to skip<input aria-label="Analysis row skip" type="number" min="0" max="10" step="1" value={input.skip} onChange={event => change('skip',event.target.value)} className="block w-full n-glass p-2" /></label>
      <label>Operation<select aria-label="Analysis operation" value={input.operation} onChange={event => change('operation',event.target.value)} className="block w-full n-glass p-2">{['sum','mean','min','max','count'].map(value => <option key={value}>{value}</option>)}</select></label>
      <label>Declared unit<input aria-label="Analysis declared unit" maxLength={60} value={input.unit} onChange={event => change('unit',event.target.value)} className="block w-full n-glass p-2" /></label>
      <button type="submit" disabled={state.running} className="n-cta rounded p-2" data-testid="run-source-analysis">{state.running ? 'Calculating…' : 'Calculate exact results'}</button>
    </form>
    {state.error && <p role="alert">{state.error}</p>}
    {result && <div className="space-y-3" data-testid="source-analysis-result">
      <p data-testid="analysis-coverage">Included {result.coverage.included_records}; excluded {result.coverage.excluded_records}; skipped {result.coverage.skipped_records}. {result.worksheet ? `Worksheet: ${result.worksheet.name} (${result.worksheet.state}).` : ''}</p>
      <p>Unit: {result.unit.label || 'none declared'}. {result.numeric_policy}</p>
      <div className="overflow-x-auto"><table className="w-full text-left" data-testid="analysis-exact-table"><thead><tr><th>Group</th><th>Exact value</th><th>Included records</th></tr></thead><tbody>{result.groups.map((row,index) => <tr key={index}><td className="break-all">{row.label}</td><td className="break-all">{row.value}</td><td>{row.included_records}</td></tr>)}</tbody></table></div>
      {chart && <figure><figcaption>Approximate bar positions; exact values are in the table above.</figcaption><svg viewBox={`0 0 600 ${result.groups.length*28+20}`} role="img" aria-label="Source-backed value comparison" className="w-full" data-testid="analysis-bar-chart">
        {result.groups.map((row,index) => { const width = Math.abs(numeric[index])/scale*150; return <g key={index}><title>{`${row.label}: ${row.value}`}</title><text x="0" y={index*28+20} fill="currentColor" fontSize="12">{row.label.slice(0,28)}</text><rect x={numeric[index]<0 ? 400-width : 400} y={index*28+8} width={width} height="16" fill="#2e9bff" /></g>; })}
        <line x1="400" x2="400" y1="0" y2={result.groups.length*28+20} stroke="currentColor" />
      </svg></figure>}
      {!result.groups.length && <p>No included numeric observations; no chart is inferred.</p>}
      <details><summary>Source and derivation evidence</summary><pre className="whitespace-pre-wrap break-all">{JSON.stringify({ document_id: result.document_id, revision: result.revision, original_sha256: result.original_sha256, analysis_sha256: result.analysis_sha256, request: result.request, coverage: result.coverage, included_cell_locators: result.included_cell_locators },null,2)}</pre></details>
    </div>}
  </section>;
}
