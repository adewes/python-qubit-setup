import numpy
import math
from config.instruments import *
from pyview.lib.datacube import Datacube
from pyview.helpers.datamanager import DataManager
from pyview.helpers.instrumentsmanager import Manager

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