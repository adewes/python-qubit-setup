import sys
import getopt
import numpy

from pyview.lib.classes import *
from pyview.helpers.instrumentsmanager import Manager
from numpy import *
register=Manager().getInstrument('register')

class Instr(Instrument):

      def generatePulse(self, duration=100, gaussian=False,frequency=12., amplitude=1.,phase=0., allowModifyMWFrequency=False,DelayFromZero=0, useCalibration=True,shape=None):
        MWFrequency=self._MWSource.frequency()
        self._MWSource.turnOn()
        f_sb=MWFrequency-frequency
        try:
          pulse = numpy.zeros(register['repetitionPeriod'],dtype = numpy.complex128)
          if shape==None:
            if gaussian:
              print 'gaussian pulse is not working !!!'
              pulse = gaussianPulse2(length=duration,delay = DelayFromZero,flank = flank)
            else:
              pulse[DelayFromZero:DelayFromZero+duration] = amplitude
          else:
            pulse[:]=shape[:]
          pulse*=numpy.exp(1.0j*phase)/2
          if useCalibration:
            (iOffset, qOffset, c, phi)=self._IQMixer.calibrationParameters(f_sb=f_sb, f_c=MWFrequency)
#            print "iOffset %f, qOffset %f, c %f, phi %f"  % (iOffset, qOffset, c, phi)
            cr = float(c)*exp(1j*float(phi))
            sidebandPulse = exp(-1.j*f_sb*2.0*math.pi*(arange(DelayFromZero,DelayFromZero+len(pulse))))+cr*exp(1.j*f_sb*2.0*math.pi*(arange(DelayFromZero,DelayFromZero+len(pulse))))
            self._AWG.setOffset(self._params["AWGChannels"][0],iOffset)
            self._AWG.setOffset(self._params["AWGChannels"][1],qOffset)
          else:
            sidebandPulse = exp(-1.j*2.0*math.pi*f_sb*(arange(DelayFromZero,DelayFromZero+len(pulse))))
            self._AWG.setOffset(self._params["AWGChannels"][0],0)
            self._AWG.setOffset(self._params["AWGChannels"][1],0)
          pulse[:]*=sidebandPulse 
          self.totalPulse[:]+=pulse
        except:
          raise
        return True
        
        
      def sendPulse(self,pulse=None):
          markers=(zeros(register['repetitionPeriod'],dtype=int8),zeros(register['repetitionPeriod'],dtype=int8))
          markers[0][:register['readoutDelay']]=3
          markers[1][:register['readoutDelay']]=3
          if pulse==None:
            self._AWG.loadiqWaveform(iqWaveform=self.totalPulse,channels=self._params["AWGChannels"],waveformNames=(self.name()+'i',self.name()+'q'),markers=markers)
          else:
            self._AWG.loadiqWaveform(iqWaveform=pulse,channels=self._params["AWGChannels"],waveformNames=(self.name()+'i',self.name()+'q'),markers=markers)
          
      def clearPulse(self):
          self.totalPulse[:]=0
          self.sendPulse()
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



      def parameters(self):    
        return self._params

      def initialize(self, name, MWSource, IQMixer, AWG, AWGChannels):
        instrumentManager=Manager()
        self._MWSource=instrumentManager.getInstrument(MWSource)
        self._IQMixer=instrumentManager.getInstrument(IQMixer)
        self._AWG=instrumentManager.getInstrument(AWG)
        self._params=dict()
        self._params["MWSource"]=MWSource
        self._params["IQMixer"]=IQMixer
        self._params["AWG"]=AWG
        self._params["AWGChannels"]=AWGChannels
        self.totalPulse=numpy.zeros(register['repetitionPeriod'],dtype = numpy.complex128)
        return
