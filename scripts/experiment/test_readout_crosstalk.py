phases = [0,math.pi/2.0,math.pi]

#data = Datacube("Qubit Readout Crosstalk")
#data.setParameters(instrumentManager.parameters())
#dataManager.addDatac(data)

qubit1.turnOnDrive()
qubit2.turnOnDrive()

vars1 = dict()
vars2 = dict()

for phase in phases:
	vars1[phase] = []
	vars2[phase] = []

for phase1 in phases:
	for phase2 in phases:
		qubit1.loadRabiPulse(phase = phase1,readout = qubit1.parameters()["timing.readout"])
		qubit2.loadRabiPulse(phase = phase2,readout = qubit2.parameters()["timing.readout"])
		acqiris.bifurcationMap(ntimes = 200)
		print "phase 1:%3.3f\tphase 2:%3.3f\tQ1:%3.3f\tQ2:%3.3f" % (phase1*180.0/math.pi,phase2*180.0/math.pi,acqiris.Psw()["p1x"]*100,acqiris.Psw()["px1"]*100)
		vars1[phase1].append(acqiris.Psw()["p1x"])
		vars2[phase2].append(acqiris.Psw()["px1"])

for phase in phases:
	print "phase = %g" % phase
	print "Qubit 1 span: %g %%" % ((max(vars1[phase])-min(vars1[phase]))*100)
	print "Qubit 2 span: %g %%" % ((max(vars2[phase])-min(vars2[phase]))*100)
