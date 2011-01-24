from numpy import *
from pyview.lib.classes import *
import math
import sys
import inspect

class JBACalibration(Macro):

  def __init__(self):
    Macro.__init__(self)

  #Calibrates the Qubit readout to a given switching probability with a given accuracy.
  def calibrate(self,level = 0.2,accuracy = 0.025):
    self._attenuator.turnOn()
    self._qubitmwg.turnOff()
    
    self.notify("status","Starting calibration.")
    voltages = arange(0.0,2.0,0.1)
    (ps,max,maxVoltage) = self._attenuatorRangeCheck(voltages)
    if self.stopped():
      return
    voltages2 = arange(maxVoltage-0.1,maxVoltage+0.1,0.005)
    (p2s,max,maxVoltage2) = self._attenuatorRangeCheck(voltages2)
    if self.stopped():
      return
    self.notify("status","Voltage calibration complete...")
    self._attenuator.setVoltage(maxVoltage2*self._polarity)
    if self.stopped():
      return
    self.notify("status","Adjusting offset and rotation...")
    self._adjustRotationAndOffset()
    self.adjustSwitchingLevel(level,accuracy)
    self.notify("status","Calibration complete")
    return (voltages,ps,voltages2,p2s,self.trends)
        
  def _attenuatorRangeCheck(self,voltages):
    ps = []
    max = 0
    maxVoltage = 0
    self.variances = zeros((len(voltages),2))
    self.variances[:,0] = voltages
    for i in range(0,len(voltages)):
      if self.stopped():
        print "Stopped. Quitting."
        return
      v = voltages[i] * self._polarity 
      self._attenuator.setVoltage(v)
      self._acqiris.bifurcationMap()
      varsum =cov(self._acqiris.trends[self._acqirisChannel])+cov(self._acqiris.trends[self._acqirisChannel+1])
      print "Variance: %f" % varsum
      self.variances[i,1] = varsum
      self.notify("variance",self.variances)
      ps.append(varsum)
      if varsum > max:
        max = varsum
        maxVoltage = voltages[i]
    return (ps,max,maxVoltage)
      
        
  def adjustSwitchingLevel(self,level = 0.2,precision = 0.05):
    vOld = self._attenuator.voltage()
    cnt = 0
    p = self.switchingProbability()
    while fabs(p-level)>precision:
      print "p = %f" % p
      cnt+=1
      diff = p - level
      v = self._attenuator.voltage()
      self._attenuator.setVoltage(v+min(diff,0.01)*self._polarity*precision/0.05)
      if cnt>100:
        self._attenuator.setVoltage(vOld)
        return
      p = self.switchingProbability()
    
  def _adjustRotationAndOffset(self):
    #We set all offsets and angles to 0.
    self._acqiris.ConfigureChannel(self._acqirisChannel+1,offset = 0)
    self._acqiris.ConfigureChannel(self._acqirisChannel+2,offset = 0)
    self._acqiris.setBifurcationMapRotation(self._acqirisChannel/2,0)
    self._acqiris.bifurcationMap(calculateTrends = True,ntimes = 20)
  
    means = mean(self._acqiris.trends[self._acqirisChannel:self._acqirisChannel+2,:],axis = 1)
  
    covar = cov(self._acqiris.trends[self._acqirisChannel],self._acqiris.trends[self._acqirisChannel+1])
    angle = math.atan2(covar[1,0],covar[0,0])

    self._acqiris.setBifurcationMapRotation(self._acqirisChannel/2,angle)
    self._acqiris.ConfigureChannel(self._acqirisChannel+1,offset = -means[0])
    self._acqiris.ConfigureChannel(self._acqirisChannel+2,offset = -means[1])

    self._acqiris.bifurcationMap(calculateTrends = True,ntimes = 20)

    means = mean(self._acqiris.trends[self._acqirisChannel:self._acqirisChannel+2,:],axis = 1)

    pBefore = self._acqiris.probabilities[self._acqirisChannel/2,0]
    oldVoltage = self._attenuator.voltage()
    self._attenuator.setVoltage(oldVoltage+0.2*self._polarity)
    
    self._acqiris.bifurcationMap(calculateTrends = True,ntimes = 20)

    pAfter = self._acqiris.probabilities[self._acqirisChannel/2,0]

    if pAfter > pBefore:
      angle+=3.1415
      self._acqiris.setBifurcationMapRotation(self._acqirisChannel/2,angle)
    
    self._attenuator.setVoltage(oldVoltage)

    self._acqiris.bifurcationMap(calculateTrends = True,ntimes = 20)
    self.trends = zeros((2,len(self._acqiris.trends[0,:])))

    self.trends[0,:] = self._acqiris.trends[self._acqirisChannel,:]*cos(angle) + self._acqiris.trends[self._acqirisChannel+1,:]*sin(angle)
    self.trends[1,:] = -self._acqiris.trends[self._acqirisChannel,:]*sin(angle) + self._acqiris.trends[self._acqirisChannel+1,:]*cos(angle)

    self.notify("iqdata",self.trends)
  
  def initialize(self, params = dict(),acqirisChannel = 0,muwave = "cavity1mwg",attenuator  = "AttS2",acqiris = "acqiris",qubitmwg = "qubit1mwg",polarity = 1,afg = "afg3",waveform = "USER1"):
    manager = Manager()
    self.params = params
    self._muwave = manager.getInstrument(muwave)
    self._polarity = polarity
    self._register = manager.getInstrument("register")
    self._acqiris = manager.getInstrument(acqiris)
    self._afg = manager.getInstrument(afg)
    self._waveform = waveform
    self._attenuator = manager.getInstrument(attenuator)
    self._acqirisChannel = acqirisChannel
    self._qubitmwg = manager.getInstrument(qubitmwg)
