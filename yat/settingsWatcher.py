import os
from importlib import reload
import _settings


class settingsWatcher(object):

    # Constructor
    def __init__(self, watch_file: str = '_settings.py'):
        self._cached_stamp = 0
        self.settings = {}
        self.settings = self.build_dict()
        self.filename = watch_file
        self.call_func_on_change = self.reload_watched_file

    # Look for changes
    def look(self):
        is_refreshed = False
        stamp = os.stat(self.filename).st_mtime
        if stamp != self._cached_stamp:
            self._cached_stamp = stamp
            # File has changed, call reloading module
            is_refreshed = True
            if self.call_func_on_change is not None:
                self.call_func_on_change()
        return is_refreshed

    # Call this function each time a change happens
    def reload_watched_file(self):
        self.importOrReload('_settings')
        self.settings.clear()
        self.settings = self.build_dict()

    @staticmethod
    def importOrReload(module_name, *names):
        import sys

        if module_name in sys.modules:
            reload(sys.modules[module_name])
        else:
            __import__(module_name, fromlist=names)

        for name in names:
            globals()[name] = getattr(sys.modules[module_name], name)

    def build_dict(self):
        """Build and return a dict of settings from imported module
        """
        return {attr: getattr(_settings, attr) for attr in dir(_settings) if not callable(
                getattr(_settings, attr)) and not attr.startswith("__")}
