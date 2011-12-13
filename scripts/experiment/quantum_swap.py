#Measure a quantum swap between the two qubits and perform a tomography of the resulting states.
#Before you run this script, make sure that the Rabi pulses for both qubits are calibrated!
import sys
from instruments import *
from config.startup import *
importModule("scripts.state_tomography.state_simulation")


def measureSwapSequence(swapDuration = 0,pulseHeight = 0,delayBeforeTomography = 0,measurements = ["zz"],averaging = 100,state = [[0,0],[math.pi,0]],piLength = 0,tomographyLength = 0,tomographyDelay = 0,xyRotation = 0,measurementRotations = None,use12Pulse = False,alpha = 0,beta = 0,zrot = 0):

	f_sb1 = qubit1.parameters()["pulses.xy.f_sb"]
	f_sb2 = qubit2.parameters()["pulses.xy.f_sb"]

	from instruments.qubit import PulseSequence

#	print "Length of tomgography pulse: %g" % tomographyLength		
	
	qb1BaseFlux = qubit1.fluxlineBaseWaveform()
	qb2BaseFlux = qubit2.fluxlineBaseWaveform()
	qb1FluxSeq = PulseSequence()
	qb1FluxSeq.addPulse(qb1BaseFlux)
	qb2FluxSeq = PulseSequence()
	qb2FluxSeq.addPulse(qb2BaseFlux)

	if use12Pulse:
		tomographyLength+=pi12Length
	
	ro1 = qubit1.parameters()["timing.readout"]
	ro2 = qubit2.parameters()["timing.readout"]

	readout = max(ro1,ro2)

	swapPulse = qubit1.generateZPulse(length = swapDuration,gaussian = False)*pulseHeight
	zRot = qubit1.generateZPulse(length = zrot,gaussian = False)
	zLen = len(swapPulse)+delayBeforeTomography+len(zRot)
	qb1FluxSeq.addPulse(swapPulse,delay = ro1-zLen-tomographyLength,position = 0)
	qb1FluxSeq.addPulse(zRot*alpha,delay = ro1-zLen-tomographyLength+len(swapPulse),position = 0)
	qb2FluxSeq.addPulse(zRot*beta,delay = ro1-zLen-tomographyLength+len(swapPulse),position = 0)

	qubit1.loadFluxlineWaveform(qb1FluxSeq.getWaveform(),factor = qubit1.parameters()["flux.compensationFactor"],compensateResponse = qubit1.parameters()["flux.compensateResponse"])
	qubit2.loadFluxlineWaveform(qb2FluxSeq.getWaveform(),factor = qubit2.parameters()["flux.compensationFactor"],compensateResponse = qubit2.parameters()["flux.compensateResponse"])
	npsw = dict()

	if measurementRotations == None:
		for m in measurements:
				x = m[0]
				y = m[1]
	#			print "Measuring along %s%s" % (x,y)
				qb2Seq = PulseSequence()
				qb1Seq = PulseSequence()
				qb1Seq.addPulse(qubit1.generateRabiPulse(phase = state[0][0],angle = state[0][1],f_sb = f_sb1,delay = readout-zLen-piLength-tomographyLength),position = 0)	
				qb2Seq.addPulse(qubit2.generateRabiPulse(phase = state[1][0],angle = state[1][1],f_sb = f_sb2,delay = readout-zLen-piLength-tomographyLength),position = 0)	
	
				phasex = xyRotation
				phasey = 0
	
				if x[0] == "m":
					phasex += math.pi
				if y[0] == "m":
					phasey += math.pi
	
				if x == "x" or x == "mx":
					#We add a Pi/2 rotation around Y to measure along X	
					qb1Seq.addPulse(qubit1.generateRabiPulse(angle = -math.pi/2.0+phasex,phase = math.pi/2.0,delay = readout-tomographyLength+tomographyDelay,f_sb = f_sb1),position = 0)
				elif x == "y" or x == "my":
					#We add a -Pi/2 rotation around X to measure along Y
					qb1Seq.addPulse(qubit1.generateRabiPulse(angle = phasex,phase = math.pi/2.0,delay = readout-tomographyLength+tomographyDelay,f_sb = f_sb1),position = 0)
				elif x == "mz":
					qb1Seq.addPulse(qubit1.generateRabiPulse(angle = 0,phase = math.pi,delay = readout-tomographyLength+tomographyDelay,f_sb = f_sb1),position = 0)
				else:
					qb1Seq.addWait(tomographyLength)

				if y == "x" or y == "mx":
					#We add a Pi/2 rotation around Y to measure along X
					qb2Seq.addPulse(qubit2.generateRabiPulse(angle = -math.pi/2.0+phasey,phase = math.pi/2.0,delay = readout-tomographyLength+tomographyDelay,f_sb = f_sb2),position = 0)
				elif y == "y" or y == "my":
					#We add a -Pi/2 rotation around X to measure along Y
					qb2Seq.addPulse(qubit2.generateRabiPulse(angle = phasey,phase = math.pi/2.0,delay = readout-tomographyLength+tomographyDelay,f_sb = f_sb2),position = 0)
				elif y == "mz":
					qb2Seq.addPulse(qubit2.generateRabiPulse(angle = 0,phase = math.pi,delay = readout-tomographyLength+tomographyDelay,f_sb = f_sb2),position = 0)
				else:
					qb2Seq.addWait(tomographyLength)

				if use12Pulse:
					qb1Seq.addPulse(qubit1.generateRabiPulse(length = qubit1.parameters()["pulses.xy.t_pi12"],delay = readout-pi12Length,f_sb = qubit1.parameters()["pulses.xy.f_sb12"]),position = 0)
					qb2Seq.addPulse(qubit2.generateRabiPulse(length = qubit2.parameters()["pulses.xy.t_pi12"],delay = readout-pi12Length,f_sb = qubit2.parameters()["pulses.xy.f_sb12"]),position = 0)
					
	
				qubit1.loadWaveform(qb1Seq.getWaveform(),readout = readout)
				qubit2.loadWaveform(qb2Seq.getWaveform(),readout = readout)
	
				time.sleep(1)

				acqiris.bifurcationMap(ntimes = averaging)
				psw = acqiris.Psw()
				for key in psw.keys():
					npsw[x+y+key] = psw[key]
	else:
		"""
		We define explicitely the rotation angles and phases for each qubit...
		"""	
		
		(angle1,phase1,angle2,phase2) = measurementRotations
		
		qb2Seq = PulseSequence()
		qb1Seq = PulseSequence()
		qb1Seq.addPulse(qubit1.generateRabiPulse(phase = state[0][0],angle = state[0][1],f_sb = f_sb1,delay = readout-zLen-piLength-tomographyLength),position = 0)	
		qb2Seq.addPulse(qubit2.generateRabiPulse(phase = state[1][0],angle = state[1][1],f_sb = f_sb2,delay = readout-zLen-piLength-tomographyLength),position = 0)	
		qb1Seq.addPulse(qubit1.generateRabiPulse(angle = angle1,phase = phase1,delay = readout-tomographyLength+tomographyDelay,f_sb = f_sb1),position = 0)
		qb2Seq.addPulse(qubit2.generateRabiPulse(angle = angle2,phase = phase2,delay = readout-tomographyLength+tomographyDelay,f_sb = f_sb2),position = 0)

		if use12Pulse:
			qb1Seq.addPulse(qubit1.generateRabiPulse(length = qubit1.parameters()["pulses.xy.t_pi12"],delay = readout-pi12Length,f_sb = qubit1.parameters()["pulses.xy.f_sb12"]),position = 0)
			qb2Seq.addPulse(qubit2.generateRabiPulse(length = qubit2.parameters()["pulses.xy.t_pi12"],delay = readout-pi12Length,f_sb = qubit2.parameters()["pulses.xy.f_sb12"]),position = 0)


		qubit1.loadWaveform(qb1Seq.getWaveform(),readout = readout)
		qubit2.loadWaveform(qb2Seq.getWaveform(),readout = readout)
		
		time.sleep(1)
		
		acqiris.bifurcationMap(ntimes = averaging)
		npsw = acqiris.Psw()

	return npsw
	

def measureTomography(driveSequences,fluxSequences,delay = 5,use12Pulse = False,xyRotation = 0,averaging = 80,onlyZZ = False):

	f_sb1 = qubit1.parameters()["pulses.xy.f_sb"]
	f_sb2 = qubit2.parameters()["pulses.xy.f_sb"]
	
	measurements = generateCombinations(["x","y","z"],lambda x,y:x+y,2)

	from instruments.qubit import PulseSequence

	piLength = max(len(qubit1.generateRabiPulse(phase = math.pi,f_sb = f_sb1)),len(qubit2.generateRabiPulse(phase = math.pi,f_sb = f_sb2)))
	tomographyLength = ceil(max(len(qubit1.generateRabiPulse(angle = -math.pi/2.0,phase = math.pi/2.0,f_sb = f_sb1)),len(qubit2.generateRabiPulse(angle = -math.pi/2.0,phase = math.pi/2.0,f_sb = f_sb2))))
	
	if use12Pulse:
		tomographyLength+=pi12Length
		
	if onlyZZ:
		if use12Pulse:
			tomographyLength = pi12Length
		else:
			tomographyLength = 0
		measurements = ["zz"]
	
	readout = qubit1.readoutDelay()
	
	seqs = [driveSequences[0],driveSequences[1],fluxSequences[0],fluxSequences[1]]
	
	seqLength = max(map(lambda x:len(x),seqs))
	
	for i in range(0,len(seqs)):
		seqs[i].addWait(seqLength-len(seqs[i]))
	
	start = readout - tomographyLength
	
	npsw = dict()
	
	qb1BaseFlux = qubit1.fluxlineBaseWaveform()
	qb2BaseFlux = qubit2.fluxlineBaseWaveform()

	qb1FluxSeq = PulseSequence()
	qb1FluxSeq.addPulse(qb1BaseFlux)
	qb2FluxSeq = PulseSequence()
	qb2FluxSeq.addPulse(qb2BaseFlux)
	
	qb1FluxSeq.addPulse(fluxSequences[0].getWaveform(),position = start-seqLength)
	qb2FluxSeq.addPulse(fluxSequences[1].getWaveform(),position = start-seqLength)
	
	qubit1.loadFluxlineWaveform(qb1FluxSeq.getWaveform(),factor = qubit1.parameters()["flux.compensationFactor"],compensateResponse = qubit1.parameters()["flux.compensateResponse"])
	qubit2.loadFluxlineWaveform(qb2FluxSeq.getWaveform(),factor = qubit2.parameters()["flux.compensationFactor"],compensateResponse = qubit2.parameters()["flux.compensateResponse"])
		
	for m in measurements:
			x = m[0]
			y = m[1]

			qb2Seq = PulseSequence()
			qb1Seq = PulseSequence()
			
			qb1Seq.addPulse(driveSequences[0].getWaveform(),position = 0)
			qb2Seq.addPulse(driveSequences[1].getWaveform(),position = 0)

			phasex = xyRotation
			phasey = 0
	
			if x[0] == "m":
				phasex += math.pi
			if y[0] == "m":
				phasey += math.pi
	
			if x == "x" or x == "mx":
				#We add a Pi/2 rotation around Y to measure along X	
				qb1Seq.addPulse(qubit1.generateRabiPulse(angle = -math.pi/2.0+phasex,phase = math.pi/2.0,f_sb = f_sb1,delay = seqLength),position = 0)
			elif x == "y" or x == "my":
				#We add a -Pi/2 rotation around X to measure along Y
				qb1Seq.addPulse(qubit1.generateRabiPulse(angle = phasex,phase = math.pi/2.0,f_sb = f_sb1,delay = seqLength),position = 0)
			elif x == "mz":
				qb1Seq.addPulse(qubit1.generateRabiPulse(angle = 0,phase = math.pi,f_sb = f_sb1,delay = seqLength),position = 0)
			if y == "x" or y == "mx":
				#We add a Pi/2 rotation around Y to measure along X
				qb2Seq.addPulse(qubit2.generateRabiPulse(angle = -math.pi/2.0+phasey,phase = math.pi/2.0,f_sb = f_sb2,delay = seqLength),position = 0)
			elif y == "y" or y == "my":
				#We add a -Pi/2 rotation around X to measure along Y
				qb2Seq.addPulse(qubit2.generateRabiPulse(angle = phasey,phase = math.pi/2.0,f_sb = f_sb2,delay = seqLength),position = 0)
			elif y == "mz":
				qb2Seq.addPulse(qubit2.generateRabiPulse(angle = 0,phase = math.pi,f_sb = f_sb2,delay = seqLength),position = 0)

			if use12Pulse:
				qb1Seq.addPulse(qubit1.generateRabiPulse(length = qubit1.parameters()["pulses.xy.t_pi12"],delay = seqLength+tomographyLength-pi12Length,f_sb = qubit1.parameters()["pulses.xy.f_sb12"]),position = 0)
				qb2Seq.addPulse(qubit2.generateRabiPulse(length = qubit2.parameters()["pulses.xy.t_pi12"],delay = seqLength+tomographyLength-pi12Length,f_sb = qubit2.parameters()["pulses.xy.f_sb12"]),position = 0)

			maxLen = seqLength+tomographyLength

			qb1Seq.addWait(maxLen-len(qb1Seq))
			qb2Seq.addWait(maxLen-len(qb2Seq))
	
			qubit1.loadWaveform(qb1Seq.getWaveform(endAt = readout),readout = readout)
			qubit2.loadWaveform(qb2Seq.getWaveform(endAt = readout),readout = readout)
	
			time.sleep(1)

			acqiris.bifurcationMap(ntimes = averaging)
			psw = acqiris.Psw()
			for key in psw.keys():
				npsw[x+y+key] = psw[key]
	return npsw
from config.startup import importModule
importModule("scripts.state_tomography.state_simulation")
from scripts.state_tomography.state_simulation import *
	
def reconstructRho(data,row = None):
		
	(measuredSpins,measuredProbabilities) = convertDatacubeToSpins(data,indices1=["x","y","z","i"], indices2=["x","y","z","i"],saveValues = False,detectorFunction=None)
	measuredProbabilities.parameters()["defaultPlot"] = [("duration","zzp00"),("duration","zzp01"),("duration","zzp10"),("duration","zzp11")]
		
	measurements = generateCombinations([sigmax,sigmay,sigmaz,idatom],lambda x,y:tensor(x,y),2)
	labels = generateCombinations(["x","y","z","i"],lambda x,y:x+y,2)
		
	values = []
		
	for i in range(0,len(measurements)):
		if row == None:
			values.append(mean(measuredSpins[labels[i]]))
		else:
			values.append(mean(measuredSpins[labels[i]][row]))
		
	rho = reconstructDensityMatrix(measurements,values)

	return rho
	

def measureCHSH(data,phi,saveClicks = False,**kwargs):
	Q = [-math.pi/2.0,math.pi/2.0]
	R = [0,math.pi/2.0]
	S = [-math.pi/2.0+phi/180.0*math.pi,math.pi/2.0]
	T = [phi/180.0*math.pi,math.pi/2.0]
	rotations = [Q+S,R+S,R+T,Q+T]
	labels = ["qs","rs","rt","qt"]	
	data.set(phi = phi)
	if saveClicks:
		clicks = Datacube("clicks",dtype = uint8)
		data.addChild(clicks,name = "clicks")
	for i in range(0,len(rotations)):
		probs = measureSwapSequence(measurementRotations = rotations[i],**kwargs)
		data.set(cnt = cnt)
		nprobs = dict()
		for key in probs.keys():
			nprobs[labels[i]+key] = probs[key]
		data.set(**nprobs)
		if saveClicks:
			clickData = acqiris.clicks()
			clicks.createColumn("clicks - "+labels[i],clickData["clicks"])
	data.commit()
	return data

#Parameter initialization...

def initSwapParameters():

	global f_sb1,f_sb2,piLength,tomographyLength,pi12Length

	print dir()

	f_sb1=qubit1.parameters()["pulses.xy.f_sb"]
	f_sb2=qubit2.parameters()["pulses.xy.f_sb"]
	
	for qubit in [qubit1,qubit2]:
		qubit.setDriveFrequency(qubit.parameters()["frequencies.f01"]+qubit.parameters()["pulses.xy.f_sb"])
		qubit.setDriveAmplitude(I = +qubit.parameters()["pulses.xy.drive_amplitude"],Q = +qubit.parameters()["pulses.xy.drive_amplitude"])
	
	piLength = max(len(qubit1.generateRabiPulse(phase = math.pi,f_sb = f_sb1)),len(qubit2.generateRabiPulse(phase = math.pi,f_sb = f_sb2)))
	pi12Length = max(len(qubit1.generateRabiPulse(length = qubit1.parameters()["pulses.xy.t_pi12"])),len(qubit2.generateRabiPulse(length = qubit2.parameters()["pulses.xy.t_pi12"])))
	tomographyLength = ceil(max(len(qubit1.generateRabiPulse(angle = -math.pi/2.0,phase = math.pi/2.0,f_sb = f_sb1)),len(qubit2.generateRabiPulse(angle = -math.pi/2.0,phase = math.pi/2.0,f_sb = f_sb2))))
	

##Optimize the height of the fluxline pulse

initSwapParameters()

data = Datacube("Quantum Swap - Optimization of fluxline pulse height")

data.setParameters(instrumentManager.parameters())
data.parameters()["defaultPlot"] = [("flux","zzp1x"),("flux","zzpx1")]
dataManager.addDatacube(data)
try:
	for flux in arange(0.01,0.16,0.0005):
		data.set(flux = flux)
		probs = measureSwapSequence(swapDuration = 60,pulseHeight = flux,delayBeforeTomography = 2,measurements = ["zz"],averaging = 40,state = [[math.pi,0],[math.pi*0,0]],piLength = piLength,tomographyLength = tomographyLength*0,use12Pulse = True)
		data.set(**probs)
		data.commit()
finally:
	data.savetxt()

##Optimize the fluxline compensation factor
initSwapParameters()

fluxAnticrossing = 0.0917

data = Datacube("Quantum Swap - Optimization of fluxline compensation factor")

data.setParameters(instrumentManager.parameters())
data.parameters()["defaultPlot"] = [("f","zzp1x"),("f","zzpx1")]
dataManager.addDatacube(data)
try:
	for f in arange(0.,1.5,0.01):
		data.set(f = f)
		probs = measureSwapSequence(swapDuration = 57,pulseHeight = fluxAnticrossing,delayBeforeTomography = 0,measurements = ["z"],averaging = 40,state = [[math.pi,0],[0,0]],piLength = piLength,tomographyLength = tomographyLength)
		data.set(**probs)
		data.commit()
finally:
	data.savetxt()

##Measure the SWAP as a function of the duration
initSwapParameters()

fluxAnticrossing = 0.0397
data = Datacube("Quantum Swap vs duration")

data.setParameters(instrumentManager.parameters())
data.parameters()["defaultPlot"] = [("duration","zzp00"),("duration","zzp01"),("duration","zzp10"),("duration","zzp11")]
dataManager.addDatacube(data)
try:
	durations = arange(0,800,2)
	cnt = 0
	for duration in durations:
		data.set(duration = duration,cnt = cnt)
		cnt += 1
		probs = measureSwapSequence(swapDuration = duration,pulseHeight = fluxAnticrossing,delayBeforeTomography = 0,measurements = ["zz"],averaging = 120,state = [[math.pi,0],[math.pi*0,0]],piLength = piLength,tomographyLength = tomographyLength*0,use12Pulse = True)
		data.set(**probs)
		data.commit()
finally:
	data.savetxt()

##Measure one point of the SWAP
initSwapParameters()

duration = 31
state = [[math.pi/2.0,math.pi/2.0],[math.pi/2.0,math.pi/2.0]]
data = Datacube("Quantum Swap at %g ns" % duration )
phi = math.pi/4.0

targetState = tensor(gs*cos(state[0][0]/2.)+es*sin(state[0][0]/2.)*exp(1j*(math.pi/2.0-state[0][1])),gs*cos(state[1][0]/2.)+es*sin(state[1][0]/2.)*exp(1j*(math.pi/2.0-state[1][1])))
targetState = targetState / norm(targetState)
targetRho = adjoint(targetState)*targetState

swap = lambda phi: matrix([[1,0,0,0],[0,cos(phi),-1j*sin(phi),0],[0,-1j*sin(phi),cos(phi),0],[0,0,0,1]])

targetRho = swap(phi)*targetRho*adjoint(swap(phi))

data.setParameters(instrumentManager.parameters())
data.parameters()["defaultPlot"] = [("index","zzp00"),("index","zzp01"),("index","zzp10"),("index","zzp11")]
dataManager.addDatacube(data)

global tomographyData
tomographyData = data

zrot = 2
alpha = 0.00
beta = -0.0

qubit1.parameters()["driveRotation"] = 85.0/180.0*math.pi

for d in [0]:
	try:
		data.set(d = d,duration = duration)		
		probs = measureSwapSequence(swapDuration = duration,pulseHeight = fluxAnticrossing,delayBeforeTomography = 3,measurements = generateCombinations(["x","y","z"],lambda x,y:x+y,2),averaging = 80,state = state,use12Pulse = True,piLength = piLength,tomographyLength = tomographyLength,xyRotation = phi/180.0*math.pi,zrot = zrot,alpha = alpha,beta = beta)
		data.set(**probs)
		data.commit()
	finally:
		data.savetxt()

rho = reconstructRho(data,row = None)
print "Raw:",quantumFidelity(rho,targetRho)

def transform(phases):
	return tensor(rotz(phases[0]/180.0*math.pi),rotz(phases[1]/180.0*math.pi))#*tensor(rotn(math.pi/2.0,[cos(phases[2]),sin(phases[2]),0]),rotn(math.pi/2.0,[cos(phases[3]),sin(phases[3]),0]))
	
def errorFunction(phases,rho,targetRho):
	rotation = transform(phases)
	return 1.0-quantumFidelity(rotation*rho*adjoint(rotation),targetRho)
	
ps = [0,0]
	
p1s = scipy.optimize.fmin(errorFunction,ps,args = (rho,targetRho))

print p1s

print "Corrected:",quantumFidelity(transform(p1s)*rho*adjoint(transform(p1s)),targetRho)
ioff()
figure("rho")
clf()
subplot(131)
cla()
plotDensityMatrix(rho)
subplot(132)
cla()
plotDensityMatrix(transform(p1s)*rho*adjoint(transform(p1s)))
subplot(133)
plotDensityMatrix(targetRho)
show()
	

##Measure the quantum process tomography of the gate...
"""
We perform a quantum process tomography of the SWAP gate by preparing 16 different input states, which are
combinations of the states |0>,|1>,|0>+|1> and |0>+i|1>. We perform a state tomography on the input state and
a state tomography of the same input state after applying the SWAP gate to it.
"""
initSwapParameters()

duration = 31
delay = 0
states = generateCombinations([[0,0],[math.pi,0],[math.pi/2.0,math.pi],[math.pi/2.0,math.pi/2.0]],lambda x,y: [x,y],2)

averaging = 160

use12Pulse = True

for duration in [duration]*10:

	data = Datacube("Quantum Process Tomography at %g ns" % duration )
	gv.tomographyData = data
	
	phi = 0.
	data.setParameters(instrumentManager.parameters())
	data.parameters()["defaultPlot"] = [("index","zzp00"),("index","zzp01"),("index","zzp10"),("index","zzp11")]
	dataManager.addDatacube(data)
	data.parameters()["states"] = states
	
	for i in range(0,len(states)):
		try:
			state = states[i]
			targetState = tensor(gs*cos(state[0][0]/2.)+es*sin(state[0][0]/2.)*exp(1j*(math.pi/2.0-state[0][1])),gs*cos(state[1][0]/2.)+es*sin(state[1][0]/2.)*exp(1j*(math.pi/2.0-state[1][1])))
			targetState = targetState / norm(targetState)
			targetRhoInitial = adjoint(targetState)*targetState
			data.set(duration = duration,delay =delay,state = i)
			
			#We measure the initial density matricse BEFORE the swap. This gives rho'.
			
			initialProbs = measureSwapSequence(swapDuration = 0,pulseHeight = fluxAnticrossing,delayBeforeTomography = 3,measurements = generateCombinations(["x","y","z"],lambda x,y:x+y,2),averaging = averaging,state = state,use12Pulse = use12Pulse,piLength = piLength,tomographyLength = tomographyLength,xyRotation = phi/180.0*math.pi)

			data.set(**initialProbs)
			data.commit()
			
			#We measure the density matrices AFTER the swap. This gives Epsilon(rho').
			
			probs = measureSwapSequence(swapDuration = duration,pulseHeight = fluxAnticrossing,delayBeforeTomography = 3,measurements = generateCombinations(["x","y","z"],lambda x,y:x+y,2),averaging = averaging,state = state,use12Pulse = use12Pulse,piLength = piLength,tomographyLength = tomographyLength,xyRotation = phi/180.0*math.pi,zrot = zrot,alpha = alpha,beta = beta)
			data.set(**probs)
			data.commit()
			
			targetRho = swap(math.pi/4.0)*targetRhoInitial*adjoint(swap(math.pi/4.0))

			rhoInitial = reconstructRho(data,row = i*2)
			rho = reconstructRho(data,row = i*2+1)
			
			print "Raw (Input) :",quantumFidelity(rhoInitial,targetRhoInitial)
			print "Raw (Output):",quantumFidelity(rho,targetRho)
			
			figure("rho")
			clf()
			subplot(221)
			cla()
			plotDensityMatrix(rhoInitial)
			subplot(222)
			plotDensityMatrix(targetRhoInitial)
			show()

			subplot(223)
			cla()
			plotDensityMatrix(rho)
			subplot(224)
			plotDensityMatrix(targetRho)
			show()

		finally:
			data.savetxt()
##Grover Search Algorithm
"""
We perform a quantum process tomography of the SWAP gate by preparing 16 different input states, which are
combinations of the states |0>,|1>,|0>+|1> and |0>+i|1>. We perform a state tomography on the input state and
a state tomography of the same input state after applying the SWAP gate to it.
"""
import instruments
import sys
reload(sys.modules["instruments.qubit"])
from instruments.qubit import PulseSequence

initSwapParameters()

grover = Datacube("Grover Search Algorithm")
	
grover.setParameters(instrumentManager.parameters())
dataManager.addDatacube(grover)
zPulse = qubit1.generateZPulse(length = 31*2,gaussian = False)
zLen = len(zPulse)

f_sb1 = qubit1.parameters()["pulses.xy.f_sb"]
f_sb2 = qubit2.parameters()["pulses.xy.f_sb"]

swap = matrix([[1,0,0,0],[0,0,-1j,0],[0,-1j,0,0],[0,0,0,1]])

alpha = -0.022
beta = -0.017

gamma = -0.031
delta = -0.019

qubit1.setDriveRotation(70./180.0*math.pi)
qubit2.setDriveRotation(0/180.0*math.pi)

use12Pulse = True
onlyZZ = False

try:

	for state in [0,1,2,3]:
		for step in [1,2,3,4,5]:
			
			fluxSequence1 = PulseSequence()
			fluxSequence2 = PulseSequence()

			driveSequence1 = PulseSequence()
			driveSequence2 = PulseSequence()

	
			data = Datacube("State = %d - Step = %d" % (state,step))

			grover.addChild(data,state = state,step = step)
			data.setParameters(instrumentManager.parameters())
		
			if step >= 1:
					
				#We initialize the system in the state 1/2(|0>+-i|1>)(|0>+-i|1>)
				
				targetState = tensor(gs,gs)
			
				rotation = tensor(roty(math.pi/2.),roty(math.pi/2.))
			
				targetRho = adjoint(targetState)*targetState
				targetRho = rotation*targetRho*adjoint(rotation)
				
				rhoBeforeSwap = targetRho.copy()
			
				driveSequence1.addPulse(qubit1.generateRabiPulse(f_sb = f_sb1,phase = math.pi/2.,angle = math.pi/2.0))
				driveSequence2.addPulse(qubit2.generateRabiPulse(f_sb = f_sb2,phase = math.pi/2.,angle = math.pi/2.0))
				
				maxLen = max(len(driveSequence1),len(driveSequence2))
				
				driveSequence1.addWait(maxLen-len(driveSequence1))
				driveSequence2.addWait(maxLen-len(driveSequence2))
			
			if step >= 2:
			
				#We apply the tag operator...
			
				fluxSequence1.addPulse(zPulse*fluxAnticrossing,position = driveSequence1.position())
				fluxSequence2.addWait(fluxSequence1.position()-fluxSequence2.position())
				
				fluxSequence1.addPulse(qubit1.generateZPulse(length = 6,gaussian = False)*alpha)
				fluxSequence2.addPulse(qubit2.generateZPulse(length = 6,gaussian = False)*beta)
			
				fluxSequence1.addWait(3)
				fluxSequence2.addWait(3)
			
				driveSequence1.addWait(fluxSequence1.position()-driveSequence1.position())
				driveSequence2.addWait(fluxSequence2.position()-driveSequence2.position())
			
				targetRho=swap*targetRho*adjoint(swap)
			
			if step >= 3:
			
				i = state
			
				signs = [[-1,-1],[1,-1],[-1,1],[1,1]]

				amps = [[-0.004,-0.013],[0.011,-0.016],[-0.004,0.008],[0.0105,0.006]]
				
				data.parameters()["signs"] = signs
				data.parameters()["amps"] = amps
				data.parameters()["state"] = i
							
				fluxSequence1.addPulse(qubit1.generateZPulse(length = 8,gaussian = False)*amps[i][0])
				fluxSequence2.addPulse(qubit2.generateZPulse(length = 8,gaussian = False)*amps[i][1])
			
				driveSequence1.addWait(fluxSequence1.position()-driveSequence1.position())
				driveSequence2.addWait(fluxSequence2.position()-driveSequence2.position())
				
				rotation = tensor(rotz(signs[i][0]*math.pi/2.),rotz(signs[i][1]*math.pi/2.))
				
				targetRho=rotation*targetRho*adjoint(rotation)
			
			if step >= 4:
			
				fluxSequence1.addPulse(zPulse*fluxAnticrossing,position = driveSequence1.position())
				fluxSequence2.addWait(fluxSequence1.position()-fluxSequence2.position())
				
				fluxSequence1.addPulse(qubit1.generateZPulse(length = 6,gaussian = False)*gamma)
				fluxSequence2.addPulse(qubit2.generateZPulse(length = 6,gaussian = False)*delta)
			
				driveSequence1.addWait(fluxSequence1.position()-driveSequence1.position())
				driveSequence2.addWait(fluxSequence2.position()-driveSequence2.position())
				
				targetRho=swap*targetRho*adjoint(swap)
			
			if step >= 5:
			
				driveSequence1.addPulse(qubit1.generateRabiPulse(f_sb = f_sb1,phase = math.pi/2.0,angle = 0,delay = driveSequence1.position()),position = 0)
				driveSequence2.addPulse(qubit2.generateRabiPulse(f_sb = f_sb2,phase = math.pi/2.0,angle = 0,delay = driveSequence2.position()),position = 0)
			
				rotation = tensor(rotx(math.pi/2.0),rotx(math.pi/2.0))
			
				targetRho=rotation*targetRho*adjoint(rotation)
			
			ro = 5000 + len(fluxSequence1)
			
			qubit1.loadFluxlineBaseWaveform(readout = ro)
			qubit2.loadFluxlineBaseWaveform(readout = ro)

			
			data.parameters()["driveSequence1"] = driveSequence1.getWaveform().tolist()
			data.parameters()["driveSequence2"] = driveSequence2.getWaveform().tolist()
			data.parameters()["fluxSequence1"] = fluxSequence1.getWaveform().tolist()
			data.parameters()["fluxSequence2"] = fluxSequence2.getWaveform().tolist()

			probs = measureTomography([driveSequence1,driveSequence2],[fluxSequence1,fluxSequence2],delay = 3,averaging = 40,use12Pulse = use12Pulse,onlyZZ = onlyZZ)
			probsZZ = measureTomography([driveSequence1,driveSequence2],[fluxSequence1,fluxSequence2],delay = 3,averaging = 40,use12Pulse = use12Pulse,onlyZZ = True)

			for key in probsZZ.keys():
				data.set(**{"zz"+key:probsZZ[key]})

			data.set(**probs)
			data.commit()

			if onlyZZ:
				continue			

			#Make a fit of the resulting density matrix
			
			rho = reconstructRho(data,row = 0)
			
			#rho = fitDensityMatrix(measuredSpins,measuredProbabilities,hot = False,row = None ,rounds = 10,initialGuess =rho)
			
			figure("rho")
			clf()
			cla()
			plotDensityMatrix(rho)
			show()
			
			print trace(rho)
			
			def transform(phases):
				return tensor(rotz(phases[0]/180.0*math.pi),rotz(phases[1]/180.0*math.pi))#*tensor(rotn(math.pi/2.0,[cos(phases[2]),sin(phases[2]),0]),rotn(math.pi/2.0,[cos(phases[3]),sin(phases[3]),0]))
			
			def errorFunction(phases,rho,targetRho):
				rotation = transform(phases)
				return 1.0-quantumFidelity(rotation*rho*adjoint(rotation),targetRho)
			
			ps = [0,0]
			
			p1s = scipy.optimize.fmin(errorFunction,ps,args = (rho,targetRho))
			
			print p1s
			
			figure("rhos")
			
			clf()
			
			subplot(131)
			cla()
			plotDensityMatrix(rho)
			
			subplot(132)
			cla()
			
			plotDensityMatrix(transform(p1s)*rho*adjoint(transform(p1s)))
			
			subplot(133)
			cla()
			plotDensityMatrix(targetRho)
			
			show()
			
			print "Corrected fidelity:",quantumFidelity(transform(p1s)*rho*adjoint(transform(p1s)),targetRho)
			print "Raw fidelity:",quantumFidelity(rho,targetRho)
			
			data.parameters()["experimentalRho"] = rho.tolist()
			data.parameters()["targetRho"] = targetRho.tolist()
			data.parameters()["fidelity"] = float(quantumFidelity(rho,targetRho))
finally:
	grover.savetxt()		
	

##Measure the entanglement witness Phi_psi on a rotating state by turning the measurement base of on qubit.

initSwapParameters()

duration = 32

import random

survey = Datacube("Entanglement witness survey")
dataManager.addDatacube(survey)

for d in [5]*20:

	data = Datacube("Entanglement witness measurement at %g ns, delay = %g ns" % (duration,d) )
	
	data.setParameters(instrumentManager.parameters())
	data.parameters()["defaultPlot"] = [("phi","zzp00"),("phi","zzp01"),("phi","zzp10"),("phi","zzp11")]
	survey.addChild(data)
	try:
		angles = arange(0,360.0,10.0)
#		angles = [120]*10000
		cnt = 0
#		random.shuffle(angles)
		for phi in angles:
			cnt += 1
			data.set(phi = phi)
			print "phi = %g" % phi
			probs = measureSwapSequence(swapDuration = duration,pulseHeight = fluxAnticrossing,delayBeforeTomography = d,measurements = ["xx","yy","zz"],averaging = 80,state = [[math.pi,0],[0,0]],piLength = piLength,tomographyLength = tomographyLength+5,xyRotation = phi/180.0*math.pi)
			cnt+=1
#			acqiris.bifurcationMap(ntimes = 80)
#			probs = acqiris.Psw()
			data.set(cnt = cnt)
			data.set(**probs)
			data.commit()
			calculateWs(data)
		survey.savetxt()
	finally:
		survey.savetxt()
##Measure the CHSH operator of an entangled state by turning the measurement base.
initSwapParameters()

#duration = 32
#state = [[math.pi/2.0,math.pi/2.0*0],[math.pi/2.0,math.pi/2.0*0]]
duration = 33
state = [[math.pi,0],[0,0]]
#fluxAnticrossing = 0.07
fluxAnticrossing = 0.0780

import random

survey = Datacube("CHSH survey")
dataManager.addDatacube(survey)

d = 10

tomographySurvey = survey

phi_max = 200

try:

	averages = [40]

	for n in averages:
	
		basis_rotation = 0

		data = Datacube("CHSH")
		
		data.setParameters(instrumentManager.parameters())
		data.parameters()["defaultPlot"] = [("phi","zzp00"),("phi","zzp01"),("phi","zzp10"),("phi","zzp11")]
		survey.addChild(data,rotation = basis_rotation)
		survey.set(basis_rotation = basis_rotation)
		survey.set(n = n)

		if False:

			#We measure several points of the CHSH curve to make a fit and determine the angle where phi takes it's maximum value...

			fitData = Datacube("Fit")
			fitData.setParameters(instrumentManager.parameters())
			data.addChild(fitData)
	
			for phi in arange(30+phi_max,phi_max+165,15):	
				measureCHSH(data = fitData,phi = phi,saveClicks = False,swapDuration = duration,pulseHeight = fluxAnticrossing,delayBeforeTomography = d,measurements = [],averaging = 80,state = state,piLength = piLength,tomographyLength = tomographyLength+5,use12Pulse=True)
			calculateCHSH(fitData)
	
			phi_max = fitData.children(name = "spins")[0].parameters()["chsh_fit"][1]*180.0/math.pi
	
			print phi_max

			angles = [90+phi_max]
			saveClicks = True
		else:
			angles = arange(0,360,20)	
			saveClicks = False

		for phi in angles:
			measureCHSH(data = data,phi = phi,saveClicks = saveClicks,swapDuration = duration,pulseHeight = fluxAnticrossing,delayBeforeTomography = d,measurements = [],averaging = int(n),state = state,piLength = piLength,tomographyLength = tomographyLength+5,use12Pulse=True)
		
		calculateCHSH(data)

		survey.set(time = time.time(),phase = data.children(name = "spins")[0].parameters()["chsh_fit"][1]*180.0/math.pi,chsh = mean(data.children(name = "spins")[0]["chsh"]))
		survey.commit()

		survey.savetxt()
finally:
	survey.savetxt()
