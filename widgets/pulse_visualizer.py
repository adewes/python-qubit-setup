from pyview.lib.classes import *
from pyview.lib.patterns import * 

class PulseVisualizer(ReloadableWidget,QMainWindow,ObserverWidget):
  
  def __init__(self,parent = None):
    QMainWindow.__init__(self,parent)
    ObserverWidget.__init__(self)
    ReloadableWidget.__init__(self)
    self._qubits = []
    self._graphs = []
    self._layout = QGridLayout()
    self.setLayout(self._layout)
    
  def addQubit(self,qubit):
    self._qubits.append(qubit)
    picture = QPicture()
    label = QLabel("")
    label.setPicture(picture) 
    qubit.attach(self)
    self._labels.append(label)
    self._layout.addWidget(label)
    
  def updateGraph(self,index,property,value):
    pass
    
  def updatedGui(self,subject,property,value = None,modifier = None):
    for i in range(0,len(self._qubits)):
      if subject == self._qubits[i]:
        self.updateGraph(i,property,value)