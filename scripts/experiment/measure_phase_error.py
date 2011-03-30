

data = Datacube("Phase error survey")
dataManager.addDatacube(data)

cnt = 0

#Change these parameters to eliminate the phase error:
qubit1.parameters()["pulses.xy.f_shift"] = -0.003
qubit2.parameters()["pulses.xy.f_shift"] = 0.001*0

qubit1.loadFluxlineWaveform(qubit1.fluxlineBaseWaveform())
qubit2.loadFluxlineWaveform(qubit2.fluxlineBaseWaveform())

for i in [1]:
	cnt+=1
	
	for amplifyingPulses in range(0,1):
		subdata = Datacube()
		data.addChild(subdata)	
		data.set(cnt = cnt)
		data.set(phi = measurePhaseError(subdata,qubit2,amplifyingPulses = amplifyingPulses,hot = False,averaging = 80))
		data.commit()
		data.savetxt()

