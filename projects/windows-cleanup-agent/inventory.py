"""Auditable Windows cache registry: exact known locations, never arbitrary AI paths.

Sources may be measured, while only specifically allowlisted sources may be
cleaned after the user explicitly selects individual files and authorizes.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import stat

REPARSE = getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)


@dataclass(frozen=True)
class CacheSource:
    key: str
    label: str
    path: Path
    category: str
    cleanable: bool
    risk: str
    note: str

    def public(self) -> dict:
        return {'key': self.key, 'label': self.label, 'path': str(self.path),
                'category': self.category, 'cleanable': self.cleanable,
                'risk': self.risk, 'note': self.note}


def _genuine_dir(path: Path) -> bool:
    try:
        info = path.lstat()
        return stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode) and not (getattr(info, 'st_file_attributes', 0) & REPARSE)
    except OSError:
        return False


def windows_cache_sources(environ: dict | None = None, home: Path | None = None) -> list[CacheSource]:
    """Generate explicit catalog from user profile paths, not model-supplied paths.

    Exact cache subdirectories only. Chrome/Edge profiles are discovered at
    most one directory below User Data; we never scan profile databases.
    """
    env = os.environ if environ is None else environ
    user = Path.home() if home is None else home
    local = Path(env.get('LOCALAPPDATA') or user / 'AppData' / 'Local')
    roaming = Path(env.get('APPDATA') or user / 'AppData' / 'Roaming')
    win = Path(env.get('WINDIR') or 'C:/Windows')
    sources: list[CacheSource] = []
    seen: set[str] = set()

    def put(key: str, label: str, path: Path, category: str, clean: bool, risk: str, note: str):
        if not _genuine_dir(path):
            return
        # Do not follow any ancestor junction (path may be nested inside a link).
        node = path
        try:
            while node != node.parent:
                check = node.lstat()
                if stat.S_ISLNK(check.st_mode) or bool(getattr(check, 'st_file_attributes', 0) & REPARSE):
                    return
                node = node.parent
        except OSError:
            return
        canonical = os.path.normcase(str(path.resolve()))
        if canonical in seen:
            return
        seen.add(canonical)
        sources.append(CacheSource(key, label, path.resolve(), category, clean, risk, note))

    put('user-temp', 'User temporary files', local / 'Temp', 'Temporary', True, 'low',
        'Old temporary files; active or recent files are excluded.')
    put('crash-dumps', 'App crash dumps', local / 'CrashDumps', 'Diagnostics', True, 'low',
        'Old crash logs; deleting them loses diagnostic history.')
    put('dx-shaders', 'DirectX shader cache', local / 'D3DSCache', 'GPU cache', True, 'medium',
        'Shaders are rebuilt; graphics apps may initially load slower.')
    for cache_name in ('DxCache', 'DxcCache', 'Dx9Cache', 'GLCache', 'VkCache', 'OglpCache'):
        put(f'amd-{cache_name.lower()}', f'AMD {cache_name}', local / 'AMD' / cache_name,
            'GPU cache', True, 'medium',
            'Radeon shader cache; close games and graphics apps. May cause temporary shader recompilation/stutter.')
    put('intel-shaders', 'Intel shader cache', local / 'Intel' / 'ShaderCache', 'GPU cache', True, 'medium',
        'Cache may rebuild; close games and graphics apps.')
    put('nvidia-dx', 'NVIDIA DX cache', local / 'NVIDIA' / 'DXCache', 'GPU cache', True, 'medium',
        'Rebuilt by GPU driver; close games and graphics apps first.')
    put('nvidia-gl', 'NVIDIA GL cache', local / 'NVIDIA' / 'GLCache', 'GPU cache', True, 'medium',
        'Rebuilt by GPU driver; close games and graphics apps first.')
    put('pip', 'Python pip cache', local / 'pip' / 'Cache', 'Developer cache', True, 'low',
        'Pip downloads will be cached again when needed.')
    put('npm', 'Node npm cache', local / 'npm' / '_cacache', 'Developer cache', True, 'medium',
        'Npm cache will be rebuilt; avoid cleaning during npm installs.')
    put('yarn', 'Yarn package cache', local / 'Yarn' / 'Cache', 'Developer cache', False, 'medium',
        'Check Yarn configuration before clearing its cache.')
    put('vscode-cache', 'VS Code cache', roaming / 'Code' / 'Cache', 'App cache', True, 'medium',
        'Close VS Code first; interface cache is regenerated.')
    put('vscode-codecache', 'VS Code code cache', roaming / 'Code' / 'Code Cache', 'App cache', True, 'medium',
        'Close VS Code before clearing.')
    put('discord-cache', 'Discord cache', roaming / 'discord' / 'Cache', 'App cache', True, 'medium',
        'Close Discord; attachments and cache entries may re-download.')
    put('discord-codecache', 'Discord code cache', roaming / 'discord' / 'Code Cache', 'App cache', True, 'medium',
        'Close Discord before cleaning.')
    put('discord-gpu', 'Discord GPU cache', roaming / 'discord' / 'GPUCache', 'App cache', True, 'medium',
        'Close Discord before cleaning.')

    for browser, base in (('Chrome', local / 'Google' / 'Chrome' / 'User Data'),
                          ('Edge', local / 'Microsoft' / 'Edge' / 'User Data')):
        if not _genuine_dir(base):
            continue
        try:
            profiles = sorted((p for p in base.iterdir() if p.name == 'Default' or p.name.startswith('Profile ')),
                              key=lambda p: p.name)[:12]
        except OSError:
            profiles = []
        for profile in profiles:
            if not _genuine_dir(profile):
                continue
            for tail, suffix in ((('Cache', 'Cache_Data'), 'HTTP cache'),
                                 (('Code Cache', 'js'), 'script cache'),
                                 (('GPUCache',), 'GPU cache')):
                slug = ''.join(ch.lower() if ch.isalnum() else '-' for ch in profile.name)
                put(f'{browser.lower()}-{slug}-{suffix.replace(" ", "-").lower()}',
                    f'{browser} {profile.name} {suffix}', profile.joinpath(*tail),
                    'Browser cache', True, 'medium',
                    f'Close {browser} first. Cached assets will download again; browser profiles and cookies are never selected.')

    firefox = roaming / 'Mozilla' / 'Firefox' / 'Profiles'
    if _genuine_dir(firefox):
        try:
            profiles = sorted(firefox.iterdir(), key=lambda x: x.name)[:12]
        except OSError:
            profiles = []
        for profile in profiles:
            # Firefox disk cache normally resides in LocalAppData, not Roaming.
            cached = local / 'Mozilla' / 'Firefox' / 'Profiles' / profile.name / 'cache2' / 'entries'
            put(f'firefox-{profile.name}', f'Firefox {profile.name} cache', cached,
                'Browser cache', True, 'medium',
                'Close Firefox; browser session and account databases are not selected.')

    # Report-only roots are never eligible for deletion from DiskPilot.
    put('downloads', 'Downloads (review only)', user / 'Downloads', 'Personal files', False, 'high',
        'Review manually; downloaded files may be important. Never auto-delete.')
    put('ollama-models', 'Ollama models (review only)', Path(env.get('OLLAMA_MODELS') or user / '.ollama' / 'models'),
        'AI models', False, 'high', 'Move model storage to another drive or use Ollama commands; never delete model blobs.')
    put('windows-temp', 'Windows system Temp (review only)', win / 'Temp', 'System cache', False, 'high',
        'Use Windows Storage Sense or Disk Cleanup; do not delete manually from this app.')
    put('update-downloads', 'Windows Update downloads (review only)', win / 'SoftwareDistribution' / 'Download',
        'System cache', False, 'high', 'Use Windows Cleanup recommendations; avoid disrupting updates.')
    # Steam shadercache can be large and is managed by Steam itself.
    program_x86 = Path(env.get('ProgramFiles(x86)') or 'C:/Program Files (x86)')
    put('steam-shaders', 'Steam shader pre-cache (review only)', program_x86 / 'Steam' / 'steamapps' / 'shadercache',
        'Game cache', False, 'high', 'Steam manages this location. Use Steam storage/shader settings, not direct deletion.')
    put('amd-installers', 'AMD extracted installers (review only)',
        Path(env.get('SystemDrive') or 'C:') / 'AMD', 'Driver installers', False, 'high',
        'Review old driver installers manually after checking rollback/reinstall needs.')
    put('installer-cache', 'Windows Installer cache (protected)', win / 'Installer', 'System protected', False, 'critical',
        'DO NOT DELETE: needed for app repair, upgrade and uninstall.')
    # No blanket AppData, Packages, Program Files, or Windows tree cleaners.
    return sources