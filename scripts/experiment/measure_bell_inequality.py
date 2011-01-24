#Measure a quantum swap between the two qubits and perform a tomography of the resulting states.
#Before you run this script, make sure that the Rabi pulses for both qubits are calibrated!

fluxAnticrossing = -0.4955

f_sb = 0.1

readout = min(qubit1.parameters()["timing.readout"],qubit2.parameters()["timing.readout"])

qb1BaseFlux = qubit1.fluxlineWaveform()
qb2BaseFlux = qubit2.fluxlineWaveform()

piLength = max(len(qubit1.generateRabiPulse(phase = math.pi,f_sb = f_sb)),len(qubit2.generateRabiPulse(phase = math.pi,f_sb = f_sb)))
tomographyLength = ceil(max(len(qubit1.generateRabiPulse(angle = -math.pi/2.0,phase = math.pi/2.0,f_sb = f_sb)),
len(qubit2.generateRabiPulse(angle = -math.pi/2.0,phase = math.pi/2.0,f_sb = f_sb))))
print "Length of tomgography pulse: %g" % tomographyLength
reload(sys.modules["instruments.qubit"])
from instruments.qubit import *

try:

	data = Datacube("Bell's inequality")

	data.setParameters(instrumentManager.parameters())

	dataManager.addDatacube(data)

	qubit1.pushState()
	qubit2.pushState()

	flux = fluxAnticrossing
	f = 1.7
	phi = 180.0

	i = 26
	qb1FluxSeq = PulseSequence()
	qb1FluxSeq.addPulse(qb1BaseFlux)
		
	zPulse = qubit1.generateZPulse(length = i)*(flux-qb1BaseFlux[1])
	zLen = len(zPulse)+14.0
	qb1FluxSeq.addPulse(zPulse,delay = readout-zLen-tomographyLength)
	
	if i != 0:
		qubit1.loadFluxlineWaveform(qb1FluxSeq.getWaveform(),factor = f)
	
	for alpha in arange(0,360.0,10.0):
		print alpha
		data.set(alpha = alpha)
		
		qb2Seq = PulseSequence()
		qb1Seq = PulseSequence()
			
		qb1Seq.addPulse(qubit1.generateRabiPulse(phase = math.pi,angle = math.pi/2.0,f_sb = f_sb,delay = readout-zLen-piLength-tomographyLength+2))	
#		qb2Seq.addPulse(qubit2.generateRabiPulse(phase = math.pi,angle = math.pi/2.0,f_sb = f_sb,delay = readout-zLen-piLength-tomographyLength))	
		
		
		qb1Seq.addPulse(qubit1.generateRabiPulse(phase = math.pi/2.0,angle = -float(alpha)/180.0*math.pi,delay = readout-tomographyLength,f_sb = f_sb))
#		qb2Seq.addPulse(qubit2.generateRabiPulse(angle = -math.pi/2.0,phase = math.pi/2.0,delay = readout-tomographyLength,f_sb = f_sb))
		qubit1.loadWaveform(qb1Seq.getWaveform(),readout = readout)
		qubit2.loadWaveform(qb2Seq.getWaveform(),readout = readout)

		acqiris.bifurcationMap(ntimes = 40)
		psw = acqiris.Psw()
		data.set(**psw)
		data.commit()

		data.savetxt()

finally:
	data.savetxt()
	print "Restoring state..."
	qubit1.popState()
	qubit2.popState()