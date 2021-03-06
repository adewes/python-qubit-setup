from pyview.lib.datacube import Datacube
import numpy
import math
from config.instruments import *
from macros.qubit_functions import *

from pyview.helpers.datamanager import DataManager
dataManager = DataManager()
from pyview.helpers.instrumentsmanager import Manager

instruments = Manager()

def rabi(qubit,durations,data = None,variable ="p1x",f_sb = -0.1,amplitude = 1.0,averaging = 20,delay = 0,callback = None):
  if data == None:
    data = Datacube()
  data.setParameters(instrumentManager.parameters())
  data.setName("Rabi Sequence - %s" % qubit.name())
  qubit.setDriveFrequency(qubit.parameters()["frequencies.f01"]+f_sb)
  qubit.setDriveAmplitude(I = amplitude,Q = amplitude)
  qubit.turnOnDrive()
  try:
    for duration in durations:
      qubit.loadRabiPulse(length = duration,readout = qubit.parameters()["timing.readout"],f_sb = f_sb)
      if callback != None:
        callback(duration)
      acqiris.bifurcationMap(ntimes = averaging)
      data.set(duration = duration)
      data.set(**acqiris.Psw())
      data.commit()
  finally:
    try:
      params = fitRabiFrequency(data,variable)
      qubit.parameters()["pulses.xy.t_pi"] = params[1]/2.0-params[4]
      qubit.parameters()["pulses.xy.drive_amplitude"] = amplitude
      qubit.parameters()["pulses.xy.f_sb"] = f_sb
      data.parameters()["rabiFit"] = params
      qubit.loadRabiPulse(phase = math.pi,readout = qubit.parameters()["timing.readout"],f_sb = f_sb)
    except:
      pass
    data.savetxt()
  return data

def rabi12(qubit,durations,data = None,variable ="p1x",f_sb = -0.1,amplitude = 1.0,averaging = 20,delay = 0,callback = None):

  from instruments.qubit import PulseSequence

  if data == None:
    data = Datacube()
  data.setParameters(instrumentManager.parameters())
  data.setName("Rabi Sequence 12 - %s" % qubit.name())
  f_sb_12 = f_sb-qubit.parameters()["frequencies.f02"]+qubit.parameters()["frequencies.f01"]*2
  qubit.setDriveFrequency(qubit.parameters()["frequencies.f01"]+f_sb)
  qubit.setDriveAmplitude(I = amplitude,Q = amplitude)
  piLength = len(qubit.generateRabiPulse(phase = math.pi,f_sb = f_sb))
  try:
    for duration in durations:
      pulseLength = len(qubit.generateRabiPulse(length = duration,f_sb = f_sb_12))
      seq = PulseSequence()
      seq.addPulse(qubit.generateRabiPulse(phase = math.pi,delay = qubit.parameters()["timing.readout"]-pulseLength-piLength,f_sb = f_sb))
      seq.addPulse(qubit.generateRabiPulse(length = duration,delay = qubit.parameters()["timing.readout"]-pulseLength,f_sb = f_sb_12))
      qubit.loadWaveform(seq.getWaveform(),readout = qubit.parameters()["timing.readout"])
      if callback != None:
        callback(duration)
      acqiris.bifurcationMap(ntimes = averaging)
      data.set(duration = duration)
      data.set(**acqiris.Psw())
      data.commit()
  finally:
    if len(data) == 0:
      return
    params = fitRabi12Frequency(data,variable)
    qubit.parameters()["pulses.xy.t_pi12"] = params[1]/2.0-params[4]
    qubit.parameters()["pulses.xy.drive_amplitude12"] = amplitude
    qubit.parameters()["pulses.xy.f_sb12"] = f_sb
    data.parameters()["rabiFit12"] = params
    seq = PulseSequence()
    pulseLength = len(qubit.generateRabiPulse(length = params[1]/2.0-params[4],f_sb = f_sb_12))
    seq.addPulse(qubit.generateRabiPulse(phase = math.pi,delay = qubit.parameters()["timing.readout"]-pulseLength-piLength,f_sb = f_sb))
    seq.addPulse(qubit.generateRabiPulse(length = params[1]/2.0-params[4],delay = qubit.parameters()["timing.readout"]-pulseLength,f_sb = f_sb_12))
    qubit.loadWaveform(seq.getWaveform(),readout = qubit.parameters()["timing.readout"])
    data.savetxt()
  return data

def rabi02(qubit,durations,data = None,variable ="p1x",f_sb = -0.1,amplitude = 1.0,averaging = 20,delay = 0,callback = None):

  from instruments.qubit import PulseSequence

  if data == None:
    data = Datacube()
  data.setParameters(instrumentManager.parameters())
  data.setName("Rabi Sequence 02 - %s" % qubit.name())
  f_sb_12 = f_sb-qubit.parameters()["frequencies.f02"]+qubit.parameters()["frequencies.f01"]*2
  qubit.setDriveFrequency(qubit.parameters()["frequencies.f01"]+f_sb)
  qubit.setDriveAmplitude(I = amplitude,Q = amplitude)
  pi12Length = len(qubit.generateRabiPulse(phase = qubit.parameters()["pulses.xy.t_pi12"],f_sb = f_sb))
  try:
    for duration in durations:
      pulseLength = len(qubit.generateRabiPulse(length = duration,f_sb = f_sb_12))
      seq = PulseSequence()
      seq.addPulse(qubit.generateRabiPulse(length = duration,delay = qubit.parameters()["timing.readout"]-pulseLength-pi12Length,f_sb = f_sb))
      seq.addPulse(qubit.generateRabiPulse(length = qubit.parameters()["pulses.xy.t_pi12"],delay = qubit.parameters()["timing.readout"]-pi12Length,f_sb = f_sb_12))
      qubit.loadWaveform(seq.getWaveform(),readout = qubit.parameters()["timing.readout"])
      if callback != None:
        callback(duration)
      acqiris.bifurcationMap(ntimes = averaging)
      data.set(duration = duration)
      data.set(**acqiris.Psw())
      data.commit()
  finally:
    data.savetxt()
  return data

def ramsey(delays,cube = None,ntimes = 20,length = 20):
	if cube == None:
		ramseyData = Datacube()
	else:
		ramseyData = cube
	ramseyData.setParameters(instruments.parameters())
	for delay in delays:
		generateRamseyWaveform(length = length,delay = delay)
		acqiris.bifurcationMap(ntimes = ntimes)
		ramseyData.set(delay = delay,**acqiris.Psw())
		ramseyData.commit()
	return rabiData

def T1(qubit,delays,data = None,averaging = 20,variable = "p1x"):
  if data == None:
  	data = Datacube()
  data.setName("T1 - " + qubit.name())
  data.setParameters(instrumentManager.parameters())
  try:
    for delay in delays:
      qubit.loadRabiPulse(phase = math.pi,readout = qubit.parameters()["timing.readout"],delay = delay)
      acqiris.bifurcationMap(ntimes = averaging)
      data.set(delay = delay)
      data.set(**acqiris.Psw())
      data.commit()
  finally:
    params = fitT1Parameters(data,variable)
    data.setName(data.name()+" - T1 = %g ns " % params[2])
    qubit.parameters()["relaxation.t1"] = params[2]
    data.savetxt()
  return data
	

def measureSpectroscopy(qubit,frequencies,data = None,ntimes = 20,amplitude = 0.1,measureAtReadout = False,delay = 0,f_sb = 0):
  if data == None:
    data = Datacube()
  if measureAtReadout:
    qubit.loadRabiPulse(length = 500,readout = qubit.parameters()["timing.readout"]+500,f_sb = f_sb,delay = delay)
  else:
    qubit.loadRabiPulse(length = 500,readout = qubit.parameters()["timing.readout"],f_sb = f_sb,delay = delay)
  qubit.turnOnDrive()
  data.setParameters(instrumentManager.parameters())
  try:
    for f in frequencies:
      qubit.setDriveFrequency(f+f_sb)
      qubit.setDriveAmplitude(I = amplitude,Q = amplitude)
      acqiris.bifurcationMap(ntimes = ntimes)
      data.set(f = f)
      data.set(**acqiris.Psw())
      data.commit()
  finally:
    return data

def spectroscopy(qubit,frequencies,data = None,ntimes = 20,amplitude = 0.1,variable = "p1x",measureAtReadout = False,delay = 0,f_sb = 0,measure20 = True):
  if data == None:
    data = Datacube()
  if measureAtReadout:
    data.setName("Spectroscopy at Readout - %s" % qubit.name())
  else:
    data.setName("Spectroscopy - %s" % qubit.name())
  measureSpectroscopy(qubit = qubit,frequencies = frequencies,data = data,amplitude = amplitude,measureAtReadout = measureAtReadout,delay = delay,f_sb = f_sb)
  (params,rsquare) = fitQubitFrequency(data,variable)
  if measureAtReadout:
    qubit.parameters()["frequencies.readout.f01"] = params[1]
  else: 
    qubit.parameters()["frequencies.f01"] = params[1]
    qubit.setDriveFrequency(params[1])
  data.setName(data.name()+ " - f01 = %g GHz" % params[1])
  if not measureAtReadout:
    if measure20:
      data02 = Datacube("Spectroscopy of (0->2)_2 transition")
      data.addChild(data02)
      frequencies02 = arange(params[1]-0.2,params[1]-0.05,0.001)
      measureSpectroscopy(qubit = qubit,frequencies = frequencies02,data = data02,amplitude = amplitude*10.0,measureAtReadout = measureAtReadout,delay = delay,f_sb = f_sb)
      (params02,rsquare02) = fitQubitFrequency(data02,variable)
      qubit.parameters()["frequencies.f02"] = params02[1]*2.0
      data.setName(data.name()+" - f02_2 = %g GHz" % params02[1])
  data.savetxt()
  return data

def sCurves(qubit,jba,variable = "p1x",data = None,ntimes = 20,optimize = "v20"):
  """
  Measures the s curves of the JBA. Assumes that the qubit is alread preset to a pi-pulse.
  """
  def getVoltageBounds(v0,jba,variable,ntimes):
    v = v0
    jba.setVoltage(v)
    acqiris.bifurcationMap(ntimes = ntimes)
    p = acqiris.Psw()[variable]
    
    while p > 0.03 and v < v0*2.0:
      v*=1.05
      jba.setVoltage(v)
      acqiris.bifurcationMap()
      p = acqiris.Psw()[variable]
    vmax = v
    
    v = v0
    jba.setVoltage(v)
    acqiris.bifurcationMap(ntimes = ntimes)
    p = acqiris.Psw()[variable]
    
    while p < 0.98 and v > v0/2.0:
      v/=1.05
      jba.setVoltage(v)
      acqiris.bifurcationMap()
      p = acqiris.Psw()[variable]
    vmin = v
    return (vmin*0.95,vmax*1.2)

  try:
    v0 = jba.voltage()
    if data == None:
    	sData = Datacube()
    else:
    	sData = data
    sData.setName("S curves - %s" % qubit.name())
    sData.setParameters(instrumentManager.parameters())
    s0 = Datacube("S0")
    s1 = Datacube("S1")
    s2 = Datacube("S2")
    
    sData.addChild(s0)
    sData.addChild(s1)
    sData.addChild(s2)
    
    qubit.turnOffDrive()
    
    (vmin,vmax) = getVoltageBounds(v0,jba,variable,ntimes)
    measureSingleS(voltages = arange(vmin,vmax,0.005),data = s0,jba = jba,ntimes = ntimes)

    qubit.turnOnDrive()

    loadPi01Pulse(qubit)
    measureSingleS(voltages = arange(vmin,vmax,0.005),data = s1,jba = jba,ntimes = ntimes)

    failed12 = False

    try:
      loadPi012Pulse(qubit)
      measureSingleS(voltages = arange(vmin,vmax,0.005),data = s2,jba = jba,ntimes = ntimes)  
      s1.createColumn("contrast20",s2.column(variable)-s0.column(variable))
      s1.createColumn("contrast21",s2.column(variable)-s1.column(variable))
      qubit.parameters()["readout.v20"] = s1.column("v")[argmax(s1.column("contrast20"))]
      qubit.parameters()["readout.v21"] = s1.column("v")[argmax(s1.column("contrast21"))]
    except:
      failed12 = True
      raise
      
    s1.createColumn("contrast10",s1.column(variable)-s0.column(variable))
    qubit.parameters()["readout.v10"] = s1.column("v")[argmax(s1.column("contrast10"))]
    
    if optimize == "v20" and not failed12:
      imax = argmax(s1.column("contrast20"))
      qubit.parameters()["readout.p11"] = s2.column(variable)[imax]
      v0 = s1.column("v")[imax]
    elif optimize == "v21" and not failed12:
      imax = argmax(s1.column("contrast21"))
      v0 = s1.column("v")[imax]
    else:
      imax = argmax(s1.column("contrast10"))
      qubit.parameters()["readout.p11"] = s1.column(variable)[imax]
      v0 = s1.column("v")[imax]
    
    #To do: Add dialog to ask to which voltage (v10,v20,v21) in 
    
    qubit.parameters()["readout.p00"] = 1.0-s0.column(variable)[imax]

    return (sData,v0)
    
  finally: 
    jba.setVoltage(v0)
    data.savetxt()

def measureSingleS(voltages,data,jba,ntimes = 20):
  try:
    for v in voltages:
      jba.setVoltage(v)
      acqiris.bifurcationMap(ntimes = ntimes)
      data.set(**(acqiris.Psw()))
      data.set(v = v)
      data.commit()
  finally:
    pass

def loadPi012Pulse(qubit):
  from instruments.qubit import PulseSequence
  seq = PulseSequence()
  f_sb = qubit.parameters()["pulses.xy.f_sb"]
  f_sb_12 = f_sb-qubit.parameters()["frequencies.f02"]+qubit.parameters()["frequencies.f01"]*2
  piLength = len(qubit.generateRabiPulse(phase = math.pi,f_sb = f_sb))
  pulseLength = len(qubit.generateRabiPulse(length = qubit.parameters()["pulses.xy.t_pi12"],f_sb = f_sb_12))
  seq.addPulse(qubit.generateRabiPulse(phase = math.pi,delay = qubit.parameters()["timing.readout"]-pulseLength-piLength,f_sb = f_sb))
  seq.addPulse(qubit.generateRabiPulse(length = qubit.parameters()["pulses.xy.t_pi12"],delay = qubit.parameters()["timing.readout"]-pulseLength,f_sb = f_sb_12))
  qubit.loadWaveform(seq.getWaveform(),readout = qubit.parameters()["timing.readout"])

def loadPi01Pulse(qubit):
  f_sb = qubit.parameters()["pulses.xy.f_sb"]
  qubit.loadRabiPulse(phase = math.pi,readout = qubit.parameters()["timing.readout"],f_sb = f_sb)
