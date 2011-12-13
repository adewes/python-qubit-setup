
import sys
import getopt
import re
import struct
import math

from numpy import *

from pyview.lib.classes import *
from pyview.lib.datacube import Datacube
from pyview.helpers.datamanager import DataManager
from pyview.helpers.instrumentsmanager import Manager

#This is a virtual instrument for visualizing the pulses.
class Instr(Instrument):

  def parameters(self):
    """
    Returns the parameters of the visualizer.
    """
    return self._params
           
  def initialize(self, params = dict()):
    manager = Manager()

    if hasattr(self,"_params"):
      return
      
    self._params = params


