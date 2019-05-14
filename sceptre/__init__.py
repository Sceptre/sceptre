# -*- coding: utf-8 -*-

import logging


__author__ = 'Cloudreach'
__email__ = 'sceptre@cloudreach.com'
__version__ = '2.1.3'


# Set up logging to ``/dev/null`` like a library is supposed to.
# http://docs.python.org/3.3/howto/logging.html#configuring-logging-for-a-library
class NullHandler(logging.Handler):  # pragma: no cover
    def emit(self, record):
        pass


logging.getLogger('sceptre').addHandler(NullHandler())
