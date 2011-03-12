from pyview.lib.datacube import Datacube
import numpy
import math
from config.instruments import *

from macros.qubit_functions import *
reload(sys.modules["macros.qubit_functions"])
from macros.qubit_functions import *


from pyview.helpers.datamanager import DataManager
dataManager = DataManager()
from pyview.helpers.instrumentsmanager import Manager
from instruments.qubit import *
reload(sys.modules["instruments.qubit"])
from instruments.qubit import *

if qubit1==None:
  qubit1 = instrumentManager.initInstrument('qubit1',"qubit",kwargs = {'fluxlineResponse':fluxline1Response,'fluxlineWaveform':'USER1','fluxline':'afg1','iqOffsetCalibration':qubit1IQOffset,'iqSidebandCalibration':qubit1IQSideband,'iqPowerCalibration':qubit1IQPower,'jba':'jba1',"awgChannels":[1,2],"variable":1,"waveforms":["qubit1iReal","qubit1qReal"],"awg":"awg","mwg":"qubit1mwg"},forceReload = True)


instruments = Manager()

def ramsey(qubit,durations,data = None,variable ="p1x",callback = None,angle = 0,averaging = 20,amplitude = 0,f_offset = 0,correctFrequency = False):
  if data == None:
    data = Datacube()
  data.setParameters(instrumentManager.parameters())
  data.parameters()["defaultPlot"]=[["duration",variable]]
  data.setName("Ramsey Sequence - %s" % qubit.name())
  f_sb = qubit.parameters()["pulses.xy.f_sb"]
  if 'pulses.xy.f_shift' in qubit.parameters():
    f_shift=qubit.parameters()["pulses.xy.f_shift"]          
  else:
    f_shift=0
  qubit.setDriveFrequency(qubit.parameters()["frequencies.f01"]+f_sb)
  f_sb-=f_shift
  qubit.setDriveAmplitude(I = qubit.parameters()["pulses.xy.drive_amplitude"],Q = qubit.parameters()["pulses.xy.drive_amplitude"])
  qubit.turnOnDrive()
  if amplitude != 0:
    qubit.pushState()
  baseForm = qubit.fluxlineWaveform()
  try:
    for duration in durations:
      seq = PulseSequence()
      l = len(qubit.generateRabiPulse(phase = math.pi/2.0))
      zLen = len(qubit.generateZPulse(length = duration))
      if amplitude != 0:
        zSeq = PulseSequence()
        zSeq.addPulse(baseForm)
        zSeq.setPosition(0)
        zSeq.addPulse(qubit.generateZPulse(length = duration,delay = qubit.parameters()["timing.readout"]-zLen-l)*amplitude)
        qubit.loadFluxlineWaveform(zSeq.getWaveform(),compensateResponse = False)
      seq.addPulse(qubit.generateRabiPulse(angle = angle,phase = math.pi/2.0,f_sb = f_sb-f_offset,sidebandDelay = seq.position()))
      seq.addWait(zLen)
      seq.addPulse(qubit.generateRabiPulse(angle = angle,phase = math.pi/2.0,f_sb = f_sb-f_offset,sidebandDelay = seq.position()))
      qubit.loadWaveform(seq.getWaveform(endAt = qubit.parameters()["timing.readout"]),readout = qubit.parameters()["timing.readout"])
      if callback != None:
        callback(duration)
      acqiris.bifurcationMap(ntimes = averaging)
      data.set(duration = duration)
      data.set(**acqiris.Psw())
      data.commit()
  finally:
    if amplitude != 0:
      qubit.popState()
    (params,rsquare) = fitRamseyFrequency(data,variable,f_offset=f_offset)
    if rsquare > 0.5:
      qubit.parameters()["pulses.ramsey.t_pi"] = params[1]/2.0
      data.setName(data.name()+" - f_r = %g MHz - T_2 = %g ns" % ((1.0/params[1])*1000,params[2]))
      data.parameters()["ramseyFit"] = params
      if correctFrequency and amplitude == 0:
        print "Correcting qubit frequency by %g MHz" % (abs(1.0/params[1]-abs(f_offset))*1000)
        qubit.parameters()["frequencies.f01"]-=1.0/params[1]-abs(f_offset)
        qubit.setDriveFrequency(qubit.parameters()["frequencies.f01"])
    else:
      print "Ramsey fit is not good, resetting parameters..."
      qubit.parameters()["pulses.ramsey.t_pi"] = None
    data.savetxt()
  return data


def rabi(qubit,durations,data = None,variable ="p1x",f_sb = -0.1,amplitude = 1.0,averaging = 20,delay = 0,callback = None,angle = 0,compositePulse = False,gaussian = True,flank = 3):
  if data == None:
    data = Datacube()
  data.setParameters(instrumentManager.parameters())
  data.parameters()["defaultPlot"]=[["duration",variable]]

  data.setName("Rabi Sequence - %s" % qubit.name())
  qubit.setDriveFrequency(qubit.parameters()["frequencies.f01"]+f_sb)
  qubit.setDriveAmplitude(I = amplitude,Q = amplitude)
  qubit.turnOnDrive()
  try:
    for duration in durations:
      if compositePulse:
        seq = PulseSequence()
        seq.addPulse(qubit.generateRabiPulse(angle = angle,length = duration/2.0,f_sb = f_sb,sidebandDelay = seq.position(),gaussian = gaussian))
        seq.addWait(10)
        seq.addPulse(qubit.generateRabiPulse(angle = angle,length = duration/2.0,f_sb = f_sb,sidebandDelay = seq.position(),gaussian = gaussian))
        qubit.loadWaveform(seq.getWaveform(endAt = qubit.parameters()["timing.readout"]-delay),readout = qubit.parameters()["timing.readout"])
      else:
        qubit.loadRabiPulse(flank = flank,angle = angle,length = duration,delay = delay,readout = qubit.parameters()["timing.readout"],f_sb = f_sb,gaussian = gaussian)
      if callback != None:
        callback(duration)
      acqiris.bifurcationMap(ntimes = averaging)
      data.set(duration = duration)
      data.set(**acqiris.Psw())
      data.commit()
  except:
    import traceback
    traceback.print_exc()
  finally:
    (params,rsquare) = fitRabiFrequency(data,variable,withOffset = True)
    if rsquare > 0.5:
      qubit.parameters()["pulses.xy.t_pi"] = float(params[1]/2.0)
      qubit.parameters()["pulses.xy.drive_amplitude"] = float(amplitude)
      qubit.parameters()["pulses.xy.f_sb"] = float(f_sb)
      data.parameters()["rabiFit"] = params
      qubit.loadRabiPulse(flank = flank,angle = angle,phase = math.pi,readout = qubit.parameters()["timing.readout"],f_sb = f_sb)
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

def measureSpectroscopy(qubit,frequencies,data = None,ntimes = 20,amplitude = 1,measureAtReadout = False,delay = 0,f_sb = 0,delayAtReadout = 1500):
  if data == None:
    data = Datacube()
  if measureAtReadout:
    qubit.loadRabiPulse(length = 500,readout = qubit.parameters()["timing.readout"]+delayAtReadout,f_sb = f_sb,delay = delay)
  else:
    qubit.loadRabiPulse(length = 500,readout = qubit.parameters()["timing.readout"],f_sb = f_sb,delay = delay)
  qubit.turnOnDrive()
  data.setParameters(dict(data.parameters(),**instrumentManager.parameters()))
  try:
    for f in frequencies:
      qubit.setDriveFrequency(f+f_sb)
      qubit.setDriveAmplitude(I = amplitude,Q = amplitude)
      acqiris.bifurcationMap(ntimes = ntimes)
      data.set(f = f)
      data.set(**acqiris.Psw())
      data.commit()
  except StopThread:
    return data

def spectroscopy(qubit,frequencies,data = None,ntimes = 20,amplitude = 0.1,variable = "p1x",measureAtReadout = False,delay = 0,f_sb = 0,measure20 = True,fitFrequency = True,factor20 = 10.0,delayAtReadout = 1500):
  f_drive = qubit.driveFrequency()
  try:
    if data == None:
      data = Datacube()
    if measureAtReadout:
      data.setName("Spectroscopy at Readout - %s" % qubit.name())
    else:
      data.setName("Spectroscopy - %s" % qubit.name())
    data.parameters()["defaultPlot"]=[["f",variable]]
    measureSpectroscopy(qubit = qubit,frequencies = frequencies,data = data,amplitude = amplitude,measureAtReadout = measureAtReadout,delay = delay,f_sb = f_sb,delayAtReadout = delayAtReadout)
    if fitFrequency:
      (params,rsquare) = fitQubitFrequency(data,variable)
      if measureAtReadout:
        varname01 = "frequencies.readout.f01"
      else:
        varname01 = "frequencies.f01"
      if rsquare > 0.6:
        print params[1]
        qubit.parameters()[varname01] = params[1]
        data.setName(data.name()+ " - f01 = %g GHz" %  qubit.parameters()[varname01])
      else:
        print "No peak found..."
        data.savetxt()
        return data
    if measure20:
      data02 = Datacube("Spectroscopy of (0->2)_2 transition")
      data.addChild(data02)
      frequencies02 = arange(params[1]-0.2,params[1]-0.05,0.001)
      data02.parameters()["defaultPlot"]=[["f",variable]]
      measureSpectroscopy(qubit = qubit,frequencies = frequencies02,data = data02,amplitude = amplitude*factor20,measureAtReadout = measureAtReadout,delay = delay,f_sb = f_sb,delayAtReadout = delayAtReadout)
      (params02,rsquare02) = fitQubitFrequency(data02,variable)
      if rsquare02 > 0.5 and params[0] > 0.2:
        if measureAtReadout:
          varname02 = "frequencies.readout.f02"
          varname12 = "frequencies.readout.f12"
        else:
          varname02 = "frequencies.f02"
          varname12 = "frequencies.f12"
        qubit.parameters()[varname02] = params02[1]*2.0
        qubit.parameters()[varname12] = params02[1]*2.0-qubit.parameters()[varname01]
        data.setName(data.name()+" - f02_2 = %g GHz" % (qubit.parameters()[varname02]/2))
    data.savetxt()
    return data
  finally:
    qubit.setDriveFrequency(f_drive)

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
    
    if autoRange:
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
    
    #Measure T2

    ramseyData = Datacube()
    vData.addChild(ramseyData)
    durations = arange(0,200,3.0)
    ramsey(qubit = qubit,durations = durations,variable = variable,data = ramseyData,averaging = 20,amplitude = 0.0,f_offset = 0.03,correctFrequency = False)
    data.set(T2 = ramseyData.parameters()["ramseyFit"][2])
    data.set(Tphi = 1.0/(1.0/ramseyData.parameters()["ramseyFit"][2]-1.0/2./qubit.parameters()["relaxation.t1"]))

    data.commit()
    data.savetxt()

  return data
	
def sCurves(qubit,jba,variable = "p1x",data = None,ntimes = 20,s2=False,optimize = "v10",step = 0.005,measureErrors = False,saveData = True):
  """
  Measures the s curves of the JBA. Assumes that the qubit is alread preset to a pi-pulse.
  """
  def getVoltageBounds(v0,jba,variable,ntimes):
    v = v0
    jba.setVoltage(v)
    acqiris.bifurcationMap(ntimes = ntimes)
    p = acqiris.Psw()[variable]
    
    while p > 0.03 and v < v0*2.0:
      v*=1.1
      jba.setVoltage(v)
      acqiris.bifurcationMap()
      p = acqiris.Psw()[variable]
    vmax = v
    
    v = v0
    jba.setVoltage(v)
    acqiris.bifurcationMap(ntimes = ntimes)
    p = acqiris.Psw()[variable]
    
    while p < 0.98 and v > v0/2.0:
      v/=1.1
      jba.setVoltage(v)
      acqiris.bifurcationMap()
      p = acqiris.Psw()[variable]
    vmin = v
    return (vmin*0.95,vmax*1.1)

  hasFinished = False
  
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
    s0.parameters()["defaultPlot"]=[["v",variable]]
    s1.parameters()["defaultPlot"]=[["v",variable]]
    s1.parameters()["defaultPlot"].append(["v","contrast10"])

    error=False 
        
    qubit.turnOnDrive()
    qubit.loadRabiPulse(length = 0)
    
    (vmin,vmax) = getVoltageBounds(v0,jba,variable,ntimes)
    try:
      measureSingleS(voltages = arange(vmin,vmax,step),data = s0,jba = jba,ntimes = ntimes)
    except:
      error=True
      pass
    qubit.loadRabiPulse(phase = math.pi)
    try:
      measureSingleS(voltages = arange(vmin,vmax,step),data = s1,jba = jba,ntimes = ntimes)
    except:
      error=True
      pass
    failed12 = False
    if s2:
      try:
        s2 = Datacube("S2")
        s2.parameters()["defaultPlot"]=[["v",variable]]
        sData.addChild(s2)
        loadPi012Pulse(qubit)
        measureSingleS(voltages = arange(vmin,vmax,step),data = s2,jba = jba,ntimes = ntimes)  
        s1.createColumn("contrast20",s2.column(variable)-s0.column(variable))
        s1.createColumn("contrast21",s2.column(variable)-s1.column(variable))
        qubit.parameters()["readout.v20"] = float(s1.column("v")[argmax(s1.column("contrast20"))])
        qubit.parameters()["readout.v21"] = float(s1.column("v")[argmax(s1.column("contrast21"))])
        qubit.parameters()["readout.contrast20"] = float(s1.column("contrast20")[argmax(s1.column("contrast20"))])
        qubit.parameters()["readout.contrast21"] = float(s1.column("contrast21")[argmax(s1.column("contrast21"))])
      except:
        failed12 = True
        raise
    else:
      failed12=True    
    s1.createColumn("contrast10",s1.column(variable)-s0.column(variable))
    s1.parameters()["defaultPlot"].append(["v",variable])
    qubit.parameters()["readout.v10"] = float(s1.column("v")[argmax(s1.column("contrast10"))])
    qubit.parameters()["readout.contrast10"] = float(s1.column("contrast10")[argmax(s1.column("contrast10"))])
    
    if optimize == "v20" and not failed12:
      imax = argmax(s1.column("contrast20"))
      v0 = s1.column("v")[imax]
    elif optimize == "v21" and not failed12:
      imax = argmax(s1.column("contrast21"))
      v0 = s1.column("v")[imax]
    else:
      imax = argmax(s1.column("contrast10"))
      v0 = s1.column("v")[imax]
      
    hasFinished = True
    
    return (sData,v0)
    
  finally: 
    jba.setVoltage(v0)

    if hasFinished:
      if optimize == 'v20': 
        loadPi012Pulse(qubit)
      else:
        qubit.loadRabiPulse(phase = math.pi)
  
      if measureErrors:
  
        qubit.turnOffDrive()
        acqiris.bifurcationMap(ntimes = 400)
        qubit.parameters()["readout.p00"] = float(1.0-acqiris.Psw()[variable])
  
        qubit.turnOnDrive()
        acqiris.bifurcationMap(ntimes = 400)
        qubit.parameters()["readout.p11"] = float(acqiris.Psw()[variable])
        
    data.setName(data.name()+" - v01 = %g" % qubit.parameters()["readout.contrast10"])
    if saveData:
      data.savetxt()

def measureSingleS(voltages,data,jba,ntimes = 20):
  try:
    for v in voltages:
      jba.setVoltage(v)
      acqiris.bifurcationMap(ntimes = ntimes)
      data.set(v = v)
      data.set(**(acqiris.Psw()))
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


def T1precis(qubit,delays,data = None,averaging = 20,variable = "p1x"):
	print "starting T1precis..."
	if data == None:
		data = Datacube()
	data.setName("T1 - " + qubit.name())
	data.setParameters(instrumentManager.parameters())
	data.parameters()["defaultPlot"]=[["delay",variable]]
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

def T1(qubit,delays,data = None,averaging = 20,variable = "p1x",gaussian = True):
	if data == None:
		data = Datacube()
	data.setName("T1 - " + qubit.name())
	data.setParameters(instrumentManager.parameters())
	data.parameters()["defaultPlot"]=[["delay",variable]]
	try:
		for delay in delays:
			qubit.loadRabiPulse(phase = math.pi,readout = qubit.parameters()["timing.readout"],delay = delay,gaussian = gaussian)
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

print "measure.py loaded"