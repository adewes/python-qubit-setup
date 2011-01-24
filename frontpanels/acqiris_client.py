import sys

sys.path.append('.')
sys.path.append('../')

from pyview.lib.classes import *

import datetime
import re

import instruments

class Log(QTextEdit):

    def __init__(self,parent = None ):
        QTextEdit.__init__(self,parent)
#        sys.stdout = self
#Uncomment this to see error messages on console!
#        sys.stderr = self
##Until here
        MyFont = QFont("Courier",10)
        MyDocument = self.document() 
        MyDocument.setDefaultFont(MyFont)
        self.setDocument(MyDocument)
        self.setAcceptRichText(False)
        self.setReadOnly(True)
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.queuedText = ""
        self.connect(self.timer,SIGNAL("timeout()"),self.addQueuedText)
        self.timer.start()
        self.cnt=0

    def replaceNewline(self,matchobject):
        self.cnt+=1
        return ("\nout[%d]\t:" % self.cnt)

    def addQueuedText(self):
        if self.queuedText == "":
          return
        self.moveCursor(QTextCursor.End)
        string = self.queuedText
        string = re.sub(r'\n',self.replaceNewline,string)
        self.insertPlainText(QString.fromUtf8(string))
        self.queuedText = ""

    def write(self,text):
        text = re.sub(r'\0',r'\\0',text)
        self.queuedText += text
  

class Panel(FrontPanel):

    def __del__(self):
        print "Destroying myself..."     
        
    def activeChannels(self):
      channels = 0
      nchannels = 0
      pos = 0
      for active in self.active:
        if active.isChecked() == True:
          channels+=1 << pos
          nchannels+=1
        pos+=1
      return (channels,nchannels)
      
    def parameters(self):
      params = []
      for i in range(0,10):
        params.append(float(self.params.item(0,i).text()))
      return params
  
    def requestAcquire(self):
        (channels,nchannels) = self.activeChannels()
        print channels
        params = self.parameters()
        print params
        self.instrument.dispatch("AcquireV3"
        ,channels         #Channels to use
        ,int(self.numberOfSegments.text())     #Segments to read
        ,int(self.numberOfPoints.text())       #Points per segment
        ,11         #Should we average?
        ,1         #Tension
        ,0         #Delay
        ,params
        )
        
    def requestConfigure(self):
        self.instrument.dispatch("ConfigureV2"
         ,15               #usedChannels
         ,float(self.freqEch.text())           #freqEch
         ,float(self.sampleInterval.text())            #Sample interval
         ,11 # Averaging
         ,float(self.delayTime.text())               #Delay Time
         ,int(self.numberOfPoints.text())           #Number of points
         ,int(self.numberOfSegments.text())             #Number of segments
         ,100  #segments / trace
         ,float(self.fullscales[0].text())              #Fullscale 1
         ,float(self.offsets[0].text())               #Offset 1
         ,self.couplings[0].itemData(self.couplings[0].currentIndex()).toInt()[0]               #Coupling 1
         ,self.bandwidths[0].itemData(self.bandwidths[0].currentIndex()).toInt()[0]                #Bandwidth 1
         ,float(self.fullscales[1].text())              #Fullscale 2
         ,float(self.offsets[1].text())               #Offset 2
         ,self.couplings[1].itemData(self.couplings[1].currentIndex()).toInt()[0]               #Coupling 2
         ,self.bandwidths[1].itemData(self.bandwidths[1].currentIndex()).toInt()[0]                #Bandwidth 2
         ,float(self.fullscales[2].text())              #Fullscale 3
         ,float(self.offsets[2].text())               #Offset 3
         ,self.couplings[2].itemData(self.couplings[2].currentIndex()).toInt()[0]               #Coupling 3
         ,self.bandwidths[2].itemData(self.bandwidths[2].currentIndex()).toInt()[0]                #Bandwidth 3
         ,float(self.fullscales[3].text())              #Fullscale 4
         ,float(self.offsets[3].text())               #Offset 4
         ,self.couplings[3].itemData(self.couplings[3].currentIndex()).toInt()[0]               #Coupling 4
         ,self.bandwidths[3].itemData(self.bandwidths[3].currentIndex()).toInt()[0]                #Bandwidth 4
         ,self.trigger.itemData(self.trigger.currentIndex()).toInt()[0]                 #Trigger
         ,self.triggerCoupling.itemData(self.triggerCoupling.currentIndex()).toInt()[0]                #Trigger Coupling
         ,self.triggerSlope.itemData(self.triggerSlope.currentIndex()).toInt()[0]                #Trigger Slope
         ,float(self.triggerLevel.text())           #Trigger Level
         ,1               #Synchro 10 MHz
         ,1                                       #Converters per Channel
         ,1 #NbPtToMax
         ,1
         )
        
    def requestCalibrate(self):
       self.instrument.dispatch("CalibrateV1",CAL_TOUT,1)
        
    def update(self,subject,property = None, value =None, message = None):
      if subject==self.instrument:
          if property == "temperature":
            self.tempLabel.setText("Temperature:"+str(value))
          elif property == "error_str":
            self.logBook.write(time.strftime("%H:%M:%S",time.localtime())+" : ERROR: "+str(value)+"\n")
          elif property == "status_str":
            self.logBook.write(time.strftime("%H:%M:%S",time.localtime())+" : "+str(value)+"\n")
          elif property == "data":
            points = int(self.numberOfPoints.text())
            segments = int(self.numberOfSegments.text())
            (channels,nchannels) = self.activeChannels()
            if len(value)>=points*nchannels:
              print nchannels
              print "Updating..."
              xvalues = range(0,points)
              self.plots["traces"].axes.plot(xvalues,value[0:points],xvalues,value[points*1:points*2])
              self.plots["traces"].draw()
              self.plots["iqplot"].axes.scatter(value[points*nchannels+segments:points*nchannels+segments*2],value[points*nchannels+segments*2:points*nchannels+segments*3])
              self.plots["iqplot"].draw()
              self.plots["histo"].axes.scatter(range(0,len(value)),value)
              self.plots["histo"].draw()
      return 0
    
    def __init__(self,instrument,parent=None):
        super(Panel,self).__init__(instrument,parent)

        self.setWindowTitle("Acqiris Control Panel")
        
        self.tempLabel=QLabel("Temperature:")
        self.errorString=QLabel("")
        self.messageString = QLabel("")        
 
        updateButton = QPushButton("Acquire")
        configureButton = QPushButton("Configure")
        calibrateButton = QPushButton("Calibrate")

        self.connect(updateButton,SIGNAL("clicked()"),self.requestAcquire)
        self.connect(calibrateButton,SIGNAL("clicked()"),self.requestCalibrate)
        self.connect(configureButton,SIGNAL("clicked()"),self.requestConfigure)
        
        self.plots = dict()
        
        self.plots["traces"] = MyStaticMplCanvas(self, width=5, height=4, dpi=100)
        self.plots["iqplot"] = MyStaticMplCanvas(self, width=5, height=4, dpi=100)
        self.plots["histo"] = MyStaticMplCanvas(self, width=5, height=4, dpi=100)
        
        self.logBook = Log()
        self.logBook.setReadOnly(True)
        

        self.grid = QGridLayout()
        
        buttonGrid = QGridLayout()
        
        buttonGrid.addWidget(updateButton,0,0)
        buttonGrid.addWidget(configureButton,0,1)
        buttonGrid.addWidget(calibrateButton,0,2)
        
        self.grid.addWidget(self.tempLabel,0,0)
        self.grid.addItem(buttonGrid,7,1)
        
        self.plotTabs = QTabWidget()
        self.plotTabs.setMinimumHeight(400)
        
        self.plotTabs.addTab(self.plots["traces"],"Traces")
        self.plotTabs.addTab(self.plots["iqplot"],"IQ plot")
        self.plotTabs.addTab(self.plots["histo"],"Histogram")
        
        self.grid.addWidget(self.plotTabs,3,0)
        self.grid.addWidget(self.logBook,6,0,1,2)
        
        self.iGrid = QGridLayout()
        self.iGrid.setSpacing(10)
        
        
        self.couplings = list()
        self.fullscales = list()
        self.offsets = list()
        self.bandwidths = list()
        self.active = list()
              
        for i in range(0,4):
          
          couplings = QComboBox()
          couplings.addItem("Ground",0)
          couplings.addItem("DC 1 MO",1)
          couplings.addItem("AC 1 MO",2)
          couplings.addItem("DC 50 O",3)
          couplings.addItem("AC 50 O",4)
          
          couplings.setCurrentIndex(3)
          
          bandwidths = QComboBox()
          
          bandwidths.addItem("no limit",0)
          bandwidths.addItem("25  MHz",1)
          bandwidths.addItem("700 MHz",2)
          bandwidths.addItem("200 MHz",3)
          bandwidths.addItem("20  MHz",4)
          bandwidths.addItem("35  MHz",5)
          
          bandwidths.setCurrentIndex(3)
          
          active = QCheckBox("Active?")
          
          self.couplings.append(couplings)
          self.fullscales.append(QLineEdit("5.0"))
          self.bandwidths.append(bandwidths)
          self.active.append(active)
          
          offsets = ["-0.391666","-0.00150812","0.0","0.0"]
          
          self.offsets.append(QLineEdit(offsets[i]))
          self.iGrid.addWidget(QLabel("Coupling "+str(i+1)),0,i)
          self.iGrid.addWidget(self.couplings[i],1,i)
          self.iGrid.addWidget(QLabel("Fullscale "+str(i+1)),2,i)
          self.iGrid.addWidget(self.fullscales[i],3,i)
          self.iGrid.addWidget(QLabel("Offset "+str(i+1)),4,i)
          self.iGrid.addWidget(self.offsets[i],5,i)
          self.iGrid.addWidget(QLabel("Bandwidth "+str(i+1)),6,i)
          self.iGrid.addWidget(self.bandwidths[i],7,i)
          self.iGrid.addWidget(self.active[i],8,i)
          print i

        self.grid.addItem(self.iGrid,2,0,1,1)

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
        
        self.numberOfSegments = QLineEdit("1000")        
        self.paramsGrid.addWidget(QLabel("Number of segments"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.numberOfSegments,self.paramsGrid.rowCount(),0)

        
        self.memoryType = QComboBox()     
        
        self.memoryType.addItem("Default",0)
        self.memoryType.addItem("Force Internal",1)
           
        self.paramsGrid.addWidget(QLabel("Memory Type"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.memoryType,self.paramsGrid.rowCount(),0)

        self.trigger = QComboBox()        
        
        self.trigger.addItem("External 1",-1)
        self.trigger.addItem("Internal 1",1)
        self.trigger.addItem("Internal 2",2)
        self.trigger.addItem("Internal 3",3)
        self.trigger.addItem("Internal 4",4)
        
        self.paramsGrid.addWidget(QLabel("Trigger"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.trigger,self.paramsGrid.rowCount(),0)

        self.triggerCoupling = QComboBox()    
        
        self.triggerCoupling.addItem("DC",0)
        self.triggerCoupling.addItem("AC",1)
        self.triggerCoupling.addItem("HF Reject",2)
        self.triggerCoupling.addItem("DC 50 O",3)
        self.triggerCoupling.addItem("AC 50 O",4)
            
        self.paramsGrid.addWidget(QLabel("Trigger Coupling"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.triggerCoupling,self.paramsGrid.rowCount(),0)

        self.triggerSlope = QComboBox()      
        
        self.triggerSlope.addItem("Positive",0)
        self.triggerSlope.addItem("Negative",1)
        self.triggerSlope.addItem("out of Window",2)
        self.triggerSlope.addItem("into Window",3)
        self.triggerSlope.addItem("HF divide",4)
        self.triggerSlope.addItem("Spike Stretcher",5)
        
        self.triggerSlope.setCurrentIndex(1)
          
        self.paramsGrid.addWidget(QLabel("Trigger Slope"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.triggerSlope,self.paramsGrid.rowCount(),0)

        self.triggerLevel = QLineEdit("500.0")        
        self.paramsGrid.addWidget(QLabel("Trigger Level (mV)"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.triggerLevel,self.paramsGrid.rowCount(),0)

        self.synchro = QLineEdit("1")        
        self.paramsGrid.addWidget(QLabel("Synchro 10 MHz"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.synchro,self.paramsGrid.rowCount(),0)

        self.rotation = QLineEdit("0")        
        self.paramsGrid.addWidget(QLabel("Bifurcation Map: Rotation"),self.paramsGrid.rowCount(),0)
        self.paramsGrid.addWidget(self.rotation,self.paramsGrid.rowCount(),0)
        
        self.params = QTableWidget()
        self.params.setRowCount(1)
        self.params.setColumnCount(10)
        self.params.setFixedHeight(60)
        
        params = [2,250,2,250,180,0,1,0,0,0]
        
        for i in range(0,10):
          item = QTableWidgetItem()
          item.setSizeHint(QSize(50,30))
          item.setText(str(params[i]))
          self.params.setColumnWidth(i,50)
          self.params.setItem(0,i,item)


        self.grid.addItem(self.paramsGrid,2,1,2,1)        

        self.grid.addWidget(QLabel("Bifurcation Map: Parameters"),4,0,1,2)
        self.grid.addWidget(self.params,5,0,1,2)

        self.setLayout(self.grid)
        