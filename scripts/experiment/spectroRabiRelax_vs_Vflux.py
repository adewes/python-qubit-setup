# when using T1 precis : ro = 3000

importModule("scripts.experiment.measure")

vMin=0.9
fMin=6.5
aSpectroMin=0.05
aRabiMin=0.3
vMax=1.3
fMax=5.7
aSpectroMax=0.25
aRabiMax=1.2
vStep=0.01
voltageUp=list(arange(vMin,vMax,vStep))
voltageDown=[]
voltageDown.extend(voltageUp)
voltageDown.reverse()
voltages=voltageUp+voltageDown

from numpy import *

datafit = Datacube()
datafit.setParameters(instrumentManager.parameters())		
datafit.setName("Flux voltage dependance - %s" % qubit.name())
dataManager.addDatacube(datafit)

qubit=qubit2
jba2.loadReadoutWaveform()

try:
	i=0;
	iterator=1;
	while True:
		voltage=voltages[i]
		try:
			datafit.set(vflux=voltage)
			#generating waveform
			qubit.parameters()["flux.park"] = 0.0 # Volt
			qubit.parameters()["flux.manipulation"] = voltage
			qubit.parameters()["flux.readout"] = 1
			qubit.parameters()["timing.readout"] = ro # ns		
			from numpy import *		
			waveform = zeros(ro+3000)+(qubit.parameters()["flux.park"]-afg2.offset())/afg2.amplitude()*2.0	
			waveform[1:-1] = (qubit.parameters()["flux.manipulation"]-afg2.offset())/afg2.amplitude()*2.0
			waveform[ro:-1] = (qubit.parameters()["flux.readout"]-afg2.offset())/afg2.amplitude()*2.0
			qubit.loadFluxlineWaveform(waveform,compensateResponse = True,factor = 0.8	)
			print "waveform generated"
			jba2.calibrate()
			data_v=Datacube("vflux = %s" % voltage)
			datafit.addChild(data_v)
			# Spectro
			data_s=Datacube("spectro")
			data_v.addChild(data_s)
			fCenter=fMin+(fMax-fMin)/(vMax-vMin)*(voltage-vMin)
			fSpan=0.4
			fStep=0.005
			freqs = arange(fCenter-fSpan/2,fCenter+fSpan/2,fStep)
			amp=aSpectroMin+(aSpectroMax-aSpectroMin)/(vMax-vMin)*(voltage-vMin)
			scripts.experiment.measure.spectroscopy(qubit = qubit,frequencies = freqs,variable = "px1",data = data_s,ntimes = 20,amplitude = amp,measureAtReadout = False,measure20 = False)
			f01=qubit.parameters()["frequencies.f01"]
			datafit.set(f01=f01)
			print "Spectro done - f01=",f01,"GHz"	
			# Rabi
			data_r=Datacube("rabi")
			data_v.addChild(data_r)
			durations = arange(0,20,0.5)
			amp=aRabiMin+(aRabiMax-aRabiMin)/(vMax-vMin)*(voltage-vMin)
			f_sb = -0.1
			scripts.experiment.measure.rabi(qubit = qubit,durations = durations,variable = "px1",data = data_r,amplitude = amp,f_sb = f_sb,averaging = 20)
			fR1=1/(2*qubit.parameters()["pulses.xy.t_pi"])*1000/amp;
			datafit.set(fR1=fR1)
			print "Rabi done - fR1=",fR1,"MHz at drive amplitude = 1"
			# Relaxation
			data_t=Datacube("Gamma1")
			data_v.addChild(data_t)
			delays = list(arange(0,100,3))+list(arange(100,900,10))
			scripts.experiment.measure.T1precis(qubit = qubit,delays = delays,variable = "px1",data = data_t)
			gamma1=(1/qubit.parameters()["relaxation.t1"])*1000
			datafit.set(gamma1=gamma1,t1 = qubit.parameters()["relaxation.t1"])
			print "T1 done - 1/T1=",gamma1,"MHz"		
			datafit.commit()
			datafit.savetxt()
		finally:
			pass
		i+=iterator
		if (i==len(voltages)-1 or i==0):
			iterator=-iterator
finally:
	pass