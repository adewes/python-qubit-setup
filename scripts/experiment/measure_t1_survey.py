survey = Datacube("T1 survey - qubit 1")
dataManager.addDatacube(survey)
automaticT1(qubit1,[0.35]*10,arange(5.2,6.2,0.002),jba1,variable = "p1x",datacube = survey,savename = "t1-survey",cavity = 6.7,voltageRead = afg2.amplitude,voltageWrite = afg2.setAmplitude)
##
reload(sys.modules["macros.qubit_functions"])
from macros.qubit_functions import *
survey = Datacube("T1 survey - qubit 1")
dataManager.addDatacube(survey)
jba1.calibrate()
automaticT1(qubit1,list(arange(1.05,1.5,0.05))+list(arange(1.5,0.05,-0.05)),arange(5.3,6.0,0.002),jba1,variable = "p1x",datacube = survey,savename = "t1-survey",cavity = 6.7,voltageRead = afg1.amplitude,voltageWrite = afg1.setAmplitude,delay = 500)
