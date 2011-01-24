#This script performs the optimization of the two IQ mixers, saves it and updates the corresponing filenames in the register. To run the script, execute one of the following blocks to choose qubit 1 or qubit 2. Make sure that the FSP is properly connected to the corresponding power measurement port. Execute all following blocks up to the test code to perform the offset and power calibration.
##Parameters for qubit 1
mwg = qubit1_mwg
qubit = qubit1
name = "qubit1"
channels = [1,2]
cavity1_mwg.turnOff()
##Parameters for qubit 2
mwg = qubit2_mwg
qubit = qubit2
name = "qubit2"
channels = [3,4]
cavity2_mwg.turnOff()
##Module and data initialization
import datetime
importModule("macros.iq_level_optimization")
optimizer = qubit._optimizer
optimizer.reloadClass()
dataManager.addDatacube(optimizer.sidebandCalibrationData())
dataManager.addDatacube(optimizer.offsetCalibrationData())
dataManager.addDatacube(optimizer.powerCalibrationData())
##IQ mixer contrast optimization
optimizer.calibrateIQOffset()
##Save the calibration data...
filename = optimizer.offsetCalibrationData().savetxt(name+"_iq_mixer_offset_calibration_"+str(datetime.datetime.today().date()))
register["calibration.iqmixer.%s.offset" % name] = optimizer.offsetCalibrationData().filename()
##IQ mixer sideband optimization
optimizer.calibrateSidebandMixing(frequencyRange = [5.45])
##Save the calibration data...
filename = optimizer.sidebandCalibrationData().savetxt(name+"_iq_mixer_sideband_calibration_"+str(datetime.datetime.today().date()))
register["calibration.iqmixer.%s.sideband" % name] = optimizer.sidebandCalibrationData().filename()
##IQ mixer power calibration
optimizer.calibrateIQPower()
filename = optimizer.powerCalibrationData().savetxt(name+"_iq_mixer_power_calibration_"+str(datetime.datetime.today().date()))
register["calibration.iqmixer.%s.amplitude" % name] = optimizer.powerCalibrationData().filename()

######TEST CODE
print register["calibration.iqmixer.%s.offset" % name]
print register["calibration.iqmixer.%s.amplitude" % name]
##Transfer the calibration data to the qubit instrument, for testing...
qubit.setIqPowerCalibration(optimizer.powerCalibrationData())
qubit.setIqOffsetCalibration(optimizer.offsetCalibrationData())
##Test the offset calibration data...
i = 0
data = optimizer.offsetCalibrationData()
fsp.write("SENSE1:FREQUENCY:CENTER %g GHZ" % data.column("frequency")[i])
qubit.setDriveFrequency(data.column("frequency")[i])
##Test the power calibration data...
frequency = 4.6
qubit.setDriveFrequency(frequency)
fsp.write("SENSE1:FREQUENCY:CENTER %g GHZ" % frequency)
qubit.setDrivePower(I = -40)
##
import time
start = time.time()
for i in range(0,20):
	print i
	qubit1.loadRabiPulse(i)
print time.time()-start," seconds elapsed."
##
while True:
	fsp.write("SENSE1:FREQUENCY:CENTER %g GHZ" % 6.5)
	print optimizer.measureAveragePower()