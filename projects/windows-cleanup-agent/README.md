# DiskPilot V2 — Windows Disk Investigation & Cleanup Agent

A **local-first Windows disk investigator**, not a one-folder TEMP cleaner. Inspect real files, folder sizes, file types, browser caches, application caches, developer caches, GPU shader caches, and read-only Windows/system storage locations. The chat can start genuine scans, read reports, and explain actions even without Ollama (rule-based fallback); Ollama enhances natural-language analysis.

> **Safety notice:** Experimental project. Scan with your normal Windows account. Back up important files. Cleanup is permanent (does **not** use Recycle Bin) and still requires manual per-file selection and a typed confirmation. There is a small file-swap race between verification and deletion; do not use this tool on adversarial/shared machines. Stop and review any strange path before authorizing.

## What changed in V2

| Feature | What it does |
|---|---|
| Real drive investigation | Scans C: recursively, finds the 30 largest files >=32 MB, largest first-level folders, top file extensions, scan progress, error counts and limits; reads metadata only |
| Cache inventory | Locates actual cache paths for Chrome/Edge/Firefox, Discord, VS Code, Python pip, npm, Radeon/AMD, NVIDIA/Intel shaders, DirectX, CrashDumps and user Temp (only those installed/existing) |
| Report-only storage | Measures Downloads, Ollama model storage, Windows Temp, Windows Update download cache, Windows Installer, Steam shader cache, AMD driver installer extraction if present; **never delete from these paths** |
| Transparent cleanup | Only regular files **at least 7 days old**, only in explicit user-cache allowlist. Blocks symlinks/junctions, executables, scripts, database file patterns and recently changed files; selected-files plan expires after 10 minutes |
| Actual agent actions | Arabic/English commands can start scans, read the cache report, summarize largest files, and explain risk. The LLM cannot delete, use shell, or supply arbitrary paths to any tool |
| Without Ollama | Direct scan commands still work and real measurements can be summarized with deterministic offline responses |
| Lightweight | Python 3.10+ standard library, no pip packages, localhost-only server, no telemetry or cloud upload |

## Run on Windows

1. Install Python 3.10+.
2. Open this folder and double-click `start.bat` or run `py app.py`.
3. Open `http://127.0.0.1:8765` if not launched automatically.
4. Click **افحص C: والكاش**, or type **افحص الملفات والكاش في C:** in the chat. Wait for both background jobs to finish.
5. Open **الكاش والتنظيف** for measured locations and reclaimable *candidates*; choose exact eligible files, review their path and age, optionally run a dry-run, then type `DELETE SELECTED FILES` if you accept **permanent** deletion.

### Optional local AI

Install [Ollama](https://ollama.com/download), then run:

```powershell
ollama pull qwen3.5:4b
# or use a smaller model if you need to conserve RAM
ollama pull qwen3.5:2b
```

If `C:` is already full, **first** move Ollama's model storage by setting the `OLLAMA_MODELS` environment variable to a directory on a different drive (for example `D:\Ollama\Models`), then completely quit/restart Ollama. Existing model files are not automatically moved.

## Safety and limitations

- Scan never opens file contents; it reads directory metadata and file sizes. On inaccessible or linked paths, the reports show warnings; entries may be missed. Drive scan stops after 850,000 files; each cache source after 75,000 entries, 400,000 globally. These limits are explicitly reported.
- The candidate list may cap at 1,200 old files, sorted by size. It is **not** an estimate of everything you can safely remove.
- Files in `%LOCALAPPDATA%\Temp`, browser cache-data subdirectories, GPU shader caches, pip/npm caches, Discord/VS Code cache folders, and CrashDumps are only **eligible for manual review**, not guaranteed safe. Close affected applications first.
- **Never** delete `C:\Windows\Installer` manually; installer packages are required for upgrades and app repair. Windows system caches are **read-only** here. Use **Settings → System → Storage → Cleanup recommendations** or Storage Sense for native Windows cleanups.
- Downloads and cloud file storage, Ollama model blobs, Windows updates, app profiles, cookies, libraries, games, installed programs, Docker and WSL disks are **not eligible for direct deletion**; large files may appear in the read-only drive report and can be managed manually using their respective application tools.
- Model tools are allowlisted: start disk scan; start cache audit; get drive summary; get largest files; get cache overview; get recent activity. No unrestricted shell access.
- Cleanup requires selecting exact candidate IDs, server-side revalidation of path/metadata, a one-use time-limited plan and typed authorization `DELETE SELECTED FILES`. Dry-run requires no confirmation but also consumes the plan. A new plan is required afterwards.
- Audit records (counts, not private file paths) are in `%LOCALAPPDATA%\WindowsCleanupAgent\audit.jsonl`. No source or report data is uploaded to GitHub or remote AI providers.
- This version has been tested in a sandbox and with mocked browser UI/API data. **Actual cache discovery, AI inference and deletion on your Windows device remain unverified**. Do an inspection-only pass first; do not approve deletion until you have reviewed results.

## Development

```powershell
py -m unittest discover -s tests -v
py app.py --no-browser
```

Tests use temporary fixture directories; they do not delete real Windows cache files.

## Practical next acceptance tests on a Windows PC

1. Validate actual `C:` free space matches Windows Storage.
2. Check top large files and cache source paths match actual filesystem paths.
3. Verify cache scan marks Installer and Windows Update as protected and never lists their files as cleanup candidates.
4. Close app(s); dry-run a tiny known test cache file and re-scan before even considering deletion.
5. Verify audit trail, plan expiry, and cancel/error states. If anything is surprising, stop and report an issue.