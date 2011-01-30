from pyview.lib.datacube import Datacube
import numpy
import math
import random
from config.instruments import *

from pyview.helpers.datamanager import DataManager
dataManager = DataManager()
from pyview.helpers.instrumentsmanager import Manager

instruments = Manager()
def fitRabiFrequency(cube,variable = "p1x"):
	result = fitRabi(cube.column("duration"),cube.column(variable))		
	if result == None:
		return None
	(params,fitfunc,rsquare) = result
	cube.createColumn("%s_fit" % variable,fitfunc(params,cube.column("duration")))	
	cube.parameters()["rabiParameters"] = params
	return (params,rsquare)

def fitRabi12Frequency(cube,variable = "p1x"):
	result = fitRabi12(cube.column("duration"),cube.column(variable))		
	if result == None:
		return None
	(params,fitfunc,rsquare) = result
	cube.createColumn("%s_fit" % variable,fitfunc(params,cube.column("duration")))	
	cube.parameters()["rabiParameters"] = params
	return (params,rsquare)

def fitT1Parameters(cube,variable = "p1x"):
	result = fitT1(cube.column("delay"),cube.column(variable))		
	if result == None:
		return None
	(params,fitfunc) = result
	cube.createColumn("%s_fit" % variable,fitfunc(params,cube.column("delay")))	
	cube.parameters()["T1Parameters"] = params
	return params
	
def fitT1Parametersprecis(cube,variable = "p1x",highTvalue=0.2): 
	result = fitT1precis(cube.column("delay"),cube.column(variable),highTvalue)		
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
  import random
  
  fitfunc = lambda p, x: p[3]-p[0]*scipy.cos(x/abs(p[1])*math.pi*2.0+p[4])*scipy.exp(-x/p[2])
  errfunc = lambda p, x, y,ff: numpy.linalg.norm((ff(p,x)-y))
  print minP,maxP
  if ps == None:
  	ps = [(maxP-minP)/2.0,period,500.0,(minP+maxP)/2.0,0]
  import numpy.linalg
  rsquare = 0.0
  cnt = 0
  while rsquare < 0.5 and cnt < 10:
    cnt+=1
    ps[1]=period+random.gauss(0,10.0)
    p1s = scipy.optimize.fmin(errfunc, ps,args=(fs,p1,fitfunc))
    rsquare = 1.0-numpy.cov(p1-fitfunc(p1s,fs))/numpy.cov(p1)
  return (p1s,fitfunc,rsquare)

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
  rsquare = 1.0-numpy.cov(p1-fitfunc(p1s,fs))/numpy.cov(p1)
  return (p1s,fitfunc,rsquare)

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
	
def fitT1precis(fs,p1,highTvalue):
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

	fitfunc = lambda p, x: highTvalue+p[0]*scipy.exp(-x/p[1])
	errfunc = lambda p, x, y,ff: ff(p,x)-y

	ps = [numpy.max(p1)-numpy.min(p1),300]
	import numpy.linalg
	print numpy.linalg.norm(errfunc(ps,fs,p1,fitfunc))
	p1s, success = scipy.optimize.leastsq(errfunc, ps,args=(fs,p1,fitfunc))
	return (p1s,fitfunc)

print "Loaded Qubit functions."