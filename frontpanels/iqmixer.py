import sys

sys.path.append('.')
sys.path.append('../')

from pyview.lib.classes import *
from pyview.ide.frontpanel import FrontPanel
from pyview.ide.elements.numericedit import * 

import datetime

import instruments

class Panel(FrontPanel):
    
    def calibrate(self):
      kwargs={'f_sb':self.fsbEdit.getValue()}
      self.instrument.dispatch("calibrate",**kwargs)      

    def stop(self):
      self.instrument.stop()
    
    def reInit(self):
      self.instrument.dispatch("reInitCalibration")
      
    def __init__(self,instrument,parent=None):
    
    
        super(Panel,self).__init__(instrument,parent)
        
        self.title = QLabel(instrument.name())
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("QLabel {font:18px;}")
        self.fsbEdit = NumericEdit("")

        self.CalibrateButton = QPushButton("Calibrate")
        self.StopButton = QPushButton("Stop (not working)")
        self.reInitButton = QPushButton("Re-init calibration")
 
        self.grid = QGridLayout(self)
        

        self.grid.addWidget(QLabel("sidebande ?  "),1,0)
        self.grid.addWidget(self.fsbEdit,1,1)
        
        self.grid.addWidget(self.CalibrateButton,0,0)     
        self.grid.addWidget(self.StopButton,0,1)     
        self.grid.addWidget(self.reInitButton,0,2)

        self.connect(self.CalibrateButton,SIGNAL("clicked()"),self.calibrate)
        self.connect(self.StopButton,SIGNAL("clicked()"),self.stop)
        self.connect(self.reInitButton,SIGNAL("clicked()"),self.reInit)

        self.setLayout(self.grid)

        instrument.attach(self)
#        self.updateValues()
           
