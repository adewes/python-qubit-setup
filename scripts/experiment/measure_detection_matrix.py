data = Datacube("Measurement Crosstalk")
dataManager.addDatacube(data)
data.setParameters(instrumentManager.parameters())
for phi in linspace(0,math.pi,4):
	qubit1.loadRabiPulse(phase = phi,readout = qubit1.parameters()["timing.readout"])
	subcube = Datacube("phi = %d deg" % (int(phi*180.0/math.pi)))
	data.addChild(subcube)
	data.set(phi = phi)
	data.commit()
	acqiris.bifurcationMap(ntimes = 40)
	for psi in linspace(0,math.pi,4):
		qubit2.loadRabiPulse(phase = psi,readout = qubit2.parameters()["timing.readout"])
		acqiris.bifurcationMap(ntimes = 400)
		subcube.set(psi = psi)
		subcube.set(**acqiris.Psw())
		subcube.commit()		
crosstalkData = data
##
figure("crosstalk")
m = zeros((len(data)-1,len(data.childrenAt(0)[0])))
for i in range(0,len(data)-1):
	m[i,:] = data.childrenAt(i)[0].column("p1x")
cla()
imshow(m,aspect = 'auto',interpolation = 'nearest')
##Reconstruct the detection matrix of the system based on the measured probabilities

import scipy.stats

def buildDetectorMatrix(params):
	m = matrix(zeros((4,4)))
	for i in range(0,4):
		sum = 0
		for j in range(0,3):
			p = abs(params[i*3+j])
			p = p-floor(p)
			m[j,i] = p
			sum += p
		if sum > 1:
			m[j,:] /= sum
		else:
			m[3,i] = 1-sum
	return m

def parametrizeDetectorMatrix(m):
	params = zeros(12)
	for i in range(0,4):
		for j in range(0,3):
			params[i*3+j] = m[j,i]
	return params


def crosstalkErrorFunction(params,measuredValues,verbose = False):
	detectorMatrix = buildDetectorMatrix(params)
	errorSum = 0
	for i in range(0,len(measuredValues)):
		p1x = (-cos(measuredValues.column("phi")[i])+1.0)/2.0
		subcube = measuredValues.childrenAt(i)[0]
		for j in range(0,len(subcube)):
			px1 = (-cos(subcube.column("psi")[j])+1.0)/2.0
			measuredProbs = zeros(4)
			realProbs = zeros(4)
			realProbs[0] = (1.0-p1x)*(1.0-px1)
			realProbs[1] = (p1x)*(1.0-px1)
			realProbs[2] = (1.0-p1x)*(px1)
			realProbs[3] = (p1x)*(px1)

			measuredProbs[0] = subcube.column("p00")[j]
			measuredProbs[1] = subcube.column("p10")[j]
			measuredProbs[2] = subcube.column("p01")[j]
			measuredProbs[3] = subcube.column("p11")[j]

			expectedProbs = array(transpose(detectorMatrix*transpose(matrix(realProbs))))[0]
			
			p1x_expected = expectedProbs[1]+expectedProbs[3]
			px1_expected = expectedProbs[2]+expectedProbs[3]

			if verbose:
				print realProbs,measuredProbs,expectedProbs

			errorSum+= pow(numpy.linalg.norm(transpose(expectedProbs)-matrix(measuredProbs)),2.0)

	return errorSum

##

from qulib import *

detector1 = matrix([[data.parameters()["qubit1"]["readout.p00"],1.0-data.parameters()["qubit1"]["readout.p11"]],[1.0-data.parameters()["qubit1"]["readout.p00"],data.parameters()["qubit1"]["readout.p11"]]])
detector2 = matrix([[data.parameters()["qubit2"]["readout.p00"],1.0-data.parameters()["qubit2"]["readout.p11"]],[1.0-data.parameters()["qubit2"]["readout.p00"],data.parameters()["qubit2"]["readout.p11"]]])
detectorFunction = tensor(detector1,detector2)

params = parametrizeDetectorMatrix(detectorFunction)

print crosstalkErrorFunction(params,crosstalkData,verbose = True)
##
p1s = scipy.optimize.fmin(crosstalkErrorFunction,params,args = [crosstalkData])
print buildDetectorMatrix(p1s),"\n",detectorFunction
print crosstalkErrorFunction(p1s,crosstalkData,verbose = False)
##
print buildDetectorMatrix(p1s)