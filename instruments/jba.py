
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

#This is a virtual instrument representing a Josephson Bifurcation Amplifier.
class Instr(Instrument):

  def parameters(self):
    """
    Returns the parameters of the JBA.
    """
    return self._params
        
  def internalDelay(self):
    return self._params["internalDelay"]+self._params["starkPulseLength"]+self._params["starkPulseDelay"]*0
    
  def saveState(self,name):
    state = dict()
    state["params"] = copy.deepcopy(self._params)
    state["readoutWaveform"] = (copy.deepcopy(self._readoutWaveform)).tolist()
    return state
    
  def restoreState(self,state):
    self._params = copy.deepcopy(state["params"])
    self._readoutWaveform = array(copy.deepcopy(state["readoutWaveform"]))
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
    self._afg.writeWaveform(self._params["waveform"],fullWaveform)
    self._afg.setWaveform(self._params["waveform"])
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
    self._readoutWaveform = self._afg.readWaveform(self._params["waveform"])
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
    self._awg.createWaveform(self._params["waveform"],data,'INT')

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
    
  def measureSCurve(self,voltages = None,ntimes = 40,microwaveOff = True):
    self.notify("status","Measuring S curve...")
    def getVoltageBounds(v0,jba,variable,ntimes):
      v = v0
      jba.setVoltage(v)
      jba._acqiris.bifurcationMap(ntimes = ntimes)
      p = jba._acqiris.Psw()[variable]
      
      while p > 0.03 and v < v0*2.0:
        v*=1.05
        jba.setVoltage(v)
        jba._acqiris.bifurcationMap(ntimes = ntimes)
        p = jba._acqiris.Psw()[variable]
      vmax = v
      
      v = v0
      jba.setVoltage(v)
      jba._acqiris.bifurcationMap(ntimes = ntimes)
      p = jba._acqiris.Psw()[variable]
      
      while p < 0.98 and v > v0/2.0:
        v/=1.05
        jba.setVoltage(v)
        jba._acqiris.bifurcationMap(ntimes = ntimes)
        p = jba._acqiris.Psw()[variable]
      vmin = v
      return (vmin*0.95,vmax*1.2)

    try:
      v0 = self.voltage()
      state = self._qubitmwg.output()
      self._attenuator.turnOn()
      data = Datacube("S Curve")
      dataManager = DataManager()
      dataManager.addDatacube(data)
      if microwaveOff:
        self._qubitmwg.turnOff()
      if voltages == None:
        self.notify("status","Searching for proper voltage range...")
        (vmin,vmax) = getVoltageBounds(v0,self,self._params["variable"],ntimes)
        voltages = arange(vmin,vmax,0.005)
        self.notify("status","Measuring S curve in voltage range  [%g - %g]..." % (vmin,vmax))
      for v in voltages:
        self.setVoltage(v)
        self._acqiris.bifurcationMap(ntimes = ntimes)
        data.set(v = v)
        data.set(**(self._acqiris.Psw()))
        data.commit()
        self.notify("sCurve",(data.column("v"),data.column(self._params["variable"])))
    finally:
      self.notify("status","S curve complete.")
      self.setVoltage(v0)
      if state:
        self._qubitmwg.turnOn()
    
    
  #Calibrates the Qubit readout and adjust the switching probability with a given accuracy.
  def calibrate(self,level = 0.1,accuracy = 0.025,microwaveOff = True):
    try:
      state = self._qubitmwg.output()
      self._attenuator.turnOn()
      if microwaveOff:
        self._qubitmwg.turnOff()
      self._muwave.turnOn()
      self.notify("status","Starting calibration...")
      voltages = arange(0.3,1.8,0.05)
      (ps,max,maxVoltage) = self._attenuatorRangeCheck(voltages)
      voltages2 = arange(maxVoltage-0.1,maxVoltage+0.1,0.005)
      (p2s,max,maxVoltage2) = self._attenuatorRangeCheck(voltages2)
      self.notify("status","Voltage calibration complete...")
      self._attenuator.setVoltage(maxVoltage2)
      self.notify("status","Adjusting offset and rotation...")
      self.adjustRotationAndOffset()
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
    data = Datacube("Variance")
    for i in range(0,len(voltages)):
      if self.stopped():
        self._stopped = False
        raise Exception("Got stopped!")
      v = voltages[i] 
      self._attenuator.setVoltage(v)
      self._acqiris.bifurcationMap(ntimes = 10)
      trends = self._acqiris.trends()
      varsum =cov(trends[self._params["acqirisChannel"]])+cov(trends[self._params["acqirisChannel"]+1])
      data.set(v = v)
      data.set(varsum=varsum)
      data.commit()
      self.notify("variance",(data.column("v"),data.column("varsum")))
      self.notify("status","Variance at %g V: %g" % (v,varsum))
      print "Variance: %f" % varsum
      self.variances[i,1] = varsum
      ps.append(varsum)
      if varsum > max:
        max = varsum
        maxVoltage = voltages[i]
    return (ps,max,maxVoltage)
    
  def switchingProbability(self):
    self._acqiris.bifurcationMap(ntimes = 80)
    p = self._acqiris.probabilities()[self._params["acqirisChannel"]/2,0]
    return p
    
  def separationMeasure(self,acquire = True):
    if acquire:
      self._acqiris.bifurcationMap()
    trends = self._acqiris.trends()
    angle = self._acqiris.bifurcationMapRotation()[self._params["acqirisChannel"]/2]
    rotatedTrends = zeros((2,len(trends[self._params["acqirisChannel"]])))
    rotatedTrends[0,:] = trends[self._params["acqirisChannel"],:]*cos(angle) + trends[self._params["acqirisChannel"]+1,:]*sin(angle)
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
    angle = self._acqiris.bifurcationMapRotation()[self._params["acqirisChannel"]/2]
    p = self._acqiris.probabilities()[self._params["acqirisChannel"]/2,0]
    trends = self._acqiris.trends()
    rotatedTrends = zeros((2,len(trends[0])))
    rotatedTrends[0,:] = trends[self._params["acqirisChannel"],:]*cos(angle) + trends[self._params["acqirisChannel"]+1,:]*sin(angle)
    rotatedTrends[1,:] = -trends[self._params["acqirisChannel"],:]*sin(angle) + trends[self._params["acqirisChannel"]+1,:]*cos(angle)
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
      if verbose:
            print "sensitivity is %g/V" % sensitivity
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
        self._attenuator.setVoltage(voltage)
        v = self._attenuator.voltage()
        p = self.switchingProbability()
      self.notify("status","Switching probability: %g %%" % (p*100))
      return (p,cnt)
    finally:
      if status == True:
        self._qubitmwg.turnOn()

  def adjustSwitchingLevel2(self,level = 0.2,accuracy = 0.05,verbose = False,minSensitivity = 15.0,microwaveOff = True,nmax = 100,checkBivaluated=True):
    try:
      status = self._qubitmwg.output()
      if microwaveOff:
        self._qubitmwg.turnOff()
      vOld = self._attenuator.voltage()
      #First check that the distribution is bivaluated with a sufficient gap between the 2 values (with separationMeasure().
      if (checkBivaluated and (self.separationMeasure() < 0.5)):
        v = 0.0
        print "Separation (%g) is not good, re-adjusting..." % self.separationMeasure(acquire = False)
        self._attenuator.setVoltage(v)
        while self.separationMeasure(acquire = True) < 3.0:
          if verbose:
            print "Separation at %g V is %g" % (v,self.separationMeasure(acquire = False))
          v+=0.1
          self._attenuator.setVoltage(v)
          if v >= 2.0:
            self._attenuator.setVoltage(vOld)
            raise Exception("Cant't find a good working point!")
      #Measure the std of Ps
      std=0
      #Start the search
      vmin=0
      vmax=2
      vOld = self._attenuator.voltage()
      pOld = self.switchingProbability()
      dv=0.02
      cnt = 0
      while fabs(pOld-level)>accuracy:
        if self.stopped():
          raise Exception("Got stopped!")
        # increase the increment until dp is larger than twice both the variance and the target accuracy
        dp=0
        dv2=0
        while abs(dp)<2*max(std,accuracy):
          dv2+=dv
          v=vOld+dv2
          self._attenuator.setVoltage(v)
          p = self.switchingProbability()
          dp=p-pOld
        dv=dv2
        vOld=v
        self.notify("status","Switching probability at %g V: %g" % (v,p))
        # update the vmin-vmax range
        if p>level+3*max(std,accuracy):
          vmin=vOld
        if p<level-3*max(std,accuracy):
          vmax=vOld
        #Vary v according to dp/dv but staying in the vmin-vmax range
        if fabs(pOld-level)>accuracy :
          v=vOld+(p-level)*dv/dp
          v=min(v,vmax)
          v=max(v,vmin)
          if verbose:
            print "vmin= %g, vmax=%g, v = %g, p = %g, dv = %f, dp %f, next v=%f" % (vmin,vmax,vOld,p,dv,dp,v)
          if v==vOld:
            raise Exception("Twice the same attenuation voltage v although target was not reached!")   
          vOld=v
          pOld=p
          cnt+=1
          if cnt>nmax:
            raise Exception("Maximum number of steps exceeded!")
        self._attenuator.setVoltage(vOld)
        vOLd = self._attenuator.voltage()
        pOld = self.switchingProbability()
      self.notify("status","Switching probability: %g %%" % (pOld*100))
      return (p,cnt)
    finally:
      if status == True:
        self._qubitmwg.turnOn()
      
    
  def adjustRotationAndOffset(self):
    try:
      state = self._qubitmwg.output() # memorize microw generator state
      self._qubitmwg.turnOff()        # and switch microw off
      self._attenuator.turnOn()       # switch attenuator control voltage to on
      #We set all offsets and angles to 0.
      self._acqiris.ConfigureChannel(self._params["acqirisChannel"]+1,offset = 0)
      self._acqiris.ConfigureChannel(self._params["acqirisChannel"]+2,offset = 0)
      self._acqiris.setBifurcationMapRotation(self._params["acqirisChannel"]/2,0)
      cnt = 0  
      offsets = [0,0]                 # reinit offsets
      while cnt < 3:                  # repeat for higher precision
        print cnt
        cnt+=1
        self._acqiris.bifurcationMap(calculateTrends = True,ntimes = 40)    
        trends = self._acqiris.trends()
        means = mean(trends[self._params["acqirisChannel"]:self._params["acqirisChannel"]+2,:],axis = 1)    
        covar = var(trends[self._params["acqirisChannel"]:self._params["acqirisChannel"]+2,:])    
        offsets[0]-=means[0]
        offsets[1]-=means[1]    
        self.notify("iqdata",trends)
        self._acqiris.ConfigureChannel(self._params["acqirisChannel"]+1,offset = offsets[0])
        self._acqiris.ConfigureChannel(self._params["acqirisChannel"]+2,offset = offsets[1])   
        print covar   
        print means
      covar = cov(trends[self._params["acqirisChannel"]]-means[0],trends[self._params["acqirisChannel"]+1]-means[1]) 
      #We calculate the eigenvectors of the variance/covariance matrix.  
      la,v = linalg.eig(covar)    
      #We calculate the rotation angle from the eigenvector matrix.
      #M = [(cos(theta),-sin(theta)),(sin(theta),cos(theta))
      if la[1] > la[0]:
        angle = math.atan2(v[0,0],v[0,1])
      else:
        angle = math.atan2(v[1,0],v[0,0])    
      self._acqiris.setBifurcationMapRotation(self._params["acqirisChannel"]/2,angle)
      pBefore = self._acqiris.probabilities()[self._params["acqirisChannel"]/2,0]
      oldVoltage = self._attenuator.voltage()
      self._attenuator.setVoltage(oldVoltage+0.1)
      self._acqiris.bifurcationMap(calculateTrends = True,ntimes = 80)
      pAfter = self._acqiris.probabilities()[self._params["acqirisChannel"]/2,0]
      if pAfter > pBefore:
        angle+=math.pi
        self._acqiris.setBifurcationMapRotation(self._params["acqirisChannel"]/2,angle)    
      self._attenuator.setVoltage(oldVoltage)
      self._acqiris.bifurcationMap(calculateTrends = True,ntimes = 80)
      trends = self._acqiris.trends()
      self.trends = zeros((2,len(trends[0,:])))
  
      self.trends[0,:] = trends[self._params["acqirisChannel"],:]*cos(angle) + trends[self._params["acqirisChannel"]+1,:]*sin(angle)
      self.trends[1,:] = -trends[self._params["acqirisChannel"],:]*sin(angle) + trends[self._params["acqirisChannel"]+1,:]*cos(angle)
      
      print cov(self.trends[0],self.trends[1])
  
      self.notify("iqdata",self.trends)
    finally:
      if state == True:
        self._qubitmwg.turnOn()
  
  def adjustRotationAndOffset2(self):
    try:
      state = self._qubitmwg.output() # memorize microw generator state
      self._qubitmwg.turnOff()        # and switch microw off
      self._attenuator.turnOn()       # switch attenuator control voltage to on
      cnt = 0  
      offsets=self_.acqiris.parameters()["offsets"][0:2]
      while cnt < 3:                  # repeat for higher precision
        print cnt
        cnt+=1
        self._acqiris.bifurcationMap(calculateTrends = True,ntimes = 40)    
        trends = self._acqiris.trends()
        means = mean(trends[self._params["acqirisChannel"]:self._params["acqirisChannel"]+2,:],axis = 1)    
        offsets[0]-=means[0]
        offsets[1]-=means[1]    
        self.notify("iqdata",trends)
        self._acqiris.ConfigureChannel(self._params["acqirisChannel"]+1,offset = offsets[0])
        self._acqiris.ConfigureChannel(self._params["acqirisChannel"]+2,offset = offsets[1])   
        print means
      angle=self_.acqiris.parameters()["rotation"][self._params["acqirisChannel"]]
      #We calculate the covariance matrix. 
      covar = cov(trends[self._params["acqirisChannel"]]-means[0],trends[self._params["acqirisChannel"]+1]-means[1]) 
      la,v = linalg.eig(covar)        #We calculate the eigenvalues and eigenvectors of the covariance matrix.    
      #We calculate the rotation angle from the eigenvector matrix M = [(cos(theta),-sin(theta)),(sin(theta),cos(theta))], using the eigenvector of maximum weight (max eigenvalues)
      if la[1] > la[0]:
        angle+= math.atan2(v[0,0],v[0,1])
      else:
        angle+= math.atan2(v[1,0],v[0,0])
      pi=math.pi
      angle=math.fmod(angle+pi,2*pi)-pi    
      #We set the rotation angle
      self._acqiris.setBifurcationMapRotation(self._params["acqirisChannel"]/2,angle)
      pBefore = self._acqiris.probabilities()[self._params["acqirisChannel"]/2,0]
      oldVoltage = self._attenuator.voltage()
      self._attenuator.setVoltage(oldVoltage+0.1)
      self._acqiris.bifurcationMap(calculateTrends = True,ntimes = 80)
      pAfter = self._acqiris.probabilities()[self._params["acqirisChannel"]/2,0]
      if pAfter > pBefore:
        angle=math.fmod(angle+2*pi,2*pi)-pi
        self._acqiris.setBifurcationMapRotation(self._params["acqirisChannel"]/2,angle)    
      self._attenuator.setVoltage(oldVoltage)
      self._acqiris.bifurcationMap(calculateTrends = True,ntimes = 80)
      trends = self._acqiris.trends()
      self.trends = zeros((2,len(trends[0,:])))
  
      self.trends[0,:] = trends[self._params["acqirisChannel"],:]*cos(angle) + trends[self._params["acqirisChannel"]+1,:]*sin(angle)
      self.trends[1,:] = -trends[self._params["acqirisChannel"],:]*sin(angle) + trends[self._params["acqirisChannel"]+1,:]*cos(angle)
      
      print cov(self.trends[0],self.trends[1])
  
      self.notify("iqdata",self.trends)
    finally:
      if state == True:
        self._qubitmwg.turnOn()
        
  def initialize(self,**kwargs):
    manager = Manager()
    
    defaultParams = {'acqirisChannel' : 0,'variable' : "p1x",'muwave' : "cavity1mwg",'attenuator' : "AttS2",'acqiris' : "acqiris",'qubitmwg' : "qubit1mwg",'polarity' : 1,'afg' : "afg3",'waveform' : "USER1",'internalDelay' : 243,'returnDelay' : 57,'acquisitionTime' : 400,'sampleInterval' : 3e-9,'trigSlope' : 0,'safetyMargin' : 100}

    self._params = kwargs
    
    for key in defaultParams.keys():
      if not key in self._params:
        self._params[key] = defaultParams[key]
    
    self._muwave = manager.getInstrument(self._params["muwave"])
    self._register = manager.getInstrument("register")
    self._acqiris = manager.getInstrument(self._params["acqiris"])
    self._afg = manager.getInstrument(self._params["afg"])
    self._attenuator = manager.getInstrument(self._params["attenuator"])
    self._qubitmwg = manager.getInstrument(self._params["qubitmwg"])
      
#    self.loadReadoutWaveform()
