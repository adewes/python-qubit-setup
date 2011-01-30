import sys

sys.path.append('.')
sys.path.append('../')

from pyview.lib.classes import *
from pyview.ide.frontpanel import FrontPanel
from pyview.ide.elements.numericedit import * 

import datetime

import instruments

class Panel(FrontPanel):

    def changeAmplitude(self):
      self.instrument.dispatch("setAmplitude",self.AmplitudeEdit.getValue())
      
    def changeOffset(self):
      self.instrument.dispatch("setOffset",self.OffsetEdit.getValue())
      
    def changeHigh(self):
      self.instrument.dispatch("setHigh",self.HighEdit.getValue())

    def changeLow(self):
      self.instrument.dispatch("setLow",self.LowEdit.getValue())

    def changeAll(self):
      if self._setOffsetAmp:
        self.changeAmplitude()
        self.changeOffset()
      else:
        self.changeHigh()
        self.changeLow()
      self.updateValues()
        
    def updateValues(self):
      self.instrument.dispatch("amplitude")
      self.instrument.dispatch("offset")
      self.instrument.dispatch("output")
      self.instrument.dispatch("high")
      self.instrument.dispatch("low")
      
      
    def updatedGui(self,subject,property = None,value = None):
      if subject == self.instrument:
        if property == "amplitude":
          self.AmplitudeEdit.setValue(value)
        elif property == "offset":
          self.OffsetEdit.setValue(value)
        elif property == "high":
          self.HighEdit.setValue(value)
        elif property == "low":
          self.LowEdit.setValue(value)
        elif property == "output" or property == "turnOn" or property == "turnOff":
          self.outputStatus = value
          print "Updating status"
          if value == False:
            self.OutputButton.setStyleSheet("background-color:#00FF00;")
            self.OutputButton.setText("OFF")
          elif value == True:
            self.OutputButton.setStyleSheet("background-color:#FF0000;")
            self.OutputButton.setText("ON")
          else:
            print "Undefined status..."
            self.OutputButton.setStyleSheet("background-color:#CCCCCC;")
            self.OutputButton.setText("undefined")
          
    def toggleOutput(self):
      if self.outputStatus == False or self.outputStatus == None:  
        self.instrument.dispatch("turnOn")
      else:
        self.instrument.dispatch("turnOff")
      
    def OffsetAmpHighLowToggled(self,index):
      if self.toggleOffsetAmpHighLow.itemData(index) == 0:
        self._setOffsetAmp = False
        self.AmplitudeEdit.setDisabled(True)
        self.OffsetEdit.setDisabled(True)
        self.HighEdit.setEnabled(True)
        self.LowEdit.setEnabled(True)
      else:
        self._setOffsetAmp = True
        self.AmplitudeEdit.setEnabled(True)
        self.OffsetEdit.setEnabled(True)
        self.HighEdit.setDisabled(True)
        self.LowEdit.setDisabled(True)
    
    def __init__(self,instrument,parent=None):
        FrontPanel.__init__(self,instrument,parent)

        self.title = QLabel(instrument.name())
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("QLabel {font:18px;}")
        self.outputStatus = False

        self._setOffsetAmp = True

        self.AmplitudeEdit  = NumericEdit("")
        self.OffsetEdit = NumericEdit("")
        self.LowEdit  = NumericEdit("")
        self.HighEdit = NumericEdit("")
        self.SetButton = QPushButton("Set")
        self.UpdateButton = QPushButton("Update")
        self.OutputButton = QPushButton("Undefined")
        self.toggleOffsetAmpHighLow = QComboBox()
        self.toggleOffsetAmpHighLow.addItem("High/Low",0)
        self.toggleOffsetAmpHighLow.addItem("Offset/Amplitude",1)

        self.connect(self.toggleOffsetAmpHighLow,SIGNAL("currentIndexChanged(int)"),self.OffsetAmpHighLowToggled)
        self.toggleOffsetAmpHighLow.setCurrentIndex(1)

        self.grid = QGridLayout(self)

        buttonsLayout = QBoxLayout(QBoxLayout.LeftToRight)
        
        buttonsLayout.addWidget(self.SetButton)
        buttonsLayout.addWidget(self.UpdateButton)
        buttonsLayout.addWidget(self.OutputButton)
        buttonsLayout.addStretch()

        self.grid.addWidget(self.title,0,0,1,3)
        self.grid.addWidget(QLabel("Amplitude"),1,0)
        self.grid.addWidget(self.AmplitudeEdit,1,1)
        self.grid.addWidget(QLabel("Offset"),2,0)
        self.grid.addWidget(self.OffsetEdit,2,1)
        self.grid.addWidget(QLabel("High"),3,0)
        self.grid.addWidget(self.HighEdit,3,1)
        self.grid.addWidget(QLabel("Low"),4,0)
        self.grid.addWidget(self.LowEdit,4,1)
        self.grid.addLayout(buttonsLayout,5,0,1,2)
        self.grid.addWidget(QLabel("Set:"),6,0)
        self.grid.addWidget(self.toggleOffsetAmpHighLow,6,1)
        
        
                
        self.connect(self.SetButton,SIGNAL("clicked()"),self.changeAll)
        self.connect(self.UpdateButton,SIGNAL("clicked()"),self.updateValues)
        self.connect(self.OutputButton,SIGNAL("clicked()"),self.toggleOutput)
        
        self.setLayout(self.grid)

        self.updateValues()
           
