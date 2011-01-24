##We create different qubit states and measure the switching probability of the JBA after applying I,Q pulses of different lengths (like in Steffen, PRL 97 050502 2006 http://www.physics.ucsb.edu/~martinisgroup/papers/Steffen2006.pdf)

import time
time.sleep(60*10)

name = "Qubit 1"
qubit = qubit1
var = "p1x"

reload(sys.modules["instruments.qubit"])
from instruments.qubit import *

waveform = zeros(6000)
waveform[1:-1] = 0.8

data = Datacube("IQ tomography - %s" % name)
data.setParameters(instrumentManager.parameters())
dataManager.addDatacube(data)
delay = 3000

margin1 = 3
margin2 = 3

f_sb = -0.12

#State preparation...

qubit2.setDriveFrequency(qubit.parameters()["frequencies.f01"]+f_sb)
qubit2.setDriveAmplitude(I = qubit.parameters()["pulses.xy.drive_amplitude"],Q = qubit.parameters()["pulses.xy.drive_amplitude"])

#State |0> (we do nothing :)

#State |1>

#preparation.addPulse(qubit2.generateRabiPulse(phase = math.pi,f_sb = f_sb,delay = delay,angle = 0))

#State |0>+|1>
#preparation.addPulse(qubit2.generateRabiPulse(phase = math.pi/2.0,f_sb = f_sb,delay = delay,angle = 0))

#State |0>+i*|1>

preparationPulse = qubit.generateRabiPulse(angle = math.pi/2.0,phase = math.pi/2.0,f_sb = f_sb,delay = 0)

tomographyPulse = qubit.generateRabiPulse(length = 70,f_sb = f_sb,delay = len(preparationPulse)+1,angle = 0)*0.5

readoutDelay = qubit.parameters()["timing.readout"]-len(tomographyPulse)

#delta_f_12 = -qubit.parameters()["frequencies.f02"]+2*qubit.parameters()["frequencies.f01"]

Ivalues = linspace(-1,1,200)
Qvalues = linspace(-1,1,200)

matrix= zeros((len(Ivalues),len(Qvalues)))

#...and measurement:

figure("matrix")

clf()
cla()

imshow(matrix)

x = 0	
for I in Ivalues:
	y = 0
	for Q in Qvalues:
		drive = PulseSequence()

		drive.addPulse(preparationPulse,delay = readoutDelay)

		drive.addPulse(tomographyPulse*(I+1j*Q),delay =readoutDelay)

		qubit.loadWaveform(drive.getWaveform(),len(drive)+1)
	
		acqiris.bifurcationMap(ntimes  = 50)
		
		psw = acqiris.Psw()

		data.set(**psw)
		data.set(I = I,Q = Q)
		data.commit()
		data.savetxt()
		
		matrix[x,y] = psw[var]
	
		y+=1

	imshow(matrix)
	x+=1
##
clf()
imshow(matrix,extent = (-1,1,-1,1),interpolation = 'nearest')
xlabel("I quadrature amplitude")
ylabel("Q quadrature amplitude")
