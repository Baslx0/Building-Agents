"""Fixture-only inventory tests. Never scan or delete an actual computer."""
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from inventory import CacheSource, windows_cache_sources
from core import CleanupEngine, disk_scan


class TestInventory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def add_old_file(self, root: Path, name: str, data=b'old'):
        root.mkdir(parents=True, exist_ok=True)
        f = root / name
        f.write_bytes(data)
        ago = time.time() - 15 * 86400
        os.utime(f, (ago, ago))
        return f

    def test_cache_inventory_and_protected_cannot_plan(self):
        good = self.base / 'Cache'
        protected = self.base / 'Installer'
        target = self.add_old_file(good, 'cache.bin', b'A' * 32)
        important = self.add_old_file(protected, 'keep.msi', b'B' * 80)
        sources = [CacheSource('cache', 'Test cache', good, 'Cache', True, 'low', 'Test'),
                   CacheSource('installer', 'Protected', protected, 'System', False, 'critical', 'Never')]
        cleaner = CleanupEngine(sources=sources)
        result = cleaner.discover()
        self.assertEqual(result['inspected_bytes'], 112)
        self.assertEqual(result['total_bytes'], 32)
        self.assertEqual(len(result['items']), 1)
        self.assertEqual(len(result['sources']), 2)
        self.assertFalse(next(i for i in result['sources'] if i['key'] == 'installer')['cleanable'])
        plan = cleaner.make_plan([result['items'][0]['id']])
        cleaner.execute(plan['plan_id'], '', dry_run=True)
        self.assertTrue(target.exists())
        self.assertTrue(important.exists())

    def test_changes_in_cache_prevent_deletion(self):
        root = self.base / 'Cache'
        file = self.add_old_file(root, 'old.png')
        cleaner = CleanupEngine(sources=[CacheSource('cache', 'cache', root, 'Cache', True, 'medium', '')])
        item = cleaner.discover()['items'][0]
        plan = cleaner.make_plan([item['id']])
        file.write_bytes(b'new contents')
        outcome = cleaner.execute(plan['plan_id'], 'DELETE SELECTED FILES')
        self.assertEqual(outcome['results'][0]['status'], 'skipped')
        self.assertTrue(file.exists())

    def test_known_browser_cache_only_not_profile_database(self):
        local = self.base / 'Local'
        profile = local / 'Google' / 'Chrome' / 'User Data' / 'Default'
        target = self.add_old_file(profile / 'Cache' / 'Cache_Data', 'old_cache.bin')
        cookies = self.add_old_file(profile, 'Cookies')
        result = windows_cache_sources(environ={'LOCALAPPDATA': str(local), 'APPDATA': str(self.base / 'Roaming'),
                                               'WINDIR': str(self.base / 'Windows')}, home=self.base)
        paths = [src.path for src in result]
        self.assertIn(target.parent, paths)
        self.assertNotIn(profile, paths)
        self.assertFalse(any(src.path == cookies.parent for src in result))

    def test_largest_files_and_file_types_are_real(self):
        folder = self.base / 'stuff'
        folder.mkdir()
        big = folder / 'archive.zip'
        big.write_bytes(b'X' * (33 * 1024 * 1024))
        result = disk_scan(self.base, threading.Event())
        self.assertEqual(result['files_seen'], 1)
        self.assertEqual(result['largest_files'][0]['path'], str(big))
        self.assertEqual(result['file_types'][0]['extension'], '.zip')

    def test_never_select_cache_config_or_database_file(self):
        root = self.base / 'Cache'
        self.add_old_file(root, 'settings.json')
        self.add_old_file(root, 'browser.db')
        valid = self.add_old_file(root, 'cache.bin')
        cleaner = CleanupEngine(sources=[CacheSource('cache','Cache',root,'Cache',True,'low','')])
        result = cleaner.discover()
        self.assertEqual([item['path'] for item in result['items']], [str(valid)])

    def test_symlink_cache_source_is_not_inspected(self):
        target = self.base / 'Elsewhere'
        target.mkdir()
        self.add_old_file(target, 'cache.bin')
        alias = self.base / 'Fake'
        try:
            alias.symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest('Symlink unavailable')
        sources = windows_cache_sources(environ={'LOCALAPPDATA': str(alias), 'APPDATA': str(self.base / 'Roaming')}, home=self.base)
        self.assertEqual([s for s in sources if s.path == target], [])


if __name__ == '__main__':
    unittest.main()