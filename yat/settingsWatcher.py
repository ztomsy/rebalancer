import os
from importlib import reload
import settings


class settingsWatcher(object):

    def __init__(self):
        self._cached_stamp = 0
        self.settings = None
        self.settings = self.build_dict()
        self.filename = self.settings['WATCHED_FILE']
        self.call_func_on_change = self.reload_watched_file

    def look(self) -> bool:
        """
        Look for changes in watched filename
        and call predefined self.call_func_on_change

        :return: True if watched file is refreshed
        """
        is_refreshed = False
        stamp = os.stat(self.filename).st_mtime
        if stamp != self._cached_stamp:
            self._cached_stamp = stamp
            # File has changed, call reloading module
            is_refreshed = True
            if self.call_func_on_change is not None:
                self.call_func_on_change()
        return is_refreshed

    def reload_watched_file(self):
        """
        This function calls each time a change happens
        Reload settings module
        Write new setting dict from newly imported module to self.settings
        """
        self.import_or_reload('settings')
        self.settings.clear()
        self.settings = self.build_dict()

    @staticmethod
    def import_or_reload(module_name, *names):
        """
        Reload module and redefine globals
        :param module_name:
        :param names:
        :return:
        """
        import sys

        if module_name in sys.modules:
            reload(sys.modules[module_name])
        else:
            __import__(module_name, fromlist=names)

        for name in names:
            globals()[name] = getattr(sys.modules[module_name], name)

    def build_dict(self):
        """
        Build and return a dict of settings from imported settings module
        """
        return {attr: getattr(settings, attr) for attr in dir(settings) if not callable(
                getattr(settings, attr)) and not attr.startswith("__")}
