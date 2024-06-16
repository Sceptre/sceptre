# -*- coding: utf-8 -*-

import logging
import warnings
import sys

from importlib.metadata import version

__author__ = "SceptreOrg"
__email__ = "sceptreorg@gmail.com"
__version__ = version(__package__ or __name__)


# Set up logging to ``/dev/null`` like a library is supposed to.
# http://docs.python.org/3.3/howto/logging.html#configuring-logging-for-a-library
class NullHandler(logging.Handler):  # pragma: no cover
    def emit(self, record):
        pass


if not sys.warnoptions:
    warnings.filterwarnings("default", category=DeprecationWarning, module="sceptre")

logging.getLogger("sceptre").addHandler(NullHandler())
