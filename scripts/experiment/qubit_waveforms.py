##Put fluxline and signal waveforms here. Waveforms that are used frequently should eventually be provided in a seperate class or through the instrument itself.
#Fluxline waveform for reducing the heating of the cryostat during the measurement.

ro = 1000 #readout time

#Qubit I

waveform = zeros(ro+3000)-afg1.offset()/afg1.amplitude()*2
waveform[1:-1] = 0.61 #about 5.28 GHz
#waveform[1:-1] = 0.6 #about 5.46 GHz
#waveform[1:-1] = 0.55 #about 5.65 GHz
#waveform[1:-1] = 0.504 #about 5.8 GHz (qubits are coupled)
waveform[ro:-1] = 0.28 #qubit at 6.3 GHz (readout)
#waveform[ro:-1] = 0.7

qubit1.parameters()["flux.readout"] = afg1.offset()+waveform[ro]*afg1.amplitude()/2.0
qubit1.parameters()["flux.park"] = afg1.offset()+waveform[0]*afg1.amplitude()/2.0
qubit1.parameters()["flux.manipulation"] = afg1.offset()+waveform[1]*afg1.amplitude()/2.0
qubit1.parameters()["timing.readout"] = ro	

qubit1.loadFluxlineWaveform(waveform,compensateResponse = True,factor = 0.8)

#Qubit II

from numpy import *

waveform = zeros(ro+3000)-afg2.offset()/afg2.amplitude()*2
waveform[1:-1] = 0.65
waveform[ro:-1] = 0.52

qubit2.parameters()["flux.readout"] = afg2.offset()+waveform[ro]*afg2.amplitude()/2.0
qubit2.parameters()["flux.park"] = afg2.offset()+waveform[0]*afg2.amplitude()/2.0
qubit2.parameters()["flux.manipulation"] = afg2.offset()+waveform[1]*afg2.amplitude()/2.0
qubit2.parameters()["timing.readout"] = ro+10

qubit2.loadFluxlineWaveform(waveform,compensateResponse = False,factor = 0.8)
