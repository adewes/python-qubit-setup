import sys
import getopt
import time

from pyview.lib.classes import *
from pyview.lib.datacube import *

class Trace:
  """
  A class storing trace data for the FSP.
  """
  pass

class Instr(VisaInstrument):

  """
  The Rhode & Schwarz FSP instrument class.
  """
  
  def getSingleTrace(self,trace = 1,timeout = 20):
    """
    Sets the instrument to single sweep mode, resets the sweep count, waits until the data acqusition finishes and transfers the data from the instrument.
    """
    self.write("INIT:CONT OFF")
    self.write("INIT;*WAI")

    result = 0 
    cnt = 0

    #Check the status of the data acquisition operation.
    while True:
      try:
        result = int(self.ask("*OPC?"))
      except VisaIOError:
        pass
      if result == 1 or cnt > timeout*10:
        break
      cnt+=1
      time.sleep(0.1)
    return self.getTrace()    
    
  def setReferenceLevel(self,level):
    self.write("DISP:TRACE1:Y:RLEVEL %g" % level)
		
  def referenceLevel(self):
    return float(self.ask("DISP:TRACE1:Y:RLEVEL?"))
    
  def saveState(self,name):
    self.storeConfig(name)
    return name
    
  def restoreState(self,name):
    self.loadConfig(name)
   
  def storeConfig(self,name = "default"):
    """
    Stores the instrument configuration in a file on the harddisk of the instrument.
    """
    self.write("MMEM:STOR:STAT 1,'%s'" % name)    
  
  def loadConfig(self,name = "default"):
    """
    Loads a given configuration file.
    """
    print "Restoring:",name
    self.write("MMEM:LOAD:STAT 1,'%s'" % name)
    
  def getConfig(self,name = "default"):
    """
    Transfers a given configuration file from the instrument.
    """
    currentDirectory = self.ask("MMEM:CDIR?")[1:-1]
    data = self.ask("MMEM:DATA? '%s%s.fsp'" % (currentDirectory,name))
    #Remove the GPIB header from the data. This header is of the form "#xyyyyy", where "x" indicates the number of digits "y" that follow it. 
    length = int(data[1])
    data = data[2+length:]
    return data
  
  def getTrace(self,trace = 1):
    """
    Transfers a trace from the FSP.
    """
    if DEBUG:
      print "Getting trace..."
    freq_mode = self.ask("FREQ:MODE?")
    timedomain = False
    sweeptime = 0
    freqStart = 0
    freqStop = 0
    if freq_mode == 'FIX':
          #This is a time domain measurement.
          if DEBUG:
            print "Time domain measurement..."
          timedomain = True
          sweeptime = float(self.ask("SWE:TIME?"))
          if DEBUG:
            print "Sweeptime: %f " % sweeptime
    else:
          #This is a frequency domain measurement.
          freqStart = float(self.ask("FREQ:START?"))
          freqStop = float(self.ask("FREQ:STOP?"))
          if DEBUG:
            print "Frequency domain measurement from %f to %f" % (freqStart,freqStop)
    self.write("FORM ASC;TRAC? TRACE%d" % trace)
    trace = self.read()
    values = trace.split(',')
    values = map(lambda x:float(x),values)
    if timedomain:
          result = [[i * sweeptime / len(values) for i in range(0,len(values))],values]
    else:
          result = [[ freqStart+ i * (freqStop-freqStart) / len(values) for i in range(0,len(values))],values]
    return result
  
  def initialize(self):
    try:
      self._name = "Rhode & Schwarz FSP"
      if DEBUG:
        print "Initializing FSP"
      self._visaAddress = "TCPIP0::192.168.0.17::inst0"
    except:
      self.statusStr("An error has occured. Cannot initialize FSP.")        
