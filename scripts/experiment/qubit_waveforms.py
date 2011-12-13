##Put fluxline and signal waveforms here. Waveforms that are used frequently should eventually be provided in a seperate class or through the instrument itself.
from config.startup import *
ro = 5000

offset = 0.2*0
qubit1.loadFluxlineBaseWaveform(parkFlux =0.65+offset,manipulationFlux = 0.65+offset,readoutFlux = 0.65+offset,readout = ro,compensationFactor = 0.,compensateResponse = False,readoutDelay = 0)

qubit2.loadFluxlineBaseWaveform(parkFlux =1.12,manipulationFlux = 1.12,readoutFlux = 1.12,readout = ro,compensationFactor = 0.,compensateResponse = False,readoutDelay = 0)

##Default working point:

offset = -0.	

qubit1.loadFluxlineBaseWaveform(parkFlux = 0.68,manipulationFlux = 1.17+offset,readoutFlux = 0.68,readout = ro,compensationFactor = 0.8,compensateResponse = True,readoutDelay = 0)
qubit2.loadFluxlineBaseWaveform(parkFlux =1.0,manipulationFlux = 1.56+offset,readoutFlux = 1.0,readout = ro,compensationFactor = 1.2,compensateResponse = True,readoutDelay = 0)

##Set vflux2 to constant 1.12V:
qubit2.loadFluxlineBaseWaveform(parkFlux =1.14,manipulationFlux = 1.12,readoutFlux = 1.14,readout = ro,compensationFactor = 1.2,compensateResponse = False,readoutDelay = 0)

##Default parking point at 0V:

qubit1.loadFluxlineBaseWaveform(parkFlux =0,manipulationFlux = 0,readoutFlux = 0,readout = 0,compensationFactor = 0.8,compensateResponse = False,readoutDelay = 0)
qubit2.loadFluxlineBaseWaveform(parkFlux =0,manipulationFlux = 0,readoutFlux = 0,readout = 0,compensationFactor = 1.2,compensateResponse = False,readoutDelay = 0)

##Record s curves:

qubit1.loadFluxlineBaseWaveform(parkFlux =1.56*0,manipulationFlux = 0.73,readoutFlux = 0.73,readout = ro,compensationFactor = 0.8,readoutDelay = 0)
qubit2.loadFluxlineBaseWaveform(parkFlux =1.56*0,manipulationFlux = 1.12,readoutFlux = 1.12,readout = ro,compensationFactor = 1.2,readoutDelay = 0)


##Testing of fluxline without qubits
loadBaseWaveform(qubit1,afg1,jba1,parkFlux =0,manipulationFlux = 0.0,readoutFlux = 0.0,readout = ro,compensationFactor = 0.8)
loadBaseWaveform(qubit2,afg2,jba2,parkFlux =0,manipulationFlux = 0.0,readoutFlux = 0.0,readout = ro,compensationFactor = 0.8)
##
from instruments.qubit import PulseSequence
instrumentManager.reloadInstrument("awg")
instrumentManager.reloadInstrument("awg2")
qubit1.reloadClass()
qubit2.reloadClass()
f1Seq = PulseSequence()
f1Seq.addPulse(qubit1.fluxlineBaseWaveform()*0.6)
waveform = zeros(qubit1.parameters()["timing.readout"])
waveform[qubit1.parameters()["timing.readout"]-20:qubit1.parameters()["timing.readout"]]+=0.2
f1Seq.addPulse(waveform,position = 0)
qubit1.loadFluxlineWaveform(f1Seq.getWaveform(),compensateResponse = False)
qubit1.loadRabiPulse(length = 20,delay = -10,f_sb = 0.00)
qubit2.loadRabiPulse(length = 20,delay = -10,f_sb = 0)

## 
figure("waveform")
cla()
print (1*((1 << 14) - 1)) & 0xFFFF
print numpy.array((numpy.array(qubit1.driveWaveform())+1.0)/2.0*((1 << 14)-1),dtype = int16)& 0xFFFF
plot(numpy.array((numpy.array(qubit1.driveWaveform())+1.0)/2.0*((1 << 14)-1),dtype = int16))
##
awg.writeRealData(numpy.zeros(1000),numpy.zeros(1000,dtype = numpy.uint8))
##
import ctypes
testform = zeros(1000,dtype = numpy.ushort)+1	
print testform.ctypes.data