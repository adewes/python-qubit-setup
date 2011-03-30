def testQubitSwitching(qubit,testLength = True):
	qubit.turnOnDrive()
	if testLength:
		phases = [0,math.pi/2.0,math.pi]
		print "Testing pulse length calibration:"
		phase_errors = []
		for phase in phases:
			qubit.loadRabiPulse(phase = phase,readout = qubit.parameters()["timing.readout"])
			psw = qubit.Psw(normalize = True,ntimes = 400)
			expected = (-cos(phase)+1.0)/2.0
			err = abs(psw-expected)
			phase_errors.append(err)
			print "P(Q1 = 1,phi = %g) = %.2f %% (exp. %.2f %%) error: %.2f %%" % (phase*180.0/math.pi,psw*100,expected*100,err*100.0)
		print "Average phase error: %g %%" % (mean(phase_errors)*100)

	print "Testing X-Y pulse sequences:"
	angles = [0,math.pi/2.0,-math.pi/2.0]
	for a1 in angles:
		for a2 in angles:
			seq = PulseSequence()
			seq.addPulse(qubit.generateRabiPulse(phase = math.pi/2.0,angle = a1,f_sb = qubit.parameters()["pulses.xy.f_sb"],sidebandDelay = seq.position()))
			seq.addPulse(qubit.generateRabiPulse(phase = math.pi/2.0,angle = a2,f_sb = qubit.parameters()["pulses.xy.f_sb"],sidebandDelay = seq.position()))
			qubit.loadWaveform(seq.getWaveform(endAt = qubit.parameters()["timing.readout"]),readout = qubit.parameters()["timing.readout"])
			if a1 == a2:
				expected = 1
			elif abs(a1-a2) == math.pi:
				expected = 0
			else:
				expected = 0.5
			time.sleep(2)
			psw = qubit.Psw(normalize = True,ntimes = 400)
			print "Pi/2(%g)-Pi/2(%g)\tp: %.2f %%,\terror: %.2f %%" % (a1*180.0/math.pi,a2*180.0/math.pi,psw*100.0,abs(expected-psw)*100)
		
print "Qubit 1:"
testQubitSwitching(qubit1,testLength = False)
print "Qubit 2:"
testQubitSwitching(qubit2,testLength = False)