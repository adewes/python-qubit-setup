import sys
import time

sys.path.append('.')
sys.path.append('../')

from pyview.lib.classes import *
from pyview.lib.canvas import MyMplCanvas as Canvas
from pyview.ide.elements.numericedit import * 
import pylab
import matplotlib.ticker as ticker
import datetime

import instruments

class Panel(FrontPanel):

    def formatDate(self,x,pos = None):
      date = datetime.datetime.fromtimestamp(x)
      return date.strftime('%H:%M:%S')

    def updatedGui(self,subject,property,value):
      if property == "temperature": 
        self.updateTemperature(value)

    def updateTemperature(self,t):
      if t == None:
        return
      newTime = time.time()
      self.temperatures.append(t*1000)
      self.times.append(newTime)
      if len(self.gliding) > 0:
        self.gliding.append(self.gliding[-1]*0.7+t*0.3*1000)
      else:
        self.gliding.append(t*1000)
      while len(self.temperatures) > 200:
        self.temperatures.pop(0)
        self.times.pop(0)
        self.gliding.pop(0)
      self.canvas.axes.clear()
      self.canvas.axes.plot(self.times,self.temperatures)
      self.canvas.axes.plot(self.times,self.gliding)
      self.canvas.axes.set_xticks((self.times[0],self.times[-1]))
      xAxis = self.canvas.axes.xaxis
      xAxis.set_major_formatter(ticker.FuncFormatter(self.formatDate))
      self.canvas.draw()
      if len(self.gliding)>1:
        slope = (self.gliding[-1]-self.gliding[-2])/(self.times[-1]-self.times[-2])*60*60
      else:
        slope = 0
      if (slope>500) and t < 0.5:
        warning = "<br><font size=\"14\"color=\"red\"><blink><b>WARNING!</b></blink></font>"
      else:
        warning = ""
      if abs(slope) > 1000:
        slopeInfo = "%g K/hour" % (slope/1000.0)
      else:
        slopeInfo = "%g mK/hour" % (slope)
      if t < 1.0:
        self.temperature.setText("%g mK (%s)%s" % ((t*1000),slopeInfo,warning))
      else:
        self.temperature.setText("%g K (%s)%s" % (t,slopeInfo,warning))
    
          
    def __init__(self,instrument,parent=None):
        super(Panel,self).__init__(instrument,parent)

        self.title = QLabel(instrument.name())
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("QLabel {font:18px;}")
        self.temperatures = []
        self.times = []
        self.gliding = []

        self.temperature = QLabel("Please wait, fetching temperature...")
        self.temperature.setAlignment(Qt.AlignCenter)
        self.temperature.setStyleSheet("QLabel {font:14px;}")
        self.canvas = Canvas(dpi = 100)
        self.canvas.setFixedHeight(150)

        self.grid = QGridLayout(self)
        self.interval = 10000
        
        self.grid.addWidget(self.title,0,0)
        self.grid.addWidget(self.temperature,1,0)
        self.grid.addWidget(self.canvas)
        
        self.timer = QTimer(self)
        self.timer.setInterval(self.interval)
        self.timer.start()
        
        self.connect(self.timer,SIGNAL("timeout()"),lambda :self.instrument.dispatch("temperature"))
        
        self.setLayout(self.grid)

        instrument.attach(self)
          