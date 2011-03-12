import sys
import getopt
import re
import visa
import struct
import numpy
import ctypes

from pyview.lib.classes import *
      
class Instr(VisaInstrument):

  def saveState(self,name):
    self.write("*SAV 1")
    self.write("MMemory:STORE:STATE 1,\"%s.TFS\"" % name)
    params = dict()
    params["name"] = name
    params["output"] = self.output()
    return params
    
  def restoreState(self,state):
    self.write("MMemory:LOAD:STATE 1,\"%s.TFS\"" % state["name"])
    self.write("*RCL 1")
    if state["output"]:
      self.turnOn()

  def offset(self):
    o = float(self.ask("SOURCE%d:VOLTAGE:LEVEL:IMMEDIATE:OFFSET?" % (self._source)))
    self.notify("offset",o)
    self._params['offset'] = o
    return o
    
  def output(self):
    state = int(self.ask("OUTPUT%d:STATE?" % (self._source)))
    if state:
      self._params['output'] = True
      return True
    self._params['output'] = False
    return False
    
  #Set the repetition frequency in MHz
  def setFixedFrequency(self,freq):
    self.write("SOURCE%d:FREQUENCY:FIXED %f MHz" % (self._source,freq))
    
  def writeVectorWaveform(self,name,points,length,baseLevel = 0):
    waveform = numpy.zeros((length))
    if baseLevel != 0:
      waveform[:] = baseLevel
    start = points[0]
    for i in range(1,len(points)):
      end = points[i]
      for j in range(start[0],end[0]+1):
        if j > 0 and j < len(waveform):
          waveform[j]=start[1]+int(float((end[1]-start[1])*(j-start[0]))/float(end[0]-start[0]))
      start = end
    self.writeWaveform(name,waveform)
    
  def _encodeWaveform(self,waveform,fastMethod = True):
    if fastMethod:
      #We use numpy to quickly convert our data to a binary string...
      data = numpy.zeros(len(waveform),dtype = numpy.dtype(">i2"))
      data[:] = waveform[:]
      ptr = data.ctypes.data_as(ctypes.POINTER(ctypes.c_char))[:len(waveform)*2]
      return ptr
    data = ""
    for element in waveform:
      data+=struct.pack(">H",int(element))
    return data
    
  def readWaveform(self,name):
    self.write("DATA:COPY EMemory,%s" % name)
    data = self.ask("DATA:DATA? EMEMORY")
    length = int(data[1])
    bytes = data[1:1+length+1]
    values = data[1+length+1:]
    data = []
    for i in range(0,len(values)/2):
      value = unpack(">H1",values[i*2:i*2+2])
      if not value == None:
        data.append(value[0])
    return data
    
  def writeWaveform(self,name,waveform):
    data = self._encodeWaveform(waveform)
    self.write("DATA:DATA EMemory,#%d%d%s" % (len(str(len(waveform)*2)),len(waveform)*2,data))
    self.write("DATA:COPY %s,EMemory" % name)
    
  def setWaveform(self,name):
    self.write("SOURCE%d:FUNCTION:SHAPE %s" % (self._source,name))
    
  def turnOn(self):
    self.write("OUTPUT%d:STATE ON" % self._source)
    return self.output()
    
  def turnOff(self):
    self.write("OUTPUT%d:STATE OFF" % self._source)
    return self.output()

  def triggerDelay(self):
    td = float(self.ask("SOURCE%d:BURST:TDELAY?" % (self._source)))
    self._params['triggerDelay'] = td
    return td

  def setTriggerDelay(self,d):
    self.write("SOURCE%d:BURST:TDELAY %f ns" % (self._source,d))
    self._params['triggerDelay'] = d
    return self.pulseDelay()

  def setPulseDelay(self,d):
    self.write("SOURCE%d:PULSE:DELAY %f ns" % (self._source,d))
    return self.pulseDelay()

  def setPulseWidth(self,w):
    self.write("SOURCE%d:PULSE:WIDTH %f ns" % (self._source,w))
    return self.pulseWidth()

  def setOffset(self,o):
    self.write("SOURCE%d:VOLTAGE:LEVEL:IMMEDIATE:OFFSET %f" % (self._source,o))
    return self.offset()
    
  def setAmplitude(self,a):
    self.write("SOURCE%d:VOLTAGE:LEVEL:IMMEDIATE:AMPLITUDE %f" % (self._source,a))
    return self.amplitude()
    
  def setLow(self,o):
    self.write("SOURCE%d:VOLTAGE:LEVEL:IMMEDIATE:LOW %f V" % (self._source,o))
    return self.low()
    
  def low(self):
    l = float(self.ask("SOURCE%d:VOLTAGE:LEVEL:IMMEDIATE:LOW?" % (self._source)))
    self.notify("low",l)
    self._params['low'] = l
    return l

  def pulseDelay(self):
    pd = float(self.ask("SOURce%d:PULSe:DELAY?" % (self._source)))
    self.notify("pulseDelay",pd)
    self._params['pulseDelay'] = pd
    return pd

  def pulseWidth(self):
    pw = float(self.ask("SOURCE%d:PULSE:WIDTH?"% (self._source)))
    self.notify("pulseWidth",pw)
    self._params['pulseWidth'] = pw
    return pw
    
  def high(self):
    h = float(self.ask("SOURCE%d:VOLTAGE:LEVEL:IMMEDIATE:HIGH?" % (self._source)))
    self.notify("high",h)
    self._params['high'] = h
    return h
    
  def setHigh(self,a):
    self.write("SOURCE%d:VOLTAGE:LEVEL:IMMEDIATE:HIGH %f V" % (self._source,a))
    return self.high()
    
  def amplitude(self):
    a = float(self.ask("SOURCE%d:VOLTAGE:LEVEL:IMMEDIATE:AMPLITUDE?" % (self._source)))
    self.notify("amplitude",a)
    self._params['amplitude'] = a
    return a
    
  def setPeriod(self,p):
    self.setFrequency(1.0/p*1e9)
    
  def period(self):
    p = 1.0/float(self.ask("SOURCE%d:FREQUENCY:FIXED?" % self._source))*1e9
    self._params["period"] = p
    self._params["frequency"] = 1.0/p
    return p
  
  def setFrequency(self,f):
    if f > 60e6:
      raise Exception("AFG Repetition frequency is too high!")
    self.write("SOURCE%d:FREQUENCY:FIXED %f Hz" % (self._source,f))

  def frequency(self):
    f = float(self.ask("SOURCE%d:FREQUENCY:FIXED?" % self._source))
    self._params["frequency"] = f
    self._params["period"] = 1.0/f
    return f

  def parameters(self,lazy = True):
    if not lazy:
      self._params['amplitude'] = self.amplitude()
      self._params['offset'] = self.offset()
      self._params['output'] = self.output()
      self._params['pulseDelay'] = self.pulseDelay()
      self._params['pulseWidth'] = self.pulseWidth()
      self._params['triggerDelay'] = self.triggerDelay()
      self._params['low'] = self.low()
      self._params['high'] = self.high()
    return self._params
        
  def initialize(self,visaAddress = "TCPIP0::192.168.0.21::inst0",name = "Tektronix AFG",source = 1):
    try:
      self._params = dict()
      self.waveforms = []
      self._name = name
      self._source = source
      self._visaAddress = visaAddress
      self.parameters(lazy = False)
    except:
      self.statusStr("An error has occured. Cannot initialize %s." % self._name)        
