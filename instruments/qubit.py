import sys
import getopt
import re
import struct
import math
import numpy
import scipy
import scipy.interpolate

from pyview.lib.classes import *
import pyview.helpers.instrumentsmanager
if 'macros.iq_level_optimization' in sys.modules:
  reload(sys.modules["macros.iq_level_optimization"])

from macros.iq_level_optimization import IqOptimization
from pyview.lib.datacube import Datacube
  
class WaveformException(Exception):
  pass
  
class QubitException(Exception):
  pass
  
def gaussianFilter(x,cutoff = 0.5):
  return numpy.exp(-numpy.power(numpy.fabs(numpy.real(x))/cutoff,2.0) )

def gaussianPulse(length = 500,delay = 0,flank = 4,normalize = True,resolution = 1,filterFrequency = 0.2):
  waveform = numpy.zeros((math.ceil(flank*2)+1+int(math.ceil(length))+math.ceil(delay))*int(1.0/resolution),dtype = numpy.complex128)
  if length == 0:
    return waveform
  for i in range(0,len(waveform)):
    t = float(i)*resolution
    if t <= flank+delay:
      waveform[i] = numpy.exp(-0.5*math.pow(float(t-delay-flank)/float(flank)*3.0,2.0))
    elif t >= flank+delay+length:
      waveform[i] = numpy.exp(-0.5*math.pow(float(t-delay-flank-length)/float(flank)*3.0,2.0))
    else:
      waveform[i] = 1.0
  pulseFFT = numpy.fft.rfft(waveform)
  freqs = numpy.linspace(0,1.0,len(pulseFFT))
  filteredPulseFFT = pulseFFT
  filteredPulse = numpy.array(numpy.fft.irfft(filteredPulseFFT,len(waveform)),dtype = numpy.complex128)
  filteredPulse = waveform
  integral = numpy.sum(filteredPulse)
  if normalize:
    filteredPulse/=integral/float(length)*resolution
  return filteredPulse
  
class Pulse:

  def __init__(self,shape,delay):
    self._shape = shape
    self._delay = delay
    
  def shape(self):
    return self._shape
    
  def delay(self):
    return self._delay
    
  def __len__(self):
    return len(self._shape)+self._delay
  
class PulseSequence:
  
  def __init__(self):
    self._base = dict()
    self._pulses = []
    self._length = 1
    self._offset = 0
    
  def setLength(self,length):
    self._length = length
    
  def setOffset(self,offset):
    self._offset = offset
    
  def addPulse(self,shape,delay = 0):
    pulse = Pulse(shape,delay)
    self._pulses.append(pulse)
    if delay+len(shape) > self._length:
      self._length = delay+len(shape)
    
  def __len__(self):
    return self._length
    
  def clearPulses(self):
    self._pulses = []
    
  def getWaveform(self,dataType = numpy.complex128):
    waveform = numpy.zeros(self._length,dtype =dataType)+self._offset
    for pulse in self._pulses:
      totalLength = len(pulse.shape())+pulse.delay()
      if totalLength > len(waveform):
        oldLength = len(waveform)
        waveform.resize(totalLength)
        waveform[oldLength:] = self._offset
      waveform[math.ceil(pulse.delay()):math.ceil(pulse.delay())+len(pulse.shape())] += pulse.shape()
    return waveform
  
#This is a virtual instrument representing a Quantum Bit.
#This class provides convenience functions for setting the Qubit parameters and for
#making measurements of the Qubit state.
class Instr(Instrument):

      def parameters(self):
        params = copy.deepcopy(self._params)
        return self._params
        
      def saveState(self,name):
        params = copy.deepcopy(self._params)
        params['waveforms'] = copy.deepcopy(self._waveforms)
        return params
        
      
      def restoreState(self,state):
        self._params = state
        if 'drive.frequency' in state:
          self.setDriveFrequency(state['drive.frequency'])
        if 'drive.amplitude.I' in state and 'drive.amplitude.Q' in state:
          self.setDriveAmplitude(I = state['drive.amplitude.I'], Q = state['drive.amplitude.Q'])
        if 'drive.state' in state:
          if state['drive.state'] == True:
            self.turnOnDrive()
          else:
            self.turnOffDrive()
        if 'waveforms' in state:
          if 'fluxline' in state['waveforms']:
            print "Restoring fluxline waveform..."
            self.loadFluxlineWaveform(state['waveforms']['fluxline'],compensateResponse = self._params["fluxline.compensateResponse"],factor = self._params["fluxline.compensationFactor"],samplingInterval = self._params["fluxline.samplingInterval"])
          if 'drive' in state['waveforms']:
            print "Restoring drive waveform..."
            self.loadWaveform(state['waveforms']['drive'],readout = state['readoutDelay'])
        self._waveforms = state['waveforms']
        del self._params['waveforms']
        
      def initQubit(self):
        """
        Initializes the qubit with some standard parameters.
        """
        self.setDriveFrequency(self._mwg.frequency())
        self.setDriveAmplitude(I = 2.0)
        self.loadRabiPulse()
        self.loadFluxlineWaveform([0.0]*100)
        self._fluxline.turnOn()
        self.setFluxlineDelay(0)

      def turnOnDrive(self):
        self._mwg.turnOn()
  
      def turnOffDrive(self):
        self._mwg.turnOff()
  
      def driveFrequency(self):
        return self._mwg.frequency()
  
      def setDriveFrequency(self,f):
        """
        Changes the drive frequency of the qubit and adjust the AWG minimum voltages on the IQ channels to minimze the power leakage through the IQ mixer.
        """
        self._params["drive.frequency"] = f
        self._mwg.setFrequency(f)
        if self._optimizer != None:
          self._awg.setOffset(self._awgChannels[0],self._optimizer.iOffset(f))
          self._awg.setOffset(self._awgChannels[1],self._optimizer.qOffset(f))
          
      def setDrivePower(self,I = None,Q = None):
        f = self._mwg.frequency()
        aI = None
        aQ = None
        if I != None:
          frequencies = self._optimizer.iqPowerCalibrationData().column("frequency")
          coeffs = self._optimizer.iqPowerCalibrationData().column("coeffI")
          iInt = scipy.interpolate.interp1d(frequencies,coeffs)
          cI = iInt(f)
          aI = math.sqrt(math.pow(10.0,I/10.0)/cI)
        if Q != None:
          frequencies = self._iqPowerCalibration.column("frequency")
          coeffs = self._iqPowerCalibration.column("coeffQ")
          qInt = scipy.interpolate.interp1d(frequencies,coeffs)
          cQ = qInt(f)
          aQ = math.sqrt(math.pow(10.0,Q/10.0)/cQ)
        self.setDriveAmplitude(I = aI,Q = aQ)

      def setDriveAmplitude(self,**kwargs):
        channels = {"I":0,"Q":1}
        for arg in ["I","Q"]:
          if arg in kwargs and kwargs[arg] != None:
            self._params["drive.amplitude.%s" % arg] = kwargs[arg]
            offset = self._awg.offset(self._awgChannels[channels[arg]])
            self._awg.setAmplitude(self._awgChannels[channels[arg]],kwargs[arg])
            diff = math.fabs(self._awg.amplitude(self._awgChannels[channels[arg]]) - kwargs[arg])
            if diff>0.001:
              raise QubitException("AWG voltage chosen too high: Got %g V instead of %g V, %g" % (self._awg.high(self._awgChannels[channels[arg]]),minValue+kwargs[arg],diff))
            if self._awg.offset(self._awgChannels[channels[arg]]) != offset:
              raise QubitException("AWG minimum voltage has been changed: Got %g V instead of %g V" % (self._awg.low(self._awgChannels[channels[arg]]),minValue))
        return True     
      
      def generateZPulse(self,length = None,phase = None,delay = 0,height = None,gaussian = True,flank = 3):
        """
        Generates a z pulse
        """
        if height == None:
          height = 1.0
        if (length == None and phase == None) or (length != None and phase != None):
          raise QubitException("Error in generateZPulse: You must specify either the length or the phase of the pulse!")
        if phase != None:
          if not "pulses.xy.t_pi" in self._params:
            raise QubitException("Error: Length of pi pulse is not calibrated!")
          height = self._params["pulses.z.drive_amplitude"]
          length = phase*self._params["pulses.z.t_pi"]/math.pi
          if length < 0:
            height = -height
            length = -length
        if gaussian:
          pulse = gaussianPulse(length,delay = delay,flank = flank,normalize = False)
        else:
          pulse = numpy.zeros((length+delay))
          pulse[delay:delay+length] = 1.0
        return pulse*height
      
      def generateRabiPulse(self,length = None,phase = None,delay = 0,height = 1.0,gaussian = True,flank = 3,f_c = None,f_sb = 0,angle = 0,sidebandDelay = None):
        """
        Generates a Rabi pulse
        """
        seq = PulseSequence()
        if sidebandDelay == None:
          sidebandDelay = delay
        if (length == None and phase == None) or (length != None and phase != None):
          raise QubitException("Error: You must specify either the length or the phase of the pulse!")
        if phase != None:
          if phase < 0:
            phase = -phase
            angle+=math.pi
          if not "pulses.xy.t_pi" in self._params:
            raise QubitException("Error: Length of pi pulse is not calibrated!")
          length = phase*self._params["pulses.xy.t_pi"]/math.pi
        elif length < 0:
          length = -length
          angle+=math.pi
        if gaussian:
          pulse = gaussianPulse(length,delay = delay,flank = flank)
        else:
          pulse = numpy.zeros(max(1,(length+delay)),dtype = numpy.complex128)
          pulse[delay:delay+length] = height
        if f_sb != 0:
          if f_c == None:
            f_c = self.driveFrequency()
          sidebandPulse = self._optimizer.generateCalibratedSidebandWaveform(f_c = f_c,f_sb = f_sb,length = len(pulse)-delay,delay = sidebandDelay)
          pulse[delay:]*=sidebandPulse
        seq.addPulse(pulse*numpy.exp(1.0j*angle))
        return seq.getWaveform()
      
      
      def loadRabiPulse(self,length = None,phase = None,delay = 0,height = 1.0,readout = None,gaussian = True,flank = 3,f_sb = None,angle = 0,sidebandDelay = 0):
        """
        Loads a Rabi pulse into the AWG memory.
        """          
        if f_sb == None and 'pulses.xy.f_sb' in self.parameters():
          f_sb = self.parameters()['pulses.xy.f_sb']
        elif f_sb == None:
          raise QubitException("Error: You must specify a sideband frequency via parameter f_sb!")
        seq = PulseSequence()
        if readout != None:
          pulse = self.generateRabiPulse(length = length,phase = phase,height = height,gaussian = gaussian,flank = flank, f_sb = f_sb,angle = angle,sidebandDelay = sidebandDelay)
          seq.addPulse(self.generateRabiPulse(length = length,phase = phase,delay = readout-len(pulse)-1-delay,height = height,gaussian = gaussian,flank = flank, f_sb = f_sb,angle = angle))
          return self.loadWaveform(seq.getWaveform(),readout = readout)
        else:
          seq.addPulse(self.generateRabiPulse(length = length,phase = phase,delay = delay,height = height,gaussian = gaussian,flank = flank, f_sb = f_sb,angle = angle,sidebandDelay = sidebandDelay))
          return self.loadWaveform(seq.getWaveform(),readout = len(seq)+1)
        
      def loadRamseyPulse(self,delay = 0,interval = 0,height = 1.0,piLength = 100,spinEcho = False,flank = 1,readoutDelay = 0):
        """
        Loads a Ramsey waveform into the AWG memory.
        """
        piOver2Pulse = gaussianPulse(piLength/2.0,flank = flank)
        piPulse = gaussianPulse(piLength,flank = flank)
        pulse = numpy.zeros(len(piOver2Pulse)*2+interval+delay)-1.0
        pulse[delay:len(piOver2Pulse)+delay] = piOver2Pulse
        pulse[delay+len(piOver2Pulse)+interval:] = piOver2Pulse
        return self.loadWaveform(pulse,readout = len(piOver2Pulse)*2.0+delay+interval+readoutDelay)
        
      def setFluxlineDelay(self,delay):
        offset =  self._params['driveWaitTime']-self._register['fluxlineTriggerDelay']-self._params['fluxlineWaitTime']
        if offset < 0:
          raise QubitException("Fluxline delay is negative!")
        self._fluxline.setTriggerDelay(delay+offset)
        
      def readoutDelay(self):
        return self._params['readoutDelay']
        
      def setReadoutDelay(self,delay):
        offset = self._params['driveWaitTime']-self._jba.internalDelay()
        if offset < 0:
          raise QubitException("Readout delay is negative!")
        self._params['readoutDelay'] = float(delay)
        markers = numpy.zeros((self._repetitionPeriod),dtype = numpy.uint8) + 3
        markers[0:len(markers)-1000]-=1
        markers[offset+delay:offset+delay+200]-=2
        self._awg.updateMarkers(self._params["readoutMarkerWaveform"],markers)
        self.notify("readoutDelay",self._params["readoutDelay"])

      def fluxlineWaveform(self):
        if "fluxline" in self._waveforms:
          return self._waveforms["fluxline"]
        return []
        
      def loadFluxlineWaveform(self,waveform,compensateResponse = True,samplingInterval = 1.0,factor = 1.0):
        if not type(waveform) == list:
          self._waveforms["fluxline"] = waveform.tolist()
        else:
          self._waveforms["fluxline"] = waveform
        self._params["fluxline.compensateResponse"] = compensateResponse
        self._params["fluxline.compensationFactor"] = factor
        self._params["fluxline.samplingInterval"] = samplingInterval
        if compensateResponse:
          return self.loadCompensatedFluxlineWaveform(waveform,samplingInterval,factor)
        return self.loadPlainFluxlineWaveform(waveform,samplingInterval)
      
      def loadCompensatedFluxlineWaveform(self,waveform,samplingInterval = 1.0,factor = 1.0,simulate = False):
        if self._fluxlineResponse == None:
          raise QubitException("No fluxline calibration data available!")
        if samplingInterval < 0.5:
          raise QubitException("Waveform sampling interval too small!")
        finalLength = 1
        while finalLength < len(waveform)+1000:
          finalLength = finalLength << 1
        fullWaveform = numpy.zeros((finalLength))-1.0
        fullWaveform[:len(waveform)] = waveform
        fullWaveform[len(waveform):] = waveform[-1]
        if finalLength in self._fluxlineResponseInterpolations and False:
          responseFunction = self._fluxlineResponseInterpolations[finalLength]
        else:
          print "Generating fluxline response function of length %d" % finalLength
          frequencies = numpy.linspace(0,1.0/samplingInterval,finalLength/2+1)
          interpolation = scipy.interpolate.interp1d(self._fluxlineResponse.column("frequency"),self._fluxlineResponse.column("response_dac")*numpy.power(self._fluxlineResponse.column("response_input_sample"),factor))
          self._fluxlineResponseInterpolations[finalLength] = interpolation(frequencies)/numpy.power(gaussianFilter(frequencies,cutoff = 0.45),factor)
          responseFunction = self._fluxlineResponseInterpolations[finalLength]
        correctedWaveform = numpy.fft.irfft(numpy.fft.rfft(fullWaveform)/responseFunction)
        correctedWaveform[0] = waveform[0]
        correctedWaveform[-1] = waveform[-1]
        if max(correctedWaveform) > 1.0 or min(correctedWaveform) < -1.0:
          raise QubitException("Corrected waveform exceeds maximum range!")
        if simulate:
          return correctedWaveform
        self.loadPlainFluxlineWaveform(correctedWaveform,samplingInterval)
        return correctedWaveform
        
      def loadPlainFluxlineWaveform(self,waveform,samplingInterval = 1.0):
        """
        Loads a waveform into the Qubit's fluxline buffer.
        One point of the waveform corresponds to 0.5 ns.
        """
        delay = self._params["fluxlineWaitTime"]*2

        transformed = numpy.zeros((max(len(waveform),150)))-1.0
        transformed[:len(waveform)] = waveform
        transformed[len(waveform):] = waveform[-1]
        transformed = (transformed+1.0)*((1<<14)/2.0-1.0)
        #If the data is sampled at 0.5 ns we just take it as it is. If not we interpolate.
        if samplingInterval == 0.5:
          fullWaveform = numpy.zeros((len(transformed)+delay),dtype = numpy.uint16)
          fullWaveform[delay:] = transformed 
          fullWaveform[:delay] = transformed[0]         
        else:
          multiplier = int(samplingInterval/0.5)
          fullWaveform = numpy.zeros((multiplier*(len(transformed)-1)+1+delay),dtype = numpy.uint16)
          for i in range(0,len(transformed)-1):
            for j in range(0,multiplier):
              fullWaveform[delay+i*multiplier+j] = transformed[i]+(transformed[i+1]-transformed[i])/float(multiplier)*float(j)
          fullWaveform[delay+multiplier*(len(transformed)-1)] = transformed[-1]              
          fullWaveform[:delay] = transformed[0]
        self._fluxline.writeWaveform(self._fluxlineWaveform,fullWaveform)
        self._fluxline.setWaveform(self._fluxlineWaveform)
        self._fluxline.setPeriod(len(fullWaveform)/2.0)
        self.setFluxlineDelay(0)
        self._outputWaveforms["fluxline"] = fullWaveform
        self.notify("fluxlineWaveform",fullWaveform)
        return fullWaveform
              
      def waveform(self):
        if 'drive' in self._outputWaveforms:
          return self._outputWaveforms["drive"]
        return None
              
      def loadWaveform(self,iqWaveform,readout = 10000):
        """
        Loads an IQ waveform into the AWG memory.
        The "readout" parameter sets the time at which the qubit should be read out.
        """
        if len(iqWaveform) > self._register["repetitionPeriod"]-self._params["driveWaitTime"]:
          raise WaveformException("Given waveform is too long!")
          return False
        iMarkers = numpy.zeros((self._repetitionPeriod),dtype = numpy.uint8) + 3
        qMarkers = numpy.zeros((self._repetitionPeriod),dtype = numpy.uint8) + 3
        iChannel = numpy.zeros((self._repetitionPeriod))
        qChannel = numpy.zeros((self._repetitionPeriod))
        safetyMargin = self._params["driveWaitTime"]
        iChannel[safetyMargin:safetyMargin+len(iqWaveform)] = numpy.real(iqWaveform)
        qChannel[safetyMargin:safetyMargin+len(iqWaveform)] = numpy.imag(iqWaveform)
        #Flux pulse trigger and readout trigger
        
        iMarkers[1:-1]-=3 
        qMarkers[1:-1]-=1

        if not "I" in self._outputWaveforms["drive"] or not numpy.allclose(iChannel,self._outputWaveforms["drive"]["I"]) or not numpy.allclose(iMarkers,self._outputWaveforms["drive"]["markers"]["I"]):
          iData = self._awg.writeRealData(iChannel,iMarkers)
          self._awg.createWaveform(self._waveformNames["awg"][0],iData,"REAL")
          self._awg.setWaveform(self._awgChannels[0],self._waveformNames["awg"][0])

        if not "Q" in self._outputWaveforms["drive"] or not numpy.allclose(qChannel,self._outputWaveforms["drive"]["Q"]) or not numpy.allclose(iMarkers,self._outputWaveforms["drive"]["markers"]["Q"]):
          qData = self._awg.writeRealData(qChannel,qMarkers)
          self._awg.createWaveform(self._waveformNames["awg"][1],qData,"REAL")
          self._awg.setWaveform(self._awgChannels[1],self._waveformNames["awg"][1])
        

        if not type(iqWaveform) == list:
          self._waveforms["drive"] = iqWaveform.tolist()
        else:
          self._waveforms["drive"] = iqWaveform
        
        self._outputWaveforms["drive"]["I"] = iChannel
        self._outputWaveforms["drive"]["Q"] = qChannel
        self._outputWaveforms["drive"]["markers"]["I"] = iMarkers
        self._outputWaveforms["drive"]["markers"]["Q"] = qMarkers

        self.setReadoutDelay(readout)
        
        finalIqWaveform = iChannel +1j*qChannel
                
        self.notify("driveWaveform",(finalIqWaveform,iMarkers,qMarkers))

        return (finalIqWaveform,iMarkers,qMarkers)
        
      def driveWaveform(self):
        return self._waveforms["drive"]
                
      def updateWaveforms(self):
        try:
          iChannel = self._awg.getWaveform(self._waveformNames["awg"][0])
          qChannel = self._awg.getWaveform(self._waveformNames["awg"][1])
        except VisaIOError:
          print "Error when retrieving waveform data..."
        self._outputWaveforms["drive"]["I"]=iChannel._data
        self._outputWaveforms["drive"]["Q"]=qChannel._data
        self._outputWaveforms["drive"]["markers"]["I"] = iChannel._markers
        self._outputWaveforms["drive"]["markers"]["Q"] = qChannel._markers
        self.notify("driveWaveform",(self._outputWaveforms["drive"]["I"],self._outputWaveforms["drive"]["Q"],self._outputWaveforms["drive"]["markers"]))
        self._outputWaveforms["fluxline"] = self._fluxline.readWaveform(self._fluxlineWaveform)
        self.notify("fluxlineWaveform",self._outputWaveforms["fluxline"])
        
      def generatePulse(self,length = 1000,delay = 0,tMeasurement = 16000,totalLength = 20000):
        data = numpy.zeros((totalLength))
        markers = numpy.zeros((totalLength))
        for i in range(tMeasurement-length-delay,tMeasurement-delay):
        	markers[i]= 255
        	data[i] = 250
        data = self._awg.writeIntData(data,markers)
        self._awg.createWaveform(self._waveform,data,"INT")
              
      def setIqOffsetCalibration(self,calibration):
        self._optimizer.setOffsetCalibrationData(calibration)
        
      def setIqPowerCalibration(self,calibration):
        self._optimizer.setPowerCalibrationData(calibration)
        
      def Psw(self,ntimes = 20):
        self._acqiris.bifurcationMap(ntimes = ntimes)
        return self._acqiris.Psw()[self._acqirisVariable]
        
      def calibrateIqOffset(self,frequency = None,saveCalibration = True,changeFrequency = True):
        """
        Recalibrates the IQ offset at a given single frequency and (if requested) updates the calibration data file.
        If no frequency is given, the current drive frequency will be used.
        If changeFrequency is True, the function will change the qubit drive frequency to the given frequency after the calibration.
        """
        if frequency == None:
          frequency = self._mwg.frequency()
        self._optimizer.calibrateIQOffset([frequency])
        if saveCalibration:
          self._optimizer.offsetCalibrationData().savetxt()
        if changeFrequency:
          self.setDriveFrequency(frequency)
        
      def setFluxlineResponse(self,response):
        self._fluxlineResponse = response
        self._fluxlineResponseInterpolations = dict()

      def initialize(self,awgChannels = [1,2],mwg = "qubit1mwg",readoutMarkerWaveform = "qubit1qReal",fsp = "fsp",fluxlineResponse = None,iqOffsetCalibration = None,iqPowerCalibration = None,iqSidebandCalibration = None,jba = "jba1",coil = "coil",awg = "awg",fluxline = "afg1",waveforms = ["qubit1i","qubit1q"],variable = 1,acqiris = "acqiris",acqirisVariable = "p1x",triggerDelay = 280,repetitionPeriod = 20000,fluxlineWaveform = "USER1"):
        manager = pyview.helpers.instrumentsmanager.Manager()
        if not hasattr(self,'_params'):
          self._params = dict()
        if not hasattr(self,'_waveforms'):
          self._waveforms = dict()
        self._outputWaveforms = dict()
        self._inputWaveforms = dict()

        self._register = manager.getInstrument("register")

        self._outputWaveforms["drive"] = dict()
        self._acqirisVariable = acqirisVariable
        self._outputWaveforms["drive"]["markers"] = dict()
        
        
        self._params["driveWaitTime"] = 2000
        self._params['fluxlineWaitTime'] = 50
        self._params["fluxlineInternalDelay"] = 130

        self._params["readoutMarkerWaveform"] = readoutMarkerWaveform
        self._params["readoutMarkerChannel"] = 1

        self._awgChannels = awgChannels

        self._waveformNames = dict()
        
        self._waveformNames["awg"] = waveforms
        self._waveformNames["fluxline"] = fluxlineWaveform
        self._waveformNames["readoutMarker"] = readoutMarkerWaveform
        
        self._fluxlineResponseInterpolations = dict()
        self._fluxlineResponse = fluxlineResponse

        self._fluxlineWaveform = fluxlineWaveform
        self._mwg = manager.getInstrument(mwg)
        self._repetitionPeriod = repetitionPeriod
        self._jba = manager.getInstrument(jba)
        self._fsp = manager.getInstrument(fsp)
        self._awg = manager.getInstrument(awg)
        self._acqiris = manager.getInstrument(acqiris)
        self._variable = variable
        self._coil = manager.getInstrument(coil)
        self._fluxline = manager.getInstrument(fluxline)

        sidebandCalibration = Datacube()
        
        k = "calibration.iqmixer.%s.sideband" % self.name()
        
        if self._register.hasKey(k):
          sidebandCalibration.loadtxt(self._register[k])

        self._optimizer = IqOptimization(self._mwg,self._fsp,self._awg,self._awgChannels)
        self._optimizer.setOffsetCalibrationData(iqOffsetCalibration)
        self._optimizer.setPowerCalibrationData(iqPowerCalibration)
        self._optimizer.setSidebandCalibrationData(iqSidebandCalibration)
