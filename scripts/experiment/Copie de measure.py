from pyview.lib.datacube import Datacube
import numpy
import math
from config.instruments import *
from macros.qubit_functions import *

from pyview.helpers.datamanager import DataManager
dataManager = DataManager()
from pyview.helpers.instrumentsmanager import Manager

instruments = Manager()

def measureRabi(qubit,durations,data = None,variable ="p1x",f_sb = -0.1,amplitude = 1.0,averaging = 20,delay = 0,callback = None):
  if data == None:
    data = Datacube()
  data.setParameters(instrumentManager.parameters())
  data.setName("Rabi Sequence - %s" % qubit.name())
  qubit.setDriveFrequency(qubit.parameters()["frequencies.f01"]+f_sb)
  qubit.setDriveAmplitude(I = amplitude,Q = amplitude)
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
    params = fitRabiFrequency(data,variable)
    qubit.parameters()["pulses.xy.t_pi"] = params[1]/2.0
    qubit.parameters()["pulses.xy.drive_amplitude"] = amplitude
    qubit.parameters()["pulses.xy.f_sb"] = f_sb
    data.parameters()["rabiFit"] = params
    qubit.loadRabiPulse(phase = math.pi,readout = qubit.parameters()["timing.readout"],f_sb = f_sb)
    data.savetxt()
  return data

def measureRabi12(qubit,durations,data = None,variable ="p1x",f_sb = -0.1,amplitude = 1.0,averaging = 20,delay = 0,callback = None):

  from instruments.qubit import PulseSequence

  if data == None:
    data = Datacube()
  data.setParameters(instrumentManager.parameters())
  data.setName("Rabi Sequence - %s" % qubit.name())
  f_sb_12 = f_sb-qubit.parameters()["frequencies.f02"]+qubit.parameters()["frequencies.f01"]*2
  print f_sb_12
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
    qubit.parameters()["pulses.xy.t_pi12"] = params[1]/2.0
    qubit.parameters()["pulses.xy.drive_amplitude12"] = amplitude
    qubit.parameters()["pulses.xy.f_sb12"] = f_sb
    data.parameters()["rabiFit12"] = params
    qubit.loadRabiPulse(phase = math.pi,readout = qubit.parameters()["timing.readout"],delay = piLength,f_sb = f_sb)
    qubit.loadRabiPulse(phase = math.pi,readout = qubit.parameters()["timing.readout"],f_sb = f_sb_12)
    data.savetxt()
  return data


def measureRamsey(delays,cube = None,ntimes = 20,length = 20):
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

def measureT1(qubit,delays,data = None,averaging = 20,variable = "p1x"):
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
	

def measureSpectroscopy(qubit,frequencies,data = None,ntimes = 20,amplitude = 0.1,variable = "p1x"):
  if data == None:
    data = Datacube()
  data.setName("Spectroscopy - %s" % qubit.name())
  qubit.loadRabiPulse(length = 500,readout = qubit.parameters()["timing.readout"],f_sb = 0)
  qubit.turnOnDrive()
  data.setParameters(instrumentManager.parameters())
  try:
    for f in frequencies:
      qubit.setDriveFrequency(f)
      qubit.setDriveAmplitude(I = amplitude,Q = amplitude)
      acqiris.bifurcationMap(ntimes = ntimes)
      data.set(f = f)
      data.set(**acqiris.Psw())
      data.commit()
  finally:
    (params,rsquare) = fitQubitFrequency(data,variable)
    qubit.parameters()["frequencies.f01"] = params[1]
    qubit.setDriveFrequency(params[1])
    data.setName(data.name()+" - f01 = %g GHz" % params[1])
    data.savetxt()
  return spectroData

def measureSCurves(qubit,jba,variable = "p1x",data = None,ntimes = 20):
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
    return (vmin*0.9,vmax*1.1)

  try:
    v0 = jba.voltage()
    if data == None:
    	sData = Datacube()
    else:
    	sData = data
    sData.setName("S curves - %s" % qubit.name())
    sData.setParameters(instrumentManager.parameters())
    sOff = Datacube("SOFF")
    sOn = Datacube("SON")
    sData.addChild(sOff)
    sData.addChild(sOn)
    
    qubit.turnOffDrive()
    
    (vmin,vmax) = getVoltageBounds(v0,jba,variable,ntimes)
    
    for v in arange(vmin,vmax,0.005):
      jba.setVoltage(v)
      acqiris.bifurcationMap(ntimes = ntimes)
      sOff.set(**(acqiris.Psw()))
      sOff.set(v = v)
      sOff.commit()
    
    qubit.turnOnDrive()
    
    for v in arange(vmin,vmax,0.005):
      jba.setVoltage(v)
      acqiris.bifurcationMap(ntimes = ntimes)
      sOn.set(**acqiris.Psw())
      sOn.set(v = v)
      sOn.commit()
    
    sOn.createColumn("contrast",sOn.column(variable)-sOff.column(variable))
    
    v0 = sOn.column("v")[argmax(sOn.column("contrast"))]
    maxContrast = max(sOn.column("contrast"))
    
    return (sData,maxContrast,v0)
    
  finally: 
    jba.setVoltage(v0)

