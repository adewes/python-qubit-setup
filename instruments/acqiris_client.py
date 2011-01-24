import sys
import getopt
import socket
import sys
import struct

from pyview.lib.classes import *

___TEST___ = False

CAL_TOUT = 0
CAL_VOIE_COURANTE	= 1
CAL_RAPIDE = 4

#This class simply connects to the Acqiris server.

class Instr(Instrument):

      def __del__(self):
        print "Dying..."

      def initialize(self,host = "localhost",port = 2200):
        self.params = self.defaultParams()
    
        self.params["host"] = host
        self.params["port"] = port  
        self.params["bifurcation"] = [2,250,2,250,180,0,1,0,0,0]
        self.params["offsets"] = list([0,0,0,0])
        self.params["couplings"] = list([3,3,3,3])
        self.params["fullscales"] = list([5,5,5,5])
        self.params["bandwidth"] = list([3,3,3,3])
        
        
        
        usedChannels = 15,freqEch = 499999999.9999999,sampleInterval = 2e-9,averaging = 11,delayTime = 400e-9,numberOfPoints = 250,numberOfSegments = 2000,memType = 100,fullScale1 = 5,offset1 = 0,coupling1 = 3,bandwidth1 = 3,fullScale2 = 5,offset2 = 0,coupling2 = 3,bandwidth2 = 3,fullScale3 = 5,offset3 = 0,coupling3 = 3,bandwidth3 = 3,fullScale4 = 5,offset4 = 0,coupling4 = 3,bandwidth4 = 3,trigSource = -1,trigCoupling = 0,trigSlope = 1,trigLevel = 500,synchro = 1,nbrConvertersPerChannel = 1,nbPtNomMax = 1,confAuto = 1,convertersPerChannel = 0
        
      def defaultParams():
        params = dict()
        
        params["usedchannels"] = 15
        params["freqech"] = 499999999.9999999
        params["sampleinterval"] = 2e-9
        params["averaging"] = 11
        params["delaytime"] = 400e-9
        params["numberofpoints"] = 250
        params["numberofsegments"] = 2000
        params["memtype"]
        
        
        params["fullscale1"] = fullScale1     
        params["fullscale2"] = fullScale2
        params["fullscale3"] = fullScale3
        params["fullscale4"] = fullScale4        

        params["offset1"] = offset1
        params["offset2"] = offset2
        params["offset3"] = offset3
        params["offset4"] = offset4

        params["coupling1"] = coupling1
        params["coupling2"] = coupling2
        params["coupling3"] = coupling3
        params["coupling4"] = coupling4

        params["bandwidth1"] = bandwidth1
        params["bandwidth2"] = bandwidth2
        params["bandwidth3"] = bandwidth3
        params["bandwidth4"] = bandwidth4

        
      def bandwidth(self,channel):
        return self.bandwidths[channel]

      def fullScale(self,channel):
        return self.fullScales[channel]

      def offset(self,channel):
        return self.offsets[channel]

      def coupling(self,channel):
        return self.couplings[channel]

      def _temperature(self):
        return self.__temperature.value

      def setParameters(self,params):
        self.params = params
              
  
      def transformErr2Str(self,*args):
        error_code = c_int32(args[0])
        error_str = create_string_buffer("\000"*1024)
        status = self.__acqiris.transformErr2Str(self.__vi_session,error_code,error_str)        
        self.errorStr(error_str.value)      
      
      def askServer(self,message):
        try:
        	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        	sock.settimeout(30)
        	sock.connect((self.params["host"], self.params["port"]))
        	sock.send(message)
        except:
          print sys.exc_info()
          return None
          
      	chunk = 2048
      	buffer = ""
      	try:
        	received = sock.recv(chunk)
        	while len(received)>0:	
        		buffer+=received
        		received = sock.recv(chunk)
        except:
          print sys.exc_info()
          return None  
        return buffer
        

      def ConfigureV2(self,params):     
        
        for key in params.keys():
          self.params[key] = params[key]
        
        self.statusStr("Configuring...")
        
        configureArgs = ("channels","freqech","sampleinterval","averaging","delaytime","numberofpoints","numberofsegments","memtype","fullscale1","fullscale2","fullscale3","fullscale4","trigsource","trigcoupling","trigslope","triglevel","synchro","nbrconvertersperchannel","nbptnommax","confauto","convertersperchannel")
                
        data = "ConfigureV2|"+str.join("|",map(lambda x:str(params[x]),configureArgs))+"|\0"

        answer = self.askServer(data)
        
        if answer == None:
          return None

        self.statusStr("Answer:"+answer)
        
        self.statusStr("Configuring channels...")
        
        
          
        self.configureChannel(1,params["fullscale1"],params["offset1"],params["coupling1"],params["bandwidth1"])
        self.configureChannel(2,params["fullscale2"],params["offset2"],params["coupling2"],params["bandwidth2"])
        self.configureChannel(3,params["fullscale3"],params["offset3"],params["coupling3"],params["bandwidth3"])
        self.configureChannel(4,params["fullscale4"],params["offset4"],params["coupling4"],params["bandwidth4"])

        self.AcquireV1(0)
  
      def ConfigureChannel(self,channel,fullScale = None,offset = None,coupling = None,bandwidth = None):
        data = "ConfigureChannel|%d|%f|%f|%d|%d|\0" % (fullScale,offset,coupling,bandwidth)
        return self.askServer(data)
                
      def CalibrateV1(self,options,channels):
        data = "CalibrateV1|%d|%|d\0" % (options,channels)
        return self.askServer(data)
      
      def switchingProbability(self,channels = 15,segments = 1000,points = 250,averaging = 11,tension = 1,delay = 400e-9,params = [2,250,2,250,180,0,0,0,0,0]):
        values = self.AcquireV3(channels,segments,points,averaging,tension,delay,params)
        return (values[points],values[points+1],values[points+2])
        
      def AcquireV1(self,preAcquisition):
        data = "AcquireV1|%d|\0" % (preAcquisition)
        return self.askServer(data)
                    
      def AcquireV3(self,averaging = 11,tension = 1,delay = 400e-9,bifurcationParams = None):
        self.statusStr("Acquiring data...")
        self.params["averaging"] = averaging
        self.params["tension"] = tension
        self.params["delay"] = delay
        data = "AcquireV2|%d|%d|%d|%d|%d|%f|\0" % (self.params["usedchannels"],self.params["numberofsegments"],self.params["numberofpoints"],self.params["averaging"],self.params["tension"],self.params["delay"])
        if params != None:
          self.params["bifurcation"] = bifurcationParams
        for param in self.params["bifurcation"]:
        	data+=struct.pack("d",double(param))
        data+='\0'
        response = self.askServer(data)
        if response == None:
          print "No response or timeout!"
          print sys.exc_info()
          return None
      	strlen = 0
      	for i in range(0,len(response)):
      		code = struct.unpack("B1",response[i])[0]
      		if code == 0:
      			strlen = i 
      			break
      	index0 = strlen
      	fieldLen = 8
      	values = []
      	for i in range(0,(len(response)-index0)/fieldLen):
      		values.append(struct.unpack("d",response[index0+i*fieldLen:index0+(i+1)*fieldLen])[0])
      	self.notify("data",values)
      	self.statusStr("Acquisition successful!")
      	return array(values)
        

      def TemperatureV1(self,*args):
        pass
        