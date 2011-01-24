#Matplotlib settings: Enable interactive plotting with custom backend.
from matplotlib.pyplot import *
from pyview.ide.mpl.backend_agg import figure
import sys

def importModule(name):
 	if name in sys.modules:
		reload(sys.modules[name])
	exec("from %s import *\n" % name,globals(),globals())


importModule("config.parameters")
importModule("config.instruments")
importModule("macros.qubit_functions")
importModule("macros.iq_level_optimization")

print "Initialization done."
