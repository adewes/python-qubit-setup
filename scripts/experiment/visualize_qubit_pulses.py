figure("qubit pulses")
clf()
xmax = max(len(qubit1.fluxlineWaveform()),len(qubit2.fluxlineWaveform()))
cla()

#Qubit 1

ax1 = subplot(411)
plot(real(qubit1.driveWaveform()))
plot(imag(qubit1.driveWaveform()))
xlim(0,xmax)
axvline(qubit1.readoutDelay(),ls = "-.")

legend(("Q1 I","Q1 Q"))

#Qubit 2
		
subplot(412,sharex = ax1)
plot(real(qubit2.driveWaveform()))
plot(imag(qubit2.driveWaveform()))
axvline(qubit2.readoutDelay(),ls = "-.")

legend(("Q2 I","Q2 Q"))

#Fluxline

subplot(413,sharex = ax1)
plot(array(qubit1.fluxlineWaveform())*awg2.amplitude(1)/2.0+awg2.offset(1))
plot(array(qubit2.fluxlineWaveform())*awg2.amplitude(2)/2.0+awg2.offset(2))
axvline(qubit1.readoutDelay(),ls = "-.")
axvline(qubit2.readoutDelay(),ls = "-.")

ylabel("voltage [V]")

legend(("Q1","Q2"))

#Readout

subplot(414,sharex = ax1)

delay = acqiris.parameters()["delayTime"]*1e9
numberOfPoints = acqiris.parameters()["numberOfPoints"]
sampleInterval = acqiris.parameters()["sampleInterval"]*1e9

plot(linspace(qubit1.readoutDelay(),qubit1.readoutDelay()+len(jba1.readoutWaveform())/2.0,len(jba1.readoutWaveform())),array(jba1.readoutWaveform()))
plot(linspace(qubit2.readoutDelay(),qubit2.readoutDelay()+len(jba2.readoutWaveform())/2.0,len(jba2.readoutWaveform())),array(jba2.readoutWaveform()))
axvline(qubit1.readoutDelay()+delay)
axvline(qubit1.readoutDelay()+delay+numberOfPoints*sampleInterval)



xlabel("time [ns]")

legend(("Q1","Q2"))
