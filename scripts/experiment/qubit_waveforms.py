##Put fluxline and signal waveforms here. Waveforms that are used frequently should eventually be provided in a seperate class or through the instrument itself.
#Fluxline waveform for reducing the heating of the cryostat during the measurement.

ro = 3000 #readout time

def loadBaseWaveform(qubit = qubit1,afg = afg1,jba = jba1,parkFlux = 0,manipulationFlux = 0.0,readoutFlux = 0.0,readout = 2000,compensationFactor = 0.8):
	
	qubit.parameters()["flux.park"] = parkFlux
	qubit.parameters()["flux.manipulation"] = manipulationFlux
	qubit.parameters()["flux.readout"] = readoutFlux
	qubit.parameters()["timing.readout"] = readout


	waveform = zeros(readout+3500)+(qubit.parameters()["flux.park"]-afg.offset())/afg.amplitude()*2.0
	waveform[1:-1] = (qubit.parameters()["flux.manipulation"]-afg.offset())/afg.amplitude()*2.0
	waveform[ro:-1] = (qubit.parameters()["flux.readout"]-afg.offset())/afg.amplitude()*2.0

	#jba1.loadReadoutWaveform(starkPulseLength = 20,starkPulseHeight = 1.0,starkPulseDelay = 0,scale = 0.5)
	qubit.loadFluxlineWaveform(waveform,compensateResponse = True,factor = compensationFactor	)
	jba.loadReadoutWaveform()
	

loadBaseWaveform(qubit1,afg1,jba1,parkFlux =0,manipulationFlux = 1.08,readoutFlux = 0.8,readout = ro)
loadBaseWaveform(qubit2,afg2,jba2,parkFlux =0,manipulationFlux = 0.0,readoutFlux = 0.0,readout = ro)
##
import yaml
print str(yaml.dump({"d":4,"test":[1,2,3]}))