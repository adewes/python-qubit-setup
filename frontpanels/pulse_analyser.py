import sys

sys.path.append('.')
sys.path.append('../')

from pyview.lib.classes import *
from pyview.ide.frontpanel import FrontPanel
from pyview.ide.elements.numericedit import * 

import datetime

import instruments

class Panel(FrontPanel):
    
    def clear(self):
      self.instrument.dispatch("clear")      
      
    def analyse(self):
      self.instrument.dispatch("analyse")      


    def addFrequency(self):
      kwargs={'f':self.FrequencyEdit.getValue()}
      self.instrument.dispatch("addFrequency",**kwargs)      

      
    def __init__(self,instrument,parent=None):
    
    
        super(Panel,self).__init__(instrument,parent)
        
        self.title = QLabel(instrument.name())
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("QLabel {font:18px;}")
        self.outputStatus = False

        self.FrequencyEdit = NumericEdit("")
        self.AddButton = QPushButton("Add")
        self.AnalyseButton = QPushButton("Analyse")
        self.ClearButton = QPushButton("Clear")
 
        self.grid = QGridLayout(self)

        self.grid.addWidget(QLabel("Frequency"),1,0)
        self.grid.addWidget(self.FrequencyEdit,1,1)
        self.grid.addWidget(self.AddButton,2,1)    
        self.grid.addWidget(self.AnalyseButton,3,1)     
        self.grid.addWidget(self.ClearButton,4,1)     
        
        self.connect(self.AddButton,SIGNAL("clicked()"),self.addFrequency)
        self.connect(self.AnalyseButton,SIGNAL("clicked()"),self.analyse)
        self.connect(self.ClearButton,SIGNAL("clicked()"),self.clear)

        self.setLayout(self.grid)

        instrument.attach(self)
           
