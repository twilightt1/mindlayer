"use client";

import { useRef, useState } from "react";
import { importExportFile, type ImportSummary } from "@/lib/api/hub";

const FORMATS = [
  { value: "auto", label: "Auto-detect" },
  { value: "chatgpt", label: "ChatGPT (conversations.json)" },
  { value: "claude", label: "Claude export" },
  { value: "gemini", label: "Gemini Takeout" },
  { value: "copilot", label: "Copilot export" },
  { value: "openclaw", label: "OpenClaw session dump" },
  { value: "generic", label: "Generic JSON / PAM bundle" },
];

const MAX_UPLOAD_BYTES = 20 * 1024 * 1024;

export function ImportDashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [format, setFormat] = useState("auto");
  const [busy, setBusy] = useState(false);
  const [summary, setSummary] = useState<ImportSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleImport() {
    if (!file) return;
    if (file.size > MAX_UPLOAD_BYTES) {
      setError("File exceeds the 20 MiB limit.");
      return;
    }
    setBusy(true);
    setError(null);
    setSummary(null);
    try {
      const result = await importExportFile(file, format);
      setSummary(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Import failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-lg border p-6">
        <h2 className="mb-1 text-lg font-semibold">Import an export file</h2>
        <p className="mb-4 text-sm text-muted-foreground">
          Bring your ChatGPT, Claude, Gemini, Copilot or OpenClaw history into
          your Orivory brain. Duplicates (same source ref) are skipped
          automatically; anything over 10k characters per conversation is
          truncated with a marker.
        </p>

        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Export file (JSON, max 20 MiB)</label>
            <input
              ref={inputRef}
              type="file"
              accept=".json,.txt"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="w-full cursor-pointer rounded-md border bg-transparent p-2 text-sm file:mr-3 file:rounded file:border-0 file:bg-muted file:px-3 file:py-1.5"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">Format</label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              className="w-64 rounded-md border bg-transparent px-3 py-2 text-sm"
            >
              {FORMATS.map((f) => (
                <option key={f.value} value={f.value}>
                  {f.label}
                </option>
              ))}
            </select>
          </div>

          <button
            disabled={!file || busy}
            onClick={() => void handleImport()}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {busy ? "Importing…" : "Import"}
          </button>
        </div>

        {error && (
          <div className="mt-4 rounded-lg border border-red-800 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {summary && (
          <div className="mt-4 rounded-lg border border-green-800 bg-green-950/30 px-4 py-3 text-sm">
            <p className="font-medium text-green-400">Import complete</p>
            <ul className="mt-2 grid grid-cols-2 gap-1 text-sm sm:grid-cols-5">
              <li>parsed: {summary.parsed}</li>
              <li>created: {summary.created}</li>
              <li>duplicates: {summary.skipped_duplicates}</li>
              <li>failed: {summary.failed}</li>
              <li>index issues: {summary.index_failures}</li>
            </ul>
          </div>
        )}
      </section>

      <section className="rounded-lg border p-6 text-sm text-muted-foreground">
        <h3 className="mb-2 font-medium text-foreground">Where to get exports</h3>
        <ul className="list-disc space-y-1 pl-5">
          <li>
            <strong>ChatGPT</strong> — Settings → Data controls → Export data
            (use <code>conversations.json</code> from the zip). Note: the
            &quot;Memory&quot; feature contents are not included.
          </li>
          <li>
            <strong>Claude</strong> — Settings → Privacy → Export data.
          </li>
          <li>
            <strong>Gemini</strong> — Google Takeout (MyActivity.json) or the
            Gemini Conversations export.
          </li>
          <li>
            <strong>OpenRecall</strong> — convert its local SQLite with the
            recipe in <a className="underline" href="https://github.com/twilightt1/orivory/blob/main/docs/API.md">API.md §15</a>.
          </li>
        </ul>
      </section>
    </div>
  );
}
