#Measure a quantum swap between the two qubits and perform a tomography of the resulting states.
#Before you run this script, make sure that the Rabi pulses for both qubits are calibrated!
import sys
from instruments import *
importModule("scripts.state_tomography.state_simulation")
from config.startup import *


def measureSwapSequence(swapDuration = 0,pulseHeight = 0,delayBeforeTomography = 0,measurements = ["zz"],averaging = 100,state = [[0,0],[math.pi,0]],piLength = 0,tomographyLength = 0,tomographyDelay = 0,xyRotation = 0,measurementRotations = None,use12Pulse = False):

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

	zPulse = qubit1.generateZPulse(length = swapDuration,gaussian = False)*pulseHeight
	zLen = len(zPulse)+delayBeforeTomography
	qb1FluxSeq.addPulse(zPulse,delay = ro1-zLen-tomographyLength,position = 0)

	qubit1.loadFluxlineWaveform(qb1FluxSeq.getWaveform(),factor = qubit1.parameters()["flux.compensationFactor"])
	qubit2.loadFluxlineWaveform(qb2FluxSeq.getWaveform(),factor = qubit2.parameters()["flux.compensationFactor"])
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
				if y == "x" or y == "mx":
					#We add a Pi/2 rotation around Y to measure along X
					qb2Seq.addPulse(qubit2.generateRabiPulse(angle = -math.pi/2.0+phasey,phase = math.pi/2.0,delay = readout-tomographyLength+tomographyDelay,f_sb = f_sb2),position = 0)
				elif y == "y" or y == "my":
					#We add a -Pi/2 rotation around X to measure along Y
					qb2Seq.addPulse(qubit2.generateRabiPulse(angle = phasey,phase = math.pi/2.0,delay = readout-tomographyLength+tomographyDelay,f_sb = f_sb2),position = 0)
				elif y == "mz":
					qb2Seq.addPulse(qubit2.generateRabiPulse(angle = 0,phase = math.pi,delay = readout-tomographyLength+tomographyDelay,f_sb = f_sb2),position = 0)
				
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
	for flux in arange(0.05,0.16,0.001):
		data.set(flux = flux)
		probs = measureSwapSequence(swapDuration = 60,pulseHeight = flux,delayBeforeTomography = 2,measurements = ["zz"],averaging = 40,state = [[math.pi,0],[0,0]],piLength = piLength,tomographyLength = tomographyLength*0,use12Pulse = False)
		data.set(**probs)
		data.commit()
finally:
	data.savetxt()

##Optimize the fluxline compensation factor
initSwapParameters()

fluxAnticrossing = 0.0590

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
	data.savetxt()

##Measure the SWAP as a function of the duration
initSwapParameters()

fluxAnticrossing = 0.0780
data = Datacube("Quantum Swap vs duration")

data.setParameters(instrumentManager.parameters())
data.parameters()["defaultPlot"] = [("duration","zzp00"),("duration","zzp01"),("duration","zzp10"),("duration","zzp11")]
dataManager.addDatacube(data)
try:
	durations = arange(0,800,4)
	cnt = 0
	for duration in durations:
		data.set(duration = duration,cnt = cnt)
		cnt += 1
		probs = measureSwapSequence(swapDuration = duration,pulseHeight = fluxAnticrossing,delayBeforeTomography = 5,measurements = ["zz"],averaging = 80,state = [[math.pi,0],[0,0]],piLength = piLength,tomographyLength = tomographyLength*0,use12Pulse = True)
		data.set(**probs)
		data.commit()
finally:
	data.savetxt()

##Measure one point of the SWAP
initSwapParameters()

duration = 33
state = [[math.pi,0],[0,0]]
data = Datacube("Quantum Swap at %g ns" % duration )
phi = 0

data.setParameters(instrumentManager.parameters())
data.parameters()["defaultPlot"] = [("index","zzp00"),("index","zzp01"),("index","zzp10"),("index","zzp11")]
dataManager.addDatacube(data)

global tomographyData
tomographyData = data

for d in [0]*40:
	try:
		data.set(d = d,duration = duration)
		

	#	probs = measureSwapSequence(swapDuration = duration,pulseHeight = fluxAnticrossing,delayBeforeTomography = d,measurements = [],averaging = int(n),state = state,piLength = piLength,tomographyLength = tomographyLength+5,measurementRotations = rotations[i])



		probs = measureSwapSequence(swapDuration = duration,pulseHeight = fluxAnticrossing,delayBeforeTomography = 2,measurements = generateCombinations(["x","y","z"],lambda x,y:x+y,2),averaging = 80,state = state,use12Pulse = True,piLength = piLength,tomographyLength = tomographyLength+5,xyRotation = phi/180.0*math.pi)
		data.set(**probs)
		data.commit()
	finally:
		data.savetxt()

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
