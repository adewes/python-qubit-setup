#Measure a quantum swap between the two qubits and perform a tomography of the resulting states.
#Before you run this script, make sure that the Rabi pulses for both qubits are calibrated!

reload(sys.modules["instruments.qubit"])
from instruments.qubit import *

def measureSwapSequence(swapDuration = 0,pulseHeight = 0,delayBeforeTomography = 0,measurements = ["zz"],averaging = 100,state = [[0,0],[math.pi,0]],piLength = 0,tomographyLength = 0,xyRotation = 0):

	f_sb1 = qubit1.parameters()["pulses.xy.f_sb"]
	f_sb2 = qubit2.parameters()["pulses.xy.f_sb"]

#	print "Length of tomgography pulse: %g" % tomographyLength		
	
	qb1BaseFlux = qubit1.fluxlineBaseWaveform()
	qb2BaseFlux = qubit2.fluxlineBaseWaveform()
	qb1FluxSeq = PulseSequence()
	qb1FluxSeq.addPulse(qb1BaseFlux)
	qb2FluxSeq = PulseSequence()
	qb2FluxSeq.addPulse(qb2BaseFlux)
	
	ro1 = qubit1.parameters()["timing.readout"]
	ro2 = qubit2.parameters()["timing.readout"]

	readout = max(ro1,ro2)

	zPulse = qubit1.generateZPulse(length = swapDuration,gaussian = False)*pulseHeight
	zLen = len(zPulse)+delayBeforeTomography
	qb1FluxSeq.addPulse(zPulse,delay = ro1-zLen-tomographyLength,position = 0)

	qubit1.loadFluxlineWaveform(qb1FluxSeq.getWaveform(),factor = qubit1.parameters()["flux.compensationFactor"])
	qubit2.loadFluxlineWaveform(qb2FluxSeq.getWaveform(),factor = qubit2.parameters()["flux.compensationFactor"])
	npsw = dict()

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
				qb1Seq.addPulse(qubit1.generateRabiPulse(angle = -math.pi/2.0+phasex,phase = math.pi/2.0,delay = readout-tomographyLength,f_sb = f_sb1),position = 0)
			elif x == "y" or x == "my":
				#We add a -Pi/2 rotation around X to measure along Y
				qb1Seq.addPulse(qubit1.generateRabiPulse(angle = phasex,phase = math.pi/2.0,delay = readout-tomographyLength,f_sb = f_sb1),position = 0)
			elif x == "mz":
				qb1Seq.addPulse(qubit1.generateRabiPulse(angle = 0,phase = math.pi,delay = readout-tomographyLength,f_sb = f_sb1),position = 0)
			if y == "x" or y == "my":
				#We add a Pi/2 rotation around Y to measure along X
				qb2Seq.addPulse(qubit2.generateRabiPulse(angle = -math.pi/2.0+phasey,phase = math.pi/2.0,delay = readout-tomographyLength,f_sb = f_sb2),position = 0)
			elif y == "y" or y == "my":
				#We add a -Pi/2 rotation around X to measure along Y
				qb2Seq.addPulse(qubit2.generateRabiPulse(angle = phasey,phase = math.pi/2.0,delay = readout-tomographyLength,f_sb = f_sb2),position = 0)
			elif y == "mz":
				qb2Seq.addPulse(qubit2.generateRabiPulse(angle = 0,phase = math.pi,delay = readout-tomographyLength,f_sb = f_sb2),position = 0)

			qubit1.loadWaveform(qb1Seq.getWaveform(),readout = readout)
			qubit2.loadWaveform(qb2Seq.getWaveform(),readout = readout)

			time.sleep(1)

			acqiris.bifurcationMap(ntimes = averaging)

			psw = acqiris.Psw()
			for key in psw.keys():
				npsw[x+y+key] = psw[key]
	return npsw

##Parameter initialization...

f_sb1=qubit1.parameters()["pulses.xy.f_sb"]
f_sb2=qubit2.parameters()["pulses.xy.f_sb"]


for qubit in [qubit1,qubit2]:
	qubit.setDriveFrequency(qubit.parameters()["frequencies.f01"]+qubit.parameters()["pulses.xy.f_sb"])
	qubit.setDriveAmplitude(I = +qubit.parameters()["pulses.xy.drive_amplitude"],Q = +qubit.parameters()["pulses.xy.drive_amplitude"])

piLength = max(len(qubit1.generateRabiPulse(phase = math.pi,f_sb = f_sb1)),len(qubit2.generateRabiPulse(phase = math.pi,f_sb = f_sb2)))
tomographyLength = ceil(max(len(qubit1.generateRabiPulse(angle = -math.pi/2.0,phase = math.pi,f_sb = f_sb1)),len(qubit2.generateRabiPulse(angle = -math.pi/2.0,phase = math.pi,f_sb = f_sb2))))

##Optimize the height of the fluxline pulse

data = Datacube("Quantum Swap - Optimization of fluxline pulse height")

data.setParameters(instrumentManager.parameters())
data.parameters()["defaultPlot"] = [("flux","zzp1x"),("flux","zzpx1")]
dataManager.addDatacube(data)
try:
	for flux in arange(0.096,0.16,0.0005):
		data.set(flux = flux)
		probs = measureSwapSequence(swapDuration = 60,pulseHeight = flux,delayBeforeTomography = 10,measurements = ["zz"],averaging = 40,state = [[math.pi,0],[0,0]],piLength = piLength,tomographyLength = tomographyLength)
		data.set(**probs)
		data.commit()
finally:
	pass

##Optimize the fluxline compensation factor

fluxAnticrossing = 0.0852

data = Datacube("Quantum Swap - Optimization of fluxline compensation factor")

data.setParameters(instrumentManager.parameters())
data.parameters()["defaultPlot"] = [("f","zzp1x"),("f","zzpx1")]
dataManager.addDatacube(data)
try:
	for f in arange(0.,1.5,0.01):
		data.set(f = f)
		probs = measureSwapSequence(swapDuration = 57,pulseHeight = fluxAnticrossing,delayBeforeTomography = 0,measurements = ["z"],compensationFactor = f,averaging = 40,state = [[math.pi,0],[0,0]],piLength = piLength,tomographyLength = tomographyLength)
		data.set(**probs)
		data.commit()
finally:
	pass

##Measure the SWAP as a function of the duration

fluxAnticrossing = 0.101
data = Datacube("Quantum Swap vs duration")

data.setParameters(instrumentManager.parameters())
data.parameters()["defaultPlot"] = [("duration","zzp00"),("duration","zzp01"),("duration","zzp10"),("duration","zzp11")]
dataManager.addDatacube(data)
try:
	for duration in arange(0,800,4):
		data.set(duration = duration)
		probs = measureSwapSequence(swapDuration = duration,pulseHeight = fluxAnticrossing,delayBeforeTomography = 5,measurements = ["zz"],averaging = 40,state = [[math.pi,0],[0,0]],piLength = piLength,tomographyLength = tomographyLength*0)
		data.set(**probs)
		data.commit()
finally:
	data.savetxt()
	pass

##Measure one point of the SWAP
fluxAnticrossing= 0.101
duration = 33
data = Datacube("Quantum Swap at %g ns" % duration )
phi = 0

data.setParameters(instrumentManager.parameters())
data.parameters()["defaultPlot"] = [("index","zzp00"),("index","zzp01"),("index","zzp10"),("index","zzp11")]
dataManager.addDatacube(data)
try:
	for index in range(0,1000):
		data.set(index = index)
		data.set(phi = phi)
		probs = measureSwapSequence(swapDuration = duration,pulseHeight = fluxAnticrossing,delayBeforeTomography = 10,measurements = generateCombinations(["x","y","z"],lambda x,y:x+y,2),averaging = 40,state = [[math.pi,0],[0,0]],piLength = piLength,tomographyLength = tomographyLength,xyRotation = phi/180.0*math.pi)
		data.set(**probs)
		data.commit()
finally:
	pass

##Measure the entanglement witness Phi_psi on a rotating state by turning the measurement base of on qubit.

duration = 33

import random

for d in [5]:

	data = Datacube("Entanglement witness measurement at %g ns, delay = %g ns" % (duration,d) )
	
	data.setParameters(instrumentManager.parameters())
	data.parameters()["defaultPlot"] = [("phi","zzp00"),("phi","zzp01"),("phi","zzp10"),("phi","zzp11")]
	dataManager.addDatacube(data)
	try:
		angles = arange(0,360.0,2.0)
		random.shuffle(angles)
		for phi in angles:
			data.set(phi = phi)
			print "phi = %g" % phi
			probs = measureSwapSequence(swapDuration = duration,pulseHeight = fluxAnticrossing,delayBeforeTomography = d,measurements = ["xx","yy","zz"],averaging = 40,state = [[math.pi,0],[0,0]],piLength = piLength,tomographyLength = tomographyLength+5,xyRotation = phi/180.0*math.pi)
			data.set(**probs)
			data.commit()
	finally:
		pass
		data.savetxt()
	