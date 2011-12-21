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
    """
    Initialize instrument
    """
    instrumentManager=Manager()
    self._pulseGenerator=instrumentManager.getInstrument(generator)
    self._pulseAnalyser=instrumentManager.getInstrument(analyser)
    self._params=dict()
    self._params["pulseGenerator"]=generator
    self._params["pulseAnalyser"]=analyser
    self._change=True
  
  def parameters(self):
    """
    Return parameters
    """    
    return self._params      


  def init(self):
    """
    Clear the JBA (no frequency to analyse)
    """
    self._pulseGenerator.clearPulse()
    self._pulseAnalyser.clear()
    self._change=True
          
  def frequency(self, frequency, amplitude=1., duration=0., gaussian=False, delayFromZero=0,phase=0,shape=None):
    """
    Add a new frequency to analyse
    """
    while True:
      a = self._pulseGenerator.generatePulse(duration=duration, frequency=frequency, amplitude=amplitude, DelayFromZero=delayFromZero,useCalibration=True, phase=phase,shape=shape)
      b = self._pulseAnalyser.addFrequency(f=frequency)
      if a and b:
        break
      else:
        self.init()
    self._change=True    
        
  def analyse(self, debug=False, avcofr=None):
    """
    Analyse frequencies previously added
    """
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
    """
    Acquire and calculate if JBA bifurcates or not
    """
    if self._change:
      self._pulseGenerator.sendPulse()
      time.sleep(0.5)
    (av, co, fr)=self._pulseAnalyser.analyse()
    self._change=False
    r=self._pulseAnalyser._acqiris.multiplexedBifurcationMapAdd(co,fr)
    proba=self._pulseAnalyser._acqiris.convertToProbabilities(r)
    return (av, co, fr, proba)
    
  def calibrate(self,level = 0.1,accuracy = 0.025, **kwargs):
    """
    Calibrate Offset and rotation for a single frequency f, and store it
    """
    self.notify("status","Starting calibration...")
    voltages = arange(0.2,1.5,0.05)
    (ps,max,maxVoltage,data1) = self._findAmplitude(voltages, **kwargs)
    voltages2 = arange(maxVoltage-0.1,maxVoltage+0.1,0.005)
    (p2s,max,maxVoltage2,data2) = self._findAmplitude(voltages2,**kwargs)
    self.notify("status","Voltage calibration complete...")
    self.voltage=maxVoltage2
#    self.notify("status","Adjusting offset and rotation...")
    self._adjustRotationAndOffset(**kwargs)
#    return (data1,data2)
#    self.adjustSwitchingLevel(level,accuracy)
#    self.notify("status","Calibration complete. Measure of separation: %g" % self.separationMeasure(acquire = False))
#    return (voltages,ps,voltages2,p2s,self.trends)
    
     
  def _findAmplitude(self,voltages,frequency,shape):
    """
    Only used by function calibrate.
    Measure and find the amplitude where the JBA is bi-evaluated, go to this point, and store this amplitude
    """
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
    """
    Only used by function calibrate, use only where the JBA is bi-evaluated
    To find the rotation angle and offsets to discriminate properly the bi-evaluated values, at a single frequency, and store thoses values
    """
    (av,co,fr) = self.analyse(**kwargs)
    Io=mean(co[0,:,0])
    Qo=mean(co[1,:,0])
    covar=(var(co[0,:,0]),var(co[1,:,0]))
    angle=math.atan2(covar[0],covar[1])
    self._pulseAnalyser._acqiris.multiplexedBifurcationMapSetRotation(angle,Io,Qo,fr[0])
    
    
  def acquire(self, co,fr):
    """
    Convert waveforms in bifurcation click and probabilities, using offset and rotation angles previously sent
    Return probabilities
    """
    c = self._pulseAnalyser._acqiris.multiplexedBifurcationMapAdd(co,fr)
    r = self._pulseAnalyser._acqiris.convertToProbabilities(c)
    return r

  def caracteriseJBA(self, shape, frequencies,test=False):
    for f in frequencies:
      self._pulseGenerator._MWSource.setFrequency(f)
      self._pulseGenerator._IQMixer.calibrate(offsetOnly=True)
      self.frequency(frequency=f,shape=shape)
      self._pulseGenerator.sendPulse()
      
