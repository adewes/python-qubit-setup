ro=3000

qubit=qubit1
voltage=0.5
calibrate=True
try:
	#generating waveform
	waveform = zeros(ro+3000)-afg1.offset()/afg1.amplitude()*2
	waveform[1:-1] = voltage
	waveform[ro:-1] = 0.55
	qubit.parameters()["flux.readout"] = afg1.offset()+waveform[ro]*afg1.amplitude()/2.0
	qubit.parameters()["flux.park"] = afg1.offset()+waveform[0]*afg1.amplitude()/2.0
	qubit.parameters()["flux.manipulation"] = afg1.offset()+waveform[1]*afg1.amplitude()/2.0
	qubit.parameters()["timing.readout"] = ro
	qubit.loadFluxlineWaveform(waveform,compensateResponse = True,factor = 0.8	)
	print "waveform generated"
	if calibrate:
		jba1.calibrate()
finally:
	pass