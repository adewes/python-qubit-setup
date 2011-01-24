from macros.qubit_functions import *
from lib.datacube import *
from helpers.instrumentManager import *

class FluxlineCrosstalk(Macro):

  def __init__(self):
    self._qubits = []
    self._fluxlines = []
    self._jbas = []
    self._qubitFrequenciesDatacube = Datacube("Qubit Frequencies")
    self._crosstalkCoefficients = Datacube("Crosstalk coefficients")
    
  def setQubitFrequenciesDatacube(self,cube):
    self._qubitFrequenciesDatacube = cube
    
  def qubitFrequenciesDatacube(self):
    return self._qubitFrequenciesDatacube
    
  def addQubit(self,qubit,fluxline)
    self._qubits.append(qubit)
    self._fluxlines.append(fluxline)
    self._jbas.append(jba)
    
  def measureQubitFrequencies(self,i = 0,voltages,searchRange):
    survey = Datacube("Qubit %d frequency survey" % i)
    for i in range(0,len(self._qubits)):
      self._qubits[i].turnOffDrive()

    for voltage in voltages:
      self._fluxlines[i].setOffset(voltage)
      self._jbas[i].adjustSwitchingOffset()
    	spectro = Datacube("Qubit %i Spectroscopy" % i)    	
    	survey.addChild(spectro)
    	
    	measureSpectroscopy(self._qubits[i],searchRange,spectro,power = -40)
    		
    	(params2,r2) = fitQubitFrequency(spectro2,variable = "px1")
    
    	print "Qubit 2 at %g GHz" % (params2[1])
    
    	qubit2Survey.set(f2 = params2[1],v1 = v1,v2 = v2,rsquare = r2)
    	qubit2Survey.commit()
    
    	qubit2SearchRange = arange(params2[1]-0.3,params2[1]+0.3,0.002)
    
    	survey.savetxt()

          
  def measureCrosstalk(self,qubit1,qubit2,)