import sys

sys.path.append('.')
sys.path.append('../')

#We reload the base module in case it has not yet been reloaded
try:
  reload(sys.modules["frontpanels.agilent_mwg"])
except KeyError:
  pass
  
from frontpanels.agilent_mwg import *
