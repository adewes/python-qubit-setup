#Measure a quantum swap between the two qubits and perform a tomography of the resulting states.
#Before you run this script, make sure that the Rabi pulses for both qubits are calibrated!

fluxAnticrossing = 0.5021

f_sb = -0.1

readout = min(qubit1.parameters()["timing.readout"],qubit2.parameters()["timing.readout"])

qb1BaseFlux = qubit1.fluxlineWaveform()
qb2BaseFlux = qubit1.fluxlineWaveform()

piLength = max(len(qubit1.generateRabiPulse(phase = math.pi,f_sb = f_sb)),len(qubit2.generateRabiPulse(phase = math.pi,f_sb = f_sb)))
pi12Length = max(len(qubit1.generateRabiPulse(length = qubit1.parameters()['pulses.xy.t_pi'],gaussian = True,f_sb = f_sb)),len(qubit2.generateRabiPulse(length = qubit2.parameters()['pulses.xy.t_pi'],gaussian = True,f_sb = f_sb)))
tomographyLength = ceil(max(len(qubit1.generateRabiPulse(angle = -math.pi/2.0,phase = math.pi/2.0,f_sb = f_sb)),
len(qubit2.generateRabiPulse(angle = -math.pi/2.0,phase = math.pi/2.0,f_sb = f_sb))))+pi12Length

print "Length of tomgography pulse: %g" % tomographyLength
reload(sys.modules["instruments.qubit"])
from instruments.qubit import *

try:

	data = Datacube("Qubit Anticrossing")

	data.setParameters(instrumentManager.parameters())

	dataManager.addDatacube(data)

	qubit1.pushState()
	qubit2.pushState()

#	qubit2.loadFluxlineWaveform(qubit2.fluxlineWaveform(),compensateResponse = False)

#	measurements = ["x","y","z","mx","my","mz"]
#	measurements = ["x","y","z","mx","my"]
#	measurements = ["x","y","z"]
	measurements = ["z"]
	flux = fluxAnticrossing
	f = 0.8
#Uncomment this to optimize the height of the fluxline pulse at a given time index i.
	phi = 180.0
	alpha = 0
#	for flux in arange(0.500,0.508,0.0005):	
#		data.set(flux = flux)
#		i = 52
#	for f in arange(0.0,2.5,0.1):
#		data.set(factor = f)
#		i = 52
#	for fl in arange(-0.4,0.4,0.01):
#		data.set(fl = fl)
#		i = 10
#	for d in arange(0,30,1):
#		data.set(delay = d)
#		i = 52
#	for phi in arange(170,200,1.0):
#		data.set(phi = phi)
#		i = 52
#	for alpha in arange(0,360,1.0):
#		i = 26
#		data.set(alpha = alpha)
	for i in arange(0,800.0,2.0):
		data.set(duration = i)
		qb1FluxSeq = PulseSequence()

		qb1FluxSeq.addPulse(qb1BaseFlux)
			
		zPulse = qubit1.generateZPulse(length = i)*(flux-qb1BaseFlux[1])
		zLen = len(zPulse)+15.0
		qb1FluxSeq.addPulse(zPulse,delay = readout-zLen-tomographyLength)
		
		if i != 0:
			qubit1.loadFluxlineWaveform(qb1FluxSeq.getWaveform(),factor = f)
				
		for x in measurements:
			for y in measurements:
			
				print "Measuring along %s%s" % (x,y)

				qb2Seq = PulseSequence()
				qb1Seq = PulseSequence()

				qb1Seq.addPulse(qubit1.generateRabiPulse(phase = math.pi,angle = math.pi/2.0+float(alpha)/180.0*math.pi,f_sb = f_sb,delay = readout-zLen-piLength-tomographyLength+2))	
#				qb2Seq.addPulse(qubit2.generateRabiPulse(phase = math.pi/2.0,angle = math.pi/2.0*0,f_sb = f_sb,delay = readout-zLen-piLength-tomographyLength))	
				
				phasex = 0
				phasey = 0

				#We measure not only along X,Y,Z but also along -X,-Y,-Z in order to gain some additional/redundant information
				
				if x[0] == "m":
					phasex = math.pi
				if y[0] == "m":
					phasey = math.pi
		
				if x == "x" or x == "mx":
					#We add a Pi/2 rotation around Y to measure along X	
					qb1Seq.addPulse(qubit1.generateRabiPulse(angle = -math.pi/2.0+phasex,phase = math.pi/2.0,delay = readout-tomographyLength,f_sb = f_sb))
				elif x == "y" or x == "my":
					#We add a -Pi/2 rotation around X to measure along Y
					qb1Seq.addPulse(qubit1.generateRabiPulse(angle = phasex,phase = math.pi/2.0,delay = readout-tomographyLength,f_sb = f_sb))
				elif x == "mz":
					qb1Seq.addPulse(qubit1.generateRabiPulse(angle = 0,phase = math.pi,delay = readout-tomographyLength,f_sb = f_sb))

				if y == "x" or y == "my":
					#We add a Pi/2 rotation around Y to measure along X
					qb2Seq.addPulse(qubit2.generateRabiPulse(angle = -math.pi/2.0+phasey,phase = math.pi/2.0,delay = readout-tomographyLength,f_sb = f_sb))
				elif y == "y" or y == "my":
					#We add a -Pi/2 rotation around X to measure along Y
					qb2Seq.addPulse(qubit2.generateRabiPulse(angle = phasey,phase = math.pi/2.0,delay = readout-tomographyLength,f_sb = f_sb))
				elif y == "mz":
					qb2Seq.addPulse(qubit2.generateRabiPulse(angle = 0,phase = math.pi,delay = readout-tomographyLength,f_sb = f_sb))
				
				delta_f_12 = -qubit2.parameters()["frequencies.f02"]+2*qubit2.parameters()["frequencies.f01"]

				qb2Seq.addPulse(qubit2.generateRabiPulse(angle = 0,phase = math.pi,delay = readout-pi12Length,f_sb = f_sb+delta_f_12))

				delta_f_12 = -qubit1.parameters()["frequencies.f02"]+2*qubit1.parameters()["frequencies.f01"]

				qb1Seq.addPulse(qubit1.generateRabiPulse(angle = 0,phase = math.pi,delay = readout-pi12Length,f_sb = f_sb+delta_f_12))
				
				qubit1.loadWaveform(qb1Seq.getWaveform(),readout = readout)
				qubit2.loadWaveform(qb2Seq.getWaveform(),readout = readout)
	
				acqiris.bifurcationMap(ntimes = 300)

				psw = acqiris.Psw()

				npsw = dict()

				for key in psw.keys():
					npsw[x+y+key] = psw[key]
		
				data.set(**npsw)

				data.set()

		data.commit()

		data.savetxt()

finally:
	data.savetxt()
	print "Restoring state..."
	qubit1.popState()
	qubit2.popState()