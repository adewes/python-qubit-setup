import sys
import getopt
import struct

from pyview.lib.classes import *

class Trace:
      pass

#This is the baseclass for the Anrtisu MWG. Use the instrumentCopy function of the Instruments manager to create copies of this instrument with different parameters (e.g. GPIB addresses)

class Instr(VisaInstrument):

  """
  The Anritsu microwave source.
  """
  
  def saveState(self,name):
    return self.parameters()
    
  def restoreState(self,state):
    self.setFrequency(state["frequency"])
    self.setPower(state["power"])
    if state["output"] == True:
      self.turnOn()
    elif state["output"] == False:
      self.turnOff()
  
  #returned frequency is in GHz
  def frequency(self):
    freq = float(self.ask("OF1;"))/1e3
    self.notify("frequency",freq)
    return freq
  
  #Returned power is in dBm
  def power(self):
    power = float(self.ask("OL1"))
    self.notify("power",power)
    return power
  
  #Power should be supplied in dBm
  def setPower(self,power):
    self.write("L1%fDM" % power)
    return self.power()
  
  def output(self):
    self.notify("output",self._output)
    return self._output
            
  #freq is supposed to be supplied in GHz!
  def setFrequency(self,freq):
    self.write("F1%fGH" % (freq))
    return self.frequency()
  
  def parameters(self):
    params = dict()
    params['frequency'] = self.frequency()
    params['power'] = self.power()
    params['output'] = self.output()
    return params
  
  def turnOff(self):
    self.write("RF0")
    self._output = False
    return self.output()
  
  def turnOn(self):
    self.write("RF1")
    self._output = True
    return self.output()
  
  def initialize(self,name = "Anritsu 1",visaAddress = "GPIB0::6"):
    self._output = None
    try:
      self._name = name
      if DEBUG:
        print "Initializing an Anritsu MWG with address %s" % visaAddress
      self._visaAddress = visaAddress
    except:
      self.statusStr("An error has occured. Cannot initialize Anritsu MWG.")        
