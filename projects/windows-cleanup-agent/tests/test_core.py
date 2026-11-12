"""Safety and behavior tests that never touch real system files."""
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest

from core import CleanupEngine, disk_scan


class TestCleanup(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'Temp'
        self.root.mkdir()
        self.engine = CleanupEngine(temp_root=self.root)

    def old_file(self, name='cache.tmp', content=b'abc', days=14):
        path = self.root / name
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_bytes(content)
        timestamp = time.time() - days * 86400
        os.utime(path, (timestamp, timestamp))
        return path

    def test_find_only_old_regular_temp_files(self):
        old = self.old_file()
        self.old_file('new.tmp', days=1)
        self.old_file('installer.exe')
        discovered = self.engine.discover()
        self.assertEqual(len(discovered['items']), 1)
        self.assertEqual(discovered['total_bytes'], 3)
        self.assertEqual(discovered['items'][0]['path'], str(old))

    def test_requires_exact_confirmation_and_one_time_plan(self):
        target = self.old_file()
        item = self.engine.discover()['items'][0]
        plan = self.engine.make_plan([item['id']])
        with self.assertRaises(ValueError):
            self.engine.execute(plan['plan_id'], 'yes')
        self.assertTrue(target.exists())
        with self.assertRaises(ValueError):
            self.engine.execute(plan['plan_id'], 'DELETE SELECTED FILES')
        plan = self.engine.make_plan([item['id']])
        result = self.engine.execute(plan['plan_id'], 'DELETE SELECTED FILES')
        self.assertEqual(result['freed_estimate'], 3)
        self.assertFalse(target.exists())

    def test_revalidate_if_file_changed(self):
        target = self.old_file()
        item = self.engine.discover()['items'][0]
        plan = self.engine.make_plan([item['id']])
        target.write_bytes(b'changed')
        result = self.engine.execute(plan['plan_id'], 'DELETE SELECTED FILES')
        self.assertEqual(result['results'][0]['status'], 'skipped')
        self.assertTrue(target.exists())

    def test_dry_run_keeps_files(self):
        target = self.old_file()
        item = self.engine.discover()['items'][0]
        plan = self.engine.make_plan([item['id']])
        result = self.engine.execute(plan['plan_id'], '', dry_run=True)
        self.assertTrue(target.exists())
        self.assertEqual(result['freed_estimate'], 0)

    def test_refuses_external_symlink(self):
        external = Path(self.tmp.name) / 'secret.txt'
        external.write_text('private')
        link = self.root / 'fake.tmp'
        try:
            link.symlink_to(external)
        except (OSError, NotImplementedError):
            self.skipTest('Symlink creation not allowed')
        self.assertEqual(self.engine.discover()['items'], [])
        self.assertTrue(external.exists())

    def test_refuses_junction_like_directory_link(self):
        outside = Path(self.tmp.name) / 'outside'
        outside.mkdir()
        path = outside / 'old.tmp'
        path.write_text('data')
        old = time.time() - 14 * 86400
        os.utime(path, (old, old))
        try:
            (self.root / 'link').symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('Symlink creation not allowed')
        self.assertEqual(self.engine.discover()['items'], [])

    def test_unknown_candidate_cannot_be_planned(self):
        self.old_file()
        self.engine.discover()
        with self.assertRaises(ValueError):
            self.engine.make_plan(['unknown'])

    def test_read_only_disk_scan_and_cancel(self):
        path = self.root / 'folder'
        path.mkdir()
        (path / 'file.bin').write_bytes(b'x' * 100)
        result = disk_scan(self.root, threading.Event())
        self.assertEqual(result['folders'][0]['bytes'], 100)
        event = threading.Event(); event.set()
        self.assertTrue(disk_scan(self.root, event)['cancelled'])


if __name__ == '__main__':
    unittest.main()