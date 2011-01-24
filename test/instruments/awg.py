import random
import unittest

import sys

sys.path.append('.')
sys.path.append('../')

from pyview.lib.classes import *


import helpers.instrumentsmanager

class TestAWG(unittest.TestCase):

    def setUp(self):
      self.manager = helpers.instrumentsmanager.Manager()
      print "Loading AWG..."
      self.instrument = self.manager.getInstrument("awg")
      
    def test_waveform_roundtrip(self):
      self.instrument.getPredefinedWaveforms()
      for waveform in self.instrument.waveforms:
        print "Testing transfer of %s" % waveform._name
        if waveform._type == 'REAL':
          print "Generating REAL data."
          data = self.instrument.writeRealData(waveform._data,waveform._markers)
        else:
          print "Generating INT data."
          data = self.instrument.writeIntData(waveform._data,waveform._markers)  
        self.instrument.createWaveform("testform",data,waveform._type)
        receivedWaveform = self.instrument.getWaveform("testform")
        print "Received length: %d, original length: %d " % (len(receivedWaveform._data),len(waveform._data))
        self.assertEqual(waveform._data,receivedWaveform._data)
        self.assertEqual(waveform._markers,receivedWaveform._markers)
        self.assertEqual(waveform._type,receivedWaveform._type)
        self.instrument.deleteWaveform("testform")

if __name__ == '__main__':
    unittest.main()
