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

instruments = Manager()

def ramsey(qubit,durations,data = None,variable ="p1x",callback = None,angle = 0,phase = math.pi/2.0,averaging = 20,amplitude = 0,f_offset = 0,correctFrequency = False,saveData = True,transition = 01,use12Pulse = False):
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
  if 02 == transition:
    f_offset/=2.0
  if transition == 12 or use12Pulse:
    f_carrier = qubit.parameters()["frequencies.f01"]+f_sb
    f_sb_12 = -(qubit.parameters()["frequencies.f12"]-f_carrier)
    f_sb_12 = qubit.parameters()["pulses.xy.f_sb12"]
    t_pi_12 = qubit.parameters()["pulses.xy.t_pi12"]
  try:
    for duration in durations:
      seq = PulseSequence()
      l = len(qubit.generateRabiPulse(phase = phase))
      zLen = len(qubit.generateZPulse(length = duration))
      if amplitude != 0:
        zSeq = PulseSequence()
        zSeq.addPulse(baseForm)
        zSeq.setPosition(0)
        zSeq.addPulse(qubit.generateZPulse(length = duration,delay = qubit.parameters()["timing.readout"]-zLen-l)*amplitude)
        qubit.loadFluxlineWaveform(zSeq.getWaveform(),compensateResponse = False)

      if transition == 01 or 02 == transition:
        seq.addPulse(qubit.generateRabiPulse(angle = angle,phase = phase,f_sb = f_sb-f_offset,sidebandDelay = seq.position()))
        seq.addWait(zLen)
        seq.addPulse(qubit.generateRabiPulse(angle = angle,phase = phase,f_sb = f_sb-f_offset,sidebandDelay = seq.position()))
      elif transition == 12:
        seq.addPulse(qubit.generateRabiPulse(angle = angle,phase = math.pi,f_sb = f_sb,sidebandDelay = seq.position()))
        seq.addPulse(qubit.generateRabiPulse(angle = angle,length = t_pi_12/2.0*phase/math.pi*2.0,f_sb = f_sb_12-f_offset,sidebandDelay = seq.position()))
        seq.addWait(zLen)
        seq.addPulse(qubit.generateRabiPulse(angle = angle,length = t_pi_12/2.0*phase/math.pi*2.0,f_sb = f_sb_12-f_offset,sidebandDelay = seq.position()))
        seq.addPulse(qubit.generateRabiPulse(angle = angle,phase = math.pi,f_sb = f_sb,sidebandDelay = seq.position()))

      if use12Pulse:
        seq.addPulse(qubit.generateRabiPulse(angle = angle,phase = t_pi_12,f_sb = f_sb_12,sidebandDelay = seq.position()))
        
      qubit.loadWaveform(seq.getWaveform(endAt = qubit.parameters()["timing.readout"]),readout = qubit.parameters()["timing.readout"])
      if callback != None:
        callback(duration)
      acqiris.bifurcationMap(ntimes = averaging)
      data.set(duration = duration)
      data.set(**acqiris.Psw())
      data.commit()
  except:
    traceback.print_exc()
  finally:
    if amplitude != 0:
      qubit.popState()
    (params,rsquare) = fitRamseyFrequency(data,variable,f_offset=f_offset)
    if rsquare > 0.5:
      qubit.parameters()["pulses.ramsey.t_pi"] = params[1]/2.0
      data.setName(data.name()+" - f_r = %g MHz - T_2 = %g ns" % ((1.0/params[1])*1000,params[2]))
      data.parameters()["ramseyFit"] = params
      f_correct = 1.0/params[1]-abs(f_offset)
      if correctFrequency and amplitude == 0 and f_correct < 0.05:
        print "Correcting qubit frequency by %g MHz" % (f_correct*1000)
        if 01 == transition or 02 == transition:
          qubit.parameters()["frequencies.f01"]-=f_correct
        elif 12 == transition:
          qubit.parameters()["frequencies.f12"]-=f_correct
    else:
      print "Ramsey fit is not good, resetting parameters..."
      qubit.parameters()["pulses.ramsey.t_pi"] = None
    if saveData:
      data.savetxt()
  return data


def rabi(qubit,durations,data = None,variable ="p1x",f_sb = -0.1,amplitude = 1.0,averaging = 20,delay = 0,use12Pulse = False,callback = None,angle = 0,compositePulse = False,gaussian = True,flank = 3,saveData = True):
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
        seq.addWait(0)
        seq.addPulse(qubit.generateRabiPulse(angle = angle,length = duration/2.0,f_sb = f_sb,sidebandDelay = seq.position(),gaussian = gaussian))
        qubit.loadWaveform(seq.getWaveform(endAt = qubit.parameters()["timing.readout"]-delay),readout = qubit.parameters()["timing.readout"])
      else:
        seq = PulseSequence()
        seq.addPulse(qubit.generateRabiPulse(angle = angle,length = duration,f_sb = f_sb,sidebandDelay = seq.position(),gaussian = gaussian))
        if use12Pulse:
          f_carrier = qubit.parameters()["frequencies.f01"]+f_sb
          f_sb_12 = -(qubit.parameters()["frequencies.f12"]-f_carrier)
          t_pi_12 = qubit.parameters()["pulses.xy.t_pi12"]
          seq.addPulse(qubit.generateRabiPulse(angle = angle,length = t_pi_12,f_sb = f_sb_12,sidebandDelay = seq.position()))
        qubit.loadWaveform(seq.getWaveform())#endAt = qubit.parameters()["timing.readout"]-delay),readout = qubit.parameters()["timing.readout"])
        
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
    if saveData:
      data.savetxt()
  return data


def rabi12(qubit,durations,data = None,variable ="p1x",averaging = 20,delay = 0,callback = None,saveData = True):

  from instruments.qubit import PulseSequence

  if data == None:
    data = Datacube()
  
  data.setParameters(instrumentManager.parameters())
  data.setName("Rabi Sequence 12 - %s" % qubit.name())

  amplitude = qubit.parameters()["pulses.xy.drive_amplitude"]
  f_sb = qubit.parameters()["pulses.xy.f_sb"]
  f_carrier = qubit.parameters()["frequencies.f01"]+f_sb
  f_sb_12 = -(qubit.parameters()["frequencies.f12"]-f_carrier)
  
  print f_sb_12

  qubit.setDriveFrequency(f_carrier)
  qubit.setDriveAmplitude(I = amplitude,Q = amplitude)

  failed = False
  data.parameters()["defaultPlot"] = [["duration",variable],["duration","%s_fit" % variable]]
  try:
    for duration in durations:
      seq = PulseSequence()
      seq.addPulse(qubit.generateRabiPulse(phase = math.pi,f_sb = f_sb))
      seq.addPulse(qubit.generateRabiPulse(length = duration,f_sb = f_sb_12))
      seq.addPulse(qubit.generateRabiPulse(phase = math.pi,f_sb = f_sb))
      qubit.loadWaveform(seq.getWaveform(endAt = qubit.parameters()["timing.readout"]),readout = qubit.parameters()["timing.readout"])
      if callback != None:
        callback(duration)
      acqiris.bifurcationMap(ntimes = averaging)
      data.set(duration = duration)
      data.set(**acqiris.Psw())
      data.commit()
  except StopThread:
    pass
  except:
    print "Failed!"
    failed = True
    import traceback
    traceback.print_exc()
  finally:
    if len(data) == 0:
      return
    if failed:
      raise
    (params,rsquare) = fitRabi12Frequency(data,variable)
    qubit.parameters()["pulses.xy.t_pi12"] = params[1]/2.0
    qubit.parameters()["pulses.xy.drive_amplitude12"] = amplitude
    qubit.parameters()["pulses.xy.f_sb12"] = f_sb_12
    data.parameters()["rabiFit12"] = params
    if saveData:
      data.savetxt()
  return data

def measureSpectroscopy(qubit,frequencies,data = None,ntimes = 20,amplitude = 1,measureAtReadout = False,delay = 0,f_sb = 0,delayAtReadout = 1500,pulseLength = 500,gaussian=False):
  if data == None:
    data = Datacube()
  if measureAtReadout:
    qubit.loadRabiPulse(length = pulseLength,f_sb = f_sb,delay = delay,gaussian=gaussian)
  else:
    qubit.loadRabiPulse(length = pulseLength,f_sb = f_sb,delay = delay,gaussian=gaussian)
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

def spectroscopy(qubit,frequencies,data = None,ntimes = 20,amplitude = 0.1,variable = "p1x",measureAtReadout = False,delay = 0,f_sb = 0,measure20 = True,fitFrequency = True,factor20 = 10.0,delayAtReadout = 1500,saveData = True,pulseLength = 500,gaussian=True):
  f_drive = qubit.driveFrequency()
  try:
    if data == None:
      data = Datacube()
    if measureAtReadout:
      data.setName("Spectroscopy at Readout - %s" % qubit.name())
    else:
      data.setName("Spectroscopy - %s" % qubit.name())
    data.parameters()["defaultPlot"]=[["f",variable]]
    measureSpectroscopy(qubit = qubit,frequencies = frequencies,data = data,amplitude = amplitude,measureAtReadout = measureAtReadout,delay = delay,f_sb = f_sb,delayAtReadout = delayAtReadout,pulseLength = pulseLength,gaussian=gaussian)
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
      frequencies02 = arange(params[1]-0.18,params[1]-0.05,0.001)
      data02.parameters()["defaultPlot"]=[["f",variable]]
      measureSpectroscopy(qubit = qubit,frequencies = frequencies02,data = data02,amplitude = amplitude*factor20,measureAtReadout = measureAtReadout,delay = delay,f_sb = f_sb,delayAtReadout = delayAtReadout,pulseLength = pulseLength,gaussian=gaussian)
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
    if saveData:
      data.savetxt()
    return data
  finally:
    try:
      qubit.setDriveFrequency(f_drive)
    except:
      pass

def parameterSurvey(qubit,jba,values,generator,data = None,ntimes = 20,durations = arange(0,50,2),freqs = list(arange(5.0,6.5,0.002))+list(arange(7.0,8.3,0.002)),autoRange = False,spectroAmp = 0.1,rabiAmp = 1.0,f_sb = -0.1,variable = "p1x",fastMeasure=False,use12Pulse=False):
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
    
    spectroscopy(qubit = qubit,frequencies = freqs,variable = variable,data = spectroData,ntimes = 20,amplitude = spectroAmp,measureAtReadout = False,measure20=use12Pulse)
    if qubit.parameters()["frequencies.f01"] == None:
    	data.commit()
    	continue
    
    if autoRange:
      freqs = list(arange(qubit.parameters()["frequencies.f01"]-0.2,qubit.parameters()["frequencies.f01"]+0.2,0.002))
    data.set(f01 = qubit.parameters()["frequencies.f01"],f02 = qubit.parameters()["frequencies.f02"])
    
    #Measure a Rabi oscillation
    
    rabiData = Datacube()
    vData.addChild(rabiData)

    f01 = qubit1.parameters()["frequencies.f01"]
    f_sb = -0.1-(f01-round(f01,2))
    qubit.parameters()["pulses.xy.f_sb"]=float(f_sb)

    rabi(qubit = qubit,durations = rabiDurations,variable = variable,data = rabiData,amplitude = rabiAmp,f_sb = f_sb,averaging = 20)
    if qubit.parameters()["pulses.xy.t_pi"] == None:
    	data.commit()
    	continue
    
    data.set(t_pi = qubit.parameters()["pulses.xy.t_pi"])


      
    if use12Pulse:
      #Measure a Rabi 12 oscillation
      
      qubit.parameters()["pulses.xy.drive_amplitude"]=rabiAmp
      rabi12Data = Datacube()
      vData.addChild(rabi12Data)

      rabi12(qubit = qubit,durations = rabiDurations,variable = variable,data = rabi12Data,averaging = 20)
      if qubit.parameters()["pulses.xy.t_pi12"] == None:
      	data.commit()
      	continue
      
      data.set(t_pi12 = qubit.parameters()["pulses.xy.t_pi12"])
    
    #Measure S curves
    sData = Datacube()    
    vData.addChild(sData)
    sCurves(qubit = qubit,jba = jba,variable = variable,data = sData,optimize = "v10",s2=use12Pulse)
    data.set(contrast10 = qubit.parameters()["readout.contrast10"])
    
    if not fastMeasure:    
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
  

def phaseError(data,qubit,amplifyingPulses = 0, averaging = 40,phases = list(arange(0,math.pi*2.0,math.pi/10.0)),hot = False,flank = 5,delay = 0,updateNormalization = False,saveData = True):
  
  from instruments.qubit import PulseSequence
  
  data.setName("XPhi Sequence - %s" % qubit.name())
  data.setParameters(instrumentManager.parameters())
  data.parameters()["defaultPlot"] = [("phi","psw_normalized"),("phi","psw_normalized_fit")]
  
  if "pulses.xy.useDrag" in qubit.parameters() and qubit.parameters()["pulses.xy.useDrag"]:
  	data.setName(data.name()+" - DRAG")
  
  f_sb = qubit.parameters()["pulses.xy.f_sb"]
  qubit.setDriveFrequency(qubit.parameters()["frequencies.f01"]+f_sb)
  qubit.setDriveAmplitude(I = qubit.parameters()["pulses.xy.drive_amplitude"],Q = qubit.parameters()["pulses.xy.drive_amplitude"])
  
  data.setName(data.name()+" - %d amplifying pulses" % amplifyingPulses)
  failed = False
  try:
  	for phi in phases:
  		seq = PulseSequence()
  		seq.addPulse(qubit.generateRabiPulse(phase = math.pi/2.0,angle = 0.0,f_sb = f_sb,sidebandDelay = seq.position()))
  		for i in range(0,amplifyingPulses):
  			seq.addWait(10)
  			seq.addPulse(qubit.generateRabiPulse(phase = math.pi/2.0,angle = 0.0,f_sb = f_sb,sidebandDelay = seq.position()))	
  			seq.addWait(10)
  			seq.addPulse(qubit.generateRabiPulse(phase = math.pi/2.0,angle = math.pi,f_sb = f_sb,sidebandDelay = seq.position()))
  		seq.addWait(delay)
  		seq.addPulse(qubit.generateRabiPulse(phase = math.pi/2.0,angle = phi,f_sb = f_sb,sidebandDelay = seq.position()))
  		waveform = seq.getWaveform(endAt = qubit.parameters()["timing.readout"])
  		if hot:
  			figure("waveform")
  			cla()
  			plot(real(waveform[-seq.position():]))
  			plot(imag(waveform[-seq.position():]))
  		qubit.loadWaveform(waveform,readout = qubit.parameters()["timing.readout"])
  		data.set(phi = phi*180.0/math.pi)
  		data.set(psw_normalized = qubit.Psw(normalize = True,ntimes = averaging))
  		data.set(**acqiris.Psw())
  		data.commit()
  except StopThread:
  	pass
  except:
  	failed = True
  finally:
    if failed:
    	raise
    fitfunc = lambda p, x: p[2]+p[0]*(1.0+scipy.cos(-p[1]+x/180.0*math.pi))/2.0
    errfunc = lambda p, x, y,ff: numpy.linalg.norm((ff(p,x)-y))		  
    ps = [max(data.column("psw_normalized"))-min(data.column("psw_normalized")),mean(data.column("psw_normalized")),0]
    p1 = data.column("psw_normalized")
    p1s = scipy.optimize.fmin(errfunc, ps,args=(data.column("phi"),p1,fitfunc))
    rsquare = 1.0-numpy.cov(p1-fitfunc(p1s,data.column("phi")))/numpy.cov(p1)
    data.createColumn("psw_normalized_fit",fitfunc(p1s,data.column("phi")))	
    data.setDescription(data.description()+("\nPhase lag:%g deg" % (p1s[1]*180.0/math.pi))) 
    data.setName(data.name() + (" - phi = %g deg" % (p1s[1]*180.0/math.pi)))
    if saveData:
      data.savetxt()
    return (p1s[1]*180.0/math.pi)
	
def sCurves(jba,qubit = None,variable = "p1x",data = None,ntimes = 20,s2=False,optimize = "v10",step = 0.01,measureErrors = False,saveData = True,voltageBounds = None,**kwargs):
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
    data.setParameters(instrumentManager.parameters())
    v0 = jba.voltage()
    if data == None:
    	sData = Datacube()
    else:
    	sData = data
    if sData.name() == "datacube":
      if not qubit == None:
        sData.setName("S curves - %s" % qubit.name())
        s0 = Datacube("S0")
        s1 = Datacube("S1")
        sData.addChild(s0)
        sData.addChild(s1)
        s0.parameters()["defaultPlot"]=[["v",variable]]
        s1.parameters()["defaultPlot"]=[["v",variable]]
        s1.parameters()["defaultPlot"].append(["v","contrast10"])
      else:
        sData.setName("S curve - %s" % jba.name())
        sData.parameters()["defaultPlot"]=[["v",variable]]

    error=False 
    
    if not qubit == None:
        
      qubit.turnOnDrive()
      qubit.loadRabiPulse(length = 0)
    
    if voltageBounds == None:
      (vmin,vmax) = getVoltageBounds(v0,jba,variable,ntimes)
    else:
      (vmin,vmax) = voltageBound
      
    print vmin,vmax
    
    if qubit == None:
      measureSingleS(voltages = arange(vmin,vmax,step),data = sData,jba = jba,ntimes = ntimes)
      return
    else:
      measureSingleS(voltages = arange(vmin,vmax,step),data = s0,jba = jba,ntimes = ntimes)

    qubit.loadRabiPulse(phase = math.pi,**kwargs)
    measureSingleS(voltages = arange(vmin,vmax,step),data = s1,jba = jba,ntimes = ntimes)
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
        s1.parameters()["defaultPlot"].extend([["v","contrast20"],["v","contrast21"]])
        qubit.parameters()["readout.v20"] = float(s1.column("v")[argmax(s1.column("contrast20"))])
        qubit.parameters()["readout.v21"] = float(s1.column("v")[argmax(s1.column("contrast21"))])
        qubit.parameters()["readout.contrast20"] = float(s1.column("contrast20")[argmax(s1.column("contrast20"))])
        qubit.parameters()["readout.contrast21"] = float(s1.column("contrast21")[argmax(s1.column("contrast21"))])
        data.setName(data.name()+" - v20 = %g" % qubit.parameters()["readout.contrast20"])
        data.setName(data.name()+" - v21 = %g" % qubit.parameters()["readout.contrast21"])
      except:
        failed12 = True
        raise
    else:
      failed12=True    
    s1.createColumn("contrast10",s1.column(variable)-s0.column(variable))
    s1.parameters()["defaultPlot"].append(["v",variable])
    qubit.parameters()["readout.v10"] = float(s1.column("v")[argmax(s1.column("contrast10"))])
    qubit.parameters()["readout.contrast10"] = float(s1.column("contrast10")[argmax(s1.column("contrast10"))])
    data.setName(data.name()+" - v10 = %g" % qubit.parameters()["readout.contrast10"])
    if optimize == "v21" or optimize == 'v20':
      qubit.parameters()["readout.use12"] = True
    else:
      qubit.parameters()["readout.use12"] = False
    
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
      
        qubit.turnOnDrive()
        qubit.loadRabiPulse(phase=0)
        acqiris.bifurcationMap(ntimes = 1000)
        qubit.parameters()["readout.p00"] = float(1.0-acqiris.Psw()[variable])
 
        if optimize == 'v10':   
          qubit.loadRabiPulse(phase=math.pi)
        else:
          loadPi012Pulse(qubit)
        
        acqiris.bifurcationMap(ntimes = 1000)
        qubit.parameters()["readout.p11"] = float(acqiris.Psw()[variable])
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
  except StopThread:
    pass
  
def loadPi012Pulse(qubit,phase = math.pi,delay=0):
  from instruments.qubit import PulseSequence
  
  seq = PulseSequence()
  len1 = len(qubit.generateRabiPulse(length = qubit.parameters()["pulses.xy.t_pi12"]))
  len2 = len(qubit.generateRabiPulse(phase = phase))
  seq.addPulse(qubit.generateRabiPulse(phase = phase,f_sb = qubit.parameters()["pulses.xy.f_sb"],delay = qubit.parameters()["timing.readout"]-len2-len1-delay),position = 0)
  seq.addPulse(qubit.generateRabiPulse(length = qubit.parameters()["pulses.xy.t_pi12"],f_sb = qubit.parameters()["pulses.xy.f_sb12"],delay = qubit.parameters()["timing.readout"]-len1-delay),position = 0)
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

def T1(qubit,delays,data = None,averaging = 20,variable = "p1x",gaussian = True,saveData = True,state=1):
  if data == None:
  	data = Datacube()
  data.setName("T1 - " + qubit.name()+" - state "+str(state))
  data.setParameters(instrumentManager.parameters())
  data.parameters()["defaultPlot"]=[["delay",variable]]
  try:
			for delay in delays:
				if state==2:
					loadPi012Pulse(qubit,delay=delay)
				else:
					qubit.loadRabiPulse(phase = math.pi,delay = delay,gaussian = gaussian)
				acqiris.bifurcationMap(ntimes = averaging)
				data.set(delay = delay)
				data.set(**acqiris.Psw())
				data.commit()
  finally:
  	params = fitT1Parameters(data,variable)
  	data.setName(data.name()+" - T1 = %g ns " % params[2])
  	qubit.parameters()["relaxation.t1_%d" % state] = params[2]
  	if saveData:
  		data.savetxt()
  return data

def measureDetectorMatrix(averaging=80):
  states=[[0,0],[math.pi,0],[0,math.pi],[math.pi,math.pi]]
  R=matrix(zeros((4,4)))
  i = 0
  for state in states:
      
      if qubit1.parameters()["readout.use12"]:
        loadPi012Pulse(qubit1,phase = state[0])
      else:
        qubit1.loadRabiPulse(phase = state[0])
      if qubit2.parameters()["readout.use12"]:
        loadPi012Pulse(qubit2,phase = state[1])
      else:
        qubit2.loadRabiPulse(phase = state[1])
        
      acqiris.bifurcationMap(ntimes = averaging)
      R[i,:]=acqiris.Psw()["p00"],acqiris.Psw()["p10"],acqiris.Psw()["p01"],acqiris.Psw()["p11"]    
      i+=1
  R=R.transpose()
  qubit1.parameters()["detectorFunction"]=R.tolist() 
  qubit2.parameters()["detectorFunction"]=R.tolist()    
  return R


print "measure.py loaded"