import sys

import os
import os.path
from numpy import *
from numpy.random import *

sys.path.append(os.path.realpath('.'))
sys.path.append(os.path.realpath('../'))

from pyview.lib.canvas import MatplotlibCanvas as Canvas
from pyview.lib.classes import ReloadableWidget
from macros.jba import *
import helpers.instrumentsmanager


class JBAUtility(QWidget,ReloadableWidget,ObserverWidget):
  
  def __init__(self,parent = None):
    QWidget.__init__(self,parent)
    ReloadableWidget.__init__(self)
    ObserverWidget.__init__(self)

    self.layout = QGridLayout()
    self.setLayout(self.layout)
  
    self.tabs = QTabWidget()
    self.layout.addWidget(self.tabs,1,1,1,3)

    self.iq = Canvas()
    self.variance = Canvas()

    self.graphSplitter = QSplitter(Qt.Vertical)
    
    self.graphSplitter.addWidget(self.iq)
    self.graphSplitter.addWidget(self.variance)
    
    splitter = QSplitter(Qt.Horizontal)

    self.statusLabel = QLabel("[status label]")
    self.calibrateAllButton = QPushButton("Calibrate all")
    self.calibrate1Button = QPushButton("Calibrate 1")
    self.calibrate2Button = QPushButton("Calibrate 2")
    self.calibrateStopButton = QPushButton("Stop calibration")
    self.reloadButton = QPushButton("Reload widget")
    self.connect(self.calibrateAllButton,SIGNAL("clicked()"),self.calibrateAll)
    self.connect(self.calibrate1Button,SIGNAL("clicked()"),lambda: self.calibrateSetup(1))
    self.connect(self.calibrate2Button,SIGNAL("clicked()"),lambda: self.calibrateSetup(2))
    self.connect(self.calibrateStopButton,SIGNAL("clicked()"),self.stopCalibration)
    self.connect(self.reloadButton,SIGNAL("clicked()"),self.reloadWidget)
    self.layout.addWidget(self.statusLabel,2,1)
    self.layout.addWidget(splitter,3,1)
    splitter.addWidget(self.calibrateAllButton)
    splitter.addWidget(self.calibrate1Button)
    splitter.addWidget(self.calibrate2Button)
    self.layout.addWidget(self.calibrateStopButton,3,2)
    self.layout.addWidget(self.reloadButton,3,3)
  
    self.tabs.addTab(self.graphSplitter,"Graphs")
    
    self.calibrator = JBACalibration()
    self.calibrator.attach(self)
  
  def stopCalibration(self):
    self.calibrator.stop()
    
  def onReload(self):
    self.hide()
    self.__init__()
    self.show()
        
  def calibrateAll(self):
    for i in range(0,2):
      self.calibrateSetup(i+1)
        
  #Calibrate the 2 setups...
  def calibrateSetup(self,setup = 1):
    if self.calibrator.isAlive():
      return
    setup -= 1
    manager = helpers.instrumentsmanager.Manager()
    yokos = []
    yokos.append (manager.getInstrument("atts2"))
    yokos.append (manager.getInstrument("attS3"))
    polarities = [1,-1]
    channels = [1,2]
    acqiris = manager.getInstrument("acqiris")
    #We reload the macro in case it has been changed.
    self.calibrator.reloadClass()
    self.calibrator.dispatch("calibrateJBA",yokos[setup],acqiris,polarity = polarities[setup],channel = channels[setup])
        
  def updateStatus(self,message):
    self.statusLabel.setText(message)
    
  def updatedGui(self,subject,property,value):
    if subject == self.calibrator:    
      if property == "variance":
        self.variance.axes.cla()
        self.variance.axes.set_xlabel("Yoko voltage [V]")
        self.variance.axes.set_ylabel("$\sigma_I^2$+$\sigma_Q^2$")
        self.variance.axes.plot(value[:,0],value[:,1])
        self.variance.draw()
      if property == "iqdata":
        self.iq.axes.cla()
        self.iq.axes.scatter(value[0,:],value[1,:])
        self.iq.draw()
      if property == "status":
        self.updateStatus(value)
        
       
if __name__ == '__main__':  
  app = QApplication(sys.argv)
  util = JBAUtility()
  util.show()
  app.exec_()
