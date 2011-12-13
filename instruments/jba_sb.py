import sys
import getopt
import numpy
from matplotlib.pyplot import *
from pyview.ide.mpl.backend_agg import figure
from pyview.lib.classes import *
from pyview.helpers.instrumentsmanager import Manager
from numpy import *
register=Manager().getInstrument('register')
import time

from pyview.lib.datacube import Datacube

class Instr(Instrument):
  
  def initialize(self, name, generator, analyser):
  
    instrumentManager=Manager()
    self._pulseGenerator=instrumentManager.getInstrument(generator)
    self._pulseAnalyser=instrumentManager.getInstrument(analyser)
    self._params=dict()
    self._params["pulseGenerator"]=generator
    self._params["pulseAnalyser"]=analyser
    self._change=True
  
  def parameters(self):    
    return self._params      
  def init(self):
    self._pulseGenerator.clearPulse()
    self._pulseAnalyser.clear()
    self._change=True
          
  def frequency(self, frequency, amplitude=1., duration=0., gaussian=False, delayFromZero=0,phase=0,shape=None):
    while True:
      a = self._pulseGenerator.generatePulse(duration=duration, frequency=frequency, amplitude=amplitude, DelayFromZero=delayFromZero,useCalibration=True, phase=phase,shape=shape)
      b = self._pulseAnalyser.addFrequency(f=frequency)
      if a and b:
        break
      else:
        self.init()
    self._change=True    
        
  def analyse(self, debug=True, avcofr=None):
    if debug:
      return avcofr
    else:
      if self._change:
        self._pulseGenerator.sendPulse()
        time.sleep(0.5)
      (av, co, fr)=self._pulseAnalyser.analyse()
      self._change=False
      return (av, co, fr)
    
  def calculateBifurcation(self):
    if self._change:
      self._pulseGenerator.sendPulse()
      time.sleep(0.5)
    (av, co, fr)=self._pulseAnalyser.analyse()
    self._change=False
    self._pulseAnalyser._acqiris.multiplexedBifurcationMap(co,fr)
    return (av, co, fr)
    
  def calibrate(self,level = 0.1,accuracy = 0.025, **kwargs):
    self.notify("status","Starting calibration...")
    voltages = arange(0.2,1.5,0.05)
    (ps,max,maxVoltage,data1) = self._findAmplitude(voltages, **kwargs)
    voltages2 = arange(maxVoltage-0.1,maxVoltage+0.1,0.005)
    (p2s,max,maxVoltage2,data2) = self._findAmplitude(voltages2,**kwargs)
    self.notify("status","Voltage calibration complete...")
    self.voltage=maxVoltage2
    return (data1,data2)
#    self.notify("status","Adjusting offset and rotation...")
#    self._adjustRotationAndOffset()
#    return (data1,data2)
#    self.adjustSwitchingLevel(level,accuracy)
#    self.notify("status","Calibration complete. Measure of separation: %g" % self.separationMeasure(acquire = False))
#    return (voltages,ps,voltages2,p2s,self.trends)
    
     
  def _findAmplitude(self,voltages,frequency,shape):
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
      self.init()
      self.frequency(frequency=frequency,shape=v*shape)
      (av,trends, fr)=self.analyse()
      varsum =cov(trends[0,:,0])+cov(trends[1,:,0])
      data.set(v = v)
      data.set(varsum=varsum)
      data.commit()
      self.notify("variance",(data.column("v"),data.column("varsum")))
      self.notify("status","Variance at %g V: %g" % (v,varsum))
      print "Variance at v = %f : %f" % (v,varsum)
      self.variances[i,1] = varsum
      ps.append(varsum)
      if varsum > max:
        max = varsum
        maxVoltage = voltages[i]
    self.frequency(frequency=frequency,shape=maxVoltage*shape)
    return (ps,max,maxVoltage,data)

    
  def _adjustRotationAndOffset(self, **kwargs):
    (av,co,fr) = self.analyse(**kwargs)
    Io=mean(co[0,:,0])
    Qo=mean(co[1,:,0])
    
    covar=(var(co[0,:,0]),var(co[1,:,0]))

    angle=math.atan2(covar[0],covar[1])
    self._pulseAnalyser._acqiris.multiplexedBifurcationMapSetRotation(angle,Io,Qo,fr[0])
    
    return angle
    
  def acquire(self, co,fr):
    return self._pulseAnalyser._acqiris.multiplexedBifurcationMapAdd(co,fr)


  def caracteriseJBA(self, shape, frequencies,test=False):
    for f in frequencies:
      self._pulseGenerator._MWSource.setFrequency(f)
      self._pulseGenerator._IQMixer.calibrate(offsetOnly=True)
      self.frequency(frequency=f,shape=shape)
      self._pulseGenerator.sendPulse()
      
