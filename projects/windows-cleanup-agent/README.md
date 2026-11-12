# DiskPilot — Windows Cleanup Agent

A lightweight, **local-first** Windows disk analyzer with a chat dashboard, Ollama model selection, human-reviewed TEMP file recommendations, and an explicit one-time deletion approval process.

> **Security scope:** An experimental personal tool. Review the source code and back up important data before enabling cleanup. File deletion is irreversible. The conservative allowlist reduces risk but no filesystem cleaner can guarantee against every race condition, locked file, or application-specific dependency.

## Quick start (Windows 10 / 11)

1. Install **Python 3.10+** and [Ollama](https://ollama.com/download).
2. Open PowerShell inside `projects/windows-cleanup-agent`.
3. Optional for AI chat (requires several GB free on **the disk where Ollama stores models**):

   ```powershell
   ollama pull qwen3.5:4b
   # Or, for a lower-resource model:
   ollama pull qwen3.5:2b
   ```

4. Start the dashboard (no `pip install`, no npm, no frameworks):

   ```powershell
   py app.py
   ```

5. Visit **http://127.0.0.1:8765** (opens automatically), click **افحص القرص C:**, and review the findings. The dashboard still works without Ollama; only the chat needs a model.

### What each stage includes

| Stage | Delivered in this project |
|---|---|
| V1 · Analyze | Read-only disk usage inventory, largest folders, errors and cancel |
| V2 · Recommend | Finds eligible files in **your own** `%LOCALAPPDATA%\Temp` only; no guesses about other file safety |
| V3 · Review & approve | Exact path/size list, snapshot validation, 10-minute one-use plan, typed confirmation |
| V4 · Execute & audit | Individually rechecks files; removes approved regular files, no recursive folder deletion, local audit log, dry run |
| V5 · Local AI | Ollama Qwen 3.5 4B default; choose installed 2B or other; bounded read-only tool calls, no model-write capability |

## Safe cleanup rules

- The candidate search only allows existing regular files within `%LOCALAPPDATA%\Temp` belonging to the current user; **never** `C:\Windows`, `Program Files`, `Downloads`, Desktop, Documents, system temp, or another user's folders.
- Skip junctions, symbolic links, reparse points, files younger than **7 days**, files over **250 MB**, and executable/install/script types (`.exe`, `.dll`, `.sys`, `.msi`, etc.).
- At most 500 candidates per search; at most 15,000 temp entries inspected, to avoid unbounded resource use.
- Approval requires selecting specific candidate IDs → server-side snapshot recheck → preview → typing **`DELETE TEMP FILES`** → one-time action (expires in 10 minutes). This is permanent deletion; not Recycle Bin.
- The app checks file size, modification time, device, inode and allowed path immediately before each unlink. **There remains a small TOCTOU race window**, so do not run this on shared or adversarial systems.
- AI cannot call deletion, PowerShell, filesystem writing, arbitrary HTTP endpoints, or execute arbitrary commands. Only three **read-only** tools are exposed to the model: disk summary, candidate summary, and activity summary.
- The backend binds **127.0.0.1 only**, rejects foreign Host/Origin headers, and requires a local session token for POSTs.
- Audit entries (counts, not full deleted paths) are local in `%LOCALAPPDATA%\WindowsCleanupAgent\audit.jsonl`. Chat history is held in the browser tab memory, not written to disk or to GitHub.
- No cloud API, telemetry, dependencies, or external CDN. Ollama is queried on localhost only.

## Controls

- **Overview:** Start/cancel C: scan and view largest folders. System files may be inaccessible and reported sizes incomplete.
- **Cleanup:** Discover old TEMP files, select precisely, preview, dry-run, then confirm permanent deletion.
- **Activity:** Local scan/cleanup log.
- **Settings:** Choose an installed Ollama model.
- **Chat:** Ask in Arabic or English. A constrained agent may request only read-only local summaries.

## Development & tests

```powershell
py -m unittest discover -s tests -v
py app.py --no-browser
```

Requires no admin access. Run under your regular user account. For large drives a full recursive scan may take a long time; you can cancel it. Disk scanning and Temp candidate scan are synchronous background-thread operations in the local server.

**Planned improvements:** Windows API handle-based unlink for stronger race resistance; more detailed progress and per-category cleaners implemented through official Windows mechanisms; benchmark the model on Arabic tool-calling cases; signed desktop packaging.