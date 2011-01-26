import sys
import getopt
import re
import struct
import math

from numpy import *

from pyview.lib.classes import *
from pyview.helpers.instrumentsmanager import Manager

#This is a virtual instrument representing a Josephson Bifurcation Amplifier.
class Instr(Instrument):

  def parameters(self):
    return self._params
    
  def initReadout(self):
    self.loadReadoutWaveform()
    self._afg.setTriggerDelay(0)
    
  def internalDelay(self):
    return self._params["internalDelay"]+self._params["starkPulseLength"]+self._params["starkPulseDelay"]
    
  def saveState(self,name):
    state = dict()
    state["params"] = copy.deepcopy(self._params)
    state["readoutWaveform"] = copy.deepcopy(self._readoutWaveform)
    return state
    
  def restoreState(self,state):
    self._params = copy.deepcopy(state["params"])
    self._readoutWaveform = copy.deepcopy(state["readoutWaveform"])
#    self.loadReadoutWaveform(self._params["measureTime"],self._params["riseTime"],self._params["fallTime"],self._params["latchTime"],self._params["latchHeight"])
    
  def readoutDuration(self):
    return self._params["readoutWindowStart"]+self._params["measureTime"]
    
  def loadReadoutWaveform(self,measureTime = 200,riseTime = 20,fallTime = 30,latchTime = 2000,starkPulseLength = 0,starkPulseHeight = 0,starkPulseDelay = 0,scale = 1.0,latchHeight = 0.8,acquisitionTime = 250,waitTime = 0,fallTime2 = 10,safetyMargin = 100):
    waveformLength = 1+(waitTime+measureTime+latchTime+riseTime+fallTime+fallTime2+starkPulseLength+starkPulseDelay)*2
    fullWaveform = zeros((waveformLength),dtype = uint16)
    waveform = fullWaveform[(starkPulseLength+starkPulseDelay+waitTime)*2:]
    fullWaveform[1+waitTime*2:(waitTime+starkPulseLength)*2.0] = starkPulseHeight*((1<<14) - 1)
    waveform[1:riseTime*2+1] = linspace(0,(1<<14) - 1,riseTime*2)*scale
    waveform[1+riseTime*2:measureTime*2+1+riseTime*2] = ((1<<14) - 1)*scale
    waveform[measureTime*2+1+riseTime*2:measureTime*2+1+riseTime*2+fallTime*2] = linspace((1<<14) - 1,((1<<14)-1)*latchHeight,fallTime*2)*scale
    waveform[measureTime*2+1+riseTime*2+fallTime*2:-fallTime*2] = int((float(1<<14)-1)*latchHeight)*scale
    waveform[-fallTime*2:] = linspace(int((float(1<<14)-1)*latchHeight),0,fallTime*2)*scale
    self._afg.writeWaveform(self._waveform,fullWaveform)
    self._afg.setWaveform(self._waveform)
    self._afg.setPeriod(waveformLength/2.0)
    self._params["waitTime"] = waitTime
    self._params["riseTime"] = riseTime
    self._params["measureTime"] = measureTime
    self._params["starkPulseLength"] = starkPulseLength
    self._params["starkPulseDelay"] = starkPulseDelay
    self._params["starkPulseHeight"] = starkPulseHeight
    self._params["fallTime"] = fallTime
    self._params["latchTime"] = latchTime
    self._params["latchHeight"] = latchHeight
    self._params["fallTime2"] = fallTime2
    self._params["safetyMargin"] = safetyMargin
    self._params["readoutWindowStart"] = self._params["internalDelay"]+self._params["returnDelay"]+riseTime+measureTime+fallTime+self._params["safetyMargin"]+starkPulseLength+waitTime+starkPulseDelay
    self._readoutWaveform = fullWaveform
    self.notify("readoutWaveform",fullWaveform)
    self._acqiris.ConfigureV2(**{"delayTime":(self._params["readoutWindowStart"])*1e-9})
    
  def updateReadoutWaveform(self):
    self._readoutWaveform = self._afg.readWaveform(self._waveform)
    self.notify("readoutWaveform",self._readoutWaveform)
    return self.readoutWaveform()
        
  def readoutWaveform(self):
    return self._readoutWaveform
    
  def generatePulse(self,holdTime = 200,sampleTime = 2000,delay = 10000,holdHeight = 0.9,totalLength = 20000):
    pulse = zeros((totalLength))
    markers = zeros((totalLength))
    markers[:delay] = 255
    pulse[delay:delay+holdTime] = 255
    pulse[delay+holdTime:delay+holdTime+sampleTime] = int(255*holdHeight)
    data = self._awg.writeIntData(pulse,markers)
    self._awg.createWaveform(self._waveform,data,'INT')

  def calibrateFrequency(self,minFreq,maxFreq):
    maxVariance = 0
    maxFrequency = None
    for f in arange(minFreq,maxFreq,0.01):
      self._muwave.setFrequency(f)
      (ps,variance,voltage) = self._attenuatorRangeCheck(arange(0,2,0.05))
      self.notify("status","Variance at % GHz: %g" % (f,variance))
      if variance > maxVariance:
        maxVariance = variance
        maxFrequency = f
    self.notify("status","Maximum variance at %g GHz" % maxFrequency)
    self._muwave.setFrequency(maxFrequency)
    
  #Calibrates the Qubit readout to a given switching probability with a given accuracy.
  def calibrate(self,level = 0.2,accuracy = 0.025,microwaveOff = True):
    try:
      state = self._qubitmwg.output()
      self._attenuator.turnOn()
      if microwaveOff:
        self._qubitmwg.turnOff()
      self._muwave.turnOn()

      self.notify("status","Starting calibration.")
      voltages = arange(0.0,2.0,0.1)
      (ps,max,maxVoltage) = self._attenuatorRangeCheck(voltages)
      voltages2 = arange(maxVoltage-0.1,maxVoltage+0.1,0.005)
      (p2s,max,maxVoltage2) = self._attenuatorRangeCheck(voltages2)
      self.notify("status","Voltage calibration complete...")
      self._attenuator.setVoltage(maxVoltage2*self._polarity)
      self.notify("status","Adjusting offset and rotation...")
      self._adjustRotationAndOffset()
      self.adjustSwitchingLevel(level,accuracy)
      self.notify("status","Calibration complete. Measure of separation: %g" % self.separationMeasure(acquire = False))
      return (voltages,ps,voltages2,p2s,self.trends)
    finally:
      if state == True:
        self._qubitmwg.turnOn()
        
  def _attenuatorRangeCheck(self,voltages):
    ps = []
    max = 0
    maxVoltage = 0
    self.variances = zeros((len(voltages),2))
    self.variances[:,0] = voltages
    for i in range(0,len(voltages)):
      if self.stopped():
        self._stopped = False
        raise Exception("Got stopped!")
      v = voltages[i] * self._polarity 
      self._attenuator.setVoltage(v)
      self._acqiris.bifurcationMap()
      trends = self._acqiris.trends()
      varsum =cov(trends[self._acqirisChannel])+cov(trends[self._acqirisChannel+1])
      self.notify("status","Variance at %g V: %g" % (v,varsum))
      print "Variance: %f" % varsum
      self.variances[i,1] = varsum
      self.notify("variance",self.variances)
      ps.append(varsum)
      if varsum > max:
        max = varsum
        maxVoltage = voltages[i]
    return (ps,max,maxVoltage)
    
  def switchingProbability(self):
    self._acqiris.bifurcationMap(ntimes = 80)
    p = self._acqiris.probabilities()[self._acqirisChannel/2,0]
    return p
    
  def separationMeasure(self,acquire = True):
    if acquire:
      self._acqiris.bifurcationMap()
    trends = self._acqiris.trends()
    angle = self._acqiris.bifurcationMapRotation()[self._acqirisChannel/2]
    rotatedTrends = zeros((2,len(trends[self._acqirisChannel])))
    rotatedTrends[0,:] = trends[self._acqirisChannel,:]*cos(angle) + trends[self._acqirisChannel+1,:]*sin(angle)
    left = []
    right = []
    for value in rotatedTrends[0,:]:
      if value > 0:
        right.append(value)
      else:
        left.append(value)
    var1 = cov(left)
    var2 = cov(right)
    mu1 = mean(left)
    mu2 = mean(right)
    mu = (mu1+mu2)
    value = (pow(mu1-mu,2.0)+pow(mu2-mu,2.0))/(var1+var2)/2.0
    if math.isnan(value):
      return 0
    return value
    
  def setVoltage(self,v):
    return self._attenuator.setVoltage(v)
    
  def voltage(self):
    return self._attenuator.voltage()
    
  def acquire(self,ntimes = 20):
    self._acqiris.bifurcationMap(ntimes = ntimes)
    angle = self._acqiris.bifurcationMapRotation()[self._acqirisChannel/2]
    p = self._acqiris.probabilities()[self._acqirisChannel/2,0]
    trends = self._acqiris.trends()
    rotatedTrends = zeros((2,len(trends[0])))
    rotatedTrends[0,:] = trends[self._acqirisChannel,:]*cos(angle) + trends[self._acqirisChannel+1,:]*sin(angle)
    rotatedTrends[1,:] = -trends[self._acqirisChannel,:]*sin(angle) + trends[self._acqirisChannel+1,:]*cos(angle)
    return (p,rotatedTrends)
        
  def adjustSwitchingLevel(self,level = 0.2,accuracy = 0.05,verbose = False,minSensitivity = 15.0,microwaveOff = True,nmax = 100):
    try:
      status = self._qubitmwg.output()
      if microwaveOff:
        self._qubitmwg.turnOff()
      vOld = self._attenuator.voltage()
      cnt = 0
      #First we check that we are at a good working point by calculating a discrimination measure.
      #If the working point is not good, we search for a good one by ramping the voltage in the attenuator.
      if self.separationMeasure() < 0.5 and False:
        v = 0.0
        print "Separation (%g) is not good, re-adjusting..." % self.separationMeasure(acquire = False)
        self._attenuator.setVoltage(v)
        while self.separationMeasure(acquire = True) < 3.0:
          v+=0.1
          if verbose:
            print "Checking separation at %g V" % v
          self._attenuator.setVoltage(v)
          if v >= 2.0:
            self._attenuator.setVoltage(vOld)
            raise Exception("Cant't find a good working point!")
      vOld = self._attenuator.voltage()
      self._attenuator.setVoltage(vOld+0.02)
      p2 = self.switchingProbability()
      self._attenuator.setVoltage(vOld)
      p = self.switchingProbability()
      v = vOld
      sensitivity = (p-p2)/0.02
      while fabs(p-level)>accuracy:
        if self.stopped():
          raise Exception("Got stopped!")
        self.notify("status","Switching probability at %g V: %g" % (v,p))
        cnt+=1
        diff = p - level
        if verbose:
          print "v = %g, p = %g, dp = %f" % (v,p,diff)
        #If switching probability is too high, we increase the voltage. If it is too low, we decrease it...
        if math.fabs(sensitivity) < minSensitivity:
          sensitivity = minSensitivity*max(1,accuracy/diff)
        if verbose:
          print "Sensitivity: %f" % sensitivity
        voltage = v+diff/sensitivity
        if voltage < 0.0:
          voltage = 0.0
        if voltage > 2.0:
          voltage = 2.0
        if cnt>nmax:
          raise Exception("Maximum number of steps exceeded!")
        pOld = p
        if v == vOld:
          sensitivity = 0
        else:
          sensitiviy = (pOld-p)/(v-vOld)
        self._attenuator.setVoltage(voltage*self._polarity)
        v = self._attenuator.voltage()
        p = self.switchingProbability()
      self.notify("status","Switching probability: %g %%" % (p*100))
      return (p,cnt)
    finally:
      if status == True:
        self._qubitmwg.turnOn()
    
  def _adjustRotationAndOffset(self):
    #We set all offsets and angles to 0.
    self._acqiris.ConfigureChannel(self._acqirisChannel+1,offset = 0)
    self._acqiris.ConfigureChannel(self._acqirisChannel+2,offset = 0)
    self._acqiris.setBifurcationMapRotation(self._acqirisChannel/2,0)

    cnt = 0
    
    offsets = [0,0]

    while cnt < 10:

      print cnt

      cnt+=1

      self._acqiris.bifurcationMap(calculateTrends = True,ntimes = 40)
    
      trends = self._acqiris.trends()
      means = mean(trends[self._acqirisChannel:self._acqirisChannel+2,:],axis = 1)
    
      offsets[0]-=means[0]
      offsets[1]-=means[1]
    
      self._acqiris.ConfigureChannel(self._acqirisChannel+1,offset = offsets[0])
      self._acqiris.ConfigureChannel(self._acqirisChannel+2,offset = offsets[1])
      
      if abs(means[0]) < 0.0001 and abs(means[1]) < 0.0001:
        break
        
      print means

    covar = cov(trends[self._acqirisChannel]-means[0],trends[self._acqirisChannel+1]-means[1])
  
    #We calculate the eigenvectors of the variance/covariance matrix.
  
    la,v = linalg.eig(covar)
    
    #We calculate the rotation angle from the eigenvector matrix.
    #M = [(cos(theta),-sin(theta)),(sin(theta),cos(theta))
    
    if la[1] > la[0]:
      angle = math.atan2(v[0,0],v[0,1])
    else:
      angle = math.atan2(v[1,0],v[0,0])
    
    self._acqiris.setBifurcationMapRotation(self._acqirisChannel/2,angle)

    pBefore = self._acqiris.probabilities()[self._acqirisChannel/2,0]
    oldVoltage = self._attenuator.voltage()

    self._attenuator.setVoltage(oldVoltage+0.1*self._polarity)
    self._acqiris.bifurcationMap(calculateTrends = True,ntimes = 80)

    pAfter = self._acqiris.probabilities()[self._acqirisChannel/2,0]

    if pAfter > pBefore:
      angle+=math.pi
      self._acqiris.setBifurcationMapRotation(self._acqirisChannel/2,angle)
    
    self._attenuator.setVoltage(oldVoltage)
    self._acqiris.bifurcationMap(calculateTrends = True,ntimes = 80)
    trends = self._acqiris.trends()
    self.trends = zeros((2,len(trends[0,:])))

    self.trends[0,:] = trends[self._acqirisChannel,:]*cos(angle) + trends[self._acqirisChannel+1,:]*sin(angle)
    self.trends[1,:] = -trends[self._acqirisChannel,:]*sin(angle) + trends[self._acqirisChannel+1,:]*cos(angle)
    
    print cov(self.trends[0],self.trends[1])

    self.notify("iqdata",self.trends)
  
  def initialize(self, params = dict(),acqirisChannel = 0,variable = "p1x",muwave = "cavity1mwg",attenuator  = "AttS2",acqiris = "acqiris",qubitmwg = "qubit1mwg",polarity = 1,afg = "afg3",waveform = "USER1",internalDelay = 243,returnDelay = 57,acquisitionTime = 250,sampleInterval = 1e-9,trigSlope = 0,safetyMargin = 100):
    manager = Manager()
    self._muwave = manager.getInstrument(muwave)
    self._polarity = polarity
    self._register = manager.getInstrument("register")
    self._acqiris = manager.getInstrument(acqiris)
    self._afg = manager.getInstrument(afg)
    self._waveform = waveform
    self._attenuator = manager.getInstrument(attenuator)
    self._acqirisChannel = acqirisChannel
    self._qubitmwg = manager.getInstrument(qubitmwg)

    if hasattr(self,"_params"):
      return
    
    self._params = params
  
    self._params["variable"] = variable
    self._params["safetyMargin"] = safetyMargin
    self._params["internalDelay"] = internalDelay
    self._params["returnDelay"] = returnDelay
    self._params["acquisitionTime"] = acquisitionTime
    self._params["sampleInterval"] = sampleInterval
    self._params["trigSlope"] = trigSlope
#    self.loadReadoutWaveform()
