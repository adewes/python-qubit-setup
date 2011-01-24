##This script fits a measured set of s curves by using a reference curve (ideally measured with the qubit detuned far from the cavity).
##Load the s curve data
var = "p1x"
qubit = qubit1
sReference = sReferenceQubit1
sData = sDataQubit1
sData2 = sData2Qubit1
##Qubit 2
var = "px1"
qubit = qubit2
sReference = sReferenceQubit2
sData = sDataQubit2
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
contrast = sData.allChildren()[1].column("contrast")[xmin:xmax]

xOn2 = sData2.allChildren()[1].column("v")[xmin:xmax]
yOn2 = sData2.allChildren()[1].column(var)[xmin:xmax]
contrast2 = sData2.allChildren()[1].column("contrast")[xmin:xmax]

xOff = sData.allChildren()[0].column("v")[xmin:xmax]
yOff = sData.allChildren()[0].column(var)[xmin:xmax]

plot(xOff,yOff)
plot(xOn,yOn)
plot(xOn2,yOn2)
plot(xRef,yRef)
##Fit the contrast
import scipy
import scipy.optimize
import numpy.linalg

def errfuncGauss(p,xOn,contrast):
	return numpy.linalg.norm(contrast-p[0]*(1-pow((xOn-p[1])/p[2],2.0)) )

ps = [max(contrast),xOn[argmax(contrast)],0.1]
ps2 = [max(contrast2),xOn2[argmax(contrast2)],0.1]

xmax = argmax(contrast)
xmax2 = argmax(contrast2)

cp = scipy.optimize.fmin(errfuncGauss,ps,args=(xOn[xmax-10:xmax+10],contrast[xmax-10:xmax+10]),xtol = 1e-8,disp = 1,maxiter = 1e5,maxfun = 1e5)
cp2 = scipy.optimize.fmin(errfuncGauss,ps2,args=(xOn2[xmax2-10:xmax2+10],contrast2[xmax2-10:xmax2+10]),xtol = 1e-8,disp = 1,maxiter = 1e5,maxfun = 1e5)

fittedContrast = cp[0]*(1-pow((xOn-cp[1])/cp[2],2.0))
fittedContrast2 = cp2[0]*(1-pow((xOn2-cp2[1])/cp2[2],2.0))

##Fit the s curve parameters

xValues = [-100]
xValues.extend(xRef)
xValues.append(100)

yValues = [1]
yValues.extend(yRef)
yValues.append(0)

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

ps2 = [0.1,-0.15,p1s[1]]

p1s2 = scipy.optimize.fmin(errfuncTriple,ps2,args=(xOn2,yOn2,refCurve,p1s),xtol = 1e-10,disp = 1,maxiter = 1e5,maxfun = 1e5)

print p1s
print p1s2

##Plot the results...

p1_off = p1s[0]
p0_on = p1s[1]
shift_off = p1s[2]
shift_on = p1s[3]

p0_on_2 = p1s2[0]
shift_on_2 = p1s2[1]


print p1_off,p0_on,p_relax

cla()

plot(xOff,yOff)
plot(xOn,yOn)
plot(xOn2,yOn2)
plot(xRef,yRef)


plot(xOff,(1-p1_off)*refCurve(xOff-shift_off)+p1_off*refCurve(xOff-shift_on),'--')

yOnFit = lambda x : p0_on*refCurve(x-shift_off)+(1-p0_on)*refCurve(x-shift_on)

plot(xOn,yOnFit(xOn),'--')

p0_on_12 = p1s2[2]

yOn2Fit = lambda x : (-(1-p0_on_12)*p0_on_2+p0_on_2)*refCurve(x-shift_off)+p0_on_2*(1-p0_on_12)*refCurve(x-shift_on)+(1-p0_on_2)*refCurve(x-shift_on_2)

plot(xOn2,yOn2Fit(xOn2),'--')
#plot(xOn,(1-p_relax)*refCurve(xOn-shift_on)+p_relax*refCurve(xOn-shift_off))

plot(xOff,refCurve(xOff-shift_off),'--')
plot(xOn,refCurve(xOn-shift_on),'--')

#plot(xOn,contrast)

#plot(xOn,yOnFit(xOn))

axvline(xOn[argmax(fittedContrast)],ls = '-.')
axvline(xOn2[argmax(fittedContrast2)],ls = '-.')
ylim(0,1)
#xlim(1.2,1.4)

xlabel("attenuator voltage")
ylabel("switching probability")

p00 = 1-refCurve(xOn[argmax(fittedContrast)]-shift_off)
p11 = refCurve(xOn[argmax(fittedContrast)]-shift_on)

p_relax   = yOnFit(xOn[argmax(fittedContrast)])
p_relax_2 = yOn2Fit(xOn2[argmax(fittedContrast2)])

title(("P(0|0>) = %.4f" % p00)+(" -  P(1|1>) = %.4f " % p11) + (" - P(1|1>) w. relax. = %.4f" % p_relax) + (" - P(2|2>) - w. relax.  = %.4f" % p_relax_2))

qubit.parameters()["readout.p00"] = p00
qubit.parameters()["readout.p11"] = p11

##

xlabel("attenuator voltage [V]")
ylabel("switching probability")
title("S curves")

legend(("s-ON","s-OFF","s-ON (fit)","s-OFF (fit)"))
##
annotate('arrowstyle', xy=(0.5, 1),  xycoords='data',
                xytext=(-50, 30), textcoords='offset points',
                arrowprops=dict(arrowstyle="->")
                )
draw()