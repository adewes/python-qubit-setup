from pyview.lib.datacube import Datacube
import numpy
import math
from config.instruments import *

from pyview.helpers.datamanager import DataManager
dataManager = DataManager()
from pyview.helpers.instrumentsmanager import Manager

instruments = Manager()

def generateRabiWaveform(length = 1000,delay = 0,tm = 10000,namei = "qubit1i",nameq = "qubit1q",compensation = 208,waveformLength = 20000):
	data = numpy.zeros(waveformLength)
	markers = numpy.zeros(waveformLength)
	markers+= 255
	for i in range(min(tm-length-delay,tm-compensation),waveformLength):
		if i>= tm-delay-length and i< tm-delay:
			data[i]=250
		if i >= tm-compensation:
			markers[i]=0
	awg.createRawWaveform(namei,data,markers,"INT")
	dataq = numpy.zeros(waveformLength)
	awg.createRawWaveform(nameq,dataq,markers,"INT")
	return True

def generateRabiIQWaveform(length = 1000,delay = 0,tm = 10000,namei = "qubit1i",nameq = "qubit1q",compensation = 208,waveformLength = 20000,freqOffset = 0.1,phase = 0):
	dataI = numpy.zeros(waveformLength)
	dataQ = numpy.zeros(waveformLength)
	markers = numpy.zeros(waveformLength)
	markers+= 255
	for i in range(min(tm-length-delay,tm-compensation),waveformLength):
		if i>= tm-delay-length and i< tm-delay:
			signalTime = float(i-tm-delay-length)/1.0
			dataI[i]=128+120*cos(i*freqOffset*2.0*math.pi+phase)
			dataQ[i]=128+120*sin(i*freqOffset*2.0*math.pi)
		if i >= tm-compensation:
			markers[i]=0
	awg.createRawWaveform(namei,dataI,markers,"INT")
	awg.createRawWaveform(nameq,dataQ,markers,"INT")
	return True

def generateRamseyWaveform(length = 1000,delay = 0,tm = 10000,name = "qubit1i",compensation = 208):
	data = []
	markers = []
	for i in range(0,20000):
		markers.append(255)
		data.append(0)
		if i >= tm-length*2-delay and i < tm-delay-length:
			data[i]=250
		if i >= tm-length and i < tm:
			data[i]=250
		if i >= tm-compensation:
			markers[i]=0
	data = awg.writeIntData(data,markers)
	awg.createWaveform(name,data,"INT")


def automaticT1(qubit,voltages,spectroRange,jba,variable = "p1x",datacube = None,savename = None,cavity = 6.8,voltageRead = transmon_coil.voltage,voltageWrite = transmon_coil.setVoltage,delay = 0):
  r = []
  r.extend(arange(0,200,2))
  r.extend(arange(200,400,10))
  r.extend(arange(400,2000,50))
  r.extend(arange(2000,5000,500))
  if datacube == None:
  	t1Survey = Datacube()
  else:
  	t1Survey = datacube
  t1Survey.setParameters(instrumentManager.parameters())
  for voltage in voltages:
    voltageWrite(voltage)
#    qubit.initQubit()
    jba.adjustSwitchingLevel(level = 0.2,accuracy = 0.01)
    spectro = Datacube()
    spectro.setName("Spectroscopy, coil = %g" % voltageRead())
    t1Survey.addChild(spectro)
    qubit.setDriveAmplitude(I = 0.1)
    measureSpectroscopy(qubit,spectroRange,spectro,power = -40,ntimes = 20,delay = delay)	
    (result,func,rsquare) = fitLorentzian(spectro.column("f"),spectro.column(variable))
    if result[1] < 3.0 or result[1] > 9.0:
    	continue
    spectro.createColumn("%s_fit" % variable,func(result,spectro.column("f")))
    spectro.setName("Spectroscopy, coil = %g, f0 = %g GHz" % (voltageRead(),result[1]))
    qubit.setDriveAmplitude(I = 0.5)

    t1Survey.set(vcoil = voltageRead(),f0 = result[1])
    spectroRange = arange(result[1]-0.4,result[1]+0.4,0.004)
    print "Resonance at %g" % result[1]
    qubit.setDriveFrequency(result[1])

    #Perform a Rabi experiment:    

    rabiData = Datacube("Rabi, coil = %g" % voltageRead())

    t1Survey.addChild(rabiData)
      
    measureRabi(qubit,arange(0,100,2.0),rabiData,delay = delay)
    params = fitRabiFrequency(rabiData,variable)

    rabiData.setName("Rabi, coil = %g, T(pi)) = %g ns" % (voltageRead(),params[1]/2.0))

    #Load the pi-pulse:

    qubit.loadRabiPulse(length = params[1]/2.0,delay = delay)
    rabiDelay = qubit.readoutDelay()

    #Optimize the readout contrast by measuring the s curves of the JBA in the 0 and 1 state of the qubit:

    sCurves = Datacube("S curves")
    t1Survey.addChild(sCurves)

    (sData,contrast,v0) = measureSCurves(qubit,jba,variable,sCurves)

    t1Survey.set(contrast = contrast,v0 = v0)

    #Perform a T1 experiment.

    t1Data = Datacube()
    t1Data.setParameters(instrumentManager.parameters())
    t1Data.setName("T1 - coil = %g" % voltageRead())
    t1Survey.addChild(t1Data)
    
    for i in r:	
      qubit.setReadoutDelay(rabiDelay+i+2)
      print "t = %f" % i
      acqiris.bifurcationMap(ntimes = 50)
      t1Data.set(t = i,**acqiris.Psw())
      t1Data.commit()
    (res,func) = fitT1(t1Data.column("t"),t1Data.column(variable))
    t1Data.createColumn("%s_fit" % variable,func(res,t1Data.column("t")))
    print "T1 = %g" % res[2]
    t1Data.setName("T1 - coil = %g, T1 = %g ns" % (voltageRead(),res[2]))
    t1Survey.set(T1 = res[2])
    t1Survey.commit()
    t1Survey.savetxt()
  return t1Survey

def fitRabiFrequency(cube,variable = "p1x"):
	result = fitRabi(cube.column("duration"),cube.column(variable))		
	if result == None:
		return None
	(params,fitfunc) = result
	cube.createColumn("%s_fit" % variable,fitfunc(params,cube.column("duration")))	
	cube.parameters()["rabiParameters"] = params
	return params


def fitRabi12Frequency(cube,variable = "p1x"):
	result = fitRabi12(cube.column("duration"),cube.column(variable))		
	if result == None:
		return None
	(params,fitfunc) = result
	cube.createColumn("%s_fit" % variable,fitfunc(params,cube.column("duration")))	
	cube.parameters()["rabiParameters"] = params
	return params

def fitT1Parameters(cube,variable = "p1x"):
	result = fitT1(cube.column("delay"),cube.column(variable))		
	if result == None:
		return None
	(params,fitfunc) = result
	cube.createColumn("%s_fit" % variable,fitfunc(params,cube.column("delay")))	
	cube.parameters()["T1Parameters"] = params
	return params

class FitException(Exception):
  pass

def fitQubitFrequency(cube,variable = "p1x"):
	result = fitLorentzian(cube.column("f"),cube.column(variable))		
	initParams = [0]*7
	initParams[:4] = result[0]
	initParams[4] = 0.5
	initParams[5] = 5.128
	initParams[6] = 0.002
	result = fitDoubleLorentzian(cube.column("f"),cube.column(variable),initParams = initParams)		
	if result == None:
		return None
	(params,fitfunc,rsquare) = result
	cube.createColumn("%s_fit" % variable,fitfunc(params,cube.column("f")))	
	return (params,rsquare)

def findAnticrossing(voltageRead,voltageWrite,searchRange1,searchRange2,cube = None):
	if cube == None:
		cube = Datacube()
	spectro = Datacube()
	spectro.setName("Qubit 1 Spectroscopy")
	cube.addChild(spectro)
	jba.calibrate()
	params = getQubitFrequency(mwg,initialRange,variable,spectro)

#Try to set the qubit frequency to a given value using a specified voltage source...
def setQubitFrequency(mwg,voltageRead,voltageWrite,jba,frequency,initialRange,cube = None,variable = "p1x",maximumVoltage = 2,stepSize = 0.4,probeSize = 0.05,precision = 0.02):
	if cube == None:
		cube = Datacube()
	scanRange = initialRange
	cube.set(voltage = voltageRead())
	spectro = Datacube()
	spectro.setName("Initial Spectroscopy")
	cube.addChild(spectro)
	jba.calibrate()
	params = getQubitFrequency(mwg,initialRange,variable,spectro)
	if params == None:
		return
	f0 = params[1]
	spectro.setName("Initial Spectroscopy,f0 = %g GHz" % f0)
	print "Qubit found at %g GHz" % f0
	voltage = voltageRead()
	voltageWrite(voltage+probeSize)

	spectro = Datacube()
	spectro.setName("Offset Spectroscopy")
	cube.addChild(spectro)
	params2 = getQubitFrequency(mwg,initialRange,variable,spectro)
	if params2 == None:
		return
	f02 = params2[1]
	voltageWrite(voltage)
	slope = (f02-f0)/probeSize
	halfwidth = params[0]+params[3]
	spectro.setName("Offset Spectroscopy, f0 = %g GHz" % f02)
	cnt = 0
	print "Frequency derivative: %g GHz/V" % slope
	print "f0 = %g at voltage = %g" % (f0,voltage)
	while math.fabs(f0-frequency)>precision and cnt < 200:
		cnt+=1
		mwg.setFrequency(f0)
		acqiris.bifurcationMap(ntimes = 50)
		p = acqiris.Psw()[variable]
		diff = math.fabs(f0-frequency)
		if diff > stepSize:
			step = stepSize
		else:
			step = diff
		if f0 < frequency:
			newVoltage = voltage+diff/slope
			f0Estimated = f0+diff
		if f0 > frequency:
			newVoltage = voltage-diff/slope
			f0Estimated = f0-diff
		if math.fabs(newVoltage)>maximumVoltage:
			print "Voltage too high, returning!"
			return None
		scanRange= arange(f0Estimated-0.3,f0Estimated+0.3,0.002)
		voltageWrite(newVoltage)
		spectro = Datacube()
		spectro.setName("Spectroscopy at v = %g" % newVoltage)
		cube.addChild(spectro)
		jba.calibrate()
		paramsLoop = getQubitFrequency(mwg,scanRange,variable,spectro)
		if paramsLoop == None:
			return
		slope = (paramsLoop[1]-f0)/(newVoltage-voltage)
		voltage = newVoltage
		print "Frequency derivative: %g GHz/V" % slope
		f0 = paramsLoop[1]
		cube.set(voltage = newVoltage,f0 = f0)
		cube.commit()
		spectro.setName("Spectroscopy at v = %g, f0 = %g GHz" % (newVoltage,f0))
		print "f0 = %g at voltage = %g" % (f0,voltage)

#This function fits a lorentzian to a given Qubit spectroscopic curve...
def fitGaussian(fs,p1,ps = None):
  maxi = 0
  maxI = 0
  nAverage = 5
  for i in range(nAverage,len(fs)-nAverage):
  	v = 0
  	for j in range(-nAverage,nAverage+1):
  		v+=p1[i+j]
  	v/=nAverage*2+1
  	if (i == 0 or v>max):
  		maxi = v
  		maxI = i
  import numpy
  smean = numpy.mean(p1)
  
  fitfunc = lambda p, x: p[3]+p[0]*exp(-pow((x-p[1])/p[2],2.0))
  errfunc = lambda p, x, y,ff: numpy.linalg.norm(ff(p,x)-y)
  if ps == None:
    ps = [maxi-smean,fs[maxI],2.0,smean]
  import numpy.linalg
  
  import scipy
  import scipy.optimize
  print errfunc(ps,fs,p1,fitfunc)
  p1s = scipy.optimize.fmin(errfunc, ps,args=(fs,p1,fitfunc))
  rsquare = 1.0-numpy.cov(p1-fitfunc(p1s,fs))/numpy.cov(p1)
  return (list(p1s),fitfunc,rsquare)

	
#This function fits a lorentzian to a given Qubit spectroscopic curve...
def fitLorentzian(fs,p1):
	maxValue = 0
	maxI = 0
	nAverage = 2
	for i in range(nAverage,len(fs)-nAverage):
		v = 0
		for j in range(-nAverage,nAverage+1):
			v+=p1[i+j]
		v/=nAverage*2+1
		if (i == 0 or v>maxValue):
			maxValue = v
			maxI = i
	import numpy
	smean = numpy.mean(p1)

	fitfunc = lambda p, x: p[3]+p[0]/(1.0+pow((x-p[1])/p[2],2.0))
	errfunc = lambda p, x, y,ff: numpy.linalg.norm(ff(p,x)-y)

	ps = [maxValue-smean,fs[maxI],0.005,smean]
	print ps
	import numpy.linalg
	import scipy
	import scipy.optimize
	p1s = scipy.optimize.fmin(errfunc, ps,args=(fs,p1,fitfunc))
	rsquare = 1.0-numpy.cov(p1-fitfunc(p1s,fs))/numpy.cov(p1)
	return (list(p1s),fitfunc,rsquare)

#This function fits a lorentzian to a given Qubit spectroscopic curve...
def fitDoubleLorentzian(fs,p1,initParams,cavity = 6.85):
  import numpy.linalg
  import scipy
  import scipy.optimize
  
  meanValue = mean(p1)
  minValue = min(p1)
  maxValue = max(p1)
  
  fitfunc = lambda p, x: p[3]+p[0]/(1.0+pow((x-p[1])/p[2],2.0))+p[4]/(1.0+pow((x-p[5])/p[6],2.0))
  errfunc = lambda p, x, y,ff: numpy.linalg.norm(ff(p,x)-y)
  
  fittedParams = scipy.optimize.fmin(errfunc, initParams,args=(fs,p1,fitfunc))
  rsquare = 1.0-numpy.cov(p1-fitfunc(fittedParams,fs))/numpy.cov(p1)
  return (list(fittedParams),fitfunc,rsquare)

#This function fits a lorentzian to a given Qubit spectroscopic curve...
def fitRabi(fs,p1,ps = None):
  maxP = 0
  minP = 0
  maxI = 0
  avg = mean(p1)
  integral = 0
  lastIntegralValue = None
  signChanges = 0
  period = None
  for i in range(1,len(fs)-1):
    v = (p1[i]+p1[i+1]+p1[i-1])/3.0
    integral+=v-avg
    if i == 1 or v < minP:
      minP = v
    if i == 1 or v>maxP:
    	maxP = v
    	maxI = i
    if lastIntegralValue != None and sign(integral) != sign(lastIntegralValue) and period == None:
      signChanges+=1
    lastIntegralValue = integral
  if period == None:
    if signChanges == 0:
      period = fs[i]-fs[0]
    else:
      period = (fs[i]-fs[0])/float(signChanges)*3.0/2.0
  import numpy
  smean = numpy.mean(p1)
  
  import math
  import scipy
  import scipy.optimize
  
  fitfunc = lambda p, x: p[3]-p[0]*scipy.cos(x/p[1]*math.pi*2.0+p[4])*scipy.exp(-x/p[2])
  errfunc = lambda p, x, y,ff: numpy.linalg.norm((ff(p,x)-y))
  print minP,maxP
  if ps == None:
  	ps = [(maxP-minP)/2.0,period,500.0,(minP+maxP)/2.0,0]
  import numpy.linalg
  p1s = scipy.optimize.fmin(errfunc, ps,args=(fs,p1,fitfunc))
  p1s = scipy.optimize.fmin(errfunc, p1s,args=(fs,p1,fitfunc))
  p1s = scipy.optimize.fmin(errfunc, p1s,args=(fs,p1,fitfunc))
#  p1s = ps
  return (p1s,fitfunc)

#This funct2ion fits a lorentzian to a given Qubit spectroscopic curve...
def fitRabi12(fs,p1,ps = None):
  maxP = 0
  minP = 0
  maxI = 0
  avg = mean(p1)
  integral = 0
  lastIntegralValue = None
  signChanges = 0
  period = 18
  for i in range(1,len(fs)-1):
    v = (p1[i]+p1[i+1]+p1[i-1])/3.0
    integral+=v-avg
    if i == 1 or v < minP:
      minP = v
    if i == 1 or v>maxP:
    	maxP = v
    	maxI = i
    if lastIntegralValue != None and sign(integral) != sign(lastIntegralValue) and period == None:
      signChanges+=1
    lastIntegralValue = integral
  if period == None:
    if signChanges == 0:
      period = fs[i]-fs[0]
    else:
      period = (fs[i]-fs[0])/float(signChanges)*3.0/2.0
  import numpy
  smean = numpy.mean(p1)
  
  import math
  import scipy
  import scipy.optimize
  
  fitfunc = lambda p, x: p[3]*scipy.exp(-x/p[2])-p[0]*scipy.cos(x/p[1]*math.pi*2.0+p[4])
  errfunc = lambda p, x, y,ff: numpy.linalg.norm((ff(p,x)-y))
  print minP,maxP
  if ps == None:
  	ps = [(maxP-minP)/2.0,period,500.0,(minP+maxP)/2.0,0]
  import numpy.linalg
  p1s = scipy.optimize.fmin(errfunc, ps,args=(fs,p1,fitfunc))
  p1s = scipy.optimize.fmin(errfunc, p1s,args=(fs,p1,fitfunc))
  p1s = scipy.optimize.fmin(errfunc, p1s,args=(fs,p1,fitfunc))
#  p1s = ps
  return (p1s,fitfunc)

def fitT1(fs,p1):
	max = 0
	maxI = 0
	for i in range(1,len(fs)-1):
		v = (p1[i]+p1[i+1]+p1[i-1])/3.0
		if i == 0 or v>max:
			max = v
			maxI = i
	import numpy
	smean = numpy.mean(p1)

	import math
	import scipy
	import scipy.optimize

	fitfunc = lambda p, x: p[0]+p[1]*scipy.exp(-x/p[2])
	errfunc = lambda p, x, y,ff: ff(p,x)-y

	ps = [numpy.min(p1),numpy.max(p1)-numpy.min(p1),100]
	import numpy.linalg
	print numpy.linalg.norm(errfunc(ps,fs,p1,fitfunc))
	p1s, success = scipy.optimize.leastsq(errfunc, ps,args=(fs,p1,fitfunc))
	return (p1s,fitfunc)

print "Loaded Qubit functions."