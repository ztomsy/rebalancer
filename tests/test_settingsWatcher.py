import unittest
from yat.settingsWatcher import settingsWatcher


class TestSettingsWatcher(unittest.TestCase):

    def setUp(self):
        self.sw = settingsWatcher()
        self.sw.filename = '../settings.py'

    def test_look(self):
        self.assertEqual(self.sw.look(), True)

    def test_import_or_reload(self):
        self.sw.import_or_reload('settings')

    def test_build_dict(self):
        self.sw.build_dict()
        self.assertIsInstance(self.sw.settings, dict)
