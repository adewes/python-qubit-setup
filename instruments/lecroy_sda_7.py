import sys
import getopt
import re
import struct
import numpy

sys.path.append('.')
sys.path.append('../')

from pyview.lib.classes import *
      
class Instr(VisaInstrument):

  def parameters(self,lazy = True):
    return self._params

  def initialize(self,visaAddress = "TCPIP0::192.168.0.33::inst0",name = "Lecroy SDA 7"):
    try:
      self._params = dict()
      self._visaAddress = visaAddress
      self.parameters(lazy = False)
    except:
      self.statusStr("An error has occured. Cannot initialize %s." % self._name)        
