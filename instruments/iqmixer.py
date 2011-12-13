import sys
import getopt
import numpy

from pyview.lib.classes import *
from pyview.helpers.instrumentsmanager import Manager
from numpy import *
register=Manager().getInstrument('register')
if 'lib.datacube' in sys.modules:
  reload(sys.modules['lib.datacube'])
  
from pyview.lib.classes import *
from pyview.lib.datacube import Datacube

from macros.iq_level_optimization import IqOptimization
reload(sys.modules["macros.iq_level_optimization"])
from macros.iq_level_optimization import IqOptimization

class Instr(Instrument):

      def calibrate(self, f_sb=0.1,offsetOnly=False):
        print 'calibration in progress'
        
        register["%s OffsetCal" % self._params["realMixer"]]=self._calibration.calibrateIQOffset()
        if not(offsetOnly):
          register["%s IQCal" % self._params["realMixer"]]=self._calibration.calibrateSidebandMixing(sidebandRange=arange(-f_sb,f_sb+0.01,0.1))
        

        print 'calibration ended'
        return

      def reInitCalibration(self):
        self._calibration.initCalibrationData()
        return
        
      def calibrationParameters(self, f_c, f_sb):
        return self._calibration.calibrationParameters(f_c=f_c, f_sb=f_sb)  
              
      def parameters(self):    
        return self._params

      def initialize(self, name, MWSource, AWG, AWGChannels, fsp,realMixer):
        instrumentManager=Manager()
        self._MWSource=instrumentManager.getInstrument(MWSource)
        self._fsp=instrumentManager.getInstrument(fsp)
        self._AWG=instrumentManager.getInstrument(AWG)
        self._params=dict()
        self._params["MWSource"]=MWSource
        self._params["AWG"]=AWG
        self._params["AWGChannels"]=AWGChannels
        self._params["fsp"]=fsp
        self._params["realMixer"]=realMixer
        self._calibration=IqOptimization(fsp=self._fsp, awg=self._AWG, mwg=self._MWSource, channels=self._params["AWGChannels"])
        try:
          self._calibration._sidebandCalibrationData=Datacube()
          self._calibration._sidebandCalibrationData.loadtxt(register.parameters()["%s IQCal" % realMixer], loadChildren=True)
          self._calibration._offsetCalibrationData=Datacube()
          self._calibration._offsetCalibrationData.loadtxt(register["%s OffsetCal" % realMixer], loadChildren=True)
          self._calibration.updateOffsetCalibrationInterpolation()
        except:
          pass