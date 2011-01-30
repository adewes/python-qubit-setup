"""
Initializes all the instruments and stores references to them in local variables.
"""

import sys

import os
import os.path

sys.path.append(os.path.realpath('.'))
sys.path.append(os.path.realpath('../'))

from pyview.helpers.instrumentsmanager import *
if 'pyview.lib.datacube' in sys.modules:
  reload(sys.modules['pyview.lib.datacube'])
from pyview.lib.datacube import *
from pyview.config.parameters import params

print "Initializing instruments..."

serverHost = "127.0.0.1:8000"

instrumentManager = Manager()

#The parameter register
register = instrumentManager.initInstrument("rip://%s/register" % serverHost,forceReload = True)

#The temperature information.
temperature = instrumentManager.initInstrument('rip://%s/temperature' % serverHost,"temperature",forceReload = True)

#The temperature information.
helium_level = instrumentManager.initInstrument('rip://%s/helium_level' % serverHost,"helium_level",forceReload = True)

#The Qubit mu-wave generators
cavity1_mwg = instrumentManager.initInstrument('rip://%s/Cavity1MWG' % serverHost,"anritsu_mwg",[],{'name' : 'Cavity 1','visaAddress' : "GPIB0::4"},forceReload = True)
cavity2_mwg = instrumentManager.initInstrument('rip://%s/Cavity2MWG' % serverHost,"anritsu_mwg",[],{'name' : 'Cavity 2','visaAddress' : "GPIB0::6"},forceReload = True)

#The cavity mu-wave generators
qubit1_mwg = instrumentManager.initInstrument('rip://%s/Qubit1MWG' % serverHost,"agilent_mwg",kwargs = {'name' : 'Qubit 1','visaAddress' : "TCPIP::192.168.0.12"},forceReload = True)
qubit2_mwg = instrumentManager.initInstrument('rip://%s/Qubit2MWG' % serverHost,"agilent_mwg",kwargs = {'name' : 'Qubit 2','visaAddress' : "TCPIP::192.168.0.13"},forceReload = True)

#The two VNAs
vna1 = instrumentManager.initInstrument('rip://%s/VNA1' % serverHost,"vna",kwargs = {'name' : 'VNA Qubit 1','visaAddress' : 'GPIB0::15'},forceReload = True)
#vna2 = instrumentManager.initInstrument('rip://192.168.0.1:8000/VNA2',"vna",kwargs = {'name' : 'VNA Qubit 2','visaAddress' : 'GPIB0::16'},forceReload = True)

#The two qubit attenuators
qubit1_att = instrumentManager.initInstrument('rip://%s/AttS2' % serverHost,"yokogawa",kwargs = {'name' : 'Attenuator Qubit 1','visaAddress' : 'GPIB0::9'},forceReload = True)
qubit2_att = instrumentManager.initInstrument('rip://%s/AttS3' % serverHost,"yokogawa",kwargs = {'name' : 'Attenuator Qubit 2','visaAddress' : 'GPIB0::19'},forceReload = True)

#The transmon coil
transmon_coil = instrumentManager.initInstrument('rip://%s/Coil' % serverHost,"yokogawa",kwargs = {'name' : 'Transmon Coil','visaAddress' : 'GPIB0::2','slewRate':5.0},forceReload = True)

#The Acqiris card
acqiris = instrumentManager.initInstrument('rip://192.168.0.22:8000/acqiris',"acqiris",kwargs = {'name': 'Acqiris Card'},forceReload = True)

#The Arbitrary Waveform generator
awg = instrumentManager.initInstrument('rip://%s/awg' % serverHost,"awg",forceReload = True)

##The Rhode & Schwarz FSP
fsp = instrumentManager.initInstrument("rip://%s/fsp" % serverHost,"fsp",forceReload = True)

#The LeCroy Oscilloscope
sda = instrumentManager.initInstrument("rip://%s/sda" % serverHost,"lecroy_sda_7",forceReload = True)

#The AFG signal generators
afg1 = instrumentManager.initInstrument('rip://%s/afg1' % serverHost,"afg",kwargs = {"name": "AFG 1, Channel 1"},forceReload = True)
afg2 = instrumentManager.initInstrument('rip://%s/afg2' % serverHost,"afg",kwargs = {"name": "AFG 1, Channel 2","source":2},forceReload = True)

afg3 = instrumentManager.initInstrument('rip://%s/afg3' % serverHost,"afg",kwargs = {"visaAddress": "TCPIP0::192.168.0.5::inst0","name": "AFG 2, Channel 1"},forceReload = True)
afg4 = instrumentManager.initInstrument('rip://%s/afg4' % serverHost,"afg",kwargs = {"visaAddress": "TCPIP0::192.168.0.5::inst0","name": "AFG 2,Channel 2","source":2},forceReload = True)


#The two JBAs
jba1 = instrumentManager.initInstrument('jba1',"jba",kwargs = {"attenuator":'atts2',"acqirisChannel":0,"muwave":'cavity1mwg','waveform':'USER1','afg':'afg3','variable':'p1x'},forceReload = True)
jba2 = instrumentManager.initInstrument('jba2',"jba",kwargs = {"attenuator":'atts3',"acqirisChannel":2,"muwave":'cavity2mwg','waveform':'USER2','afg':'afg4',"qubitmwg" : "qubit2mwg",'variable':'px1'},forceReload = True)


#Load the IQ mixer calibration data for the first qubit.
qubit1IQOffset = Datacube()
qubit1IQPower = Datacube()
qubit1IQSideband = Datacube()
#Load the IQ mixer calibration data for the second qubit.
qubit2IQOffset = Datacube()
qubit2IQPower = Datacube()
qubit2IQSideband = Datacube()

fluxline1Response = Datacube()
fluxline2Response = Datacube()

try:

  qubit2IQOffset.loadtxt(register["calibration.iqmixer.qubit2.offset"],loadChildren = False)
  qubit2IQPower.loadtxt(register["calibration.iqmixer.qubit2.amplitude"],loadChildren = False)
  if register.hasKey("calibration.iqmixer.qubit2.sideband"):
    qubit2IQSideband.loadtxt(register["calibration.iqmixer.qubit2.sideband"])

  qubit1IQOffset.loadtxt(register["calibration.iqmixer.qubit1.offset"],loadChildren = False)
  qubit1IQPower.loadtxt(register["calibration.iqmixer.qubit1.amplitude"],loadChildren = False)
  if register.hasKey("calibration.iqmixer.qubit1.sideband"):
    qubit1IQSideband.loadtxt(register["calibration.iqmixer.qubit1.sideband"])

  fluxline1Response.loadtxt(register["calibration.fluxline.qubit1"])
  fluxline2Response.loadtxt(register["calibration.fluxline.qubit2"])

except:
  print "Cannot load qubit calibration data!"
  print sys.exc_info()

qubit1 = instrumentManager.initInstrument('qubit1',"qubit",kwargs = {'fluxlineResponse':fluxline1Response,'fluxlineWaveform':'USER1','fluxline':'afg1','iqOffsetCalibration':qubit1IQOffset,'iqSidebandCalibration':qubit1IQSideband,'iqPowerCalibration':qubit1IQPower,'jba':'jba1',"awgChannels":[1,2],"variable":1,"waveforms":["qubit1iReal","qubit1qReal"],"awg":"awg","mwg":"qubit1mwg"},forceReload = True)
qubit2 = instrumentManager.initInstrument('qubit2',"qubit",kwargs = {'fluxlineResponse':fluxline2Response,'fluxlineWaveform':'USER2','fluxline':'afg2','iqOffsetCalibration':qubit2IQOffset,'iqSidebandCalibration':qubit2IQSideband,'iqPowerCalibration':qubit2IQPower,'jba':'jba2',"awgChannels":[3,4],"variable":2,"waveforms":["qubit2iReal","qubit2qReal"],"awg":"awg","mwg":"qubit2mwg","acqirisVariable":"px1"},forceReload = True)
