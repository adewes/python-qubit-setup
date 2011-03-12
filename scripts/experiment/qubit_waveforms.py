##Put fluxline and signal waveforms here. Waveforms that are used frequently should eventually be provided in a seperate class or through the instrument itself.


ro = 8000

#Good values: 0.68,1.12

qubit1.loadFluxlineBaseWaveform(parkFlux =1.4*0,manipulationFlux = 1.16-0.03,readoutFlux = 0.68,readout = ro,compensationFactor = 0.8,readoutDelay = 0)
qubit2.loadFluxlineBaseWaveform(parkFlux =1.56*0,manipulationFlux = 1.65+0.03,readoutFlux = 1.125,readout = ro,compensationFactor = 1.2,readoutDelay = 0)

##Testing of fluxline without qubits
loadBaseWaveform(qubit1,afg1,jba1,parkFlux =0,manipulationFlux = 0.0,readoutFlux = 0.0,readout = ro,compensationFactor = 0.8)
loadBaseWaveform(qubit2,afg2,jba2,parkFlux =0,manipulationFlux = 0.0,readoutFlux = 0.0,readout = ro,compensationFactor = 0.8)

##
import re
for key in sorted(register.parameters().keys()):
	if re.match("^qubit",key):
		print key
		del register[key]
##stark pulse
jba1.loadReadoutWaveform(scale = 0.7,starkPulseLength = 1000,starkPulseHeight = 0.7,starkPulseDelay = 200)
##no stark pulse
jba2.loadReadoutWaveform(scale = 1.0)