import unittest
from functools import wraps
import sys

if sys.version_info >= (3, 0):
    from urllib.request import urlopen
    from urllib.error import URLError
    from tests.server import TPBApp
else:
    from urllib2 import urlopen, URLError
    from server import TPBApp

def remote_func(func):
    """
    Executes func on remote url if the remote url is available.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self._is_remote_available:
            return unittest.skip('Remote URL {} is not available'.format(
                self.url))
        self.url = self.remote
        return func(self, *args, **kwargs)
    return wrapper


class RemoteTestMetaclass(type):
    """
    Duplicate all tests so every test is executed with local and remote urls.
    """
    def __new__(cls, clsname, bases, dct):
        attrs = {}
        for attr, value in dct.items():
            if attr.startswith('test') and hasattr(value, '__call__'):
                attrs[attr+'_local'] = value
                attrs[attr+'_remote'] = remote_func(value)
            else:
                attrs[attr] = value
        return super(RemoteTestMetaclass, cls).__new__(cls, clsname, bases, attrs)


class RemoteTestCase(unittest.TestCase):
    __metaclass__ = RemoteTestMetaclass

    @classmethod
    def setUpClass(cls):
        """
        Start local server and setup local and remote urls defaulting to local
        one.
        """
        cls.server = TPBApp('localhost', 8000)
        cls.server.start()
        cls.remote = 'http://thepiratebay.sx'
        cls.local = cls.server.url
        cls.url = cls.local

    @classmethod
    def tearDownClass(cls):
        """
        Stop local server.
        """
        cls.server.stop()

    @property
    def _is_remote_available(self):
        """
        Check connectivity to remote.
        """
        try:
            urlopen(self.remote)
        except URLError:
            return False
        else:
            return True

    def _assertCountEqual(self, first, second):
        """
        Compatibility function to test if the first sequence contains the
        same elements as the second one.

        This was done in order to have backwards compatibility between python
        2.x and 3.x
        """
        if sys.version_info >= (3, 0):
            self.assertCountEqual(first, second)
        else:
            self.assertItemsEqual(first, second)
