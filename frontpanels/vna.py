import sys

sys.path.append('.')
sys.path.append('../')

from pyview.lib.classes import *
from pyview.ide.mpl.canvas import *
from pyview.ide.frontpanel import FrontPanel
import string

from datetime import *

#This is the VNA dashboard.
class Panel(FrontPanel):

    def updateTraceList(self):
      self.traces.setRowCount(len(self._traces))
      for i in range(0,len(self._traces)):
        self.traces.setItem(i,0,QTableWidgetItem(self._traces[i].name()))
        self.traces.setItem(i,1,QTableWidgetItem(self._traces[i].description()))

        myLayout = QGridLayout()
        myLabel = QLabel("")
        myCheckBox = QCheckBox("show")
        print self.visibility(i)
        myCheckBox.setCheckState(Qt.Checked if self.visibility(i) == True else Qt.Unchecked)
        myLayout.addWidget(myCheckBox,0,0)
        myLabel.setFixedHeight(50)
        myLabel.setLayout(myLayout)
        deleteButton = QPushButton("delete")
        saveButton = QPushButton("save")
        refButton = QPushButton("make ref")
        myLayout.addWidget(deleteButton,0,1)
        myLayout.addWidget(saveButton,0,2)
        myLayout.addWidget(refButton,0,3)
        
        #Programming with "lambda" rocks :)
        self.connect(myCheckBox,SIGNAL("stateChanged(int)"),lambda state, x = i: self.setVisibility(x,state))
        self.connect(deleteButton,SIGNAL("clicked()"),lambda x = i: self.deleteTrace(x))
        self.connect(saveButton,SIGNAL("clicked()"),lambda x = i: self.saveTrace(x))
        self.connect(refButton,SIGNAL("clicked()"),lambda x = i: self.makeReference(x))
        
        self.traces.setCellWidget(i,2,myLabel)
        self.traces.setRowHeight(i,50)        
    

    #Plots the given traces.
    def plotTraces(self):
      if len(self._traces) == 0:
        self.sc.axes.set_visible(False)
        self.phase.axes.set_visible(False)
        self.sc.draw()
        self.phase.draw()
        return
      plots = []
      phaseplots = []
      legends = []
      for x in range(0,len(self._traces)):
        if self.visibility(x):
          plots.append(map(lambda x : x / 1e9 ,self._traces[x]["freq"]))
          phaseplots.append(map(lambda x : x / 1e9 ,self._traces[x]["freq"]))
          if self._reference != None and self._reference != self._traces[x]:
           plots.append(self._traces[x]["mag"] -self._reference["mag"])
           phaseplots.append(self._traces[x]["phase"] -self._reference["phase"])
          else:
           plots.append(self._traces[x]["mag"])
           phaseplots.append(self._traces[x]["phase"])
          legends.append(self._traces[x].name())

      if len(plots) == 0:
        self.sc.axes.set_visible(False)
        self.phase.axes.set_visible(False)
      else:
        self.sc.axes.clear()
        self.sc.axes.plot(*list(plots))
        self.sc.axes.grid(True)
        self.sc.axes.legend(legends,'lower left')
        self.sc.axes.set_xlabel("frequency [GHz]")
        self.sc.axes.set_ylabel("amplitude [dB]")
        self.sc.axes.set_visible(True)

        self.phase.axes.clear()
        self.phase.axes.plot(*list(phaseplots))
        self.phase.axes.grid(True)
        self.phase.axes.legend(legends,'lower left')
        self.phase.axes.set_xlabel("frequency [GHz]")
        self.phase.axes.set_ylabel("phase [deg]")
        self.phase.axes.set_visible(True)

      self.sc.draw()
      self.phase.draw()


    #Update handler. Gets inoked whenever the instrument gets a new trace.
    def updatedGui(self,subject,property = None,value = None,message = None):
      if subject == self.instrument:
        if property == "getTrace":
          print "Trace data arrived!"
          if not value in self._traces:
            self._traces.append(value)
            self.plotTraces()
            self.updateTraceList()
                    
    #Request a trace from the instrument.
    def requestAcquire(self):
      self.instrument.dispatch("getTrace")
        
    def makeReference(self,i):
      if i == None:
        self._reference = None
      else:
        self._reference = self._traces[i]
      self.plotTraces()
      
    #Deletes a given trace.
    def deleteTrace(self,i):
      self._traces.pop(i)
      self.plotTraces()
      self.updateTraceList()
      

    #Save the plot with all the traces to a file (PDF, PNG, EPS, ...)    
    def savePlot(self):
      plot = self.tabs.currentWidget()
      if plot.axes.get_visible() == False:
          return
      if self._workingDirectory != '':
          self.fileDialog.setDirectory(self._workingDirectory)
      self.fileDialog.setAcceptMode(1)
      self.fileDialog.setNameFilter("Image files (*.png *.eps *.jpg)");
      self.fileDialog.setDefaultSuffix('eps')
      filename = str(self.fileDialog.getSaveFileName())
      if len(filename) > 0:
          self._workingDirectory = str(self.fileDialog.directory().dirName())
          plot.figure.savefig(filename)

    def setVisibility(self,i,state):
      self._traces[i].parameters()["visible"] = state
      self.plotTraces()
      
    def visibility(self,i):
      if not "visible" in self._traces[i].parameters():
        self._traces[i].parameters()["visible"] = True
      return bool(self._traces[i].parameters()["visible"])
      
    def toggleVisibility(self,i):
      self.setVisibility(i,not self.visibility(i))
          
    #Updates the properties of a trace according to the values the user entered in the table.
    def updateTraceProperties(self,i,j):
        if j == 0:
            #We change the name of the trace...
            print "Updating name..."
            self._traces[i].setName(str(self.traces.item(i,j).text().toAscii()))
            self.plotTraces()
        if j == 1:
            #We change the name of the trace...
            print "Updating description..."
            self._traces[i].setDescription(str(self.traces.item(i,j).text().toAscii()))
            self.plotTraces()

    #Deletes all traces that have been taken so far.
    def clearTraces(self):
        self._traces = []
        self.plotTraces()
        self.updateTraceList()

    #Write a given trace to a file.
    def writeTrace(self,filename,trace):
      trace.savetxt(filename)

    #Saves all the traces to a directory chosen by the user. The individual traces will be named according to the filenames in the first column of the table.
    #The first column of each data file will contain the description entered by the user in the second column of the table.
    def saveTraces(self):
        self.fileDialog.setAcceptMode(1)
        if self._workingDirectory != '':
            self.fileDialog.setDirectory(self._workingDirectory)
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        dirname = str(self.fileDialog.getExistingDirectory())
        if len(dirname) > 0:
           self._workingDirectory = dirname
           for x in range(0,len(self._traces)):
              trace = self._traces[x]
              sanitized_filename = ''.join(c for c in trace.name() if c in valid_chars)
              print "Storing trace 1 in file %s" % sanitized_filename
              self.writeTrace(dirname + '/'+ sanitized_filename+ '.dat',trace)

    #Saves one single trace to a file.
    def saveTrace(self,x):
        if self._workingDirectory != '':
            self.fileDialog.setDirectory(self._workingDirectory)
        self.fileDialog.setAcceptMode(1)
        filename = str(self.fileDialog.getSaveFileName())
        if len(filename) > 0:
            self._workingDirectory = self.fileDialog.directory().dirName()
            self.writeTrace(filename,self._traces[x])

    def hideAll(self):
      for i in range(0,len(self._traces)):
        self.setVisibility(i,False)

    #Initializes the front panel.
    def __init__(self,instrument,parent=None):
        super(Panel,self).__init__(instrument,parent)

        self._reference = None
        self._traces = []
        self._workingDirectory = ''
        self.fileDialog = QFileDialog()
        
        self.setWindowTitle("VNA Control Panel")
        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        self.sc = MatplotlibCanvas(self, width=5, height=4, dpi=100)
        self.sc.axes.set_visible(True)
        self.phase = MatplotlibCanvas(self, width=5, height=4, dpi=100)
        self.phase.axes.set_visible(True)
        updateButton = QPushButton("Get Trace")
        self.connect(updateButton,SIGNAL("clicked()"),self.requestAcquire)

        subGrid = QGridLayout()
        subGrid.setSpacing(10)

        self.traces = QTableWidget()
        self.traces.horizontalHeader().setStretchLastSection(True)
        self.traces.setColumnCount(3)
        self.traces.setColumnWidth(1,340)
        self.traces.setHorizontalHeaderItem(0,QTableWidgetItem("filename"))
        dw = QTableWidgetItem("description")
        dw.setSizeHint(QSize(400,30))
        self.traces.setHorizontalHeaderItem(1,dw)
        self.traces.setHorizontalHeaderItem(2,QTableWidgetItem("options"))

        self.connect(self.traces,SIGNAL("cellChanged(int,int)"),self.updateTraceProperties)

        clearButton = QPushButton("Clear Traces")
        self.connect(clearButton,SIGNAL("clicked()"),self.clearTraces)

        saveButton = QPushButton("Save All Traces")
        self.connect(saveButton,SIGNAL("clicked()"),self.saveTraces)

        saveFigButton = QPushButton("Save Figure")
        self.connect(saveFigButton,SIGNAL("clicked()"),self.savePlot)

        clearRefButton = QPushButton("Clear Ref")
        self.connect(clearRefButton,SIGNAL("clicked()"),lambda : self.makeReference(None))

        hideAllButton = QPushButton("Hide all")
        self.connect(hideAllButton,SIGNAL("clicked()"),self.hideAll)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self.sc,"Amplitude")
        self.tabs.addTab(self.phase,"Phase")
        
        self.grid.addWidget(self.tabs,0,0)
        subGrid.addWidget(updateButton,0,0)
        subGrid.addWidget(clearButton,0,1)
        subGrid.addWidget(saveButton,0,2)
        subGrid.addWidget(saveFigButton,0,3)
        subGrid.addWidget(clearRefButton,0,4)
        subGrid.addWidget(hideAllButton,0,5)

        self.grid.addItem(subGrid,1,0)

        self.grid.addWidget(self.traces,2,0)
    
        self.setLayout(self.grid)
        self.setMinimumWidth(640)
        self.setMinimumHeight(500)
        
        self.plotTraces()
