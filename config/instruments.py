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

serverAddress = "rip://127.0.0.1:8000"

instrumentManager = Manager()

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

register = instrumentManager.initInstrument("register")

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

instruments = [
    {
      'name' : 'register',
      'serverAddress': serverAddress
    },
    {
      'name' : 'vna',
      'gpibAddress': "GPIB0::6"
    },
    {
      'name' : 'temperature',
      'serverAddress': serverAddress
    },
    {
      'name' : 'helium_level',
      'serverAddress': serverAddress
    },
    {
      'name' : 'cavity_1_mwg',
      'class' : 'anritsu_mwg',
      'serverAddress' : serverAddress,
      'kwargs' : {'name' : 'Cavity 1','visaAddress' : "GPIB0::4"}
    },
    {
      'name' : 'qubit_1_mwg',
      'class' : 'agilent_mwg',
      'serverAddress' : serverAddress,
      'kwargs' : {'name' : 'Qubit 1','visaAddress' : "TCPIP::192.168.0.12"}
    },
    {
      'name' : 'qubit_1_att',
      'class' : 'yokogawa',
      'serverAddress' : serverAddress,
      'kwargs' : {'name' : 'Attenuator Qubit 1','visaAddress' : 'GPIB0::9'}
    },
    {
      'name' : 'acqiris',
      'serverAddress' : 'rip://192.168.0.22:8000',
      'kwargs' : {'name': 'Acqiris Card'}
    },
    {
      'name' : 'awg',
      'serverAddress' : serverAddress,
      'kwargs' : {'visaAddress' : "TCPIP0::192.168.0.3::inst0"}
    },
    {
      'name' : 'fsp',
      'serverAddress' : serverAddress
    },
    {
      'name' : 'qubit1',
      'class' : 'qubit',
      'kwargs' : {'fluxlineTriggerDelay':459,'fluxlineResponse':fluxline1Response,'fluxline':'awg2','fluxlineWaveform':'fluxlineQubit1','fluxlineChannel':1,'iqOffsetCalibration':qubit1IQOffset,'iqSidebandCalibration':qubit1IQSideband,'iqPowerCalibration':qubit1IQPower,'jba':'jba1',"awgChannels":[3,4],"variable":1,"waveforms":["qubit1iInt","qubit1qInt"],"awg":"awg","mwg":"qubit_1_mwg"}
    },
    {
      'name' : 'MixerJBA',
      'class' : 'iqmixer',
      'kwargs' : {'name' : 'MixerJBA', 'MWSource':'cavity_1_mwg', 'AWG':'awg', 'AWGChannels':(1,2), 'fsp':'fsp','realMixer':'mixer1'}
    },
    {
      'name' : 'MWpulse_gene_JBA1',
      'class' : 'pulse_generator',
      'kwargs' : {'name' : 'Pulse generator JBA 1', 'MWSource':'cavity_1_mwg', 'IQMixer':'MixerJBA', 'AWG':'awg', 'AWGChannels':(1,2)}
    },
    {
      'name' : 'Pulse_Analyser_JBA1',
      'class' : 'pulse_analyser',
      'kwargs' : {'name' : 'Pulse analyser JBA 1', 'MWSource':'cavity_1_mwg', 'acqiris':'acqiris', 'pulse_generator':'MWpulse_gene_JBA1','realMixer':'mixer2'}
    },
    {
      'name' : 'JBA1',
      'class' : 'jba_sb',
      'kwargs' : {'name' : 'JBA 1', 'generator':'MWpulse_gene_JBA1' , 'analyser':'Pulse_Analyser_JBA1'}
    }
]

unused = [
    {
      'name' : 'afg3',
      'class' : 'afg',
      'serverAddress' : serverAddress,
      'kwargs' : {"visaAddress": "TCPIP0::192.168.0.5::inst0","name": "AFG 2, Channel 1"}
    },
    {
      'name' : 'afg4',
      'class' : 'afg',
      'serverAddress' : serverAddress,
      'kwargs' : {"visaAddress": "TCPIP0::192.168.0.5::inst0","name": "AFG 2, Channel 2","source":2}
    },
    {
      'name' : 'jba2',
      'class' : 'jba',
      'kwargs': {"attenuator":'qubit_2_att',"acqirisChannel":2,"muwave":'cavity_2_mwg','waveform':'USER2','afg':'afg4','variable':'px1',"qubitmwg":"qubit_2_mwg"}    
    },
    {
      'name' : 'qubit2',
      'class' : 'qubit',
      'kwargs' : {'fluxlineTriggerDelay':459,'fluxlineResponse':fluxline2Response,'fluxline':'awg2','fluxlineWaveform':'fluxlineQubit2','fluxlineChannel':2,'iqOffsetCalibration':qubit2IQOffset,'iqSidebandCalibration':qubit2IQSideband,'iqPowerCalibration':qubit2IQPower,'jba':'jba2',"awgChannels":[3,4],"variable":2,"waveforms":["qubit2iInt","qubit2qInt"],"awg":"awg","mwg":"qubit_2_mwg","acqirisVariable":"px1","additionalFluxlineDelay":-5}
    },
    {
      'name' : 'awg2',
      'class' : 'awg',
      'serverAddress' : serverAddress,
      'kwargs' : {'visaAddress' : "TCPIP0::192.168.0.14::inst0"}
    },
    {
      'name' : 'qubit_2_att',
      'class' : 'yokogawa',
      'serverAddress' : serverAddress,
      'kwargs' : {'name' : 'Attenuator Qubit 2','visaAddress' : 'GPIB0::19'}
    },
    {
      'name' : 'qubit_2_mwg',
      'class' : 'agilent_mwg',
      'serverAddress' : serverAddress,
      'kwargs' : {'name' : 'Qubit 2','visaAddress' : "TCPIP::192.168.0.13"}
    },
    {
      'name' : 'cavity_2_mwg',
      'class' : 'anritsu_mwg',
      'serverAddress' : serverAddress,
      'kwargs' : {'name' : 'Cavity 2','visaAddress' : "GPIB0::6"}
    },
    {
      'name' : 'jba1',
      'class' : 'jba',
      'kwargs': {"attenuator":'qubit_1_att',"acqirisChannel":0,"muwave":'cavity_1_mwg','waveform':'USER1','awg':'awg',"awgChannels":[1,2],'variable':'p1x',"qubitmwg":"qubit_1_mwg"}    
    }
]

instrumentManager.initInstruments(instruments,globalParameters = {'forceReload' : True} )

for name in instrumentManager.instrumentNames():
  globals()[name] = instrumentManager.getInstrument(name)
