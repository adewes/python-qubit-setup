data = Datacube("Qubit Readout Crosstalk")

data.setParameters(instrumentManager.parameters())
dataManager.addDatacube(data)

qubits = [qubit2,qubit1]

qubits[0].turnOnDrive()
qubits[0].loadRabiPulse(phase = math.pi)
qubits[1].loadRabiPulse(phase = math.pi)

qubit1.loadFluxlineBaseWaveform(readoutFlux = 0.65)
qubit2.loadFluxlineBaseWaveform(readoutFlux = 1.1)

for fl2 in arange(0.9,1.3,0.01):
	for mw in [False,True]:
		if mw == True:
			qubits[0].turnOnDrive()
			variable = "crosstalk_on"
			prefix = "1"
		else:
			qubits[0].turnOffDrive()
			prefix = "0"
			variable = "crosstalk_off"
		qubits[0].loadFluxlineBaseWaveform(readoutFlux = fl2)
		qubits[1].turnOnDrive()
		acqiris.bifurcationMap(ntimes = 80)
		psw_on = acqiris.Psw()
		data.set(fl2 = fl2)
		qubits[1].turnOffDrive()
		acqiris.bifurcationMap(ntimes = 80)
		psw_off = acqiris.Psw()
		data.set(**{variable : psw_on[qubits[0]._acqirisVariable]-psw_off[qubits[0]._acqirisVariable]})
		data.set(**dict(zip(map(lambda x:prefix+"1"+x,psw_on.keys()),psw_on.values())))
		data.set(**dict(zip(map(lambda x:prefix+"0"+x,psw_off.keys()),psw_off.values())))
	data.commit()