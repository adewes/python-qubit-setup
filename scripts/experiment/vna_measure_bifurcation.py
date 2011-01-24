##Take the reference measurement...
vna1.setAttenuation(10)
vna1.setPower(-25)
vna1.waitFullSweep()
reference = vna1.getTrace()
attenuation = float(vna1.ask("SA1?"))
power = float(vna1.ask("PWR?"))
reference.setName("reference - %g dB attenuation - power %g dB" % (attenuation,power))
reference.savetxt()
##Measure the transmission at different power levels...
vna1.setAttenuation(0)
for power in arange(-10,1,0.25):
	vna1.setPower(power)
	vna1.waitFullSweep()
	trace = vna1.getTrace()
	trace.setName("power = %g dB" % (vna1.power()-vna1.attenuation()))
	trace.savetxt()	