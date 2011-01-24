import sys
import time

sys.path.append('.')
sys.path.append('../')

from pyview.lib.classes import *
from numpy import *
from pyview.conf.parameters import *
from pyview.ide.elements.numericedit import * 
import PyQt4.uic as uic
if 'pyview.scripts.xyplot' in sys.modules:
  reload(sys.modules['pyview.scripts.xyplot'])
from pyview.scripts.xyplot import *

import datetime

import instruments

class PulseVisualizer(QWidget,ObserverWidget):
  
  def updateDrivePlot(self):
    self._drive.setData(0,list(linspace(0,len(self._waveforms["drive"]["I"]),len(self._waveforms["drive"]["I"]))),self._waveforms["drive"]["I"])
    self._drive.setData(1,list(linspace(0,len(self._waveforms["drive"]["Q"]),len(self._waveforms["drive"]["Q"]))),self._waveforms["drive"]["Q"])
    
  def updateFluxlinePlot(self):
    xvalues = list(linspace(0,len(self._waveforms["fluxline"])*0.5,len(self._waveforms["fluxline"]))+self.instrument.parameters()["waveformDelay"]-self.instrument.parameters()["fluxlineWaveformDelay"])
    xvalues.append(xvalues[-1]*2-xvalues[-2])
    xvalues.append(20000.0)
    waveform = list(self._waveforms["fluxline"])
    waveform.append(waveform[0])
    waveform.append(waveform[0])
    self._flux.setData(0,xvalues,waveform)
    
    
  def updateReadoutPlot(self):
    xvalues = list(linspace(0,len(self._waveforms["readout"])*0.5,len(self._waveforms["readout"]))+self._readoutDelay+self.instrument.parameters()["waveformDelay"])
    xvalues.insert(0,0)
    xvalues.append(xvalues[-1]*2-xvalues[-2])
    xvalues.append(20000.0)
    waveform = list(self._waveforms["readout"])
    waveform.insert(0,0)
    waveform.append(waveform[0])
    waveform.append(waveform[0])
    self._readout.setData(0,xvalues,waveform)
    

  def updatedGui(self,subject,property,value = None,modifier = None):
    if subject == self.instrument:
      if property == "driveWaveform":
        self._waveforms["drive"] = dict()
        self._waveforms["drive"]["I"] = value[0]
        self._waveforms["drive"]["Q"] = value[1]
        self._waveforms["drive"]["markers"] = value[2]
        self._modified["drive"] = True
      elif property == "fluxlineWaveform":
        self._waveforms["fluxline"] = value
        self._modified["fluxline"] = True
      elif property == "readoutDelay":
        self._readoutDelay = value
        self._modified["readout"] = True
    elif subject == self.instrument._jba:
      if property == "readoutWaveform":
        self._waveforms["readout"] = value
        self._modified["readout"] = True
    
  def limitsChanged(self,limits):
    for plot in [self._flux,self._drive,self._readout]:
      if plot.limits().left() != limits.left() or plot.limits().right() != limits.right():
        plot.setXLimits(limits.left(),limits.right())
    
  def onTimer(self):
    if self._modified["drive"]:
      self._modified["drive"] = False
      self.updateDrivePlot()
    if self._modified["readout"]:
      self._modified["readout"] = False
      self.updateReadoutPlot()
    if self._modified["fluxline"]:
      self._modified["fluxline"] = False
      self.updateFluxlinePlot()
    
  def __init__(self,instrument,parent = None):

    QWidget.__init__(self,parent)
    ObserverWidget.__init__(self)

    layout = QGridLayout()

    self.instrument = instrument
    self.instrument.attach(self)
    self.instrument._jba.attach(self)

    self._waveforms = dict()
    self._modified = dict()
    self._modified['drive'] = False
    self._modified["readout"] = False
    self._modified["fluxline"] = False
    self._readoutDelay = self.instrument.readoutDelay()

    self.timer = QTimer(self)
    self.timer.setInterval(1000)
    self.connect(self.timer,SIGNAL("timeout()"),self.onTimer)
    self.timer.start()

    self._drive = XYPlot("Drive")
    self._flux = XYPlot("Flux")
    self._readout = XYPlot("Readout")

#    layout.addWidget(QLabel("Drive"))
    layout.addWidget(self._drive)
#    layout.addWidget(QLabel("Flux"))
    layout.addWidget(self._flux)
#    layout.addWidget(QLabel("Readout"))
    layout.addWidget(self._readout)

    self.setLayout(layout)
    
    self.connect(self._drive,SIGNAL("limitsChanged(QRectF)"),self.limitsChanged)
    self.connect(self._flux,SIGNAL("limitsChanged(QRectF)"),self.limitsChanged)
    self.connect(self._readout,SIGNAL("limitsChanged(QRectF)"),self.limitsChanged)

class Panel(FrontPanel):
  
  def __del__(self):
    self.instrument.detach(self)
    self.instrument._jba.detach(self)
  
  def __init__(self,instrument,parent=None):
    super(Panel,self).__init__(instrument,parent)
    instrument.attach(self)
    self.instrument = instrument
    layout = QGridLayout()
    self._visualizer = PulseVisualizer(instrument)
    layout.addWidget(self._visualizer)
    self.setLayout(layout)
    self.instrument.dispatch("updateWaveforms")
    self.instrument._jba.dispatch("updateReadoutWaveform")
          