import sys

sys.path.append('.')
sys.path.append('../')

from pyview.lib.classes import *
from pyview.ide.frontpanel import FrontPanel
from pyview.ide.elements.numericedit import * 

import datetime

import instruments

class Panel(FrontPanel):
    
    def clearPulse(self):
      self.instrument.dispatch("clearPulse")      
      self.array.setRowCount(0)
      
    def sendPulse(self):
      self.instrument.dispatch("sendPulse")      


    def generatePulse(self):
      kwargs={'duration':self.DurationEdit.getValue(),'DelayFromZero':self.DelayFromZeroEdit.getValue(),'phase':self.PhaseEdit.getValue(),'frequency':self.FrequencyEdit.getValue(),
        'gaussian':self.GaussianEdit.isChecked(),'useCalibration':self.UseCalibrationEdit.isChecked(), 'amplitude':self.AmplitudeEdit.getValue(), 'allowModifyMWFrequency':self.ModifyMWFrequencyEdit.isChecked()}
      self.instrument.dispatch("generatePulse",**kwargs)      
      
      self.array.setRowCount(self.array.rowCount()+1)
      self.array.setItem(self.array.rowCount()-1,0,QTableWidgetItem(str(self.AmplitudeEdit.getValue())))
      self.array.setItem(self.array.rowCount()-1,1,QTableWidgetItem(str(self.FrequencyEdit.getValue())))
      self.array.setItem(self.array.rowCount()-1,2,QTableWidgetItem(str(self.DurationEdit.getValue())))
      self.array.setItem(self.array.rowCount()-1,3,QTableWidgetItem(str(self.PhaseEdit.getValue())))
      self.array.setItem(self.array.rowCount()-1,4,QTableWidgetItem(str(self.DelayFromZeroEdit.getValue())))
      
      
    def __init__(self,instrument,parent=None):
    
    
        super(Panel,self).__init__(instrument,parent)
        
        self.title = QLabel(instrument.name())
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("QLabel {font:18px;}")
        self.outputStatus = False

        self.AmplitudeEdit  = NumericEdit("")
        self.FrequencyEdit = NumericEdit("")
        self.DurationEdit = NumericEdit("")
        self.PhaseEdit = NumericEdit("")
        self.DelayFromZeroEdit = NumericEdit("")
        self.GaussianEdit = QCheckBox("Gaussian")
        self.UseCalibrationEdit = QCheckBox("Use Calibration")
        self.ModifyMWFrequencyEdit = QCheckBox("Allow Modify MW source frequency")
        self.GenerateButton = QPushButton("Generate")
        self.SendButton = QPushButton("Send")
        self.ClearButton = QPushButton("Clear")
 
        self.grid = QGridLayout(self)

        self.grid.addWidget(self.title,0,0,1,3)
        self.grid.addWidget(QLabel("Amplitude"),1,0)
        self.grid.addWidget(self.AmplitudeEdit,1,1)
        self.grid.addWidget(QLabel("Frequency"),2,0)
        self.grid.addWidget(self.FrequencyEdit,2,1)
        self.grid.addWidget(QLabel("Duration"),3,0)
        self.grid.addWidget(self.DurationEdit,3,1)
        self.grid.addWidget(QLabel("Phase"),4,0)
        self.grid.addWidget(self.PhaseEdit,4,1)
        self.grid.addWidget(QLabel("DelayFromZero"),5,0)
        self.grid.addWidget(self.DelayFromZeroEdit,5,1)
        self.grid.addWidget(self.GaussianEdit,6,1)
        self.grid.addWidget(self.UseCalibrationEdit,7,1)
        self.grid.addWidget(self.ModifyMWFrequencyEdit,8,1)
        self.grid.addWidget(self.GenerateButton,9,1)    
        self.grid.addWidget(self.SendButton,10,1)     
        self.grid.addWidget(self.ClearButton,11,1)     
        
        self.connect(self.GenerateButton,SIGNAL("clicked()"),self.generatePulse)
        self.connect(self.SendButton,SIGNAL("clicked()"),self.sendPulse)
        self.connect(self.ClearButton,SIGNAL("clicked()"),self.clearPulse)

        self.array=QTableWidget(self)
        self.array.setRowCount(0)
        self.array.setColumnCount(5)
        self.array.setHorizontalHeaderLabels(['amplitude','frequency','duration','phase','delay'])
        
        
        self.grid.addWidget(self.array,12,0,1,-1)

        self.setLayout(self.grid)

        instrument.attach(self)
#        self.updateValues()
           
