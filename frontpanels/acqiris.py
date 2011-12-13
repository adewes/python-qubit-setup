import sys

sys.path.append('.')
sys.path.append('../')

from numpy import cos,sin
from pyview.lib.classes import *
from pyview.ide.frontpanel import FrontPanel
from pyview.ide.mpl.canvas import *
#from instruments.acqiris import CAL_TOUT

import datetime

import instruments
import re


class Panel(FrontPanel):
    """
    The frontpanel class for the Acqiris Fast Acquisition card.
    
    Authors (add your name here if not present):
      - Andreas Dewes, andreas.dewes@gmail.com (creator)
      
    Description:
    """
    
    def requestAcquire(self):
      """
      Request the generation of a bifurcation map.
      """
      self.instrument.dispatch("bifurcationMap",ntimes = int(self.ntimes.text()))
      
    def getParameters(self):
      """
      Reads all the parameter values from the frontpanel and returns them in a dictionary.
      This dictionary can be used as a parameter to "ConfigureV2"
      """
      params = dict()
      params['offsets'] = list()
      params['fullScales'] = list()
      params['couplings'] = list()
      params['bandwidths'] = list()
      for i in range(0,4):
        params["offsets"].append(float(self.offsets[i].text()))
        params["fullScales"].append(float(self.fullScales[i].text()))
        params["couplings"].append(self.couplings[i].itemData(self.couplings[i].currentIndex()).toInt()[0])
        params["bandwidths"].append(self.bandwidths[i].itemData(self.bandwidths[i].currentIndex()).toInt()[0])
        
      params["freqEch"] = float(self.freqEch.text())
      params["usedChannels"] = 0
      for i in range(0,4):
        if self.activated[i].isChecked():
          params["usedChannels"]+=1<<i
      print params["usedChannels"]
      params["sampleInterval"] = float(self.sampleInterval.text())
      params["delayTime"] = float(self.delayTime.text())
      params["numberOfPoints"] = int(self.numberOfPoints.text())
      params["numberOfSegments"] = int(self.numberOfSegments.text())
      params["memType"] = self.memType.itemData(self.memType.currentIndex()).toInt()[0]
      params["trigSource"] = self.trigSource.itemData(self.trigSource.currentIndex()).toInt()[0]
      if params["trigSource"] == 0:
        params["trigSource"] = -1
      params["trigCoupling"] = self.trigCoupling.itemData(self.trigCoupling.currentIndex()).toInt()[0]
      params["trigSlope"] = self.trigSlope.itemData(self.trigSlope.currentIndex()).toInt()[0]
      params["trigLevel"] = float(self.trigLevel.text())
      params["synchro"] = int(self.synchro.text())
      
      return params
    
    def requestConfigure(self):
      """
      Configures the Acqiris board with the parameters that are displayed in the frontend.
      """
      params = self.getParameters()
      self.instrument.dispatch("ConfigureV2",**params)
        
        
    def requestCalibrate(self):
      """
      Requests a calibration of the Acqiris board.
      """
      self.instrument.dispatch("CalibrateV1",1)
    
    def plotData(self):
      trends = self.instrument.trends()
      averages = self.instrument.averages()
      means = self.instrument.means()
      print "Plotting..."
      params = self.getParameters()
      self.averagesPlot.axes.cla()
      self.meansPlot.axes.cla()
      self.trendsPlot.axes.cla()
      angles = self.instrument.bifurcationMapRotation()
      for i in range(0,4):
        if params["usedChannels"] & (1 << i):
          self.averagesPlot.axes.plot(averages[i,:])
      for i in range(0,2):
        if params["usedChannels"] & (1*2 << i):
          self.meansPlot.axes.hist(cos(angles[i])*trends[i*2,:]+sin(angles[i])*trends[i*2+1,:],bins = 30)
          self.trendsPlot.axes.plot(cos(angles[i])*trends[i*2,:]+sin(angles[i])*trends[i*2+1,:],-sin(angles[i])*trends[i*2,:]+cos(angles[i])*trends[i*2+1,:],'o')
      self.averagesPlot.draw()
      self.meansPlot.draw()
      self.trendsPlot.draw()
    
    def updatedGui(self,subject,property = None, value =None, message = None):
      """
      Processes status updates from the Acqiris card and updates the frontpanel information accordingly.
      """
      if subject==self.instrument:
        if property == "temperature":
          pass
        elif property == "bifurcationMap":
          if self.updatePlots.isChecked():
            self._updatePlots = True
        elif property == "parameters":
          self.updateParameters(**value)

    def onTimer(self):
      if self._updatePlots:
        self._updatePlots = False
        self.plotData()
          
    def updateParameters(self,**params):
      """
      Updates the frontpanel information according to a given set of parameters.
      """
      if "couplings" in params and len(params["couplings"])==4:
        for i in range(0,4):
          self.couplings[i].setCurrentIndex(int(params["couplings"][i]))
      if "bandwidths" in params and len(params["bandwidths"])==4:
        for i in range(0,4):
          self.bandwidths[i].setCurrentIndex(int(params["bandwidths"][i]))
      if "fullScales" in params and len(params["fullScales"])==4:
        for i in range(0,4):
          self.fullScales[i].setText(str(params["fullScales"][i]))
      if "offsets" in params and len(params["offsets"])==4:
        for i in range(0,4):
          self.offsets[i].setText(str(params["offsets"][i]))

      if "usedChannels" in params:
        for i in range(0,4):
           self.activated[i].setChecked(int(params["usedChannels"]) & (1 << i))
      
      for key in ["sampleInterval","freqEch","numberOfPoints","delayTime","numberOfSegments","trigLevel","synchro"]:
        if key in params and hasattr(self,key):
          getattr(self,key).setText(str(params[key]))
      for key in ["memType","trigCoupling","trigSlope"]:
        if key in params and hasattr(self,key):
          getattr(self,key).setCurrentIndex(int(params[key]))   
      if "trigSource" in params:
        if int(params["trigSource"]) != -1:
          self.trigSource.setCurrentIndex(int(params["trigSource"]))
        else:
          self.trigSource.setCurrentIndex(0)
          
    def __init__(self,instrument,parent=None):
        """
        Initializes the frontpanel
        """
        
        super(Panel,self).__init__(instrument,parent)
        self.setWindowTitle("Acqiris Control Panel")
        
        self.errorString=QLabel("")
        self.messageString = QLabel("")        
        
        #Some buttons
 
        self.updatePlots = QCheckBox("Autorefresh plots")
        updateButton = QPushButton("Acquire")
        configureButton = QPushButton("Configure")
        calibrateButton = QPushButton("Calibrate")
        plotButton = QPushButton("Update plots")

        self.connect(updateButton,SIGNAL("clicked()"),self.requestAcquire)
        self.connect(calibrateButton,SIGNAL("clicked()"),self.requestCalibrate)
        self.connect(configureButton,SIGNAL("clicked()"),self.requestConfigure)
        self.connect(plotButton,SIGNAL("clicked()"),self.plotData)
        
        #Some data graphs.
        
        self.averagesPlot = MatplotlibCanvas(width=5, height=4, dpi=100)
        self.meansPlot = MatplotlibCanvas(width=5, height=4, dpi=100)
        self.trendsPlot = MatplotlibCanvas(width=5, height=4, dpi=100)

        self.plotTabs = QTabWidget()
        
        timer = QTimer(self)
        timer.setInterval(2000)
        timer.start()
        self.connect(timer,SIGNAL("timeout()"),self.onTimer)
        
        self.plotTabs.addTab(self.averagesPlot,"Averages")
        self.plotTabs.addTab(self.meansPlot,"Means")
        self.plotTabs.addTab(self.trendsPlot,"Trends")
        
        buttonGrid = QBoxLayout(QBoxLayout.LeftToRight)
        
        buttonGrid.addWidget(updateButton)
        buttonGrid.addWidget(configureButton)
        buttonGrid.addWidget(calibrateButton)
        buttonGrid.addWidget(plotButton)
        buttonGrid.addWidget(self.updatePlots)
        buttonGrid.addStretch()

        #The grid layout that contains the parameters for the different channels.
        self.channelGrid = QGridLayout()
        self.channelGrid.setSpacing(10)
        
        #Lists containing the parameters controls of the different channels.
        self.couplings = list()
        self.fullScales = list()
        self.offsets = list()
        self.bandwidths = list()
        self.activated = list()
              
        #Here we generate the parameter controls of the different channels.
        for i in range(0,4):
          
          activated = QCheckBox("Activated")
          activated.setChecked(True)
          
          coupling = QComboBox()
          coupling.addItem("Ground",0)
          coupling.addItem("DC 1 MO",1)
          coupling.addItem("AC 1 MO",2)
          coupling.addItem("DC 50 O",3)
          coupling.addItem("AC 50 O",4)
          coupling.setCurrentIndex(3)
          
          bandwidth = QComboBox()
          
          bandwidth.addItem("no limit (0)",0)
          bandwidth.addItem("25  MHz (1)",1)
          bandwidth.addItem("700 MHz (2)",2)
          bandwidth.addItem("200 MHz (3)",3)
          bandwidth.addItem("20  MHz (4)",4)
          bandwidth.addItem("35  MHz (5)",5)
          bandwidth.setCurrentIndex(3)
                    
          self.activated.append(activated)
          self.couplings.append(coupling)
          self.fullScales.append(QLineEdit("5.0"))
          self.bandwidths.append(bandwidth)
          self.offsets.append(QLineEdit("0.0"))
          self.channelGrid.addWidget(QLabel("Channel %d" % (i+1)),0,i)
          self.channelGrid.addWidget(activated,1,i)
          self.channelGrid.addWidget(QLabel("Coupling "+str(i+1)),2,i)
          self.channelGrid.addWidget(self.couplings[i],3,i)
          self.channelGrid.addWidget(QLabel("Fullscale "+str(i+1)),4,i)
          self.channelGrid.addWidget(self.fullScales[i],5,i)
          self.channelGrid.addWidget(QLabel("Offset "+str(i+1)),6,i)
          self.channelGrid.addWidget(self.offsets[i],7,i)
          self.channelGrid.addWidget(QLabel("Bandwidth "+str(i+1)),8,i)
          self.channelGrid.addWidget(self.bandwidths[i],9,i)

        #The parameter grid, which contains all the global parameters of the card.
        self.paramsGrid = QGridLayout()
        
        self.sampleInterval = QLineEdit("2e-9")   
             
        self.paramsGrid.addWidget(QLabel("Sample Interval"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.sampleInterval,self.paramsGrid.rowCount(),0)

        self.freqEch = QLineEdit("499999999.9999999")        
        
        self.paramsGrid.addWidget(QLabel("Freq Ech."),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.freqEch,self.paramsGrid.rowCount(),0)
        
        self.delayTime = QLineEdit("400e-9")        
        
        self.paramsGrid.addWidget(QLabel("Delay time (s)"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.delayTime,self.paramsGrid.rowCount(),0)

        self.numberOfPoints = QLineEdit("250")        
        
        self.paramsGrid.addWidget(QLabel("Number of points"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.numberOfPoints,self.paramsGrid.rowCount(),0)
        
        self.numberOfSegments = QLineEdit("100")        

        self.ntimes = QLineEdit("20")        
        
        self.paramsGrid.addWidget(QLabel("Number of segments"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.numberOfSegments,self.paramsGrid.rowCount(),0)

        
        self.memType = QComboBox()     
        self.memType.addItem("Default",0)
        self.memType.addItem("Force Internal",1)
        self.memType.setCurrentIndex(1)
           
        self.paramsGrid.addWidget(QLabel("Memory Type"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.memType,self.paramsGrid.rowCount(),0)

        self.trigSource = QComboBox()        
        self.trigSource.addItem("External 1",0)
        self.trigSource.addItem("Internal 1",1)
        self.trigSource.addItem("Internal 2",2)
        self.trigSource.addItem("Internal 3",3)
        self.trigSource.addItem("Internal 4",4)
        
        self.paramsGrid.addWidget(QLabel("Trigger"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.trigSource,self.paramsGrid.rowCount(),0)

        self.trigCoupling = QComboBox()    
        self.trigCoupling.addItem("DC (0)",0)
        self.trigCoupling.addItem("AC (1)",1)
        self.trigCoupling.addItem("HF Reject (2)",2)
        self.trigCoupling.addItem("DC 50 O (3)",3)
        self.trigCoupling.addItem("AC 50 O (4)",4)
        self.trigCoupling.setCurrentIndex(3)
            
        self.paramsGrid.addWidget(QLabel("Trigger Coupling"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.trigCoupling,self.paramsGrid.rowCount(),0)

        self.trigSlope = QComboBox()      
        self.trigSlope.addItem("Positive (0)",0)
        self.trigSlope.addItem("Negative (1)",1)
        self.trigSlope.addItem("out of Window (2)",2)
        self.trigSlope.addItem("into Window (3)",3)
        self.trigSlope.addItem("HF divide (4)",4)
        self.trigSlope.addItem("Spike Stretcher (5)",5)
        self.trigSlope.setCurrentIndex(1)
          
        self.paramsGrid.addWidget(QLabel("Trigger Slope"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.trigSlope,self.paramsGrid.rowCount(),0)

        self.trigLevel = QLineEdit("500.0")        
        
        self.paramsGrid.addWidget(QLabel("Trigger Level"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.trigLevel,self.paramsGrid.rowCount(),0)

        self.synchro = QLineEdit("0")
        
        self.paramsGrid.addWidget(QLabel("Synchro 10 MHz"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.synchro,self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(QLabel("Averaging Count"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.ntimes,self.paramsGrid.rowCount(),0)

        #The grid layout of the frontpanel:
        self.grid = QGridLayout()
        
        self.grid.addItem(self.channelGrid,0,0)
        self.grid.addWidget(self.plotTabs,1,0)
        self.grid.addItem(self.paramsGrid,0,1,2,1)        
        self.grid.addItem(buttonGrid,2,0,1,2)

        self.setLayout(self.grid)
        
        self._updatePlots = False
        #We request the current parameters from the card.
        self.instrument.dispatch("parameters")
        
        