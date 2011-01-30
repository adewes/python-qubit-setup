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
    (params,rsquare) = fitRabiFrequency(data,variable)
    if rsquare > 0.5:
      qubit.parameters()["pulses.xy.t_pi"] = params[1]/2.0-params[4]
      qubit.parameters()["pulses.xy.drive_amplitude"] = amplitude
      qubit.parameters()["pulses.xy.f_sb"] = f_sb
      data.parameters()["rabiFit"] = params
      qubit.loadRabiPulse(phase = math.pi,readout = qubit.parameters()["timing.readout"],f_sb = f_sb)
    else:
      print "Rabi fit is not good, resetting parameters..."
      qubit.parameters()["pulses.xy.t_pi"] = None
      qubit.parameters()["pulses.xy.drive_amplitude"] = None
      qubit.parameters()["pulses.xy.f_sb"] = None
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
    varname = "frequencies.readout.f01"
  else:
    varname = "frequencies.f01"
  if rsquare > 0.6:
    qubit.parameters()[varname] = params[1]
    data.setName(data.name()+ " - f01 = %g GHz" % params[1])
  else:
    print "No peak found, setting qubit frequency to undefined..."
    qubit.parameters()[varname] = None
    return data
  if not measureAtReadout:
    if measure20:
      data02 = Datacube("Spectroscopy of (0->2)_2 transition")
      data.addChild(data02)
      frequencies02 = arange(params[1]-0.2,params[1]-0.05,0.001)
      measureSpectroscopy(qubit = qubit,frequencies = frequencies02,data = data02,amplitude = amplitude*5.0,measureAtReadout = measureAtReadout,delay = delay,f_sb = f_sb)
      (params02,rsquare02) = fitQubitFrequency(data02,variable)
      if rsquare02 > 0.5 and params[0] > 0.2:
        qubit.parameters()["frequencies.f02"] = params02[1]*2.0
        data.setName(data.name()+" - f02_2 = %g GHz" % params02[1])
      else:
        qubit.parameters()["frequencies.f02"] = None
  data.savetxt()
  return data

def parameterSurvey(qubit,jba,values,generator,data = None,ntimes = 20,rabiDurations = arange(0,50,2),freqs = list(arange(5.0,6.5,0.002))+list(arange(7.0,8.3,0.002)),autoRange = False,spectroAmp = 0.1,rabiAmp = 1.0,f_sb = -0.1,variable = "p1x"):
  """
  Measure the characteristic properties of the qubit (T1, Rabi period, transition frequency, readout contrast) for a list of different parameters.
  "params" contains a list of parameters, which are iterated over and passed to the function "generator" at each iteration.
  
  Example:
    
    values = [0.0,1.0,2.0]
    
    def generator(x):
      #Set the amplitude of AFG1 to the given parameter value      
      afg1.setAmplitude(x)
  
  """

  if data == None:
    data = Datacube()
  
  data.setName("Parameter Survey - %s" % qubit.name())
  
  for v in values:
    generator(v)

    try:
      jba.calibrate()
    except:
    	continue
    
    vData = Datacube("flux = %g V" % v)
    data.addChild(vData)
    data.set(flux = v)
    
    spectroData = Datacube()
    vData.addChild(spectroData)
    
    #Measure a spectroscopy
    
    spectroscopy(qubit = qubit,frequencies = freqs,variable = variable,data = spectroData,ntimes = 20,amplitude = spectroAmp,measureAtReadout = False)
    if qubit.parameters()["frequencies.f01"] == None:
    	data.commit()
    	continue
    
    freqs = list(arange(qubit.parameters()["frequencies.f01"]-0.2,qubit.parameters()["frequencies.f01"]+0.2,0.002))
    data.set(f01 = qubit.parameters()["frequencies.f01"],f02 = qubit.parameters()["frequencies.f02"])
    
    #Measure a Rabi oscillation
    
    rabiData = Datacube()
    vData.addChild(rabiData)
    
    rabi(qubit = qubit,durations = rabiDurations,variable = variable,data = rabiData,amplitude = rabiAmp,f_sb = f_sb,averaging = 20)
    if qubit.parameters()["pulses.xy.t_pi"] == None:
    	data.commit()
    	continue
    
    data.set(t_pi = qubit.parameters()["pulses.xy.t_pi"])
    sData = Datacube()
    vData.addChild(sData)
    
    #Measure S curves
    
    sCurves(qubit = qubit,jba = jba,variable = variable,data = sData,optimize = "v10")
    data.set(contrast10 = qubit.parameters()["readout.contrast10"])
    
    #Measure T1
    
    t1Data = Datacube()
    vData.addChild(t1Data)
    delays = list(arange(0,200,10))+list(arange(200,2000,50))
    T1(qubit = qubit,delays = delays,variable = variable,data = t1Data, averaging=20)
    data.set(T1 = qubit.parameters()["relaxation.t1"])
    data.commit()
    data.savetxt()

  return data
	
def sCurves(qubit,jba,variable = "p1x",data = None,ntimes = 20,s2=False,optimize = "v10"):
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
    sData.addChild(s0)
    sData.addChild(s1)
   
    
    qubit.turnOffDrive()
    
    (vmin,vmax) = getVoltageBounds(v0,jba,variable,ntimes)
    try:
      measureSingleS(voltages = arange(vmin,vmax,0.005),data = s0,jba = jba,ntimes = ntimes)
    except:
      raise
    qubit.turnOnDrive()
    loadPi01Pulse(qubit)
    try:
      measureSingleS(voltages = arange(vmin,vmax,0.005),data = s1,jba = jba,ntimes = ntimes)
    except:
      raise
    failed12 = False
    if s2:
      try:
        s2 = Datacube("S2")
        sData.addChild(s2)
        loadPi012Pulse(qubit)
        measureSingleS(voltages = arange(vmin,vmax,0.005),data = s2,jba = jba,ntimes = ntimes)  
        s1.createColumn("contrast20",s2.column(variable)-s0.column(variable))
        s1.createColumn("contrast21",s2.column(variable)-s1.column(variable))
        qubit.parameters()["readout.v20"] = s1.column("v")[argmax(s1.column("contrast20"))]
        qubit.parameters()["readout.v21"] = s1.column("v")[argmax(s1.column("contrast21"))]
        qubit.parameters()["readout.contrast20"] = s1.column("contrast20")[argmax(s1.column("contrast20"))]
        qubit.parameters()["readout.contrast21"] = s1.column("contrast21")[argmax(s1.column("contrast21"))]
      except:
        failed12 = True
        raise
    else:
      failed12=True    
    s1.createColumn("contrast10",s1.column(variable)-s0.column(variable))
    qubit.parameters()["readout.v10"] = s1.column("v")[argmax(s1.column("contrast10"))]
    qubit.parameters()["readout.contrast10"] = s1.column("contrast10")[argmax(s1.column("contrast10"))]
    
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


def T1precis(qubit,delays,data = None,averaging = 20,variable = "p1x"):
	print "starting T1precis..."
	if data == None:
		data = Datacube()
	data.setName("T1 - " + qubit.name())
	data.setParameters(instrumentManager.parameters())	
	highTdelays=arange(2500,2600,5)
	try:
		for delay in highTdelays:
			qubit.loadRabiPulse(phase = math.pi,readout = qubit.parameters()["timing.readout"],delay = delay)
			acqiris.bifurcationMap(ntimes = averaging)
			data.set(delay=delay)
			data.set(**acqiris.Psw())
			data.commit()
		highTvalue=data.ColumnMean(variable)
		highTValueFound=True
		print "Long time ps=",highTvalue		
	except:
		highTValueFound=False
		raise 
	try:
		for delay in delays:
			qubit.loadRabiPulse(phase = math.pi,readout = qubit.parameters()["timing.readout"],delay = delay)
			acqiris.bifurcationMap(ntimes = averaging)
			data.set(delay=delay)
			data.set(**acqiris.Psw())
			data.commit()
	finally:
		if highTValueFound:
			print "calling fitT1Parametersprecis"
			params = fitT1Parametersprecis(data,variable,highTvalue)
		else:
			params = fitT1Parameters(data,variable)
		data.setName(data.name()+" - T1 = %g ns " % params[1])
		qubit.parameters()["relaxation.t1"] = params[1]
		data.savetxt()
	return data

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

def essai(data=None):
	print "toto"
	return data

	
print "measure.py loaded"