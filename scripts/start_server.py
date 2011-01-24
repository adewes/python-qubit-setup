import sys

import os
import os.path

sys.path.append(os.path.realpath(os.path.dirname(__file__)+"/../") )

from config.environment import *
from pyview.server.pickle import *

if __name__ == '__main__':
  startServer()