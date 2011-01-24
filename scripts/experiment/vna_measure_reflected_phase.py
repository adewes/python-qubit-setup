##Initialization
#This script sweeps the voltage in the transmon coil (or any other instrument) and measures the phase and magnitude of a transmitted microwave signal using the VNA. The phase of the signal is fitted with a linear resonator model to obtain the resonance frequency and the Q factor.
title = "Cavity 2"
afg = afg1
data = Datacube("Cavity Anticrossing - %s" % title)
dataManager.addDatacube(data)	
data.setParameters(instrumentManager.parameters())
trace = vna1.getTrace(correctPhase = True)
matrix = zeros((len(trace.column("phase")),300))
cnt = 0

import math
import scipy
import scipy.optimize

#We define the functions for fitting the reflected phase.

fitfunc = lambda p, x : 2.0*p[0]*scipy.arctan(2.0*p[1]*(x/p[2]-1))+p[3]
errfunc = lambda p, x, y,ff: ff(p,x)-y

figure("transmission")
xlabel("frequency [GHz]")
cla()
##Choose sweep parameters...

start = -1.5
stop = 1.5
step = 0.1

fluxes = list(arange(start,stop,step))

##Perform the measurement and fit

while len(fluxes) > 0:

	#Get the next value of the flux

	flux = fluxes.pop(0)

	#Change the voltage in the instrument

	afg1.setOffset(flux)
#	afg2.setOffset(flux)
#	transmon_coil.setVoltage(flux)

	#Reset the VNA, wait until a full cycle has been completed and transfer the measured trace.

	vna1.waitFullSweep()
	trace = vna1.getTrace(correctPhase = True)
	data.addChild(trace)

	#Initial guess for fitting parameters

	p1 = [180.0,2000.0,(trace.column("freq")[-1]+trace.column("freq")[0])/2.0,0]

	#Fit the measured phase with the model defined earlier...

	p1s, success = 	scipy.optimize.leastsq( errfunc, p1, args = (trace.column("freq") , 	trace.column("phase") , fitfunc))

	trace.createColumn("phase_fit",fitfunc(p1s,trace.column("freq")))
	trace.setName("transmission - v = %g V" % flux)

	data.set(voltage = flux,Q = p1s[1],f0 = p1s[2])

	#Commit and save the datacube...

	data.commit()
	data.savetxt()	

	#Add the phase signal to the matrix and display it...

	matrix[:,cnt] = trace.column("phase")
	cnt+=1

	cla()

	imshow(matrix[:,:cnt] ,aspect = 'auto',interpolation = 'nearest', origin = 'lower',extent = (start,start+step*cnt,trace.column("freq")[0],trace.column("freq")[-1]))
##
savefig('transmission-coil.pdf')
