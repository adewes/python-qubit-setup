import sys

sys.path.append('.')
sys.path.append('../')

from pyview.lib.classes import *
from pyview.ide.frontpanel import FrontPanel
from pyview.ide.elements.numericedit import * 

import datetime

import instruments

class Panel(FrontPanel):

    def updateValues(self):
      self.instrument.dispatch("voltage")
      self.instrument.dispatch("output")
    
    
    def changeVoltage(self):
      self.instrument.dispatch("setVoltage",self.VoltageEdit.getValue())
    
    def toggleOutput(self):
      if self.outputStatus == False: 
        self.instrument.dispatch("turnOn")
      else:
        self.instrument.dispatch("turnOff")
      
    def updatedGui(self,subject = None,property = None,value = None):
      if subject == self.instrument:
        if property == "setVoltage" or property == "voltage":
          self.VoltageEdit.setValue(value)
        if property == "turnOn" or property == "turnOff" or property == "output":
          self.outputStatus = value
          if value == False:
            self.OutputButton.setStyleSheet("background-color:#00FF00;")
            self.OutputButton.setText("OFF")
          else:
            self.OutputButton.setStyleSheet("background-color:#FF0000;")
            self.OutputButton.setText("ON")
    
    def onReload(self):
      self.__init__(self.instrument,self.parent())
    
    def __init__(self,instrument,parent=None):
        super(Panel,self).__init__(instrument,parent)

        self.title = QLabel(instrument.name())
        self.title.setStyleSheet("QLabel {font:18px;}")
        self.title.setAlignment(Qt.AlignCenter)
        self.outputStatus = False
            
        buttonsLayout = QBoxLayout(QBoxLayout.LeftToRight)

        self.VoltageEdit = NumericEdit()
        self.SetButton = QPushButton("Sets")
        self.UpdateButton = QPushButton("Update")
        self.OutputButton = QPushButton("UNDEFINED")
        self.OutputButton.setStyleSheet("background-color:#CCCCCC; width:100px;")
        
        buttonsLayout.addWidget(self.SetButton)
        buttonsLayout.addWidget(self.UpdateButton)
        buttonsLayout.addWidget(self.OutputButton)
        buttonsLayout.addStretch()
        
        self.grid = QGridLayout(self)

        self.grid.addWidget(self.title,0,0,1,2)
        self.grid.addWidget(QLabel("Voltage"),1,0)
        self.grid.addWidget(self.VoltageEdit,1,1)
        self.grid.addLayout(buttonsLayout,3,0,1,2)
                
        self.connect(self.SetButton,SIGNAL("clicked()"),self.changeVoltage)
        self.connect(self.OutputButton,SIGNAL("clicked()"),self.toggleOutput)
        self.connect(self.UpdateButton,SIGNAL("clicked()"),self.updateValues)
        
        self.setLayout(self.grid)

        self.instrument.attach(self)
        
        self.updateValues()
           
