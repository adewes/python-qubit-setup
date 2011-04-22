#This class optimizes the AWG offset in order to increase the contrast
import scipy
import sys
from numpy import *
import traceback
import scipy.optimize

if 'lib.datacube' in sys.modules:
  reload(sys.modules['lib.datacube'])
  
from pyview.lib.classes import *
from pyview.lib.datacube import Datacube

import sys
import time

print "iq_level_optimization reloaded"

class IqOptimization(Reloadable):
  
  """
  Optimizes the parameters of an IQ mixer.
  """
  
  def __init__(self,mwg,fsp,awg,channels = [1,2]):
    Reloadable.__init__(self)
    self._mwg = mwg
    self._fsp = fsp
    self._awg = awg
    self._awgChannels = channels
    self.initCalibrationData()
  
  def initCalibrationData(self):
    """
    Initialize the datacubes that contain the IQ calibration data.
    """
    self._offsetCalibrationData = Datacube()
    self._offsetCalibrationData.setName("IQ mixer calibration - Offset Calibration Data")
    self._powerCalibrationData = Datacube()
    self._powerCalibrationData.setName("IQ mixer calibration - Power Calibration Data")
    self._sidebandCalibrationData = Datacube()
    self._sidebandCalibrationData.setName("IQ mixer calibration - Sideband Mixing Calibration Data")
  
  def sidebandCalibrationData(self):
    return self._sidebandCalibrationData
    
  def setSidebandCalibrationData(self,data):
    self._sidebandCalibrationData = data
  
  def offsetCalibrationData(self):
    """
    Return the datacube containing the offset calibration data.
    """
    return self._offsetCalibrationData
  
  def setOffsetCalibrationData(self,data):
    self._offsetCalibrationData = data
    self.updateOffsetCalibrationInterpolation()
    
  def updateOffsetCalibrationInterpolation(self):
    frequencies = self._offsetCalibrationData.column("frequency")
    self._iOffsetInterpolation = scipy.interpolate.interp1d(frequencies,self._offsetCalibrationData.column("lowI"))        
    self._qOffsetInterpolation = scipy.interpolate.interp1d(frequencies,self._offsetCalibrationData.column("lowQ"))
    
        
  
  def powerCalibrationData(self):
    """
    Return the datacube containing the power calibration data.
    """
    return self._powerCalibrationData

  def setPowerCalibrationData(self,data):
    self._powerCalibrationData = data
  
  def teardown(self):
  	"""
  	Restore the original configuration.
  	"""
  	self._fsp.loadConfig("IQCalibration")
  	self._awg.loadSetup("iq_calibration.awg")
  	self._mwg.restoreState(self._mwgState)
  
  def setup(self,averaging = 10,reference = 0):
    """
    Configure the AWG and the FSP for the IQ mixer calibration.
    """
    self._fsp.storeConfig("IQCalibration")
    self._awg.saveSetup("iq_calibration.awg")
    self._mwgState = self._mwg.saveState("iq calibration")
    self._fsp.write("SENSE1:FREQUENCY:SPAN 0 MHz")
#    period = int(1.0/self._awg.repetitionRate()*1e9*0.8)
    self._fsp.write("SWE:TIME 2 ms")
    self._rbw = 300
    self._fsp.write("SENSE1:BAND:RES %f Hz" % self._rbw)
    self._fsp.write("SENSE1:BAND:VIDEO AUTO")
    self._fsp.write("TRIG:SOURCE EXT")
    self._fsp.write("TRIG:HOLDOFF 0 s")
    self._fsp.write("TRIG:LEVEL 0.5 V")
    self._fsp.write("TRIG:SLOP POS")
    self._fsp.write("SENSE1:AVERAGE:COUNT %d" % averaging)
    self._fsp.write("SENSE1:AVERAGE:STAT1 ON")
    self._fsp.write("DISP:TRACE1:Y:RLEVEL %f" % reference)
    self.setupWaveforms()
  	
  def setupWaveforms(self):
    self._awg.write("AWGC:RMOD CONT")
    period = int(1.0/self._awg.repetitionRate()*1e9)
    waveformOffset = zeros((period))
    waveformActive = zeros((period))+1.0
    waveformPassive = zeros((period))-1.0
    self._markers = zeros((period),dtype = uint8)
    self._markers[1:len(self._markers)/2] = 255
    self._awg.createRawWaveform("IQ_Offset_Calibration",waveformOffset,self._markers,"REAL")
    self._awg.createRawWaveform("IQ_Power_Calibration_active",waveformActive,self._markers,"REAL")
    self._awg.createRawWaveform("IQ_Power_Calibration_passive",waveformPassive,self._markers,"REAL")

    length = int(1.0/self._awg.repetitionRate()*1e9)
    waveform = self.generateSidebandWaveform(f_sb = 0, c = 0,phi = 0,length = length)

    self._awg.createRawWaveform("IQ_Sideband_Calibration_I",waveform,self._markers,"REAL")
    self._awg.createRawWaveform("IQ_Sideband_Calibration_Q",waveform,self._markers,"REAL")
        
  def loadSidebandWaveforms(self):
    self._awg.setWaveform(1,"IQ_Sideband_Calibration_I")
    self._awg.setWaveform(2,"IQ_Sideband_Calibration_Q")
    self._awg.setWaveform(3,"IQ_Sideband_Calibration_I")
    self._awg.setWaveform(4,"IQ_Sideband_Calibration_Q")

  def loadSidebandCalibrationWaveform(self,f_sb = 0,c = 0,phi = 0):
    
    length = int(1.0/self._awg.repetitionRate()*1e9)
    waveform = self.generateSidebandWaveform(f_sb = f_sb, c = c,phi = phi,length = length)
    self._awg.createRawWaveform("IQ_Sideband_Calibration_I",real(waveform)*0.5,self._markers,"REAL")
    self._awg.createRawWaveform("IQ_Sideband_Calibration_Q",imag(waveform)*0.5,self._markers,"REAL")

    return waveform
    
  def sidebandParameters(self,f_c,f_sb):
  
    if self.sidebandCalibrationData().column("f_c") == None:
      return (0,0)
  
    min_index = argmin(abs(self.sidebandCalibrationData().column("f_c")-f_c))
    
    if min_index == None:
      return (0,0)
    
    calibrationData = self.sidebandCalibrationData().childrenAt(min_index)[0]
    
    rows = calibrationData.search(f_sb = f_sb)
    
    if rows != []:
      c = calibrationData.column("c")[rows[0]]
      phi = calibrationData.column("phi")[rows[0]]
    else:      
      phiInterpolation = scipy.interpolate.interp1d(calibrationData.column("f_sb"),calibrationData.column("phi"))      
      cInterpolation = scipy.interpolate.interp1d(calibrationData.column("f_sb"),calibrationData.column("c"))      
      
      c = cInterpolation(f_sb)
      phi = phiInterpolation(f_sb)
    
    return (c,phi)
        

  def generateCalibratedSidebandWaveform(self,f_c,f_sb = 0,length = 100,delay = 0):
  
    (c,phi) = self.sidebandParameters(f_c,f_sb)

#    print "Generating a sideband waveform at f_c = %g GHz at f_sb = %g GHZ, c = %g, phi = %g deg" % (f_c,f_sb,c,phi*180.0/math.pi)
    
    return self.generateSidebandWaveform(f_sb,length = length,delay = delay,c = c,phi = phi)*0.8  
    

  def generateSidebandWaveform(self,f_sb = 0,c = 0,phi = 0,length = 100,delay = 0,normalize = True):
    """
    Generates a sideband waveform using a sideband frequency "f_sb", an amplitude correction "c" and a phase correction "phi"
    """
    
    if length == 0:
      return array([])
    
    waveformIQ = zeros((max(1,length)),dtype = complex128)

    times = arange(0,length,1)
    
    cr = c*exp(1j*phi)
    
    waveformIQ = exp(-1.j*f_sb*2.0*math.pi*(times+float(delay)))+cr*exp(1.j*f_sb*2.0*math.pi*(times+float(delay)))

    return waveformIQ

  def calibrateIQPower(self,amplitude = 3.0):
    """
    Calibrate the IQ mixer output power.
    """
    try:
      self.setup(averaging = 100,reference = 0)
      params = dict()
      params["power"] = self._mwg.power()
      params["amplitude"] = amplitude
      params["channels"] = self._awgChannels
      params["mwg"] = self._mwg.name()
      params["awg"] = self._awg.name()
      params["fsp"] = self._fsp.name()
      self.powerCalibrationData().setParameters(params)
      freqs = self.offsetCalibrationData().column("frequency")
      Is = self.offsetCalibrationData().column("lowI")
      Qs = self.offsetCalibrationData().column("lowQ")
      for i in range(0,len(freqs)):
        f = freqs[i]
        amp = max(0,min(4.5,4.5-2.0*max(Is[i],Qs[i])))
        self._mwg.setFrequency(f)
        self._awg.setLow(self._awgChannels[0],Is[i])
        self._awg.setLow(self._awgChannels[1],Qs[i])
        self._awg.setHigh(self._awgChannels[0],Is[i]+                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             amp)
        self._awg.setHigh(self._awgChannels[1],Qs[i]+amp)
      	self._fsp.write("SENSE1:FREQUENCY:CENTER %f GHZ" % f)
      	for channels in [[self._awgChannels[0],self._awgChannels[1],"I"],[self._awgChannels[1],self._awgChannels[0],"Q"]]:
          name = channels[2]
          
          self._awg.setWaveform(channels[0],"IQ_Power_Calibration_passive")
          self._awg.setWaveform(channels[1],"IQ_Power_Calibration_passive")
          
          time.sleep(0.5)
          
          trace = self._fsp.getSingleTrace()
          zero = mean(trace[1])
          
          self._awg.setWaveform(channels[0],"IQ_Power_Calibration_active")
          
          time.sleep(0.5)
          
          trace = self._fsp.getSingleTrace()
          level = mean(trace[1])
          diff = level - zero
          
          #This is the linear output coefficient:
          coefficient =(pow(10.0,level/10.0)-pow(10.0,zero/10.0))/pow(amp,2.0)
          self._powerCalibrationData.set(frequency = f)
          params = {"power"+name : sqrt(exp(log(10.0)*diff/10.0)),"powerDBM"+name : diff, "zero"+name : zero,"level"+name : level,"coeff"+name : coefficient}
          self._powerCalibrationData.set(**params)
      	self._powerCalibrationData.commit()
    finally:
      self.teardown()
    
  def calibrateIQOffset(self,frequencyRange = arange(4.5,8.6,0.1)):
    """
    Calibrate the IQ mixer DC offset.
    """
    try:
      self.setup()
      params = dict()
      params["power"] = self._mwg.power()
      params["channels"] = self._awgChannels
      params["mwg"] = self._mwg.name()
      params["awg"] = self._awg.name()
      params["fsp"] = self._fsp.name()
      self.offsetCalibrationData().setParameters(params)
      self._mwg.turnOn()
      for channel in [1,2,3,4]:
        self._awg.setWaveform(channel,"IQ_Offset_Calibration")
      for frequency in frequencyRange:
        self._mwg.setFrequency(frequency)
        (voltages,minimum) = self.optimizeIQMixerPowell()
        minimum = self.measurePower(voltages) 
        print "Optimum value of %g dBm at offset %g V, %g V" % (minimum,voltages[0],voltages[1])
        rows = self._offsetCalibrationData.search(frequency = frequency)
        if rows != []:
          self._offsetCalibrationData.removeRows(rows)
        self._offsetCalibrationData.set(frequency = frequency,lowI = voltages[0],lowQ = voltages[1],minimum = minimum)
        self._offsetCalibrationData.commit()
        self._offsetCalibrationData.sortBy("frequency")
        self._offsetCalibrationData.savetxt()
    except StopThread:
      pass
    except:
      traceback.print_exc()
    finally:
      self.teardown()
      self.updateOffsetCalibrationInterpolation()
      
  def calibrateSidebandMixing(self,frequencyRange = arange(4.5,8.6,0.1),sidebandRange = arange(-0.3,0.3,0.1)+0.05):
    """
    Calibrate the IQ mixer sideband generation.
    """
    try:
      self.setup()
      params = dict()
      params["power"] = self._mwg.power()
      params["channels"] = self._awgChannels
      params["mwg"] = self._mwg.name()
      params["awg"] = self._awg.name()
      params["fsp"] = self._fsp.name()
      self.sidebandCalibrationData().setParameters(params)
      self._mwg.turnOn()
      channels = self._awgChannels
      self.loadSidebandWaveforms()
      for f_c in frequencyRange:
        #We round the center frequency to an accuracy of 1 MHz
        f_c = round(f_c,3)
        self.setDriveFrequency(f_c)
        self._awg.setAmplitude(channels[0],1.26)
        self._awg.setAmplitude(channels[1],1.26)
        data = Datacube("f_c = %g GHz" % f_c)
        rowsToDelete = []
        for i in range(0,len(self._sidebandCalibrationData.column("f_c"))):
          if abs(self._sidebandCalibrationData.column("f_c")[i]-f_c) < 0.1:
            rowsToDelete.append(i)
        self._sidebandCalibrationData.removeRows(rowsToDelete)
        self._sidebandCalibrationData.addChild(data)
        self._sidebandCalibrationData.set(f_c = f_c)
        self._sidebandCalibrationData.commit()
        for f_sb in sidebandRange: 
          print "f_c = %g GHz, f_sb = %g GHz" % (f_c,f_sb)
          self._fsp.write("SENSE1:FREQUENCY:CENTER %f GHZ" % (f_c+f_sb))
          result = scipy.optimize.fmin_powell(lambda x,*args: self.measureSidebandPower(x,*args),[0,0],args = [f_sb],full_output = 1,xtol = 0.00001,ftol = 1e-4,maxiter = 2)
          params = result[0]
          value = result[1]
          print "f_c = %g GHz, f_sb = %g GHz, c = %g, phi = %g rad" % (f_c,f_sb,params[0],params[1])
          self.loadSidebandCalibrationWaveform(f_sb = f_sb,c = params[0],phi = params[1])
          for i in [-3,-2,-1,0,1,2,3]:
            self._fsp.write("SENSE1:FREQUENCY:CENTER %f GHZ" % (f_c+f_sb*i))
            if i < 0:
              suppl = "m"
            else:
              suppl = ""
            data.set(**{"p_sb%s%d" % (suppl,abs(i)) : self.measureAveragePower()})
          data.set(f_c = f_c,f_sb = f_sb,c = params[0],phi = params[1])
          data.commit()
        self._sidebandCalibrationData.sortBy("f_c")
        self._sidebandCalibrationData.savetxt()
    finally:
      self.teardown()
      
  def iOffset(self,f):
    return self._iOffsetInterpolation(f)
    
  def qOffset(self,f):
    return self._qOffsetInterpolation(f)
    
  def setDriveFrequency(self,f):
    self._mwg.setFrequency(f)
    self._awg.setOffset(self._awgChannels[0],self.iOffset(f))
    self._awg.setOffset(self._awgChannels[1],self.qOffset(f))
  
  def optimizeIQMixerPowell(self):
    """
    Use Powell's biconjugate gradient method to minimize the power leak in the IQ mixer.
    """
    f = self._mwg.frequency()
    self._mwg.turnOn()
    self._fsp.write("SENSE1:FREQUENCY:CENTER %f GHZ" % f)
    result = scipy.optimize.fmin_powell(lambda x: self.measurePower(x),[0.,0.],full_output = 1,xtol = 0.0001,ftol = 1e-2,maxiter =1500,maxfun =1000, disp=True, retall=True)
    return (result[0],result)

  def measureSidebandPower(self,x,f_sb):
    
    c = x[0]
    
    if c > 0.5 or c < -0.5:
      return 100

    phi = fmod(x[1],math.pi*2)
    
    self.loadSidebandCalibrationWaveform(f_sb = f_sb,c = c,phi = phi)
    
    power = self.measureAveragePower()
    
    print "Sideband power at f_sb = %g GHz,c = %g, phi = %g : %g dBm" % (f_sb,c,phi,power) 

    return power

  def measureAveragePower(self):
  
    trace = self._fsp.getSingleTrace()
    
    if trace == None:
      return 0
    
    minimum =  mean(trace[1])
    return minimum
  
  def measurePower(self,lows):
    """
    Measure the leaking power of the IQ mixer at a given point.
    Used by optimizeIQMixerPowell.
    """
    for i in [0,1]:
      if math.fabs(lows[i]) > 2.0:
        return 100.0
      self._awg.setOffset(self._awgChannels[i],lows[i])
    minimum = self.measureAveragePower()
    print "Measuring power at %g,%g : %g" % (lows[0],lows[1],minimum)
    linpower = math.pow(10.0,minimum/10.0)/10.0
    return minimum 