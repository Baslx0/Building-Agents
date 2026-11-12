# Windows Cleanup Agent

A local-first, approval-gated Windows disk cleanup project built while learning Python agents.

## V1: Disk Analyzer (read-only)

The first milestone inventories disk usage. It **does not delete, move, or modify any files** and does not send file paths or scan results to GitHub or an AI model.

- Shows total, used, and free disk space.
- Scans immediate folders under a selected drive/folder and estimates their recursive sizes.
- Lists the largest folders first.
- Skips directory junctions/reparse points and symbolic links to avoid loops.
- Reports scan errors and inaccessible items; estimates can therefore be incomplete.

## Run locally (Windows)

Requires Python 3.10+; no third-party packages.

```powershell
cd projects/windows-cleanup-agent
python analyzer.py --path C:\ --top 10
```

For a quicker initial test:

```powershell
python analyzer.py --path "$env:USERPROFILE\Downloads" --top 5
```

Scanning an entire C: drive can take a while. No administrator permissions are required; inaccessible files are skipped.

**Privacy:** The report prints to your own terminal only. Avoid sharing reports containing personal folder names unless you review them first.

## Roadmap

1. **V1 — Analyze:** read-only drive and folder inventory.
2. **V2 — Recommend:** classify candidate cache/temp files with evidence and risk levels, never assume a file is disposable based only on its name.
3. **V3 — Approve:** display an explicit operation plan with exact paths, sizes, exclusions, and per-group approval.
4. **V4 — Execute safely:** scoped allowlist, path revalidation, dry-run, reversible actions where possible, logs, and verification.
5. **V5 — Optional Ollama:** natural-language explanations, with the LLM unable to directly execute shell commands or deletions.

Never automatically delete Windows, Program Files, application data, personal files, restore points, or unknown files.
