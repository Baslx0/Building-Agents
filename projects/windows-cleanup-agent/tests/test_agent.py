import unittest
from agent import chat, _direct_intent


class TestAgent(unittest.TestCase):
    def setUp(self):
        self.called = []

    def tools(self, name):
        self.called.append(name)
        if name.startswith('start_'):
            return {'status': 'running'}
        if name == 'get_disk_summary':
            return {'status': 'idle', 'result': None}
        if name == 'get_largest_files':
            return {'status': 'idle', 'largest_files': [], 'file_types': []}
        if name == 'get_cache_overview':
            return {'status': 'idle', 'sources': []}
        return {}

    def test_arabic_scan_both_without_model(self):
        r = _direct_intent('افحص الملفات والكاش في C:', self.tools)
        self.assertEqual(r['action'], 'scan_started')
        self.assertEqual(self.called, ['start_disk_scan', 'start_cache_audit'])

    def test_scan_cache_only(self):
        r = _direct_intent('ابحث عن الكاش', self.tools)
        self.assertEqual(r['action'], 'scan_started')
        self.assertEqual(self.called, ['start_cache_audit'])

    def test_largest_files_without_scan_never_hallucinates(self):
        r = _direct_intent('ما أكبر الملفات؟', self.tools)
        self.assertIsNone(r)


if __name__ == '__main__':
    unittest.main()