##Parameters
qubit = qubit1
name = "Qubit 1"

waveform = zeros(6000)
waveform[1:-1] = -0.9
##
qubit = qubit2
name = "Qubit 2"

waveform = zeros(6000)
waveform[1:-1] = -0.9
##Before running this test sequence make sure that x/y/z pulses are properly calibrated!
reload(sys.modules["instruments.qubit"])
from instruments.qubit import *

data = Datacube("XYZ sequence - %s" % name)
data.setParameters(instrumentManager.parameters())
dataManager.addDatacube(data)
delay = 3000

margin1 = 3
margin2 = 3

f_sb = -0.12

try:

	qubit.pushState()

	qubit.setDriveFrequency(qubit.parameters()["frequencies.f01"]+f_sb)
	qubit.setDriveAmplitude(I = qubit.parameters()["pulses.xy.drive_amplitude"],Q = qubit.parameters()["pulses.xy.drive_amplitude"])

	rabiPulse1 = qubit.generateRabiPulse(phase = math.pi/2.0,f_sb = f_sb,delay = delay,angle = 0)

	#delta_f_12 = -qubit.parameters()["frequencies.f02"]+2*qubit.parameters()["frequencies.f01"]

	for phi in arange(0,500,2):
		fluxSequence = PulseSequence()
		fluxSequence.addPulse(waveform)
		zPulse = qubit.generateZPulse(length = phi)*0.02

		fluxSequence.addPulse(zPulse,len(rabiPulse1)+margin1)
		fluxWaveform = fluxSequence.getWaveform()
		qubit.loadFluxlineWaveform(fluxWaveform,compensateResponse = True)
		for i in ["z","y","x"]:

			driveSequence = PulseSequence()
			driveSequence.addPulse(rabiPulse1)

			#We're done with state preparation here... Now we add the tomography pulses:
			if i == "x":
				#We add a Pi/2 rotation around Y to measure along X
				driveSequence.addPulse(qubit.generateRabiPulse(angle = -math.pi/2.0,phase = math.pi/2.0,delay = len(driveSequence)+len(zPulse)+margin1+margin2,f_sb = f_sb))
				#We add a |1> -> |2> pulse to increase the readout contrast
				#driveSequence.addPulse(qubit.generateRabiPulse(angle = 0,phase = math.pi,delay = len(driveSequence)+5,f_sb = f_sb+delta_f_12))
			elif i == "y":
				#We add a -Pi/2 rotation around X to measure along Y
				driveSequence.addPulse(qubit.generateRabiPulse(angle = 0,phase = math.pi/2.0,delay = len(driveSequence)+len(zPulse)+margin1+margin2,f_sb = f_sb))
				#We add a |1> -> |2> pulse to increase the readout contrast
				#driveSequence.addPulse(qubit.generateRabiPulse(angle = 0,phase = math.pi,delay = len(driveSequence)+5,f_sb = f_sb+delta_f_12))
			elif i == "z":
				driveSequence.addPulse([0],len(driveSequence)+len(zPulse)+margin1+margin2)
			driveWaveform = driveSequence.getWaveform()
			qubit.loadWaveform(driveWaveform,len(driveWaveform)+1)
	
			acqiris.bifurcationMap(ntimes  = 100)
		
			psw = acqiris.Psw()

			npsw = dict()

			for key in psw.keys():
				npsw[i+key] = psw[key]
		
			data.set(**npsw)
		data.set(phi = phi)
		data.commit()
		data.savetxt()
except SystemExit:
	print "Exiting..."
	data.savetxt()
finally:
	print "Restoring qubit state..."
	qubit.popState()
##
figure("test")
cla()
f = lambda x: (-cos(x)*(1.0-0.5*cos(x/2))/2+1)
xs = arange(0,100,0.1)
plot(xs,f(xs))
##
figure("pulse")
subplot(211)
cla()
plot(real(qubit2.generateRabiPulse(length = 100,angle = 0,f_sb = 0.1)))
plot(real(qubit2.generateRabiPulse(length = 100,angle = math.pi/2,f_sb = 0.1)))
subplot(212)
cla()
plot(imag(qubit2.generateRabiPulse(length = 100,angle = 0,f_sb = 0.1)))
plot(imag(qubit2.generateRabiPulse(length = 100,angle = math.pi/2,f_sb = 0.1)))