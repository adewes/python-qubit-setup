#Measure a quantum swap between the two qubits and perform a tomography of the resulting states.
#Before you run this script, make sure that the Rabi pulses for both qubits are calibrated!

fluxAnticrossing = -0.0462

f_sb1 = qubit1.parameters()["pulses.xy.f_sb"]
f_sb2 = qubit2.parameters()["pulses.xy.f_sb"]

for qubit in [qubit1,qubit2]:
	qubit.setDriveFrequency(qubit.parameters()["frequencies.f01"]+qubit.parameters()["pulses.xy.f_shift"]+qubit.parameters()["pulses.xy.f_sb"])
	qubit.setDriveAmplitude(I = +qubit.parameters()["pulses.xy.drive_amplitude"],Q = +qubit.parameters()["pulses.xy.drive_amplitude"])

readout = max(qubit1.parameters()["timing.readout"],qubit2.parameters()["timing.readout"])

qb1BaseFlux = qubit1.fluxlineWaveform()
qb2BaseFlux = qubit2.fluxlineWaveform()

piLength = max(len(qubit1.generateRabiPulse(phase = math.pi,f_sb = f_sb1)),len(qubit2.generateRabiPulse(phase = math.pi,f_sb = f_sb2)))
#pi12Length = max(len(qubit1.generateRabiPulse(length = qubit1.parameters()["pulses.xy.t_pi12"],f_sb = f_sb)),len(qubit2.generateRabiPulse(length = qubit2.parameters()["pulses.xy.t_pi12"],f_sb = f_sb)))*0
pi12Length = 0
tomographyLength = ceil(max(len(qubit1.generateRabiPulse(angle = -math.pi/2.0,phase = math.pi,f_sb = f_sb1)),
len(qubit2.generateRabiPulse(angle = -math.pi/2.0,phase = math.pi,f_sb = f_sb2))))+pi12Length

print "Length of tomgography pulse: %g" % tomographyLength
reload(sys.modules["instruments.qubit"])
from instruments.qubit import *

allData = Datacube("Bell inequality violation")
allData.setParameters(instrumentManager.parameters())
dataManager.addDatacube(allData)

try:

	qubit1.pushState()
	qubit2.pushState()

	for i in [31]:



		qb1BaseFlux = loadBaseWaveform(qubit1,afg1,jba1,parkFlux =0,manipulationFlux = 1.08,readoutFlux = 0.7,readout = ro,send=False)
		qb2BaseFlux = loadBaseWaveform(qubit2,afg2,jba2,parkFlux =0,manipulationFlux = 1.26,readoutFlux = 1.0,readout = ro,send=False)

		angles = [0,0,math.pi/2.0,0]
		phases = [0,math.pi/2.0,math.pi/2.0,math.pi]	
	
		states = zip(phases,angles)
	
#		allStates = generateCombinations(states,lambda x,y:[x,y],2)

		allStates = [[[math.pi,0],[0,0]]]
	
		globalData = Datacube("Quantum Tomography : Swap time = %g ns" % i)
		
		globalData.setParameters(instrumentManager.parameters())

		allData.set(duration = i)		
		allData.addChild(globalData)
		allData.commit()
		allData.savetxt()
			
		for state in allStates:
	
			data = Datacube("State %g,%g,%g,%g" % (state[0][0]*180.0/math.pi,state[0][1]*180.0/math.pi,state[1][0]*180.0/math.pi,state[1][1]*180.0/math.pi))
			globalData.addChild(data)
			globalData.savetxt()

			data.setParameters(instrumentManager.parameters())
			
			print state
		
		#	qubit2.loadFluxlineWaveform(qubit2.fluxlineWaveform(),compensateResponse = False)
		
		#	measurements = ["x","y","z","mx","my","mz"]
#			measurements = ["x","y","z"]
		#	measurements = ["x","y"]
		#	measurements = ["z"]
			measurements1 = ["x","z"]
			measurements2 = ["s","t"]
			flux = fluxAnticrossing
			f = 0.8
		#Uncomment this to optimize the height of the fluxline pulse at a given time index i.
			phi = 180.0
			alpha = 0
			averaging = 200
			last_i = -1
			psi = 0
			optimizeFlux = False
#			data.setName(data.name()+" - flux optimization")
#			optimizeFlux = True
#			for flux in arange(-0.03,-0.1,-0.0005):	
#				data.set(flux = flux)
#				i = 52
			for waitingtime in [1]:
				for phi in arange(-math.pi,math.pi,0.2):
					delay = 0
					data.set(duration = waitingtime)
					qb1FluxSeq = PulseSequence()
			
					qb1FluxSeq.addPulse(qb1BaseFlux)
						
					zPulse = qubit1.generateZPulse(length = i,gaussian = True)*flux
	#				zPulse2 = qubit1.generateZPulse(length = delay,gaussian = False)
					zLen = len(zPulse)+delay+piLength*0
					qb1FluxSeq.addPulse(zPulse,delay = readout-zLen-tomographyLength,position = 0)
	#				qb1FluxSeq.addPulse(zPulse2*0.01,delay = readout-len(zPulse2)-tomographyLength,position = 0)
					
					if i != 0 and last_i != i or optimizeFlux or True:
			#		if i != 0:
						qubit1.loadFluxlineWaveform(qb1FluxSeq.getWaveform(),factor = f)
            qubit2.loadFluxlineWaveform(qb2FluxSeq.getWaveform(),factor = f)
						last_i = i
							
					for x in measurements1:
						for y in measurements2:
						 
							print "Measuring along %s%s" % (x,y)
			
							qb2Seq = PulseSequence()
							qb1Seq = PulseSequence()
			
	#						qb2Seq.addPulse(qubit2.generateRabiPulse(phase = math.pi,angle = math.pi/2.0,f_sb = f_sb1,delay = readout-tomographyLength-piLength-delay),position = 0)	
			
							qb1Seq.addPulse(qubit1.generateRabiPulse(phase = state[0][0],angle = state[0][1],f_sb = f_sb1,delay = readout-zLen-piLength-tomographyLength),position = 0)	
							qb2Seq.addPulse(qubit2.generateRabiPulse(phase = state[1][0],angle = state[1][1],f_sb = f_sb2,delay = readout-zLen-piLength-tomographyLength),position = 0)	
							
							phasex = 0
							phasey = 0
			
							#We measure not only along X,Y,Z but also along -X,-Y,-Z in order to gain some additional/redundant information
							
							if x[0] == "m":
								phasex = math.pi
							if y[0] == "m":
								phasey = math.pi
			
							phasey+=psi
					
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
	
							if y == "t" or y == "mt":
								#We add a Pi/2 - phi rotation around Y to measure along T
								qb2Seq.addPulse(qubit2.generateRabiPulse(angle = phi-math.pi/2.0+phasey,phase = math.pi/2.0,delay = readout-tomographyLength,f_sb = f_sb2),position = 0)
							elif y == "s" or y == "ms":
								#We add a Pi-phi rotation around Y to measure along S
								qb2Seq.addPulse(qubit2.generateRabiPulse(angle = phi-math.pi,phase = math.pi/2.0,delay = readout-tomographyLength,f_sb = f_sb2),position = 0)
	
							qubit1.loadWaveform(qb1Seq.getWaveform(),readout = readout)
							qubit2.loadWaveform(qb2Seq.getWaveform(),readout = readout)
						
							acqiris.bifurcationMap(ntimes = averaging)
							psw = acqiris.Psw()
			
							npsw = dict()
							for key in psw.keys():
								npsw[x+y+key] = psw[key]
							data.set(**npsw)
							data.set(phi=phi)
	
	
	
	
							#delta_f_12 = -qubit2.parameters()["frequencies.f02"]+2*qubit2.parameters()["frequencies.f01"]
			
							#qb2Seq.addPulse(qubit2.generateRabiPulse(length = qubit2.parameters()["pulses.xy.t_pi12"],delay = readout-pi12Length,f_sb = f_sb+delta_f_12))
			
							#delta_f_12 = -qubit1.parameters()["frequencies.f02"]+2*qubit1.parameters()["frequencies.f01"]
			
							#qb1Seq.addPulse(qubit1.generateRabiPulse(length = qubit1.parameters()["pulses.xy.t_pi12"],delay = readout-pi12Length,f_sb = f_sb+delta_f_12))
							
	
				
					data.commit()
			
					data.savetxt()
		
finally:
	data.savetxt()
	print "Restoring state..."
	qubit1.popState()
	qubit2.popState()


## 
BelltomographyData=data

(measuredSpins,measuredProbabilities) = convertDatacubeToSpins(BelltomographyData,saveValues = True,deleteOldData = False,useDetectorMatrix=False,indices1=["x","z"],indices2=["s","t"])
##

for i in range(0,len(measuredSpins)):
	chsh=measuredSpins.column("xs")[i]+measuredSpins.column("zs")[i]+measuredSpins.column("zt")[i]-measuredSpins.column("xt")[i]
	measuredSpins.setAt(i,CHSH=chsh)

