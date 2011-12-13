import sys

sys.path.append('.')
sys.path.append('../')

from pyview.lib.classes import *
from pyview.ide.frontpanel import FrontPanel
from pyview.ide.elements.numericedit import * 

import datetime

import instruments

class Panel(FrontPanel):

    def analyse(self):
      self.instrument.dispatch("analyse")

    def define(self):
      kwargs={'duration':self.DurationEdit.getValue(),'DelayFromZero':self.DelayFromZeroEdit.getValue(),'frequency':self.FrequencyEdit.getValue(),
        'gaussian':self.GaussianEdit.isChecked(), 'amplitude':self.AmplitudeEdit.getValue()}
      self.instrument.dispatch("frequency",**kwargs)      
      
    def init(self):
      self.instrument.dispatch('init')

    def __init__(self,instrument,parent=None):
    
    
        super(Panel,self).__init__(instrument,parent)
        
        self.title = QLabel(instrument.name())
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("QLabel {font:18px;}")
        self.outputStatus = False

        self.AmplitudeEdit  = NumericEdit("")
        self.FrequencyEdit = NumericEdit("")
        self.DurationEdit = NumericEdit("")
        self.DelayFromZeroEdit = NumericEdit("")
        self.GaussianEdit = QCheckBox("Gaussian")
        self.DefineButton = QPushButton("Define")
        self.AnalyseButton = QPushButton("Analyse")
        self.ClearButton = QPushButton("Clear")
 
        self.grid = QGridLayout(self)

        self.grid.addWidget(self.title,0,0,1,3)
        self.grid.addWidget(QLabel("Amplitude"),1,0)
        self.grid.addWidget(self.AmplitudeEdit,1,1)
        self.grid.addWidget(QLabel("Frequency"),2,0)
        self.grid.addWidget(self.FrequencyEdit,2,1)
        self.grid.addWidget(QLabel("Duration"),3,0)
        self.grid.addWidget(self.DurationEdit,3,1)
        self.grid.addWidget(QLabel("DelayFromZero"),4,0)
        self.grid.addWidget(self.DelayFromZeroEdit,4,1)
        self.grid.addWidget(self.GaussianEdit,5,1)
        self.grid.addWidget(self.DefineButton,6,1)
        self.grid.addWidget(self.AnalyseButton,7,1)     
        self.grid.addWidget(self.ClearButton,8,1)     
        
        self.connect(self.DefineButton,SIGNAL("clicked()"),self.define)
        self.connect(self.AnalyseButton,SIGNAL("clicked()"),self.analyse)
        self.connect(self.ClearButton,SIGNAL("clicked()"),self.init)

        self.setLayout(self.grid)

        self.init()

        instrument.attach(self)

           
