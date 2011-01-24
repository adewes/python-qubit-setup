##We create different qubit states and measure the switching probability of the JBA after applying I,Q pulses of different lengths (like in Steffen, PRL 97 050502 2006 http://www.physics.ucsb.edu/~martinisgroup/papers/Steffen2006.pdf)

name = "Qubit 2"
qubit = qubit2
variable = "px1"
##

name = "Qubit 1"
qubit = qubit1
variable = "px1"

##
reload(sys.modules["instruments.qubit"])
from instruments.qubit import *

data = Datacube("Rabi XY - %s" % name)
data.setParameters(instrumentManager.parameters())
dataManager.addDatacube(data)

margin1 = 3
margin2 = 3

f_sb = qubit.parameters()['pulses.xy.f_sb']
##

#State preparation...

qubit.setDriveFrequency(qubit.parameters()["frequencies.f01"]+f_sb)
qubit.setDriveAmplitude(I = qubit.parameters()["pulses.xy.drive_amplitude"],Q = qubit.parameters()["pulses.xy.drive_amplitude"])


readoutDelay = qubit.parameters()["timing.readout"]

times = arange(0,370,10)

m = zeros((len(times),len(times)))

rows = []
for i in range(0,len(data)):
	child = data.childrenAt(i)[0]
	if len(child) < 40:
		rows.append(i)
print "Removing %d rows" % len(rows)
data.removeRows(rows)

cnt_x = 0
cnt_y = 0

for i in range(0,len(data)):
	subcube = data.childrenAt(i)[0]
	print data.column("x")[i]
	for j in range(0,len(subcube)):
		m[i,j] = subcube.column(variable)[j]
		cnt_y = j
	cnt_x = i

timesX = SmartRange(times)
timesY = SmartRange(times)


figure("matrix")

clf()
cla()

imshow(m)

##Measurement

for x in timesX:
	cnt_y = 0
	subcube = Datacube("x angle = %g" % x)
	data.set(x = x)
	data.addChild(subcube)
	data.commit()
	timesY = SmartRange(times)
	for y in timesY:
		print x,y
		drive = PulseSequence()

		xLen = len(qubit.generateRabiPulse(phase = x/180.0*math.pi,angle = 0,f_sb = f_sb))
		yLen = len(qubit.generateRabiPulse(phase = y/180.0*math.pi,angle = math.pi/2.0-0.0/180.0*math.pi,f_sb = f_sb))

		drive.addPulse(qubit.generateRabiPulse(f_sb = f_sb, phase = x/180.0*math.pi,angle = 0,delay = readoutDelay-xLen-yLen))
		drive.addPulse(qubit.generateRabiPulse(f_sb = f_sb, phase = y/180.0*math.pi,angle = math.pi/2.0-0.0/180.0*math.pi,delay = readoutDelay-yLen))

		qubit.loadWaveform(drive.getWaveform(),readoutDelay)
	
		acqiris.bifurcationMap(ntimes  = 40)
		
		psw = acqiris.Psw()

		subcube.set(y = y)
		subcube.set(**psw)
		subcube.commit()
		
		m[cnt_x,cnt_y] = psw[variable]
	
		cnt_y+=1

	cla()
	imshow(m,extent = (times[0],times[-1],times[-1],times[0]),interpolation = 'nearest',vmin = 0,vmax = 1)
	data.savetxt()
	cnt_x+=1
##
clf()
imshow(m,extent = (times[0],times[-1],times[-1],times[0]),interpolation = 'nearest',vmin = 0,vmax = 1)
xlabel("x angle")
ylabel("y angle")
