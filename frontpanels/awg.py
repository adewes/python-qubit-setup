import sys


sys.path.append('.')
sys.path.append('../')

from pyview.lib.classes import *
from pyview.ide.frontpanel import FrontPanel
from pyview.ide.mpl.canvas import *
from pyview.ide.patterns import *
from pyview.ide.editor.codeeditor import *
import string
import numpy

import re
import struct

from datetime import *

class ChannelWidget(QWidget,ObserverWidget):

  def updateValues(self):
    for property in self._properties:  
      getattr(self,property).setText(str(getattr(self._awg,property)(self._channel)))
    
  def setValues(self):
    for property in self._properties:
      getattr(self._awg,"set"+property[0].capitalize()+property[1:])(self._channel,float(getattr(self,property).text()))
    self.updateValues()
  
  def __init__(self,awg,channel,parent = None):
    QWidget.__init__(self,parent)
    ObserverWidget.__init__(self)
    self._awg = awg
    self._channel = channel
    self._awg.attach(self)
    
    layout = QGridLayout()
    
    self._properties = ["amplitude","offset","marker1High","marker1Low","marker2High","marker2Low"]
    
    for property in self._properties:
      setattr(self,property,QLineEdit())
        
    self.updateButton = QPushButton("Update")
    self.setButton = QPushButton("Set")
    
    self.connect(self.updateButton,SIGNAL("clicked()"),self.updateValues)
    self.connect(self.setButton,SIGNAL("clicked()"),self.setValues)
    
    self.amplitude = QLineEdit()
    self.offset = QLineEdit()
    
    cnt = 0
    
    for property in self._properties:
      layout.addWidget(QLabel(property),cnt,0)
      layout.addWidget(getattr(self,property),cnt,1)
      cnt+=1
    
    layout.addWidget(self.updateButton,cnt,0)
    layout.addWidget(self.setButton,cnt,1)

    self.setLayout(layout)
    self.updateValues()
    
  def updatedGui(self,subject,property,value = None):
    if subject == self._awg:
      pass
      
  def updated(self,subject,property,value):
    pass

class WaveformEditor(QWidget):

  def __init__(self,parent = None,panel = None):
    QWidget.__init__(self,parent)
    self.waveformname = QLineEdit("test")
    self.waveformcode = CodeEditor()
    self.waveformcode.setPlainText("""waveform = []
markers = []
import math
for i in range(0,20000):
	waveform.append(math.sin(i*0.005))
	if i > 10000:
		markers.append((1<<6)+(1<<7))
	else:
		markers.append(0)    
""")
    self.waveformcode.activateHighlighter()
    self.submitButton = QPushButton("Save")
    self.panel = panel
    layout = QGridLayout()
    layout.addWidget(self.waveformname,0,0)
    layout.addWidget(self.waveformcode,1,0)
    layout.addWidget(self.submitButton,2,0)
    self.connect(self.submitButton,SIGNAL("clicked()"),self.saveWaveform)
    self.setLayout(layout)
    
  def saveWaveform(self):
    code = str(self.waveformcode.toPlainText())
    gv = dict()
    exec(code,gv,gv)
    if 'waveform' in gv and 'markers' in gv:
      waveform = gv['waveform'] 
      markers = gv['markers'] 
      wavedata = self.panel.instrument.writeRealData(numpy.array(waveform),numpy.array(markers))
      self.panel.instrument.createWaveform(str(self.waveformname.text()),wavedata,'REAL')
      fig = self.panel.waveformGraph
      fig.axes.clear()
      fig.axes.plot(range(0,len(waveform)),waveform)
      fig.draw()
      self.panel.instrument.dispatch("updateWaveforms")

#This is the AWG frontpanel.
class Panel(FrontPanel):

    #Update handler. Gets invoked whenever the instrument gets a new trace.
    def updatedGui(self,subject,property = None,value = None):
        if subject == self.instrument:
                if property == "updateWaveforms":
                    print "Updating waveforms..."
                    self.updateWaveformList()

    def evaluateGpibCommand(self):
        print "Evaluating %s" % self.GpibCommand.text()
        print self.instrument.ask(str(self.GpibCommand.text()))

    def updateWaveformList(self):
      waveforms = self.instrument.getWaveforms()
      self.waveformlist.clear()
      for waveform in waveforms:
        item = QTreeWidgetItem()
        item.setText(0,waveform._name)
        item.setText(1,str(len(waveform._data)))
        item.setText(2,waveform._type)
        self.waveformlist.insertTopLevelItem(0,item)

    def updateGraph(self):   
      selectedItems = self.waveformlist.selectedItems()
      if len(selectedItems) == 0:
        return
      item = selectedItems[0]
      name = item.text(0)     
      waveform = self.instrument.getWaveform(name)
      self.waveformGraph.axes.clear()
      self.waveformGraph.axes.plot(range(0,len(waveform._data)),waveform._data)
      self.waveformGraph.draw()
      
    #Initializes the front panel.
    def __init__(self,instrument,parent=None):

        super(Panel,self).__init__(instrument,parent)

        self.waveformGraph = MyMplCanvas(self, width=5, height=4, dpi=100)
        self.channels = QWidget()
        channelsLayout = QBoxLayout(QBoxLayout.LeftToRight)
        
        channelsLayout.addWidget(ChannelWidget(instrument,1,self))
        channelsLayout.addWidget(ChannelWidget(instrument,2,self))
        channelsLayout.addWidget(ChannelWidget(instrument,3,self))
        channelsLayout.addWidget(ChannelWidget(instrument,4,self))
        
        cw = ChannelWidget(instrument,1,self)
        
        self.channels.setLayout(channelsLayout)
        
        self.GpibCommand = QLineEdit()
        self.tabs = QTabWidget()
        self.waveformlist = QTreeWidget()
        self.waveformlist.setHeaderLabels(["Name","Length","Type"])
        self.tabs.addTab(self.channels,"Channels")
        self.tabs.addTab(self.waveformlist,"Waveforms")
        self.waveformEditor = WaveformEditor(self,panel = self)
        self.tabs.addTab(self.waveformEditor,"Editor")
        GpibSubmit = QPushButton("Submit")
        
        splitter = QSplitter(Qt.Vertical)

        splitter.addWidget(self.tabs)
        splitter.addWidget(self.waveformGraph)
        
        self.grid = QGridLayout()

        self.grid.addWidget(splitter,0,0,1,2)
        self.grid.addWidget(self.GpibCommand,1,0)
        self.grid.addWidget(GpibSubmit,1,1)

        self.connect(self.GpibCommand,SIGNAL("returnPressed()"),self.evaluateGpibCommand)
        self.connect(GpibSubmit,SIGNAL("clicked()"),self.evaluateGpibCommand)
        self.connect(self.waveformlist,SIGNAL("itemSelectionChanged()"),self.updateGraph)

        self.setLayout(self.grid)
        self.instrument.dispatch("updateWaveforms")
#        self.updateWaveformList()
