"""Dependency-free, loopback-only local dashboard for Windows Cleanup Agent."""
from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import threading
import webbrowser
import argparse

from core import CleanupEngine, disk_scan
from agent import DEFAULT_MODEL, installed_models, chat

HERE = Path(__file__).resolve().parent
STATIC = HERE / 'static'
BIND_HOST = '127.0.0.1'
BIND_PORT = 8765


class State:
    def __init__(self):
        self.lock = threading.RLock()
        self.csrf = secrets.token_urlsafe(32)
        self.scan = {'status': 'idle', 'progress': '', 'result': None}
        self.cancel_scan = threading.Event()
        self.cleaner = CleanupEngine()
        self.candidates = None
        self.cache = {'status': 'idle', 'progress': '', 'result': None}
        self.model = DEFAULT_MODEL
        # Never write reports or personal filenames into the GitHub repository.
        self.audit_path = Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'WindowsCleanupAgent' / 'audit.jsonl'

    def activity(self, kind: str, extra: dict):
        record = {'at': datetime.now(timezone.utc).isoformat(), 'event': kind, **extra}
        try:
            self.audit_path.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_path.open('a', encoding='utf8') as file:
                file.write(json.dumps(record, ensure_ascii=False) + '\n')
        except OSError:
            pass

    def history(self) -> list[dict]:
        try:
            with self.audit_path.open('r', encoding='utf8') as file:
                return [json.loads(line) for line in file.readlines()[-40:] if line.strip()][-25:][::-1]
        except (OSError, ValueError):
            return []

    def start_scan(self, requested_path: str = '') -> dict:
        with self.lock:
            if self.scan['status'] == 'running':
                raise ValueError('A scan is already running')
            # Scan only the system drive; no arbitrary filesystem traversal via API.
            system_drive = Path(os.environ.get('SystemDrive', 'C:') + '\\') if os.name == 'nt' else Path.home()
            if requested_path and os.path.normcase(str(Path(requested_path).resolve())) != os.path.normcase(str(system_drive.resolve())):
                raise ValueError('Only your Windows system drive can be scanned')
            self.cancel_scan = threading.Event()
            self.scan = {'status': 'running', 'progress': 'Starting...', 'result': None}

        def worker():
            try:
                def update(folder):
                    with self.lock:
                        self.scan['progress'] = folder
                result = disk_scan(system_drive, self.cancel_scan, update)
                with self.lock:
                    self.scan.update(status='cancelled' if result.get('cancelled') else 'complete', result=result,
                                     progress='Finished' if not result.get('cancelled') else 'Cancelled')
                if not result.get('cancelled'):
                    self.activity('scan', {'path': str(system_drive), 'warnings': result['errors'],
                                           'files_seen': result.get('files_seen', 0),
                                           'truncated': result.get('truncated', False)})
            except Exception as exc:
                with self.lock:
                    self.scan.update(status='error', progress=f'{type(exc).__name__}: {exc}')
        threading.Thread(target=worker, daemon=True).start()
        return {'status': 'running'}

    def start_cache_scan(self) -> dict:
        with self.lock:
            if self.cache['status'] == 'running':
                return {'status': 'running', 'progress': self.cache['progress']}
            self.cache = {'status': 'running', 'progress': 'Locating known caches...', 'result': None}
            self.candidates = None

        def worker():
            try:
                def update(source):
                    with self.lock:
                        self.cache['progress'] = source
                # Windows-only real cache discovery; fixture tests use engine directly.
                report = self.cleaner.discover(update)
                with self.lock:
                    self.candidates = report
                    self.cache = {'status': 'complete', 'progress': 'Finished', 'result': report}
                self.activity('cache_audit', {'sources': len(report['sources']),
                                               'eligible_bytes': report['total_bytes'],
                                               'limited': report['limited']})
            except Exception as exc:
                with self.lock:
                    self.cache.update(status='error', progress=f'{type(exc).__name__}: {exc}')
        threading.Thread(target=worker, daemon=True).start()
        return {'status': 'running'}

    def tool_summary(self, name: str) -> dict:
        # All callbacks are controlled application functions; no model-supplied
        # paths, commands, file names or deletion IDs are accepted here.
        if name == 'start_disk_scan':
            try:
                return self.start_scan()
            except ValueError as exc:
                return {'status': 'running', 'message': str(exc)}
        if name == 'start_cache_audit':
            return self.start_cache_scan()
        with self.lock:
            if name == 'get_disk_summary':
                r = self.scan['result']
                return {'status': self.scan['status'], 'progress': self.scan['progress'],
                        'result': ({'total': r['total'], 'free': r['free'], 'used': r['used'],
                                    'folders': r.get('folders', [])[:12], 'files_seen': r.get('files_seen', 0),
                                    'errors': r['errors'], 'truncated': r.get('truncated', False)} if r and 'total' in r else None)}
            if name == 'get_largest_files':
                r = self.scan['result'] or {}
                return {'status': self.scan['status'], 'largest_files': r.get('largest_files', [])[:20],
                        'file_types': r.get('file_types', [])[:10],
                        'complete': self.scan['status'] == 'complete' and not r.get('truncated') and not r.get('errors')}
            if name in ('get_temp_candidates', 'get_cache_overview'):
                r = self.candidates or {}
                return {'status': self.cache['status'], 'progress': self.cache['progress'],
                        'source_count': len(r.get('sources', [])), 'total_eligible_bytes': r.get('total_bytes', 0),
                        'inspected_bytes': r.get('inspected_bytes', 0),
                        'limited': r.get('limited', False),
                        'sources': [{k: s[k] for k in ('label', 'category', 'path', 'bytes', 'eligible_bytes',
                                    'cleanable', 'risk', 'limited', 'note')}
                                    for s in r.get('sources', [])[:18]]}
            if name == 'get_activity':
                return {'events': [{k: v for k, v in record.items() if k != 'path'} for record in self.history()[:8]]}
            return {'error': 'Tool not permitted'}


STATE = State()


class Handler(BaseHTTPRequestHandler):
    server_version = 'DiskPilot/2.0'

    def log_message(self, fmt, *args):
        # Do not spam user's terminal with chat text or file names.
        pass

    def _origin_ok(self) -> bool:
        host = self.headers.get('Host', '')
        if host not in (f'{BIND_HOST}:{BIND_PORT}', f'localhost:{BIND_PORT}'):
            return False
        origin = self.headers.get('Origin')
        return origin is None or origin in (f'http://{BIND_HOST}:{BIND_PORT}', f'http://localhost:{BIND_PORT}')

    def _send(self, code: int, data: dict):
        raw = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'none'")
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _static(self, file: str, mime: str):
        data = (STATIC / file).read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; connect-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; form-action 'none'")
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self._origin_ok():
            return self._send(403, {'error': 'Untrusted host/origin'})
        if self.path in ('/', '/index.html'):
            return self._static('index.html', 'text/html; charset=utf-8')
        if self.path == '/style.css':
            return self._static('style.css', 'text/css; charset=utf-8')
        if self.path == '/ui.js':
            return self._static('ui.js', 'text/javascript; charset=utf-8')
        if self.path == '/api/status':
            return self._send(200, {'csrf': STATE.csrf, 'model': STATE.model, 'models': installed_models(),
                      'platform': os.name, 'temp_available': STATE.cleaner.root is not None,
                      'scan': STATE.scan, 'cache': STATE.cache})
        if self.path == '/api/scan':
            with STATE.lock:
                return self._send(200, dict(STATE.scan))
        if self.path == '/api/candidates':
            return self._send(200, STATE.candidates or {'available': False, 'items': [], 'sources': [], 'reason': 'Run the cache audit first'})
        if self.path == '/api/caches':
            with STATE.lock:
                return self._send(200, dict(STATE.cache))
        if self.path == '/api/activity':
            return self._send(200, {'entries': STATE.history()})
        self._send(404, {'error': 'Not found'})

    def do_POST(self):
        if not self._origin_ok() or self.headers.get('X-Local-Token') != STATE.csrf:
            return self._send(403, {'error': 'Forbidden; missing local session token'})
        length = int(self.headers.get('Content-Length', 0))
        if length < 0 or length > 24_000:
            return self._send(413, {'error': 'Request too large'})
        try:
            body = json.loads(self.rfile.read(length) or b'{}')
            if not isinstance(body, dict):
                raise ValueError('Expected JSON object')
            if self.path == '/api/scan/start':
                return self._send(200, STATE.start_scan())
            if self.path == '/api/scan/cancel':
                STATE.cancel_scan.set()
                return self._send(200, {'cancel_requested': True})
            if self.path in ('/api/caches/start', '/api/candidates/refresh'):
                return self._send(200, STATE.start_cache_scan())
            if self.path == '/api/plan':
                return self._send(200, STATE.cleaner.make_plan(body.get('ids', [])))
            if self.path == '/api/execute':
                result = STATE.cleaner.execute(body.get('plan_id', ''), body.get('confirm', ''), bool(body.get('dry_run', False)))
                if not result['dry_run']:
                    STATE.activity('cleanup', {'deleted': sum(x['status'] == 'deleted' for x in result['results']),
                                               'freed_estimate': result['freed_estimate'],
                                               'failed': sum(x['status'] != 'deleted' for x in result['results'])})
                    STATE.candidates = None
                    STATE.cache = {'status': 'idle', 'progress': 'Re-run cache audit after cleanup', 'result': None}
                return self._send(200, result)
            if self.path == '/api/model':
                model = body.get('model', '')
                if not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9_.:/-]{1,80}', model):
                    raise ValueError('Invalid model name')
                if model not in installed_models():
                    raise ValueError('Model is not installed in Ollama')
                STATE.model = model
                return self._send(200, {'model': model})
            if self.path == '/api/chat':
                message = body.get('message', '')
                history = body.get('history', [])
                if not isinstance(message, str) or not message.strip() or len(message) > 2000:
                    raise ValueError('Enter a message of 1 to 2000 characters')
                if not isinstance(history, list):
                    raise ValueError('Invalid chat history')
                return self._send(200, chat(message, history[-12:], STATE.model, STATE.tool_summary))
            return self._send(404, {'error': 'Not found'})
        except (ValueError, TypeError) as exc:
            return self._send(400, {'error': str(exc)})
        except Exception as exc:
            return self._send(500, {'error': f'{type(exc).__name__}: {exc}'})


def main():
    parser = argparse.ArgumentParser(description='Windows Cleanup Agent — local dashboard')
    parser.add_argument('--no-browser', action='store_true', help='Do not open a browser automatically')
    args = parser.parse_args()
    server = ThreadingHTTPServer((BIND_HOST, BIND_PORT), Handler)
    print(f'Windows Cleanup Agent: http://{BIND_HOST}:{BIND_PORT}')
    print('Local access only. No files will be deleted without explicit review and approval.')
    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(f'http://{BIND_HOST}:{BIND_PORT}')).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nDashboard stopped')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()