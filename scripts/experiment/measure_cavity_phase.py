phaseData = Datacube("phase data")
import math
phaseData.setParameters(instrumentManager.parameters())

dataManager.addDatacube(phaseData)

df = 0.0005

mwg = cavity2_mwg
channels = [2,3]

for f in arange(6.65,6.8,df):
	mwg.setFrequency(f)	
	acqiris.bifurcationMap()
	phaseData.set(f = f)
	I = mean(acqiris.averages()[channels[0]])
	Q = mean(acqiris.averages()[channels[1]])
	phaseData.set(i = I,q = Q)
	phaseData.commit()	

##
iA = max(phaseData.column("i"))-min(phaseData.column("i"))
qA = max(phaseData.column("q"))-min(phaseData.column("q"))

import numpy.linalg

def fitFunction(p,x):
	return p[0]+p[1]*cos(math.pi*2.0*x*p[2]+p[3])

def errorFunction(p,x,y):
	
	yFit = fitFunction(p,x)
	
	return numpy.linalg.norm(yFit-y)

phaseData.createColumn("i",(phaseData.column("i")-mean(phaseData.column("i")))/iA)
phaseData.createColumn("q",(phaseData.column("q")-mean(phaseData.column("q")))/qA)

pI = [0,0.5,65,-1.]

import scipy.optimize

pIo = scipy.optimize.fmin(errorFunction,pI,args = (phaseData.column("f")[:10],phaseData.column("i")[:10]))

print pIo

phaseData.createColumn("i_fit",fitFunction(pIo,phaseData.column("f")))


##

def fourierParameters(signal):
	
	fft = numpy.fft.rfft(signal)

	mf = argmax(abs(fft[1:]))+1

	#Returns offset, amplitude,frequency and phase
	return (abs(fft[0])/len(signal),abs(fft[mf])/len(signal)*2,float(mf)*2,angle(fft[mf]))

iParams = fourierParameters(phaseData.column("i"))
qParams = fourierParameters(phaseData.column("q"))

phaseData.createColumn("i_normalized",(phaseData.column("i")-iParams[0]))
qc = sqrt(1-pow(cos(iParams[0]-qParams[0]+math.pi/2.0),2))
phaseData.createColumn("q_normalized",(phaseData.column("q")-qParams[0])*iParams[1]/qParams[1]*qc)

phaseData.createColumn("phase",arctan2(phaseData.column("q_normalized"),phaseData.column("i_normalized")))
phaseData.createColumn("amplitude",sqrt(pow(phaseData.column("q_normalized"),2)+pow(phaseData.column("i_normalized"),2)))

phase = phaseData.column("phase")

dphi = 0

newPhase = []

for i in range(0,len(phase)-1):
	newPhase.append(phase[i]+dphi)
	if phase[i+1]-phase[i] > math.pi:
		dphi-=math.pi*2.0
	elif phase[i+1]-phase[i] < -math.pi:
		dphi+=math.pi*2.0
newPhase.append(phase[-1]+dphi)
newPhase = array(newPhase)
diff = max(newPhase)-min(newPhase)
newPhase += diff*linspace(0,1,len(newPhase))
phaseData.createColumn("flatPhase",newPhase)
##
figure("phase")
cla()
plot(phaseData.column("phase")+linspace(0,20.0,len(phaseData.column("phase"))))