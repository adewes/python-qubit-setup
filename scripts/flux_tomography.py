##Reconstructs the shape of a fluxline pulse by using the qubit as a probe for the flux.
#Prerequisites:
# -The length and amplitude of a non-gaussian, rectangular pi-pulse must be defined for the qubit to be investigated.
# - The JBA has to be calibrated at the value of the magnetic flux given by (readoutFlux)
from config.startup import *

def maximizeSwitching(qubit,jba,waveform,t,readoutMargin = 30,fastMethod = False,samplingRate = 1.0,hot = True,cube = None,preCompensate = False,factor = 1.0,startRange = arange(-0.4,0.2,0.04)):
 	"""
	Reconstructs the value of flux of a fluxline waveform (waveform).
	The following method is used to reconstruct the value of the magnetic flux at the qubit:
	-A pi-pulse with a delay (t) is loaded as a qubit drive waveform.
	-A fluxline waveform is generated, where
	  -The first point (which will be output by the AFG before the waveform starts) is set to (extraFlux)
	  -The following (cutPoint) points contain the waveform to be analyzed (waveform[0:cutPoint])
	  -The following part of length (readoutMargin+2000) is set to (readoutFlux)
	  -The last point is set to (extraFlux)
	-(cutPoint) corresponds to time (t) plus the duration of the Rabi pulse.
	-The readout of the qubit is done at time (cutPoint+1+readoutMargin)
	-(extraFlux) is varied and the value that maximizes the switching probability (p) is returned as the 		flux seen by the qubit.
	"""	
	qubit.pushState()
	try:
		
		minFlux = min(waveform)
		maxFlux = max(waveform)
		
		baseWaveform = qubit.fluxlineBaseWaveform()
		readout = qubit.parameters()["timing.readout"]
		baseWaveform[readout-t:readout] += waveform[:t]

		f_sb = qubit.parameters()["pulses.xy.f_sb"]
		f01 = qubit.parameters()["frequencies.f01"]
		
		qubit.loadRabiPulse(phase = math.pi,readout = readout+readoutMargin,delay = readoutMargin,gaussian = False)
		
		if cube == None:
			cube = Datacube()
		
		cube.setName("Switching probability optimization at t = %g ns" % t )
		cube.setParameters(instrumentManager.parameters())
		
		steps = 30
		
		span = fabs(max(-1,-1-min(waveform))-min(1.0,1-max(waveform)))
		
		rounds = 3
		cnt = 0
		searchRange = startRange
		span = max(searchRange)-min(searchRange)
		
		qubit.loadFluxlineWaveform(baseWaveform,compensateResponse = preCompensate,factor = factor)
		qubit.loadRabiPulse(phase = math.pi,readout = readout+readoutMargin,delay = readoutMargin,gaussian = True,f_sb = f_sb)
	
		while cnt<rounds:
			roundCube = Datacube("Fitting, step %d" % (cnt+1))
			roundCube.parameters()["defaultPlot"] = [["f","p"],["f","p_fit"]]
			cube.addChild(roundCube)
			#Vary (f) and measure the switching probability of the qubit:
		  
			for f in searchRange:	
				
				qubit.setDriveFrequency(f01+f+f_sb)
				qubit.setDriveAmplitude(I = qubit.parameters()["pulses.xy.drive_amplitude"],Q = qubit.parameters()["pulses.xy.drive_amplitude"])
				ntimes = 40
				p = qubit.Psw(ntimes = ntimes)
				roundCube.set(p = p , t = t,f = f)
				roundCube.commit()

			maxFlux = roundCube.column("f")[argmax(roundCube.column("p"))]
			maxP = roundCube.column("p")[argmax(roundCube.column("p"))]
			result = fitLorentzian(roundCube.column("f"),roundCube.column("p"))
			(params,fitfunc,rsquare) = result
			maxFlux = -params[1]
			maxP = params[0]
			roundCube.createColumn("p_fit",fitfunc(params,roundCube.column("f")))	
			#Divide the search span by 2 and center it around the maximum found in the current step:
			span/=4.0
			cnt+=1
			searchRange = linspace(-maxFlux-span/2.0,-maxFlux+span/2.0,steps)
			#Return the parameters of the best fit:
		return (-maxFlux,maxP,cube)
	finally:
		pass
		qubit.popState()
##Parameters for qubit 2:
qubit = qubit2
jba = jba2
readoutFlux = 0.52
name = "qubit 2"
##Parameters for qubit 1:
qubit = qubit1
jba = jba1
name = "qubit 1"
##Perform the tomography:
times = list(arange(210,500,1))

data = Datacube("pulse tomography of %s" % name)
data.setParameters(instrumentManager.parameters())
dataManager.addDatacube(data)

tomographyWaveform = zeros(2000)
tomographyWaveform[1000:] = 0.1

ts = list(arange(1000,1050,1))+list(arange(1050,1100,5))+list(arange(1100,1400,10))+list(arange(1400,2000,100))

for t in ts:
	cube = Datacube()
	data.addChild(cube)
	(flux,maximum,rcube) = maximizeSwitching(qubit,jba,tomographyWaveform,t = t,readoutMargin = 10,cube = cube,preCompensate = True,factor = 1.0)
	data.set(t = t,flux = flux,maximum = maximum)
	data.commit()
	data.savetxt()
