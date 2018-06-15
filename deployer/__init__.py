from logging.config import logging
import os

__author__ = 'Veracode'
__appname__ = 'seek-and-deploy'
__email__ = 'dl-something@veracode.com'
__version__ = '0.0.dev0'


try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
path = os.path.join(os.path.dirname(__file__), 'conf', 'logging.conf')
logging.config.fileConfig(path)
