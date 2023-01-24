# -*- coding: utf-8 -*-

import logging
import sys
import warnings


__author__ = "Cloudreach"
__email__ = "sceptre@cloudreach.com"
__version__ = "4.0.0"


# Set up logging to ``/dev/null`` like a library is supposed to.
# http://docs.python.org/3.3/howto/logging.html#configuring-logging-for-a-library
class NullHandler(logging.Handler):  # pragma: no cover
    def emit(self, record):
        pass


if not sys.warnoptions:
    warnings.filterwarnings("default", category=DeprecationWarning, module="sceptre")

logging.getLogger("sceptre").addHandler(NullHandler())
