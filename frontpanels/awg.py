import sys


sys.path.append('.')
sys.path.append('../')

from pyview.lib.classes import *
from pyview.lib.canvas import *
from pyview.ide.codeeditor import *
import string

import re
import struct

from datetime import *

class WaveformEditor(QWidget,ReloadableWidget):

  def __init__(self,parent = None,panel = None):
    QWidget.__init__(self,parent)
    ReloadableWidget.__init__(self)
    self.waveformname = QLineEdit("test")
    self.waveformcode = CodeEditor()
    self.waveformcode.setText("""waveform = []
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
    print code
    gv = dict()
    exec(code,gv,gv)
    if 'waveform' in gv and 'markers' in gv:
      waveform = gv['waveform'] 
      markers = gv['markers'] 
      wavedata = self.panel.instrument.writeRealData(waveform,markers)
      self.panel.instrument.createWaveform(str(self.waveformname.text()),wavedata,'REAL')
      fig = self.panel.waveformGraph
      fig.axes.clear()
      fig.axes.plot(range(0,len(waveform)),waveform)
      fig.draw()

#This is the AWG frontpanel.
class Panel(FrontPanel):

    #Update handler. Gets invoked whenever the instrument gets a new trace.
    def updatedGui(self,subject,property = None,value = None):
        if subject == self.instrument:
                if property == "waveforms":
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

        self.setFixedWidth(640)
        self.setMinimumHeight(500)
        
        self.waveformGraph = MyMplCanvas(self, width=5, height=4, dpi=100)
        self.GpibCommand = QLineEdit()
        self.tabs = QTabWidget()
        self.waveformlist = QTreeWidget()
        self.waveformlist.setHeaderLabels(["Name","Length","Type"])
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
        self.instrument.dispatch("getWaveforms")
        self.updateWaveformList()
