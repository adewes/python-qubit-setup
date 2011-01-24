import sys
import getopt

from pyview.lib.classes import *
if 'lib.datacube' in sys.modules:
  reload(sys.modules['lib.datacube'])
from pyview.lib.datacube import Datacube
from numpy import *
from pyvisa import vpp43

class VNATrace:

  def __init__(self):
    self.frequencies = []
    self.phase = []
    self.magnitude = []
    self.timestamp = ''
    self.instrument = None  

#This is the VNA instrument.
class Instr(VisaInstrument):

    #Initializes the instrument.
    def initialize(self,visaAddress = "GPIB::15",name = "VNA"):
        self._name = "Anritsu VNA"
        print "Initializing with resource %s" % visaAddress
        if DEBUG:
          print "Initializing VNA"
        try:
          self._visaAddress = visaAddress
        except:
          print "ERROR: Cannot initialize instrument!"


    def clearDevice(self):
      handle = self.getHandle()
      handle.timeout = 1
      cnt = 0
      handle.write("*CLS")
      while True:
        try:
          if cnt>100:
            return False
          if int(vpp43.read_stb(handle.vi)) & 128:
            return True
          time.sleep(0.1)
        except visa.VisaIOError:
          cnt+=1
      return False
      
    def triggerReset(self):
      self.write("*CLS;TRS;")
      
    def setAttenuation(self,a):
      self.write("SA1 %g DB" % a)
      return self.attenuation()
      
    def attenuation(self):
      return float(self.ask("SA1?"))
      
    def setPower(self,power):
      self.write("PWR %g,DB" % power)
      return self.power()
      
    def power(self):
      return float(self.ask("PWR?"))
          
    def waitFullSweep(self):
      self.write("*CLS;IEM 8;*SRE 128;TRS;WFS;")
      handle = self.getHandle()
      handle.timeout = 1
      cnt = 0
      while True:
        try:
          if cnt>100:
            return False
          time.sleep(1)
          status =  vpp43.read_stb(handle.vi)
          if int(status) & 128:
            return True
        except visa.VisaIOError:
          cnt+=1
          print sys.exc_info()
      return False

    def electricalLength(self):
  	  self.write("RDA")
  	  return float(self.ask("RDD?"))

    #Get a trace from the instrument and store it to a local array.
    def getTrace(self,correctPhase = False):
      print "Getting trace..."
      trace = Datacube()
      if DEBUG:
        print "Getting trace..."
      freqs = self.ask_for_values("fma;msb;OFV;")
      data = self.ask_for_values("fma;msb;OFD;")
      freqs.pop(0)
      data.pop(0)
      mag = []
      phase = []
      #If y length is twice the x length, we got phase and magnitude.
      if len(data) == 2*len(freqs):
        for i in range(0,len(data)):
          if i%2 == 0:	
            mag.append(data[i])
          else:
					 phase.append(data[i])
      else:
        mag = data
      trace.createColumn("freq",freqs)
      trace.createColumn("mag",mag)
      attenuation = float(self.ask("SA1?"))
      power = float(self.ask("PWR?"))
      trace.column("mag")[:]+= attenuation
      params = dict()
      params["attenuation"] = attenuation
      params["power"] = power
      trace.setParameters(params)
      if len(phase) > 0:
        correctedPhase = []
        if correctPhase:
          correctedPhase.append(phase[0])
          oldPhi = phase[0]
          for phi in phase[1:]:
            if fabs(phi+360.0-oldPhi) < fabs(phi-oldPhi):
              newPhi = phi+360.0
            elif fabs(phi-360.0-oldPhi) < fabs(phi-oldPhi):
              newPhi = phi-360.0
            else:
              newPhi = phi
            correctedPhase.append(newPhi)
            oldPhi = newPhi
        else:
          correctedPhase = phase
        trace.createColumn("phase",correctedPhase)
      return trace
