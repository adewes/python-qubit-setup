import sys

from pyview.lib.classes import *
import string

import re
import struct

import os
import os.path

from numpy import *
from numpy.random import *

reload(sys.modules['pyview.lib.canvas'])
from pyview.lib.canvas import MatplotlibCanvas as Canvas

class Panel(FrontPanel):
  
  """
  The JBA frontpanel.
  """
  
  def __init__(self,instrument,parent = None):
    FrontPanel.__init__(self,instrument,parent)

    #GUI elements

    self.iq = Canvas(width = 8,height = 5)
    self.variance = Canvas(width = 8,height = 5)

    self.statusLabel = QLabel("")
    self.calibrateButton = QPushButton("Calibrate JBA")
    self.calibrateStopButton = QPushButton("Stop calibration")
    self.updateButton = QPushButton("Update data")
    self.levelEdit = QLineEdit("0.2")    
    self.accuracyEdit = QLineEdit("0.05")        
    self.setLevelButton = QPushButton("Set Level")
    
    #Layout

    self.histograms = Canvas(width = 8,height = 5)

    self.tabs = QTabWidget()
    self.tabs.addTab(self.iq,"IQ data")
    self.tabs.addTab(self.histograms,"Histograms")
    self.tabs.addTab(self.variance,"Variance")

    
    self.layout = QGridLayout()
    self.layout.addWidget(self.tabs,1,1)
    self.layout.addWidget(self.statusLabel,2,1)

    buttonsLayout1 = QBoxLayout(QBoxLayout.LeftToRight)
    buttonsLayout2 = QBoxLayout(QBoxLayout.LeftToRight)

    buttonsLayout1.addWidget(self.calibrateButton)
    buttonsLayout1.addWidget(self.calibrateStopButton)
    buttonsLayout1.addWidget(self.updateButton)
    buttonsLayout1.addStretch()
    buttonsLayout2.addWidget(QLabel("p:"))
    buttonsLayout2.addWidget(self.levelEdit)
    buttonsLayout2.addWidget(QLabel("acc.:"))
    buttonsLayout2.addWidget(self.accuracyEdit)
    buttonsLayout2.addWidget(self.setLevelButton)
    buttonsLayout2.addStretch()
    
    self.layout.addLayout(buttonsLayout1,3,1)
    self.layout.addLayout(buttonsLayout2,4,1)
    
    self.setLayout(self.layout)

    self.calibrateButton.setEnabled(True)
    self.calibrateStopButton.setEnabled(False)

    #Signal connections:

    self.connect(self.calibrateButton,SIGNAL("clicked()"),self.calibrate)
    self.connect(self.calibrateStopButton,SIGNAL("clicked()"),self.stopCalibration)
    self.connect(self.updateButton,SIGNAL("clicked()"),self.updateGraphs)
    self.connect(self.setLevelButton,SIGNAL("clicked()"),self.adjustSwitchingLevel)
    self.connect(self.levelEdit,SIGNAL("returnPressed()"),self.adjustSwitchingLevel)
    self.connect(self.accuracyEdit,SIGNAL("returnPressed()"),self.adjustSwitchingLevel)
      
  def adjustSwitchingLevel(self):
    self.updateStatus("Adjusting switching level to %g %% with %g %% accuracy" % (float(self.levelEdit.text())*100,float(self.accuracyEdit.text())*100))
    self.instrument.dispatch("adjustSwitchingLevel",float(self.levelEdit.text()),float(self.accuracyEdit.text()))
      
  def stopCalibration(self):
    print "Stopping calibration..."
    self.instrument.stop()
    self.calibrateButton.setEnabled(True)
    self.calibrateStopButton.setEnabled(False)
        
  def calibrate(self):
    self.instrument.dispatch("calibrate")
    self.calibrateButton.setEnabled(False)
    self.calibrateStopButton.setEnabled(True)

  def updateStatus(self,message):
    self.statusLabel.setText(message)
    
  def updateGraphs(self):
    (p,trends) = self.instrument.acquire()
    self.histograms.axes.cla()
    self.histograms.axes.hist(trends[0],normed = True,bins = 40)
#    self.histograms.axes.hist(trends[1],normed = True,bins = 30)
    self.histograms.draw()
    self.iq.axes.cla()
    self.iq.axes.scatter(trends[0,:],trends[1,:])
    print p
    self.updateStatus("Switching probability: %g percent" % (p*100.0))
    self.iq.draw()
    
  def updatedGui(self,subject,property,value):
    if subject == self.instrument:    
      if property == "calibrate":
        self.calibrateButton.setEnabled(True)
        self.calibrateStopButton.setEnabled(False)
        (vs,ps,vs2,ps2,iqdata) = value
        self.iq.axes.cla()
        self.iq.axes.scatter(iqdata[0,:],iqdata[1,:])
        self.iq.draw()
        self.variance.axes.cla()
        self.variance.axes.set_xlabel("Yoko voltage [V]")
        self.variance.axes.set_ylabel("$\sigma_I^2$+$\sigma_Q^2$")
        self.variance.axes.plot(vs,ps,vs2,ps2)
        self.variance.draw()
      elif property == "iqdata":
        self.iq.axes.cla()
        self.iq.axes.scatter(value[0,:],value[1,:])
        self.iq.draw()
      elif property == "status":
        self.updateStatus(value)
 