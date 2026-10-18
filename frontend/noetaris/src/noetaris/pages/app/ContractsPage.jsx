import React, { useState } from "react";
import { contracts } from "../../contracts/registry";
import { PageHeader } from "./OperationsPages";

const tone = {
  VERIFIED_SNAPSHOT: "n-chip-green",
  CONTRACT_READY: "",
  PENDING_BACKEND: "n-chip-amber",
  POST_SNAPSHOT_VERIFY: "n-chip-red",
};

export default function ContractsPage() {
  const [q, setQ] = useState("");
  const list = contracts.filter((c) => (c.path + c.ui).toLowerCase().includes(q.toLowerCase()));
  return (
    <div className="p-4 md:p-8" data-testid="contracts-page">
      <PageHeader title="Developer Contracts" eyebrow="API contract register">
        Every UI seam mapped to its backend operation, owner and readiness. Full spec in /app/memory/API_CONTRACT_REGISTER.md.
      </PageHeader>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter contracts…"
        className="n-glass rounded-xl h-10 px-4 text-sm w-full sm:w-80 mb-4 outline-none" data-testid="contracts-filter-input" />
      <div className="n-glass rounded-2xl overflow-x-auto">
        <table className="w-full text-sm min-w-[640px]">
          <thead>
            <tr className="text-[11px] uppercase tracking-widest text-[color:var(--n-text-subtle)]">
              <th className="text-left py-3 px-4 font-normal">Method</th>
              <th className="text-left px-4 font-normal">Path</th>
              <th className="text-left px-4 font-normal">UI surface</th>
              <th className="text-left px-4 font-normal">Owner</th>
              <th className="text-left px-4 font-normal">Readiness</th>
            </tr>
          </thead>
          <tbody>
            {list.length === 0 && <tr><td colSpan={5} className="py-8 text-center text-sm text-[color:var(--n-text-subtle)]" data-testid="contracts-empty">No contracts match “{q}”.</td></tr>}
            {list.map((c) => (
              <tr key={c.method + c.path} className="border-t border-[color:var(--n-stroke-soft)]">
                <td className="py-2.5 px-4 font-mono text-xs text-[color:var(--n-cyan)]">{c.method}</td>
                <td className="px-4 font-mono text-xs">{c.path}</td>
                <td className="px-4">{c.ui}</td>
                <td className="px-4 text-xs">{c.owner}</td>
                <td className="px-4"><span className={"n-chip text-[10px] " + tone[c.status]}>{c.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
