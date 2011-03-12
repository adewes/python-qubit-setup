##This script fits a measured set of s curves by using a reference curve (ideally measured with the qubit detuned far from the cavity).
##Load the s curve data
var = "p1x"
qubit = qubit1
fitS02 = False
sReference = sReferenceQubit1
sData = sDataQubit1
if fitS02:
	sData2 = sData2Qubit1
##Qubit 2
var = "px1"
qubit = qubit2
sReference = sReferenceQubit2
sData = sDataQubit2
fitS02 = False
if fitS02:
	sData2 = sData2Qubit2
##Plot the data
figure("s curves")
cla()
xmin = 2
xmax = -2

xRef = sReference.allChildren()[0].column("v")[xmin:xmax]
yRef = sReference.allChildren()[0].column(var)[xmin:xmax]

xOn = sData.allChildren()[1].column("v")[xmin:xmax]
yOn = sData.allChildren()[1].column(var)[xmin:xmax]
contrast = sData.allChildren()[1].column("contrast10")[xmin:xmax]

if fitS02:
	xOn2 = sData2.allChildren()[1].column("v")[xmin:xmax]
	yOff2 = sData2.allChildren()[0].column(var)[xmin:xmax]
	yOn2 = sData2.allChildren()[1].column(var)[xmin:xmax]
	contrast2 = sData2.allChildren()[1].column("contrast20")[xmin:xmax]
	
xOff = sData.allChildren()[0].column("v")[xmin:xmax]
yOff = sData.allChildren()[0].column(var)[xmin:xmax]

plot(xOff,yOff)
plot(xOn,yOn)
if fitS02:
	plot(xOn2,yOn2)
plot(xRef,yRef)
##Fit the contrast
import scipy
import scipy.optimize
import numpy.linalg

def errfuncGauss(p,xOn,contrast):
	return numpy.linalg.norm(contrast-p[0]*(1-pow((xOn-p[1])/p[2],2.0)) )

ps = [max(contrast),xOn[argmax(contrast)],0.1]
xmax = argmax(contrast)
cp = scipy.optimize.fmin(errfuncGauss,ps,args=(xOn[xmax-10:xmax+10],contrast[xmax-10:xmax+10]),xtol = 1e-8,disp = 1,maxiter = 1e5,maxfun = 1e5)
fittedContrast = cp[0]*(1-pow((xOn-cp[1])/cp[2],2.0))

if fitS02:
	ps2 = [max(contrast2),xOn2[argmax(contrast2)],0.1]
	xmax2 = argmax(contrast2)
	cp2 = scipy.optimize.fmin(errfuncGauss,ps2,args=(xOn2[xmax2-10:xmax2+10],contrast2[xmax2-10:xmax2+10]),xtol = 1e-8,disp = 1,maxiter = 1e5,maxfun = 1e5)
	fittedContrast2 = cp2[0]*(1-pow((xOn2-cp2[1])/cp2[2],2.0))

##Fit the s curve parameters

xValues = [-100]
xValues.extend(xRef)
xValues.append(100)

yValues = [1]
yValues.extend(yRef)
yValues.append(0)

import scipy.interpolate

refInterpolation = scipy.interpolate.interp1d(xValues,yValues)

def refCurve(x):
	global refInterpolation
	return refInterpolation(x)

def errfuncDouble(p,xOff,yOff,xOn,yOn,refCurve):

	p1_off = p[0]
	p0_on = p[1]
	shift_off = p[2]
	shift_on = p[3]

	yOffFit = (1-p1_off)*refCurve(xOff-shift_off)+p1_off*refCurve(xOff-shift_on)
	yOnFit = p0_on*refCurve(xOn-shift_off)+(1-p0_on)*refCurve(xOn-shift_on)

	return pow(numpy.linalg.norm(yOffFit-yOff)+numpy.linalg.norm(yOnFit-yOn),2)

def errfuncTriple(p,xOn2,yOn2,refCurve,pDouble):

	p1_off = pDouble[0]
	p0_on = pDouble[1]
	shift_off = pDouble[2]
	shift_on = pDouble[3]

	p0_on_2 = p[0]
	shift_on_2 = p[1]
	p0_on = p[2]

	yOnFit = (-(1-p0_on)*p0_on_2+p0_on_2)*refCurve(xOn2-shift_off)+p0_on_2*(1-p0_on)*refCurve(xOn2-shift_on)+(1-p0_on_2)*refCurve(xOn2-shift_on_2)

	return pow(numpy.linalg.norm(yOnFit-yOn2),2)

import random

ps = [0.1,0.1,-0.15,-0.1]
extraArgs = (xOff,yOff,xOn,yOn,refCurve)
p1s = scipy.optimize.fmin(errfuncDouble,ps,args=extraArgs,xtol = 1e-10,disp = 1,maxiter = 1e5,maxfun = 1e5)

print p1s

if fitS02:
	ps2 = [0.1,-0.15,p1s[1]]
	p1s2 = scipy.optimize.fmin(errfuncTriple,ps2,args=(xOn2,yOn2,refCurve,p1s),xtol = 1e-10,disp = 1,maxiter = 1e5,maxfun = 1e5)
	print p1s2


##Plot the results...

p1_off = p1s[0]
p0_on = p1s[1]
shift_off = p1s[2]
shift_on = p1s[3]

if fitS02:
	p0_on_2 = p1s2[0]
	shift_on_2 = p1s2[1]


cla()

plot(xOff,yOff)
plot(xOn,yOn)
if fitS02:
	plot(xOn2,yOn2)
plot(xRef,yRef)


plot(xOff,(1-p1_off)*refCurve(xOff-shift_off)+p1_off*refCurve(xOff-shift_on),'--')

yOnFit = lambda x : p0_on*refCurve(x-shift_off)+(1-p0_on)*refCurve(x-shift_on)

plot(xOn,yOnFit(xOn),'--')

if fitS02:
	p0_on_12 = p1s2[2]
	yOn2Fit = lambda x : (-(1-p0_on_12)*p0_on_2+p0_on_2)*refCurve(x-shift_off)+p0_on_2*(1-p0_on_12)*refCurve(x-shift_on)+(1-p0_on_2)*refCurve(x-shift_on_2)
	plot(xOn2,yOn2Fit(xOn2),'--')

#plot(xOff,refCurve(xOff-shift_off),'--')
#plot(xOn,refCurve(xOn-shift_on),'--')

plot(xOn,contrast)
axvline(xOn[argmax(fittedContrast)],ls = '-.')

if fitS02:
	plot(xOn2,contrast2)
	axvline(xOn2[argmax(fittedContrast2)],ls = '-.')

ylim(0,1)

from pyview.lib.datacube import Datacube

sDataFit = Datacube("s curve analysis")

sDataFit.createColumn("x",xOn)

sDataFit.createColumn("yOff",yOff)
sDataFit.createColumn("yOn",yOn)
sDataFit.createColumn("contrast10",contrast)
sDataFit.createColumn("yOnFit",yOnFit(xOn))
sDataFit.createColumn("contrastFit",yOnFit(xOn)-yOff)
sDataFit.createColumn("xRef",xRef)
sDataFit.createColumn("yRef",yRef)

if fitS02:
	sDataFit.createColumn("x2",xOn2)
	sDataFit.createColumn("yOn2",yOn2)
	sDataFit.createColumn("contrast2",contrast2)
	sDataFit.createColumn("yOn2Fit",yOn2Fit(xOn2))
	sDataFit.createColumn("contrast2Fit",yOn2Fit(xOn2)-yOff2)

sData.addChild(sDataFit)

sData.savetxt()

xlabel("attenuator voltage")
ylabel("switching probability")

p00 = 1-refCurve(xOn[argmax(fittedContrast)]-shift_off)
p11 = refCurve(xOn[argmax(fittedContrast)]-shift_on)

p_relax   = yOnFit(xOn[argmax(fittedContrast)])

if fitS02:
	p_relax_2 = yOn2Fit(xOn2[argmax(fittedContrast2)])
	title(("P(0|0>) = %.4f" % p00)+(" -  P(1|1>) = %.4f " % p11) + (" - P(1|1>) w. relax. = %.4f" % p_relax) + (" - P(2|2>) - w. relax.  = %.4f" % p_relax_2))
else:
	title(("P(0|0>) = %.4f" % p00)+(" -  P(1|1>) = %.4f " % p11) + (" - P(1|1>) w. relax. = %.4f" % p_relax))
