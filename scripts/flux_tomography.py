##Reconstructs the shape of a fluxline pulse by using the qubit as a probe for the flux.
#Prerequisites:
# -The length and amplitude of a non-gaussian, rectangular pi-pulse must be defined for the qubit to be investigated.
# - The JBA has to be calibrated at the value of the magnetic flux given by (readoutFlux)
def maximizeSwitching(qubit,jba,waveform,t,readoutFlux = 0.5,readoutMargin = 30,fastMethod = False,samplingRate = 1.0,hot = True,cube = None,preCompensate = False,factor = 1.0,startRange = arange(-0.05,0.05,0.005)):
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
		
		baseWaveform = qubit.fluxlineWaveform()
		readout = qubit.parameters()["timing.readout"]
		newWaveform = zeros(len(baseWaveform)-t)
		print len(newWaveform)
		newWaveform[:] = baseWaveform[:len(newWaveform)]
		newWaveform[readout-t:] = baseWaveform[readout:]
		qubit.loadRabiPulse(phase = math.pi,readout = readout - t)
		
		figure("waveforms")
		cla()
		plot(baseWaveform)
		plot(newWaveform)

		qubit.loadFluxlineWaveform(newWaveform,compensateResponse = preCompensate,factor = factor,samplingInterval = 1.0)

		if cube == None:
			cube = Datacube()
		
		cube.setName("Switching probability optimization at t = %g ns" % t )
		cube.setParameters(instrumentManager.parameters())
		
		steps = 10
		
		span = fabs(max(-1,-1-min(waveform))-min(1.0,1-max(waveform)))
		
		rounds = 2
		cnt = 0
		searchRange = startRange
		span = max(searchRange)-min(searchRange)
		
		while cnt<rounds:
			roundCube = Datacube("Fitting, step %d" % (cnt+1))
			cube.addChild(roundCube)
			#Vary (extraFlux) and measure the switching probability of the qubit:
		  
			for extraFlux in searchRange:	
		    
				modifiedWaveform = zeros(len(newWaveform))
				modifiedWaveform[:] = newWaveform[:]
				modifiedWaveform[1:readout-t]+=extraFlux
				qubit.loadFluxlineWaveform(modifiedWaveform,compensateResponse = preCompensate,factor = factor,samplingInterval = 1.0)
				if cnt == rounds-1:
					ntimes = 200
				else:
					ntimes = 20
				p = qubit.Psw(ntimes = ntimes)
				print "flux = %g, p = %g" % (extraFlux,p)
				roundCube.set(p = p , t = t,extraFlux = extraFlux)
				roundCube.commit()
			maxFlux = roundCube.column("extraFlux")[argmax(roundCube.column("p"))]
			maxP = roundCube.column("p")[argmax(roundCube.column("p"))]
			result = fitLorentzian(roundCube.column("extraFlux"),roundCube.column("p"))
			(params,fitfunc,rsquare) = result
			maxFlux = -params[1]
			maxP = params[0]
			roundCube.createColumn("p_fit",fitfunc(params,roundCube.column("extraFlux")))	
			#Divide the search span by 2 and center it around the maximum found in the current step:
			span/=4.0
			cnt+=1
			searchRange = linspace(-maxFlux-span/2.0,-maxFlux+span/2.0,steps)
			#Return the parameters of the best fit:
		return (-maxFlux,maxP,cube)
	finally:
		qubit.popState()
##Parameters for qubit 2:
qubit = qubit2
jba = jba2
readoutFlux = 0.52
name = "qubit 2"
##Parameters for qubit 1:
qubit = qubit1
jba = jba1
readoutFlux = 0.5
name = "qubit 1"
##Perform the tomography:
times = list(arange(210,500,1))

data = Datacube("pulse tomography of %s" % name)
data.setParameters(instrumentManager.parameters())
dataManager.addDatacube(data)

for t in arange(100,1000,100):
	cube = Datacube()
	data.addChild(cube)
	(flux,maximum,rcube) = maximizeSwitching(qubit,jba,tomographyWaveform,t = t,readoutMargin = 20,readoutFlux = readoutFlux,cube = cube,preCompensate = True,factor = 0.8)
	data.set(t = t,flux = flux,maximum = maximum)
	data.commit()
	data.savetxt()
