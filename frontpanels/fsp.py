import sys

sys.path.append('.')
sys.path.append('../')

from pyview.lib.classes import *

import datetime

import instruments

class Panel(FrontPanel):

    def saveTrace(self):
        if self._workingDirectory != '':
            self.fileDialog.setDirectory(self._workingDirectory)
        self.fileDialog.setAcceptMode(1)
        filename = self.fileDialog.getSaveFileName()
        if len(filename) > 0:
            self._workingDirectory = self.fileDialog.directory().dirName()
            self.writeTrace(filename)
            
    def writeTrace(self,filename):
        file = open(filename,'w')
#        file.write('#'+datetime.now().strftime("%A, %d. %B %Y %I:%M%p")+"\n")
        for i in range(0,len(self.values[0])):
            file.write("%s\t%s\n" % (self.values[0][i],self.values[1][i]))
        file.close()
        
    
    def update(self,subject,property = None,value = None,message = None):
      if property == 'trace':
        self.values = value
        self.sc.axes.plot(self.values[0],self.values[1])
        self.sc.axes.set_xlabel("time ($\mu s$)")
        self.sc.axes.set_ylabel("power ($dBm$)")
        self.sc.draw()
        
    def getTrace(self):
        self.instrument.dispatch("getTrace",self.traceChannel.value())
      
    def evaluateGpibCommand(self):
        print "Evaluating %s" % self.GpibCommand.text()
        print self.instrument.ask(str(self.GpibCommand.text()))
    
    def __init__(self,instrument,parent=None):
        super(Panel,self).__init__(instrument,parent)
        self.fileDialog = QFileDialog()
        self._workingDirectory = ''
           
        self.sc = MyMplCanvas(self, width=5, height=4, dpi=100)
        self.grid = QGridLayout()
        self.grid.addWidget(self.sc,0,0)
        
        GetButton = QPushButton("Getss trace")
        SaveButton = QPushButton("Save trace")
        self.GpibCommand = QLineEdit()
        GpibSubmit = QPushButton("Submit")
        
        self.traceChannel = QSpinBox()
        self.traceChannel.setValue(1)
        self.grid.addWidget(GetButton,1,0)
        self.grid.addWidget(SaveButton,1,1)
        self.grid.addWidget(self.traceChannel,1,2)
        self.grid.addWidget(self.GpibCommand,2,0)
        self.grid.addWidget(GpibSubmit,2,1)

        self.connect(self.GpibCommand,SIGNAL("returnPressed()"),self.evaluateGpibCommand)
        self.connect(GpibSubmit,SIGNAL("clicked()"),self.evaluateGpibCommand)
        
        self.connect(GetButton,SIGNAL("clicked()"),self.getTrace)
        self.connect(SaveButton,SIGNAL("clicked()"),self.saveTrace)
        
        self.setLayout(self.grid)
           
        self.instrument.dispatch("getTrace")

