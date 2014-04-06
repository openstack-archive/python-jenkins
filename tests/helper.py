import os
import sys
sys.path.insert(0, os.path.abspath('..'))

import jenkins

try:
    # Python 2
    from StringIO import StringIO
except ImportError:
    # Python 3
    from io import StringIO
