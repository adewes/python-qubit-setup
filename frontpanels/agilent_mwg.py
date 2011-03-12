import sys

sys.path.append('.')
sys.path.append('../')

from pyview.lib.classes import *
from pyview.ide.frontpanel import FrontPanel
from pyview.ide.elements.numericedit import * 

import datetime

import instruments

class Panel(FrontPanel):

    def changeFrequency(self):
      self.instrument.dispatch("setFrequency",self.FrequencyEdit.getValue())
      
    def changePower(self):
      self.instrument.dispatch("setPower",self.PowerEdit.getValue())
      
    def changeAll(self):
      self.changePower()
      self.changeFrequency()
        
    def updateValues(self):
      self.instrument.dispatch("frequency")
      self.instrument.dispatch("power")
      self.instrument.dispatch("output")
      
    def updatedGui(self,subject,property = None,value = None):
      if subject == self.instrument:
        if property == "frequency" or property == "setFrequency":
          self.FrequencyEdit.setValue(value)
        elif property == "power" or property == "setPower":
          self.PowerEdit.setValue(value)
        elif property == "output" or property == "turnOn" or property == "turnOff":
          self.outputStatus = value
          if value == False:
            self.OutputButton.setStyleSheet("background-color:#00FF00;")
            self.OutputButton.setText("OFF")
          elif value == True:
            self.OutputButton.setStyleSheet("background-color:#FF0000;")
            self.OutputButton.setText("ON")
          else:
            self.OutputButton.setStyleSheet("background-color:#CCCCCC;")
            self.OutputButton.setText("undefined")
          
    def toggleOutput(self):
      if self.outputStatus == False or self.outputStatus == None:  
        self.instrument.dispatch("turnOn")
      else:
        self.instrument.dispatch("turnOff")
      
    
    def __init__(self,instrument,parent=None):
        super(Panel,self).__init__(instrument,parent)
        
        print "Initializing..."

        self.title = QLabel(instrument.name())
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("QLabel {font:18px;}")
        self.outputStatus = False

        self.PowerEdit  = NumericEdit("")
        self.FrequencyEdit = NumericEdit("")
        self.SetButton = QPushButton("Set")
        self.UpdateButton = QPushButton("Update")
        self.OutputButton = QPushButton("Undefined")

        self.grid = QGridLayout(self)

        self.grid.addWidget(self.title,0,0,1,3)
        self.grid.addWidget(QLabel("Power"),1,0)
        self.grid.addWidget(self.PowerEdit,1,1)
        self.grid.addWidget(QLabel("Frequency"),2,0)
        
        buttonsLayout = QBoxLayout(QBoxLayout.LeftToRight)
        
        buttonsLayout.addWidget(self.SetButton)
        buttonsLayout.addWidget(self.UpdateButton)
        buttonsLayout.addWidget(self.OutputButton)
        buttonsLayout.addStretch()
        
        self.grid.addWidget(self.FrequencyEdit,2,1)
        self.grid.addLayout(buttonsLayout,3,0,1,2)
        
                
        self.connect(self.SetButton,SIGNAL("clicked()"),self.changeAll)
        self.connect(self.UpdateButton,SIGNAL("clicked()"),self.updateValues)
        self.connect(self.OutputButton,SIGNAL("clicked()"),self.toggleOutput)
        
        self.setLayout(self.grid)

        instrument.attach(self)
        self.updateValues()
           
