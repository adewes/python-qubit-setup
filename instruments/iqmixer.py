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

from macros.new_iq_level_optimization import IqOptimization
reload(sys.modules["macros.new_iq_level_optimization"])
from macros.new_iq_level_optimization import IqOptimization

class Instr(Instrument):

      def calibrate(self, f_sb=0.1,offsetOnly=False):
        """
        Calibrate a mixer IQ using fsp, from -f_sb a +f_sb par pas de 0.1GHz
        """
        print 'calibration in progress'
        register["%s OffsetCal" % self._name] =self._calibration.calibrateIQOffset()
        if not(offsetOnly):
          register["%s IQCal" % self._name] =self._calibration.calibrateSidebandMixing(sidebandRange=arange(-f_sb,f_sb+0.01,0.1))
        print 'calibration ended'



      def reInitCalibration(self):
        """
        Re-create calibration file and store filenames in the register
        """
        (register["%s OffsetCal" % self._name],register["%s IQCal" % self._name])=self._calibration.initCalibrationData()
        
        
      def calibrationParameters(self, f_c, f_sb):
        """
        Return calibration parameters for  sideband pulse f_sb, with carrier at frequency f_c
        """
        return self._calibration.calibrationParameters(f_c=f_c, f_sb=f_sb)  
              
              
      def parameters(self): 
        """
        Returns IQ mixer parameters
        """   
        return self._params


      def initialize(self, name, MWSource, AWG, AWGChannels, fsp):
        """
        Initialize instrument, and create calibration files if needed
        """
        instrumentManager=Manager()
        self._name=name
        self._MWSource=instrumentManager.getInstrument(MWSource)
        self._fsp=instrumentManager.getInstrument(fsp)
        self._AWG=instrumentManager.getInstrument(AWG)
        self._params=dict()
        self._params["MWSource"]=MWSource
        self._params["AWG"]=AWG
        self._params["AWGChannels"]=AWGChannels
        self._params["fsp"]=fsp
        self._calibration=IqOptimization(fsp=self._fsp, awg=self._AWG, mwg=self._MWSource, channels=self._params["AWGChannels"])
        try:
          self._calibration._sidebandCalibrationData=Datacube()
          self._calibration._sidebandCalibrationData.loadtxt(register.parameters()["%s IQCal" % self._name], loadChildren=True)
          self._calibration._offsetCalibrationData=Datacube()
          self._calibration._offsetCalibrationData.loadtxt(register["%s OffsetCal" % self._name], loadChildren=True)
          self._calibration.updateOffsetCalibrationInterpolation()
        except:
          print "No calibration data found for mixer %s" % self._name
          try:
            print "creating new one..."
            self.reInitCalibration()
            print "creation succesful, continue"
          except:
            print "creation failed"
            raise