#We assume a sampling rate of 1 GSPS (i.e. 1 point per ns)

iWaveform = zeros(10000)
qWaveform = zeros(10000)

#All frequencies are in GHz

f_sideband = 0.3

from math import *

A=0.9
c= 0.09*A

phi = -8.0/180.0*pi

for i in range(0,10000):
	iWaveform[i] = A*(cos(f_sideband*2*pi*float(i)+phi)+c*cos(f_sideband*2*pi*float(i)+phi))
	qWaveform[i] = A*(-sin(f_sideband*2*pi*float(i))+c*sin(f_sideband*2*pi*float(i)))

qubit2.loadWaveform(iWaveform,qWaveform)

##
figure("waveforms")

plot(iWaveform)
plot(qWaveform)

xlim(0,200)
##Parameters for qubit 1
mwg = qubit2_mwg
qubit = qubit2
name = "qubit2"
channels = [3,4]
cavity2_mwg.turnOff()
instrumentManager.reloadInstrument("qubit2")
optimizer = qubit2._optimizer
dataManager.addDatacube(optimizer.sidebandCalibrationData())
optimizer.calibrateSidebandMixing()
##
figure("iq_waveform")
cla()
phi = 90.0/180.0*math.pi
waveform = optimizer.generateSidebandWaveform(f_sb = 0.1,c=0.0,phi = phi)
plot(real(waveform*exp(-1.0j*phi)))
plot(imag(waveform))
xlim(0,10)
##
importModule("pyview.lib.datacube")
cube = Datacube()
dataManager.addDatacube(cube)
cube.set(f_c = 2)	
subcube = Datacube("subcube line 1")
cube.addChild(subcube)
cube.commit()
cube.set(f_c = 2)
subcube = Datacube("subcube line 2,1")
cube.addChild(subcube)
cube.commit()
cube.set(f_c = 2)
subcube = Datacube("subcube line 2,2")
cube.addChild(subcube)
cube.commit()
print cube.searchChildren(f_c = 2)[0].name()
##
instrumentManager.reloadInstrument("qubit2")
cube = Datacube()
cube.loadtxt("sideband.txt")
print cube.column("phi"),cube.column("f_c")
qubit2._optimizer.setSidebandCalibrationData(cube)
##
from scipy.interpolate import RectBivariateSpline 
print  RectBivariateSpline( array([1,2,3]),array([1]),array([5,6,7]), kx=1, ky=1 )