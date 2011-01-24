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
      if property == "heliumLevel": 
        self.updateHeliumLevel(value)

    def updateHeliumLevel(self,l):
      if l == None:
        return
      newTime = time.time()
      self.heliumLevels.append(l)
      self.times.append(newTime)
      while len(self.heliumLevels) > 200:
        self.heliumLevels.pop(0)
        self.times.pop(0)
      self.canvas.axes.clear()
      self.canvas.axes.plot(self.times,self.heliumLevels)
      self.canvas.axes.set_xticks((self.times[0],self.times[-1]))
      xAxis = self.canvas.axes.xaxis
      xAxis.set_major_formatter(ticker.FuncFormatter(self.formatDate))
      self.canvas.draw()
      if l < 30:
        warning = "<br><font size=\"10\"color=\"red\"><blink><b>Refill Helium!</b></blink></font>"
      else:
        warning = ""
      self.heliumLevel.setText("%g mm%s" % (l,warning))
    
          
    def __init__(self,instrument,parent=None):
        super(Panel,self).__init__(instrument,parent)

        self.title = QLabel(instrument.name())
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("QLabel {font:18px;}")
        self.heliumLevels = []
        self.times = []
        self.gliding = []

        self.heliumLevel = QLabel("Please wait, fetching helium level...")
        self.heliumLevel.setAlignment(Qt.AlignCenter)
        self.heliumLevel.setStyleSheet("QLabel {font:14px;}")
        self.canvas = Canvas(dpi = 100)
        self.canvas.setFixedHeight(150)

        self.grid = QGridLayout(self)
        self.interval = 10000
        
        self.grid.addWidget(self.title,0,0)
        self.grid.addWidget(self.heliumLevel,1,0)
        self.grid.addWidget(self.canvas)
        
        self.timer = QTimer(self)
        self.timer.setInterval(self.interval)
        self.timer.start()
        
        self.connect(self.timer,SIGNAL("timeout()"),lambda :self.instrument.dispatch("heliumLevel"))
        
        self.setLayout(self.grid)

        instrument.attach(self)
          