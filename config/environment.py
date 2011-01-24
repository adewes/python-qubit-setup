import sys

import os
import os.path

from pyview.config.parameters import params

params["directories.pyview"] = os.path.realpath(os.path.dirname(__file__)+"/../pyview/") 
params["directories.setup"] = os.path.realpath(os.path.dirname(__file__)+"/../") 