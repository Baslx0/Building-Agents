"""Local disk analysis and conservative, approval-gated TEMP cleanup.

No model has access to these mutation APIs. The user must explicitly approve
exact snapshot candidates. This is intentionally NOT a generic file deleter.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import os
import heapq
from pathlib import Path
import secrets
import shutil
import stat
import threading
import time
from typing import Callable

from inventory import CacheSource, windows_cache_sources

REPARSE = getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)
DENIED_EXT = {'.exe', '.dll', '.sys', '.msi', '.msp', '.ps1', '.bat', '.cmd', '.vbs', '.reg', '.com', '.db', '.sqlite', '.sqlite3', '.ldb', '.lock', '.wal', '.journal', '.json', '.ini', '.yaml', '.yml'}
MIN_AGE_DAYS = 7
MAX_FILE_BYTES = 1024 * 1024 * 1024
MAX_CANDIDATES = 1200
PLAN_LIFETIME = 600


def bytes_label(value: int) -> str:
    value = float(value)
    for unit in ('B', 'KB', 'MB', 'GB', 'TB', 'PB'):
        if value < 1024 or unit == 'PB':
            return f'{value:.1f} {unit}'
        value /= 1024
    return '?'


def _reparse(path: Path) -> bool:
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & REPARSE)


def _safe_descendant(path: Path, root: Path) -> bool:
    """Fail closed if any component of the path is a junction/reparse/symlink."""
    try:
        root = root.resolve(strict=True)
        if _reparse(root):
            return False
        candidate = Path(os.path.abspath(path))
        if os.path.normcase(str(candidate)) == os.path.normcase(str(root)):
            return False
        # Windows paths are case-insensitive (normcase handles this on Windows).
        relative = Path(os.path.normcase(str(candidate))).relative_to(Path(os.path.normcase(str(root))))
        current = root
        for part in relative.parts:
            current /= part
            if _reparse(current):
                return False
        return candidate.resolve(strict=True).is_relative_to(root)
    except (OSError, ValueError, RuntimeError):
        return False


def current_temp_root() -> Path | None:
    """Only Windows per-user LocalAppData Temp, never system temp."""
    if os.name != 'nt':
        return None
    local = os.environ.get('LOCALAPPDATA')
    if not local:
        return None
    root = Path(local) / 'Temp'
    if not root.exists() or root.is_symlink() or _reparse(root):
        return None
    return root.resolve()


def disk_scan(path: Path, cancel: threading.Event, progress: Callable[[str], None] | None = None) -> dict:
    """Traverse C read-only: top folders, largest files and broad file types.

    Never follows junctions or symlinks. Scan limits are disclosed, never
    silently presented as a complete inventory. Does not read file contents.
    """
    root = path.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Scan path must be a directory')
    usage = shutil.disk_usage(root)
    folders, largest, types = [], [], {}
    errors = skipped = files_seen = scanned = 0
    capped = False
    MAX_ENTRIES = 850000

    def include_file(entry):
        nonlocal files_seen, scanned, capped
        st = entry.stat(follow_symlinks=False)
        files_seen += 1
        scanned += st.st_size
        if files_seen >= MAX_ENTRIES:
            capped = True
        suffix = Path(entry.name).suffix.lower() or '[no extension]'
        types[suffix] = types.get(suffix, 0) + st.st_size
        if st.st_size >= 32 * 1024 ** 2:
            item = (st.st_size, str(entry.path))
            if len(largest) < 40:
                heapq.heappush(largest, item)
            elif item > largest[0]:
                heapq.heapreplace(largest, item)
        return st.st_size

    try:
        with os.scandir(root) as entries:
            children = list(entries)
    except OSError as exc:
        raise ValueError(f'Cannot inspect selected drive: {exc}') from exc
    for entry in children:
        if cancel.is_set() or capped:
            break
        try:
            if entry.is_symlink() or _reparse(Path(entry.path)):
                skipped += 1
                continue
            if entry.is_file(follow_symlinks=False):
                include_file(entry)
                continue
            if not entry.is_dir(follow_symlinks=False):
                continue
        except OSError:
            errors += 1
            continue
        if progress:
            progress(f'{entry.name} · {files_seen:,} files')
        total, pending = 0, [Path(entry.path)]
        while pending and not cancel.is_set() and not capped:
            folder = pending.pop()
            try:
                with os.scandir(folder) as items:
                    for item in items:
                        if cancel.is_set() or capped:
                            break
                        try:
                            if item.is_symlink() or _reparse(Path(item.path)):
                                skipped += 1
                                continue
                            if item.is_dir(follow_symlinks=False):
                                pending.append(Path(item.path))
                            elif item.is_file(follow_symlinks=False):
                                total += include_file(item)
                        except OSError:
                            errors += 1
            except OSError:
                errors += 1
        folders.append({'name': entry.name, 'bytes': total})
    if cancel.is_set():
        return {'cancelled': True, 'folders': folders}
    return {'path': str(root), 'total': usage.total, 'used': usage.used, 'free': usage.free,
            'folders': sorted(folders, key=lambda x: x['bytes'], reverse=True)[:30],
            'largest_files': [{'bytes': n, 'path': p} for n, p in sorted(largest, reverse=True)[:30]],
            'file_types': [{'extension': ext, 'bytes': n} for ext, n in sorted(types.items(), key=lambda x: x[1], reverse=True)[:12]],
            'scanned_bytes': scanned, 'files_seen': files_seen,
            'truncated': capped, 'errors': errors, 'skipped_links': skipped,
            'scanned_at': datetime.now(timezone.utc).isoformat()}


@dataclass(frozen=True)
class Candidate:
    id: str
    path: str
    bytes: int
    mtime_ns: int
    inode: int
    device: int
    age_days: int
    category: str = "user-temp"
    risk: str = "low"

    def public(self) -> dict:
        return {'id': self.id, 'path': self.path, 'bytes': self.bytes, 'age_days': self.age_days, 'category': self.category, 'risk': self.risk}


class CleanupEngine:
    """Allowlisted caches only. Injectable roots for isolated fixture testing."""

    def __init__(self, temp_root: Path | None = None, sources: list[CacheSource] | None = None):
        self.root = temp_root if temp_root is not None else current_temp_root()
        self.sources = (sources if sources is not None else
                        ([CacheSource('user-temp', 'Test Temp', temp_root, 'Temporary', True, 'low', 'Fixture')]
                         if temp_root is not None else windows_cache_sources() ))
        self.candidates: dict[str, Candidate] = {}
        self.plans: dict[str, dict] = {}
        self.lock = threading.RLock()
        self._testing = temp_root is not None or sources is not None

    def _snapshot(self, path: Path, now: float | None = None) -> Candidate | None:
        # A source is controlled by Python's explicit local allowlist, never LLM input.
        source = next((src for src in self.sources if src.cleanable and _safe_descendant(path, src.path)), None)
        if source is None:
            return None
        try:
            st = path.lstat()
            if not stat.S_ISREG(st.st_mode) or _reparse(path):
                return None
            age = (time.time() if now is None else now) - st.st_mtime
            if age < MIN_AGE_DAYS * 86400 or age < 0:
                return None
            if st.st_size > MAX_FILE_BYTES or path.suffix.lower() in DENIED_EXT:
                return None
            return Candidate(secrets.token_hex(8), str(path), st.st_size,
                             st.st_mtime_ns, st.st_ino, st.st_dev, int(age // 86400), source.key, source.risk)
        except OSError:
            return None

    def discover(self, progress: Callable[[str], None] | None = None) -> dict:
        """Inventory supported locations and collect eligible files for approval.

        Both read-only and cleanable sources are measured. Measurements are
        bounded; truncated sources are explicitly marked incomplete.
        """
        with self.lock:
            if not self._testing and os.name == 'nt':
                self.sources = windows_cache_sources()  # discover new browser profiles
            self.candidates.clear()
            self.plans.clear()
            rows, total_eligible = [], 0
            visited_total = 0
            for source in self.sources:
                if progress:
                    progress(source.label)
                if not source.path.is_dir() or _reparse(source.path):
                    continue
                count = bytes_found = eligible = eligible_bytes = skipped = errors = visited = 0
                pending = [source.path]
                # Per-source limit ensures one massive browser cache doesn't
                # hide all other categories. Never follow links/reparse points.
                while pending and visited < 75000 and visited_total < 400000:
                    folder = pending.pop()
                    try:
                        with os.scandir(folder) as entries:
                            for entry in entries:
                                if visited >= 75000 or visited_total >= 400000:
                                    break
                                visited += 1
                                visited_total += 1
                                p = Path(entry.path)
                                try:
                                    if _reparse(p):
                                        skipped += 1
                                    elif entry.is_dir(follow_symlinks=False):
                                        pending.append(p)
                                    elif entry.is_file(follow_symlinks=False):
                                        st = entry.stat(follow_symlinks=False)
                                        count += 1
                                        bytes_found += st.st_size
                                        if source.cleanable and len(self.candidates) < MAX_CANDIDATES:
                                            item = self._snapshot(p)
                                            if item is not None:
                                                self.candidates[item.id] = item
                                                eligible += 1
                                                eligible_bytes += item.bytes
                                    else:
                                        skipped += 1
                                except OSError:
                                    errors += 1
                    except OSError:
                        errors += 1
                item = source.public()
                item.update(bytes=bytes_found, file_count=count,
                            eligible_bytes=eligible_bytes, eligible_count=eligible,
                            skipped=skipped, errors=errors,
                            limited=bool(pending) or visited >= 75000 or visited_total >= 400000 or
                            (source.cleanable and len(self.candidates) >= MAX_CANDIDATES))
                rows.append(item)
                total_eligible += eligible_bytes
            items = sorted(self.candidates.values(), key=lambda x: x.bytes, reverse=True)
            rows.sort(key=lambda x: x['bytes'], reverse=True)
            return {'available': bool(rows), 'sources': rows,
                    'root': str(self.root or ''), 'items': [x.public() for x in items],
                    'total_bytes': total_eligible, 'inspected_bytes': sum(s['bytes'] for s in rows),
                    'skipped': sum(s['skipped'] for s in rows),
                    'errors': sum(s['errors'] for s in rows),
                    'limited': any(s['limited'] for s in rows),
                    'policy': 'Known cache locations only. Only selected regular files >=7 days old in explicitly allowlisted user cache directories can be deleted.'}

    def make_plan(self, ids: list[str]) -> dict:
        with self.lock:
            if not isinstance(ids, list) or len(ids) == 0 or len(ids) > MAX_CANDIDATES or len(set(ids)) != len(ids):
                raise ValueError('Choose one or more unique candidates')
            selected = []
            for key in ids:
                candidate = self.candidates.get(key)
                if not candidate:
                    raise ValueError('Invalid candidate ID. Refresh recommendations.')
                if not self._matches(candidate):
                    raise ValueError('Files changed. Refresh recommendations.')
                selected.append(candidate)
            self.plans.clear()
            plan_id = secrets.token_urlsafe(24)
            self.plans[plan_id] = {'ids': tuple(ids), 'created': time.monotonic()}
            return {'plan_id': plan_id, 'expires_in_seconds': PLAN_LIFETIME,
                    'items': [x.public() for x in selected], 'total_bytes': sum(x.bytes for x in selected),
                    'confirmation': 'DELETE SELECTED FILES', 'warning': 'Permanent deletion. Cannot be undone. Close affected apps first.'}

    def _matches(self, original: Candidate) -> bool:
        latest = self._snapshot(Path(original.path))
        return latest is not None and (latest.bytes, latest.mtime_ns, latest.inode, latest.device) == (
            original.bytes, original.mtime_ns, original.inode, original.device)

    def execute(self, plan_id: str, confirm: str, dry_run: bool = False) -> dict:
        with self.lock:
            plan = self.plans.pop(plan_id, None)  # single use, even on error
            if not plan or time.monotonic() - plan['created'] > PLAN_LIFETIME:
                raise ValueError('Plan missing or expired. Create a new plan.')
            if not dry_run and confirm != 'DELETE SELECTED FILES':
                raise ValueError('Type DELETE SELECTED FILES to authorize deletion.')
            # This code path is only available on Windows in production.
            if not self._testing and os.name != 'nt':
                raise ValueError('Cleanup execution is only enabled on Windows')
            results = []
            for key in plan['ids']:
                original = self.candidates.get(key)
                if not original or not self._matches(original):
                    results.append({'id': key, 'status': 'skipped', 'reason': 'Changed or no longer eligible'})
                    continue
                if dry_run:
                    results.append({'id': key, 'status': 'dry_run', 'bytes': original.bytes})
                    continue
                try:
                    # unlink only an eligible regular file. Never recursively delete directories.
                    Path(original.path).unlink()
                    results.append({'id': key, 'status': 'deleted', 'bytes': original.bytes})
                    self.candidates.pop(key, None)
                except OSError as exc:
                    results.append({'id': key, 'status': 'failed', 'reason': type(exc).__name__})
            return {'results': results, 'freed_estimate': sum(i.get('bytes', 0) for i in results if i['status'] == 'deleted'),
                    'dry_run': dry_run}