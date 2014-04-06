import os
import sys
sys.path.insert(0, os.path.abspath('..'))

import jenkins  # noqa

try:
    # Python 2
    from StringIO import StringIO  # noqa
except ImportError:  # pragma: nocover
    # Python 3
    from io import StringIO  # noqa
