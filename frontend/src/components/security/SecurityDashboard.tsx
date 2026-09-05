"use client";

import { useCallback, useEffect, useState } from "react";
import {
  fetchAccessLog,
  listAgentClients,
  listErasureReceipts,
  registerAgentClient,
  revokeAgentClient,
  requestErasure,
  type AccessLogItem,
  type AgentClientResponse,
  type ErasureReceiptItem,
} from "@/lib/api/hub";

const ACTION_LABELS: Record<string, string> = {
  mcp_search: "searched",
  mcp_get: "read",
  mcp_list: "listed",
  mcp_add: "created",
  mcp_delete: "deleted",
  mcp_forget: "erased",
};

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

export function SecurityDashboard() {
  const [agents, setAgents] = useState<AgentClientResponse[]>([]);
  const [log, setLog] = useState<AccessLogItem[]>([]);
  const [logTotal, setLogTotal] = useState(0);
  const [receipts, setReceipts] = useState<ErasureReceiptItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newAgentName, setNewAgentName] = useState("");
  const [newAgentScopes, setNewAgentScopes] = useState<string[]>(["memory:read"]);
  const [freshToken, setFreshToken] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [agentRes, logRes, receiptRes] = await Promise.all([
        listAgentClients(),
        fetchAccessLog(undefined, 100),
        listErasureReceipts(20),
      ]);
      setAgents(agentRes.items);
      setLog(logRes.items);
      setLogTotal(logRes.total);
      setReceipts(receiptRes.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load security data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleRegister() {
    if (!newAgentName.trim()) return;
    setError(null);
    try {
      const created = await registerAgentClient(newAgentName.trim(), newAgentScopes);
      setFreshToken(created.token);
      setNewAgentName("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Registration failed");
    }
  }

  async function handleRevoke(id: string) {
    setError(null);
    try {
      await revokeAgentClient(id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Revoke failed");
    }
  }

  return (
    <div className="space-y-8">
      {error && (
        <div className="rounded-lg border border-red-800 bg-red-950/40 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {/* Agent clients */}
      <section>
        <h2 className="mb-1 text-lg font-semibold">Agent clients</h2>
        <p className="mb-4 text-sm text-muted-foreground">
          Scoped tokens any MCP-capable agent uses to reach your memory. Revoking
          takes effect immediately.
        </p>
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <input
            value={newAgentName}
            onChange={(e) => setNewAgentName(e.target.value)}
            placeholder="Agent name (e.g. Claude Desktop)"
            className="w-72 rounded-md border bg-transparent px-3 py-2 text-sm"
          />
          <label className="flex items-center gap-1 text-sm">
            <input
              type="checkbox"
              checked={newAgentScopes.includes("memory:read")}
              onChange={(e) =>
                setNewAgentScopes((s) =>
                  e.target.checked ? Array.from(new Set([...s, "memory:read"])) : s.filter((x) => x !== "memory:read")
                )
              }
            />
            read
          </label>
          <label className="flex items-center gap-1 text-sm">
            <input
              type="checkbox"
              checked={newAgentScopes.includes("memory:write")}
              onChange={(e) =>
                setNewAgentScopes((s) =>
                  e.target.checked ? Array.from(new Set([...s, "memory:write"])) : s.filter((x) => x !== "memory:write")
                )
              }
            />
            write
          </label>
          <button
            onClick={() => void handleRegister()}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
          >
            Register agent
          </button>
        </div>

        {freshToken && (
          <div className="mb-4 rounded-lg border border-amber-800 bg-amber-950/40 px-4 py-3 text-sm">
            <p className="font-medium text-amber-300">
              Copy this token now — it is shown only once.
            </p>
            <code className="mt-2 block break-all rounded bg-black/40 p-2 text-xs">
              {freshToken}
            </code>
            <button
              onClick={() => setFreshToken(null)}
              className="mt-2 text-xs text-muted-foreground underline"
            >
              I saved it
            </button>
          </div>
        )}

        <div className="divide-y rounded-lg border">
          {agents.length === 0 && !loading && (
            <p className="px-4 py-6 text-sm text-muted-foreground">No agent clients yet.</p>
          )}
          {agents.map((a) => (
            <div key={a.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
              <div>
                <p className="font-medium">
                  {a.name}{" "}
                  <span
                    className={`ml-1 rounded px-1.5 py-0.5 text-xs ${
                      a.status === "active"
                        ? "bg-green-950 text-green-400"
                        : "bg-zinc-800 text-zinc-400"
                    }`}
                  >
                    {a.status}
                  </span>
                </p>
                <p className="text-xs text-muted-foreground">
                  scopes: {a.scopes.join(", ")} · last used {fmtDate(a.last_used_at)}
                </p>
              </div>
              {a.status === "active" && (
                <button
                  onClick={() => void handleRevoke(a.id)}
                  className="rounded-md border px-3 py-1.5 text-sm hover:bg-destructive/10"
                >
                  Revoke
                </button>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Access ledger */}
      <section>
        <h2 className="mb-1 text-lg font-semibold">Access ledger</h2>
        <p className="mb-4 text-sm text-muted-foreground">
          Every authorized MCP call, newest first ({logTotal} total). Append-only.
        </p>
        <div className="max-h-96 overflow-y-auto rounded-lg border">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 bg-muted/80 backdrop-blur">
              <tr>
                <th className="px-3 py-2">When</th>
                <th className="px-3 py-2">Agent</th>
                <th className="px-3 py-2">Action</th>
                <th className="px-3 py-2">Memory</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {log.map((entry) => {
                const agent = agents.find((a) => a.id === entry.agent_client_id);
                return (
                  <tr key={entry.id} className="hover:bg-muted/30">
                    <td className="whitespace-nowrap px-3 py-2 text-muted-foreground">
                      {fmtDate(entry.created_at)}
                    </td>
                    <td className="px-3 py-2">{agent?.name ?? "—"}</td>
                    <td className="px-3 py-2">{ACTION_LABELS[entry.action] ?? entry.action}</td>
                    <td className="max-w-56 truncate px-3 py-2 font-mono text-xs">
                      {entry.memory_id ?? "—"}
                    </td>
                  </tr>
                );
              })}
              {log.length === 0 && !loading && (
                <tr>
                  <td colSpan={4} className="px-3 py-6 text-center text-muted-foreground">
                    No accesses recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Erasure receipts */}
      <section>
        <h2 className="mb-1 text-lg font-semibold">Erasure receipts</h2>
        <p className="mb-4 text-sm text-muted-foreground">
          Verified right-to-be-forgotten operations. A receipt proves what was
          erased and whether anything residual remained.
        </p>
        <div className="space-y-2">
          {receipts.length === 0 && !loading && (
            <p className="rounded-lg border px-4 py-6 text-sm text-muted-foreground">
              No erasures yet. Use the MCP <code>forget_memory</code> tool or the
              API to erase memories — every operation is receipted here.
            </p>
          )}
          {receipts.map((r) => {
            const summary = r.detail?.summary;
            const isOpen = expanded === r.id;
            return (
              <div key={r.id} className="rounded-lg border">
                <button
                  className="flex w-full flex-wrap items-center justify-between gap-2 px-4 py-3 text-left"
                  onClick={() => setExpanded(isOpen ? null : r.id)}
                >
                  <div>
                    <p className="font-medium">
                      {r.status === "completed" && "✅ Erased"}
                      {r.status === "completed_with_residual" && "⚠️ Erased with residual"}
                      {r.status === "completed_with_errors" && "❌ Completed with errors"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {fmtDate(r.created_at)} · {summary?.erased ?? "?"} erased, {summary?.skipped ?? "?"} skipped
                    </p>
                  </div>
                  <span className="text-xs text-muted-foreground">{isOpen ? "hide" : "details"}</span>
                </button>
                {isOpen && (
                  <div className="border-t px-4 py-3 text-sm">
                    <pre className="max-h-64 overflow-auto whitespace-pre-wrap break-all rounded bg-black/40 p-2 text-xs">
                      {JSON.stringify(r.detail, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

export { requestErasure };
