import sys

from pyview.lib.classes import *
import string

import re
import struct

import os
import os.path

from numpy import *
from numpy.random import *

from pyview.ide.mpl.canvas import MatplotlibCanvas as Canvas
from pyview.ide.frontpanel import *

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
    self.calibrateButton = QPushButton("Calibrate")
    self.updateButton = QPushButton("Update data")
    self.adjustIQButton = QPushButton("Rotate shift IQ")
    self.measureSCurveButton = QPushButton("Measure S")
    self.levelEdit = QLineEdit("0.1")    
    self.accuracyEdit = QLineEdit("0.02")        
    self.setLevelButton = QPushButton("Set Level")
    self.StopButton = QPushButton("Stop")
    
    #Layout

    self.histograms = Canvas(width = 8,height = 5)
    self.sCurve = Canvas(width = 8,height = 5)

    self.tabs = QTabWidget()
    self.tabs.addTab(self.iq,"IQ data")
    self.tabs.addTab(self.histograms,"Histograms")
    self.tabs.addTab(self.variance,"Variance")
    self.tabs.addTab(self.sCurve,"S Curve")
  
    self.layout = QGridLayout()
    self.layout.addWidget(self.tabs,1,1)
    self.layout.addWidget(self.statusLabel,2,1)

    buttonsLayout1 = QBoxLayout(QBoxLayout.LeftToRight)
    buttonsLayout2 = QBoxLayout(QBoxLayout.LeftToRight)

    buttonsLayout1.addWidget(self.calibrateButton)
    buttonsLayout1.addWidget(self.adjustIQButton)
    buttonsLayout1.addWidget(self.updateButton)
    buttonsLayout1.addWidget(self.measureSCurveButton)
    buttonsLayout1.addWidget(self.StopButton)
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
    self.enableButtons()
    #self.calibrateButton.setEnabled(True)
    #self.StopButton.setEnabled(False)

    #Signal connections:

    self.connect(self.calibrateButton,SIGNAL("clicked()"),self.calibrate)
    self.connect(self.measureSCurveButton,SIGNAL("clicked()"),self.measureS)
    self.connect(self.updateButton,SIGNAL("clicked()"),self.updateGraphs)
    self.connect(self.adjustIQButton,SIGNAL("clicked()"),self.adjustIQ)
    self.connect(self.setLevelButton,SIGNAL("clicked()"),self.adjustSwitchingLevel)
    self.connect(self.StopButton,SIGNAL("clicked()"),self.stop)
    self.connect(self.levelEdit,SIGNAL("returnPressed()"),self.adjustSwitchingLevel)
    self.connect(self.accuracyEdit,SIGNAL("returnPressed()"),self.adjustSwitchingLevel)
      
  def disableButtons(self):
    self.calibrateButton.setEnabled(False)
    self.measureSCurveButton.setEnabled(False)
    self.adjustIQButton.setEnabled(False)
    self.updateButton.setEnabled(False)
    self.setLevelButton.setEnabled(False)    
#    self.StopButton.setEnabled(True)
    
  def enableButtons(self):
#    self.StopButton.setEnabled(False)
    self.calibrateButton.setEnabled(True)
    self.measureSCurveButton.setEnabled(True)
    self.adjustIQButton.setEnabled(True)
    self.updateButton.setEnabled(True)
    self.setLevelButton.setEnabled(True)
    
  def stop(self):
    self.updateStatus("Stopping ...")
    self.instrument.stop()
    self.enableButtons()
    self.updateStatus("")    
  
  def adjustSwitchingLevel(self):
    self.disableButtons()
    lastTab = self.tabs.currentIndex()
    self.tabs.setCurrentWidget(self.iq)
    self.updateStatus("Adjusting switching level to %g %% with %g %% accuracy" % (float(self.levelEdit.text())*100,float(self.accuracyEdit.text())*100))
    self.instrument.dispatch("adjustSwitchingLevel",float(self.levelEdit.text()),float(self.accuracyEdit.text()))
    #self.tabs.setCurrentIndex(lastTab)
    self.enableButtons()
      
  def measureS(self):
    self.disableButtons()
    print "Measuring s curve"
    lastTab = self.tabs.currentIndex()
    self.tabs.setCurrentWidget(self.sCurve)
    self.instrument.dispatch("measureSCurve")
    #self.tabs.setCurrentIndex(lastTab)
    self.enableButtons()
      
  def adjustIQ(self):
    self.disableButtons()
    lastTab = self.tabs.currentIndex()
    self.tabs.setCurrentWidget(self.iq)
    #self.instrument.dispatch("adjustRotationAndOffset",float(self.levelEdit.text()))
    self.instrument.dispatch("adjustRotationAndOffset")
    #self.tabs.setCurrentIndex(lastTab)
    self.enableButtons()
        
  def calibrate(self):
    self.disableButtons()
    lastTab = self.tabs.currentIndex()
    self.tabs.setCurrentWidget(self.variance)
    self.instrument.dispatch("calibrate",level = float(self.levelEdit.text()),accuracy = float(self.accuracyEdit.text()))
    #self.calibrateButton.setEnabled(False)
    #self.calibrateStopButton.setEnabled(True)
    #self.tabs.setCurrentIndex(lastTab)
    self.enableButtons()

  def updateStatus(self,message):
    self.statusLabel.setText(message)
    
  def updateGraphs(self):
    self.disableButtons()
    (p,trends) = self.instrument.acquire()
    self.histograms.axes.cla()
    self.histograms.axes.hist(trends[0],normed = True,bins = 40)
    self.histograms.axes.axvline(0,ls = ":")
#    self.histograms.axes.hist(trends[1],normed = True,bins = 30)
    self.histograms.draw()
    self.iq.axes.cla()
    self.iq.axes.scatter(trends[0,:],trends[1,:])
    self.iq.axes.axvline(0,ls = ":")
    self.iq.axes.axhline(0,ls = ":")
    self.updateStatus("Switching probability: %g percent" % (p*100.0))
    self.iq.draw()
    self.enableButtons()
    
  def updatedGui(self,subject,property,value):
    if subject == self.instrument:    
      if property == "calibrate":
        self.calibrateButton.setEnabled(True)
        #self.StopButton.setEnabled(False)
        (vs,ps,vs2,ps2,iqdata) = value
        self.iq.axes.cla()
        self.iq.axes.scatter(iqdata[0,:],iqdata[1,:])
        self.iq.draw()
        self.variance.axes.cla()
        self.variance.axes.set_xlabel("Yoko voltage [V]")
        self.variance.axes.set_ylabel("$\sigma_I^2$+$\sigma_Q^2$")
        self.variance.axes.plot(vs,ps,vs2,ps2)
        self.variance.draw()
      elif property == 'variance':
        self.variance.axes.cla()
        self.variance.axes.set_xlabel("Yoko voltage [V]")
        self.variance.axes.set_ylabel("$\sigma_I^2$+$\sigma_Q^2$")
        (vs,ps) = value
        self.variance.axes.plot(vs,ps)
        self.variance.draw()
      elif property == 'sCurve':
        self.sCurve.axes.cla()
        self.sCurve.axes.plot(value[0],value[1])
        self.sCurve.draw()
      elif property == "iqdata":
        self.iq.axes.cla()
        self.iq.axes.scatter(value[0,:],value[1,:])
        self.iq.draw()
      elif property == "status":
        self.updateStatus(value)
 