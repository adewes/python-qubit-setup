import sys
import getopt

from ctypes import *
from numpy import *
import time

import math
import os.path

#We import the C++/SWIG part of the Acqiris library:
import lib.swig.acqiris.acqiris as acqirislib

from pyview.lib.classes import *
from pyview.lib.datacube import Datacube

___TEST___ = False

#Some numerical parameters:
CAL_TOUT = 0
CAL_VOIE_COURANTE	= 1
CAL_RAPIDE = 4

def mybin(x,l = 8):
	s = bin(x)[2:]
	return (l-len(s))*"0"+s
	
class Instr(Instrument):

	
      """
      The instrument class for the Acqiris fast acquisition card.
      """

      def initialize(self,*args,**kwargs):
        
        """
        Initializes the Acqiris card.
        """
        
        self.__vi_session = c_uint32()
        self.__temperature = c_int32()
        self.__time_us = c_double()

        self._params = dict()

        #Acqiris virtual instrument default parameters:

        self._params["rotation"] = [0,0]
        self._params["averaging"] = 0
        self._params["fullScales"] = [5.0] * 4
        self._params["offsets"] = [0.0] * 4
        self._params["couplings"] = [3] * 4
        self._params["bandwidths"] = [3] * 4
        self._params["trigCoupling"] = 3
        self._params["trigLevel"] = 500
        self._params["trigSlope"] = 0
        self._params["trigSource"] = -1
        self._params["memType"] = 1
        self._params["synchro"] = 1
        self._params["usedChannels"] = 15
        self._params["averaging"] = 0
        self._params["delayTime"] = 700e-9
        self._params["sampleInterval"] = 3e-9
        self._params["numberOfPoints"] = 400
        self._params["numberOfSegments"] = 100
        self._params["freqEch"] = 499999999.9999999
        self._params["transferAverage"]=False 
        self._params['nFrequencies']=10
        
        if ___TEST___:
          None
        else:
           if hasattr(self,"__acqiris") is False:
             try:
               self.__acqiris = windll.LoadLibrary(os.path.dirname(os.path.abspath(__file__))+'/dllAcqiris.dll')
               self.__acqiris.FindDevicesV1(byref(self.__vi_session),byref(self.__temperature))
             except ImportError:
               print "Cannot load Acqiris DLL!"
               print sys.exc_info()
               return False

        self.ConfigureV2()
        
        return True

      def _temperature(self):
        return self.__temperature.value

      def transformErr2Str(self,*args):
        error_code = c_int32(args[0])
        error_str = create_string_buffer("\000"*1024)
        status = self.__acqiris.transformErr2Str(self.__vi_session,error_code,error_str)        
        return str(error_str)
      
      def saveState(self,name):
        return self._params
        
      def restoreState(self,state):
        self.ConfigureV2(**state)
      
      def parameters(self):
        """
        Returns the parameters of the Acqiris card.
        """
        return self._params
        
      def updateParameters(self,*args,**kwargs):
        
        """
        Updates the parameter dictionary of the Acqiris card.
        """

        for key in kwargs.keys():
          self._params[key] = kwargs[key]
        
      def ConfigureV2(self,*args,**kwargs):
      
        """
        Configures the Acqiris card with a new set of parameters that have to be passed as keyword arguments.
        """
                
        self.updateParameters(*args,**kwargs)
        
        #We create ctypes objects for all the parameters:
        used_channels = c_int32(self._params["usedChannels"])
        freq_ech = c_double(self._params["freqEch"])
        sample_interval = c_double(self._params["sampleInterval"])
        averaging = c_int32(self._params["averaging"])
        delay_time = c_double(self._params["delayTime"])
        number_of_points = c_int32(self._params["numberOfPoints"])
        number_of_segments = c_int32(self._params["numberOfSegments"])
        mem = c_int32(int(self._params["memType"]))
        trig = c_int32(self._params["trigSource"])
        trig_coupling = c_int32(self._params["trigCoupling"])
        trig_slope = c_int32(self._params["trigSlope"])
        trig_level = c_double(self._params["trigLevel"])
        fullscale_ch1 = c_double(self._params["fullScales"][0])
        fullscale_ch2 = c_double(self._params["fullScales"][1])
        fullscale_ch3 = c_double(self._params["fullScales"][2])
        fullscale_ch4 = c_double(self._params["fullScales"][3])
        synchro = c_char(str(self._params["synchro"]))
        converters_per_channel = c_int32(0)
        max_points_per_segment = c_int32(0)
        auto_config = c_int32(0)
        converters_per_channel_2 = c_int32(0)

        #We call the ConfigureV2 DLL function:
        status = self.__acqiris.ConfigureV2(self.__vi_session
        ,byref(used_channels),byref(freq_ech),byref(sample_interval),byref(averaging),byref(delay_time)
        ,byref(number_of_points),byref(number_of_segments),byref(mem)
        ,byref(fullscale_ch1)
        ,byref(fullscale_ch2)
        ,byref(fullscale_ch3)
        ,byref(fullscale_ch4)
        ,byref(trig),byref(trig_coupling),byref(trig_slope),byref(trig_level)
        ,byref(synchro),byref(converters_per_channel),byref(max_points_per_segment),byref(auto_config),byref(converters_per_channel_2)
        )      
        
        self.transformErr2Str(status)
        
        #We configure the individual channels:
        for i in range(0,4):
          self.ConfigureChannel(1+i,self._params["fullScales"][i],self._params["offsets"][i],self._params["couplings"][i],self._params["bandwidths"][i])
                  
        
        self._params["numberOfPoints"] = number_of_points.value
        self._params["numberOfSegments"] = number_of_segments.value
        
        self._waveformArray = None
        self._averagedWaveformArray = None
        self._rotatedWaveformArray = None
        
        #We initialize the C++ BifurcationMap class with the pointers of the numpy arrays that we created to store the bifurcation map data.     
        
        self.bm = acqirislib.BifurcationMap()
        self.bm.activeChannels = 15

        self.nLoops = 20
        self.bm.nLoops = self.nLoops
        self._trends = zeros((4,self._params["numberOfSegments"]*self.nLoops))
        self.bm.trends = self._trends.ctypes.data

        self._probabilities = zeros((2,1))
        self._crossProbabilities = zeros((2,2))
        self.bm.crossProbabilities = self._crossProbabilities.ctypes.data
        self.bm.probabilities = self._probabilities.ctypes.data

        self._means = zeros((4,1))
        self.bm.means = self._means.ctypes.data

        self._averages = zeros((4,self._params["numberOfPoints"]))
        self.bm.averages = self._averages.ctypes.data

        self.bm.nPoints = self._params["numberOfPoints"]
        self.bm.nSegments = self._params["numberOfSegments"]
        
        #We initialize the C++ Frequencies anaysis with the pointers of the numpy arrays that we created to store the frequencies analysis map data.     
        
        self.av = acqirislib.Averager()
        self.av.activeChannels = 15

        self.m = acqirislib.MultiplexedBifurcationMap()
             
        return self._params

      def ConfigureChannel(self,channel,fullscale = None,offset = None,coupling = None,bandwidth = None):
      
        """
        Configures one single channel of the Acqiris card.
        """
        
        channel-=1
        if fullscale != None:
          self._params["fullScales"][channel] = float(fullscale)
        if offset != None:
          self._params["offsets"][channel] = float(offset)
        if coupling != None:
          self._params["couplings"][channel] = int(coupling)
        if bandwidth != None:
          self._params["bandwidths"][channel] = int(bandwidth)
        
        status = self.__acqiris. ConfigureChannel(self.__vi_session, c_int32(channel+1), byref(c_double(self._params["fullScales"][channel])), byref(c_double(self._params["offsets"][channel])), byref(c_int32(self._params["couplings"][channel])), byref(c_int32(self._params["bandwidths"][channel])));
        self.transformErr2Str(status)
        
      def CalibrateV1(self,*args):
        
        """
        Calibrates the Acqiris card.
        """
        
        options = c_int32(CAL_TOUT)
        channels = c_int32(args[0])
        status=self.__acqiris.CalibrateV1(self.__vi_session,options,channels)        
        if status != 0:
          raise Exception(self.transformErr2Str(status))
        
      def probabilities(self):
        return self._probabilities
        
      def clicks(self):
      
        """
        Returns a datacube that contains the individual detector clicks for all measured samples in binary form.
        """
          
        clicks = Datacube("detector clicks",dtype = uint8)
        
        angles = self.bifurcationMapRotation()
        
        clicks1 = self.trends()[0]*cos(angles[0])+self.trends()[1]*sin(angles[0]) > 0
        clicks2 = self.trends()[2]*cos(angles[1])+self.trends()[3]*sin(angles[1]) > 0
        
        def mapper(t):
          (x1,x2) = t
          if x1 and x2:
            return 3
          elif x1 and not x2:
            return 1
          elif x2 and not x1:
            return 2
          else:
            return 0
            
        clicks.createColumn("clicks",map(mapper,zip(clicks1,clicks2)))
        
        return clicks
        
      def averages(self):
        """
        Returns the averaged channel data, as generated by e.g. bifurcationMap
        """
        return self._averages
        
      def trends(self):
        """
        Returns the trend data as generated by bifurcationMap.        
        """
        return self._trends
        
      def means(self):
        """
        Returns the means data as generated by bifurcationMap.
        """
        return self._means
        
      def bifurcationMapRotation(self):
        return self._params["rotation"]
        
      def setBifurcationMapRotation(self,channel,angle):
        """
        Adjusts the rotation parameters used in the bifurcationMap routine.
        """
        print "Setting rotation of channel %d to %f" % (channel,angle)
        self._params["rotation"][channel] = angle
        
      def Psw(self):
        """
        Returns the switching probabilities as generated by bifurcationMap.
        """
        return {"p1x" : self._probabilities[0,0],"px1" : self._probabilities[1,0],"p00" : self._crossProbabilities[0,0],"p01" : self._crossProbabilities[0,1],"p10" : self._crossProbabilities[1,0],"p11" : self._crossProbabilities[1,1]}
                
      def bifurcationMap(self,acquireargs = [0],dmaargs = [True,False],ntimes = 20, calculateAverages = True,calculateMeans = True,calculateTrends = True,rotateChannels = True):
        """
        Analyzes the bifurcation behaviour of the JBA.
        """
        self.bm.setRotation(self._params["rotation"][0],self._params["rotation"][1])
        
        if self._rotatedWaveformArray == None:
          self._waveformArray = zeros((4,self._params["numberOfPoints"] *self._params["numberOfSegments"]))

        self.bm.rotatedWaveform = self._rotatedWaveformArray.ctypes.data
        
        if ntimes != self.nLoops:
          self.nLoops = ntimes
          self.bm.nLoops = self.nLoops
          self._trends = zeros((4,self._params["numberOfSegments"]*self.nLoops))
          self.bm.trends = self._trends.ctypes.data

        self._trends[:,:] = 0
        self._means[:,:] = 0
        self._probabilities[:,:] = 0
        self._crossProbabilities[:,:] = 0
        self._averages[:,:] = 0

        self.bm.init()
        
        for i in range(0,self.nLoops):
          self.AcquireV1(*acquireargs)
          self.DMATransferV1(*dmaargs)
          self.bm.add(self._waveformArray.ctypes.data)

        self.bm.finish()
                
        self.notify("average",None)
          
      def AcquireV1(self,pre_acquisition = 0,timeOut=10000):
        """
        Triggers an acquisition sequence of the Acqiris card and wait for end of acquisition or timeOut(in milliseconds)
        """
        c_pre_acquisition = c_int32(pre_acquisition)
        c_timeOut=c_int32(timeOut)
        status=self.__acqiris.AcquireV1(self.__vi_session,c_pre_acquisition,byref(self.__time_us),c_timeOut) 
        return (status,self.__time_us)      
        if status != 0:
          raise Exception(self.transformErr2Str(status))
        return (status,self.__time_us)
        
      def waveformArray(self):
        return self._waveformArray
        
      def averagedWaveformArray(self):
        return self._averagedWaveformArray
      
      def DMATransferV1(self,voltage = True,getTimeStamps = False,transferAverage = False,wf=None, *args):        
        """
        Transfers the data from the Acqiris card to self._waveformArray
        """
        if wf==None:
          if transferAverage == False:
            if self._waveformArray == None:
              self._waveformArray = zeros((4,self._params["numberOfPoints"] *self._params["numberOfSegments"]))
            wf = self._waveformArray
          else:
            if self._averagedWaveformArray == None:
              self._averagedWaveformArray = zeros((4,self._params["numberOfPoints"]))
            wf=self._averagedWaveformArray
          
        wf[:,:] = 0

        c_used_channels = c_int32(self._params["usedChannels"]) 

        c_voltage = c_bool(bool(voltage))
        c_get_timestamps = c_bool(bool(getTimeStamps))
        
        c_transferAverageType = c_bool * 4
        c_transferAverageArray = c_transferAverageType(*[transferAverage]*4)
       
        
        number_of_segments = c_int32(self._params["numberOfSegments"])
        number_of_samples_per_segment = c_int32(self._params["numberOfPoints"])
        
        number_of_segments_array = zeros(4,dtype = int32)
        number_of_segments_array[:] = self._params["numberOfSegments"]

        number_of_samples_per_segment_array = zeros(4,dtype = int32)
        number_of_samples_per_segment_array[:] = self._params["numberOfPoints"]

        sampling_intervals = zeros(4,dtype = float64)
        sampling_intervals[:] = self._params["sampleInterval"]

        time_stamps_1 = c_double()
        time_stamps_2 = c_double()
        time_stamps_3 = c_double()
        time_stamps_4 = c_double()
                
        c_time_stamp = c_double()
        
        c_time_us = c_double()
        
        status=self.__acqiris.DMATransferV1(
                                      self.__vi_session,
                                      c_used_channels,
                                      number_of_segments,
                                      number_of_samples_per_segment,
                                      c_voltage,
                                      c_get_timestamps,
                                      c_transferAverageArray,
                                      number_of_segments_array.ctypes.data,
                                      number_of_samples_per_segment_array.ctypes.data,
                                      wf[0,:].ctypes.data,wf[1,:].ctypes.data,wf[2,:].ctypes.data,wf[3,:].ctypes.data,
                                      sampling_intervals.ctypes.data,
                                      byref(time_stamps_1),byref(time_stamps_2),byref(time_stamps_3),byref(time_stamps_4),
                                      byref(c_time_us)
                                      ) 
                
        return (status,wf,number_of_segments_array,number_of_samples_per_segment_array)     
        import numpy
        if status != 0:
          raise Exception(self.transformErr2Str(status))
        else:
          print number_segments_returned
          self.notify("data",(list(self.waveform_1),list(self.waveform_2),list(self.waveform_3),list(self.waveform_4)))
          
      def frequenciesAnalysis(self,frequencies=None,Ilist=None,Qlist=None,philist=None,debug=False):

      

        if frequencies==None:
          self._params['nFrequencies']=self._params['numberOfPoints']
          self._frequencies=zeros(self._params['nFrequencies'])
          self._frequencies=arange(0,1,1./self._params['numberOfPoints'])
        else:
          self._params['nFrequencies']=len(frequencies)
          self._frequencies=zeros(self._params['nFrequencies'])
          self._frequencies[:]=frequencies[:]

        if Ilist==None or Qlist==None:
          Ilist=zeros(self._params['nFrequencies'])
          Qlist=zeros(self._params['nFrequencies'])
          philist=zeros(self._params['nFrequencies'])
        self._Ilist=Ilist
        self._Qlist=Qlist
        self._philist=philist
        
        self.av.nSegments=self._params['numberOfSegments']
        self.av.nPoints=self._params["numberOfPoints"]
        self.av.nFrequencies=self._params["nFrequencies"]
        self.av.sampleInterval=self._params['sampleInterval']*1E9
        self._wave=zeros((4,self._params['numberOfSegments'],self._params["numberOfPoints"]))
        self._components=zeros((4,self._params['numberOfSegments'],self._params["nFrequencies"]))
        self._averagesF=zeros((4,self._params["nFrequencies"]))


        self.av.frequencies=self._frequencies.ctypes.data
        self.av.Icorrection=self._Ilist.ctypes.data
        self.av.Qcorrection=self._Qlist.ctypes.data
        self.av.phicorrection=self._philist.ctypes.data
        
        self.av.components=self._components.ctypes.data
        self.av.averages=self._averagesF.ctypes.data

        self.av.init()
        
        if debug:        
          self._wave=zeros((4,self._params['numberOfSegments'],self._params["numberOfPoints"]))
          self._wave[0,0,:]=cos(2*math.pi*1e-9*10E6*arange(0,self._params['numberOfPoints']))
        else:
           self.AcquireV1(0) 
           self.DMATransferV1(wf=self._wave)

#        print self.av.sampleInterval
        self.av.add(self._wave.ctypes.data)

        return (self._wave,self._averagesF,self._components,self._frequencies)

        
      def multiplexedBifurcationMapAdd(self,co,fr):
        r=zeros((4,len(co[0]),len(fr)))
        self.m.add(fr.ctypes.data, co.ctypes.data, len(fr), len(co[0]), r.ctypes.data)
        return r
        
      def multiplexedBifurcationMapSetRotation(self, r,Io,Qo,f):
        self.m.setRotation(r,Io,Qo,f)

      def convertToProbabilities(self,r):
        probabilitiesDatas=zeros((2**len(r[0])))
        self.m.convertToProbabilities(len(r[0]),r.ctypes.data,probabilitiesDatas.ctypes.data)
        proba=dict()
        for i in range(0,len(r[0])):
          proba['p%i' % mybin(i)]=probabilitiesData[i]       
        return proba


               
      def FinishApplicationV1(self,*args):
        self.__acqiris.FinishApplicationV1(self.__vi_session)

      def TemperatureV1(self,*args):
        """
        Returns the temperature of the Acqiris card.
        """
        print args[0]['foo']
        if ___TEST___:
          self.__temperature.value=random.randint(0,100)
        else:
           self.__acqiris.TemperatureV1(self.__vi_session,byref(self.__temperature))
        #We send out a notification that the temperature variable has changed.
        self.notify("temperature",self.__temperature.value)
        return self.__temperature.value
        
      def _time_us(self):
        return self.__time_us.value
        
         
      temperature = property(fget=_temperature)
      time_us = property (fget=_time_us)