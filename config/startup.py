#Matplotlib settings: Enable interactive plotting with custom backend.
import sys
from matplotlib.pyplot import *
from pyview.ide.mpl.backend_agg import figure

def importModule(name,implicit = False):
	import sys
 	if name in sys.modules:
		reload(sys.modules[name])
	if implicit:
		exec("import %s\n" % name,globals(),globals())
	else:
		exec("from %s import *\n" % name,globals(),globals())
	

importModule("config.environment")
importModule("config.instruments")
importModule("macros.qubit_functions")
importModule("macros.iq_level_optimization")


print "Initialization done."
