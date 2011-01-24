import sys

import os
import os.path

sys.path.append(os.path.realpath(os.path.dirname(__file__)+"/../") )

from config.environment import *
print "Initializing GUI"
from pyview.ide.gui import *

if __name__ == '__main__':
  startIDE()