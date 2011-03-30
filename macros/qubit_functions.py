from pyview.lib.datacube import Datacube
import numpy
import math
import random
from config.instruments import *

from pyview.helpers.datamanager import DataManager
dataManager = DataManager()
from pyview.helpers.instrumentsmanager import Manager

instruments = Manager()

def fitRabiFrequency(cube,yVariable = "p1x",xVariable = "duration",withOffset = False):
	result = fitRabi(cube.column(xVariable),cube.column(yVariable),withOffset = withOffset)		
	if result == None:
		return None
	(params,fitfunc,rsquare) = result
	cube.createColumn("%s_fit" % yVariable,fitfunc(params,cube.column(xVariable)))	
	cube.parameters()["rabiParameters"] = params
	cube.parameters()["defaultPlot"].append(["duration","%s_fit" % yVariable])
	return (params,rsquare)

def fitRamseyFrequency(cube,variable = "p1x",f_offset=0.003):
	result = fitRabi(cube.column("duration"),cube.column(variable),withOffset = True,f=f_offset)		
	if result == None:
		return None
	(params,fitfunc,rsquare) = result
	cube.createColumn("%s_fit" % variable,fitfunc(params,cube.column("duration")))	
	cube.parameters()["ramseyParameters"] = params
	if not "defaultPlot" in cube.parameters():
	 cube.parameters()["defaultPlot"] = []
	cube.parameters()["defaultPlot"].append(["duration","%s_fit" % variable])
	return (params,rsquare)

def fitRabi12Frequency(cube,variable = "p1x"):
	result = fitRabi(cube.column("duration"),cube.column(variable),fit12 = True)		
	if result == None:
		return None
	(params,fitfunc,rsquare) = result
	cube.createColumn("%s_fit" % variable,fitfunc(params,cube.column("duration")))	
	cube.parameters()["rabiParameters"] = params
	cube.parameters()["defaultPlot"].append(["duration","%s_fit" % variable])
	return (params,rsquare)

def fitT1Parameters(cube,variable = "p1x"):
  result = fitT1(cube.column("delay"),cube.column(variable))
  if result == None:
    return None
  (params,fitfunc)=result
  cube.createColumn("%s_fit" % variable,fitfunc(params,cube.column("delay")))
  cube.parameters()["T1Parameters"] = params
  cube.parameters()["defaultPlot"].append(["delay","%s_fit" % variable])
  return params
	
def fitT1Parametersprecis(cube,variable = "p1x",highTvalue=0.2): 
	result = fitT1precis(cube.column("delay"),cube.column(variable),highTvalue)		
	if result == None:
		return None
	(params,fitfunc) = result
	cube.createColumn("%s_fit" % variable,fitfunc(params,cube.column("delay")))	
	cube.parameters()["T1Parameters"] = params
	cube.parameters()["defaultPlot"].append(["delay","%s_fit" % variable])
	return params

class FitException(Exception):
  pass

def fitQubitFrequency(cube,variable = "p1x"):
  result = fitLorentzian(cube.column("f"),cube.column(variable))		
  if result == None:
    return None
  (params,fitfunc,rsquare) = result
  cube.createColumn("%s_fit" % variable,fitfunc(params,cube.column("f")))	
  if "defaultPlot" in cube.parameters():
    cube.parameters()["defaultPlot"].append(["f","%s_fit" % variable])
  else:
  	cube.parameters()["defaultPlot"] = ["f","%s_fit" % variable]
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
  return (p1s.tolist(),fitfunc,rsquare)

	
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

	ps = [maxValue-smean,fs[maxI],0.005,min(p1)]
	print ps
	import numpy.linalg
	import scipy
	import scipy.optimize
	p1s = scipy.optimize.fmin(errfunc, ps,args=(fs,p1,fitfunc))
	rsquare = 1.0-numpy.cov(p1-fitfunc(p1s,fs))/numpy.cov(p1)
	return (p1s.tolist(),fitfunc,rsquare)

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
  return (fittedParams.tolist(),fitfunc,rsquare)

#This function fits a lorentzian to a given Qubit spectroscopic curve...
def fitRabi(fs,p1,ps = None,withOffset = False,f=None,t=100,fit12 = False):

  import numpy
  import math
  import scipy
  import scipy.optimize
  import random
  import numpy.linalg
  
  if fit12:
    fitfunc = lambda p, x: p[4]*scipy.exp(-x/p[2])+p[0]*scipy.cos(x/p[1]*math.pi*2.0+p[3])*scipy.exp(-x/p[5])
  else:
    if withOffset:
      fitfunc = lambda p, x: p[3]-p[0]*scipy.cos(-p[4]+x/abs(p[1])*math.pi*2.0)*scipy.exp(-x/p[2])
    else:
      fitfunc = lambda p, x: p[3]-p[0]*scipy.cos(x/abs(p[1])*math.pi*2.0)*scipy.exp(-x/p[2])
  errfunc = lambda p, x, y,ff: numpy.linalg.norm((ff(p,x)-y))

  if ps == None:
    if fit12:
      ps = [(max(p1)-min(p1))/2.0,1,t,(min(p1)+max(p1))/2.0,max(p1),100]
    else:
      if withOffset:
      	ps = [(max(p1)-min(p1))/2.0,1,t,(min(p1)+max(p1))/2.0,0]
      else:
      	ps = [(max(p1)-min(p1))/2.0,1,t,(min(p1)+max(p1))/2.0]

  rsquare = 0.0
  ps[1] = 20
  while rsquare < 0.5 and ps[1] < 30.0:
    ps[1]-=0.5
    p1s = scipy.optimize.fmin(errfunc, ps,args=(fs,p1,fitfunc),maxfun = 1e3,maxiter = 1e3)
    rsquare = 1.0-numpy.cov(p1-fitfunc(p1s,fs))/numpy.cov(p1)
    if p1s[1] < 2:
      rsquare = 0
      #Period is too small (a very small period can give a good fit due to undersampling of the resulting curve...)
  p1s = scipy.optimize.fmin(errfunc, p1s,args=(fs,p1,fitfunc),maxfun = 1e3,maxiter = 1e3)
  rsquare = 1.0-numpy.cov(p1-fitfunc(p1s,fs))/numpy.cov(p1)
  p1s[1] = abs(p1s[1])
  print "Period: %g ns, R2: %g" % (p1s[1],rsquare)
  return (p1s.tolist(),fitfunc,float(rsquare))

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
	return (p1s.tolist(),fitfunc)
	
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
	return (p1s.tolist(),fitfunc)

print "Loaded Qubit functions."