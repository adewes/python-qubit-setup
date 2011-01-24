#Some function definitions...
from qulib import *
from numpy.linalg import *
import scipy.optimize
import random

g = matrix([1,0])
e = matrix([0,1])

#We define the measurement operators...

state_x = 1.0/sqrt(2.0)*matrix([1,1]).transpose()
state_y = 1.0/sqrt(2.0)*matrix([1,1j]).transpose()
state_z = matrix([0,1]).transpose()

proj_x = sigmax.copy()
proj_y = sigmay.copy()
proj_z = sigmaz.copy()


def generateMeasurementCombinationsNames(qubit,measurement,measurements,nqubits):
	"""
	Generates all possible combinations in a set of measurements for "nqubits" qubits.
	"""
	ms = []
	if qubit >= nqubits:
		return measurement
	for m in measurements:
		if measurement == None:
			ms.append(generateMeasurementCombinationsNames(qubit+1,m,measurements,nqubits))
		else:
			ms.append(generateMeasurementCombinationsNames(qubit+1,measurement+m,measurements,nqubits))
	return ms

##Generate and simulate the characterization of a qubit state

#A three qubit state:
#state = tensor(tensor(e,e),e)+tensor(tensor(g,g),g)*1j

#A two qubit state

state = tensor(e,g)*sqrt(0.8)+tensor(g,g)*sqrt(0.1)+tensor(e,e)*sqrt(0.1)

state = state/norm(state)

qubits = int(log(float(state.shape[1]))/log(2.0))

#We generate rho
rho0 = adjoint(state)*state
print rho0

#The measurements that we want to perform on each qubit...
measurements = [proj_x,proj_y,proj_z]

cs = generateMeasurementCombinations(0,None,measurements,qubits)

print len(cs)

measuredValues = []
expectedValues = []

samples = 200.0

for measurement in cs:
	sum = 0
	for i in range(0,samples):
		(value,rho) = measure(rho0,measurement[1])
		sum+=value
	sum/=float(samples)
	measuredValues.append(sum)
	expectedValues.append(trace(rho0*measurement[0]))
	
print measuredValues
print expectedValues
##Load some experimental data

#1 qubit measurement

#Maps the measured probabilities to spin expectation values:

if tomographyData.column("mxmxpx1") != None and False:
	indices = ["x","y","z","mx","my","i"]
else:
	indices = ["x","y","z","i"]
#detector1 = matrix([[qubit1.parameters()["readout.p00"],1-qubit1.parameters()["readout.p11"]],[1-qubit1.parameters()["readout.p00"],qubit1.parameters()["readout.p11"]]])
#detector2 = matrix([[qubit2.parameters()["readout.p00"],1-qubit2.parameters()["readout.p11"]],[1-qubit2.parameters()["readout.p00"],qubit2.parameters()["readout.p11"]]])

detector1 = matrix([[0.85,0.23],[0.15,0.77]])
detector2 = matrix([[0.77,0.23],[0.23,0.77]])

detectorFunction = tensor(detector1,detector2)

#detectorFunction = matrix(eye(4))

import numpy.linalg
import numpy

inverseDetectorFunction = numpy.linalg.inv(detectorFunction)

measuredTimes = []

measuredSpins = Datacube("Measured spins")
dataManager.addDatacube(measuredSpins)

probabilityMeasurements = []

for t in range(0,len(tomographyData)):

	row = t

	print "t = %g " % t


	measuredValues = []

	times = tomographyData.column("duration")
	
	measuredSpins.set(t = times[t])

	for i in indices:
		for j in indices:
			print i+j
			if i == "i" and j == "i":
				measuredSpins.set(**{i+j:1})
			elif i == "i":
				probs = matrix([tomographyData.column("z"+j+"p00")[row],tomographyData.column("z"+j+"p10")[row],tomographyData.column("z"+j+"p01")[row],tomographyData.column("z"+j+"p11")[row]])
				mapping = matrix([1,1,-1,-1])
			elif j == "i":			
				probs = matrix([tomographyData.column(i+"z"+"p00")[row],tomographyData.column(i+"z"+"p10")[row],tomographyData.column(i+"z"+"p01")[row],tomographyData.column(i+"z"+"p11")[row]])
				mapping = matrix([1,-1,1,-1])
			else:
				mapping = matrix([1,-1,-1,1])
				probs = matrix([tomographyData.column(i+j+"p00")[row],tomographyData.column(i+j+"p10")[row],tomographyData.column(i+j+"p01")[row],tomographyData.column(i+j+"p11")[row]])
			realProbs = inverseDetectorFunction*transpose(probs)
			if i != "i" and j != "i":
				probabilityMeasurements.extend(transpose(realProbs)[0].tolist()[0])
			expectation = (mapping*realProbs)[0,0]
			#print i+j," real probabilities: ",realProbs,probs,expectation
			measuredValues.append(expectation)
			if i != "i" or j != "i":
				measuredSpins.set(**{i+j:expectation})
	
	measuredSpins.commit()

	measuredTimes.append(measuredValues)

##We define the error and fit functions

def error_function(x,measurements,measured):
	rho = buildRho(x)
	errorsum = 0		
	v = zeros(len(measurements))
	for i in range(0,len(measurements)):
		measurement = measurements[i]
		expected = real(trace(rho*measurement))
		p = (expected+1.0)/2.0
		p10 = 0.2*0.2
		p11 = 0.8*0.8
		var = p*p*pow((p10-p11),2)+p11*p11+2.0*p11*p*(p10-p11)-p11-p*(p10-p11)
		var = -var
#		D = transpose(detectorFunction)*detectorFunction
#		var = 1e-1+trace(rho*measurement*measurement)-pow(trace(rho*measurement),2.0)
#		var = 0.1+max(0,p*(1.0-p))
		v[i]=pow(expected-measured[i],2.0)/var
	return v

def fitDensityMatrix(measurements,measuredValues,initialGuess ):
	if initialGuess == None:
		dim = pow(2,qubits)
		nparams = int((dim*dim*0.5+0.5*dim)*2)
		params = [1.0]*nparams
		initialGuess = params
#	result = scipy.optimize.fmin(lambda *args:numpy.linalg.norm(error_function(*args)),initialGuess,args=(measurements,measuredValues),xtol = 1e-9,ftol = 1e-9)
#	return result
	result = scipy.optimize.leastsq(error_function,initialGuess,args=(measurements,measuredValues),xtol = 1e-9,ftol = 1e-9)
	return result[0]
##Fit the whole time series...

timeData = Datacube("Tomography time data",dtype = complex128)
#dataManager.addDatacube(timeData)

densityMatrices = []

matrices = [sigmax,sigmay,sigmaz]

paramsGuess = None

projectors = map(lambda x:createMeasurement(x),matrices)

outcomes = [1,-1]
labels = ["0","1"]

measurements = []
measurementLabels = []

for projector_i in projectors:
	for projector_j in projectors:
		for outcome_i in outcomes:
			for outcome_j in outcomes:
				measurements.append(tensor(projector_i[outcome_i],projector_j[outcome_j]))

#Or use the classical basis
if tomographyData.column("mxmxpx1") != None and False:
	matrices = [sigmax,sigmay,sigmaz,-sigmax,-sigmay,idatom]
else:
	matrices = [sigmax,sigmay,sigmaz,idatom]
measurements = generateCombinations(matrices,lambda x,y:tensor(x,y),2)

densityMatrix = None

import numpy.random

for t in [26]:
	print "t = %g " % t
	measuredValues = measuredTimes[t]
	timeData.set(t = t)

	bestValue = None

	reconstructedRho = reconstructDensityMatrix(measurements,measuredValues)

	densityMatrix = reconstructedRho

	for i in range(0,300):

		print "Round %d" % i

		if densityMatrix == None or True:
			paramsGuess = parametrizeRho(
				matrix
					(
						[
						[abs(probabilityMeasurements[-4])+random.gauss(0,0.1),0,0,0],
						[0,abs(probabilityMeasurements[-2])+random.gauss(0,0.1),0,0],
						[0,0,abs(probabilityMeasurements[-3])+random.gauss(0,0.1),0],
						[0,0,0,abs(probabilityMeasurements[-1])+random.gauss(0,0.1)],
						]
					)
				)
		else:
			paramsGuess = parametrizeRho(densityMatrix)
			paramsGuess = map(lambda k:k+random.gauss(0,0.1),paramsGuess)
		
		#rhoGuess = reconstructedRho+numpy.random.normal(0,0.3,(4,4))+1j*numpy.random.normal(0,0.3,(4,4))

		paramsGuess = parametrizeRho(numpy.random.rand(4,4)+1j*numpy.random.rand(4,4)-(numpy.random.rand(4,4)+1j*numpy.random.rand(4,4)))
#		paramsGuess = parametrizeRho(zeros((4,4))+0.25+numpy.random.normal(0,0.1,(4,4)))
		paramsGuess = parametrizeRho(densityMatrix)
		paramsGuess = paramsGuess+numpy.random.normal(0,0.1,len(paramsGuess))
		
		print numpy.linalg.norm(error_function(paramsGuess,measurements,measuredValues))
		
		fittedParams = fitDensityMatrix(measurements,measuredValues,paramsGuess)
		matrixParameters = vectorizeRho(buildRho(fittedParams))
		
		value = numpy.linalg.norm(error_function(fittedParams,measurements,measuredValues))


		if bestValue == None or value < bestValue:
			print "New best value: %g " % value
			bestValue = value
			densityMatrix = buildRho(fittedParams)
			try:
				plotDensityMatrix(densityMatrix,"rho")
			except:
				pass

	densityMatrices.append(densityMatrix)

print densityMatrix

##

print "State simulation:" + "qubit setup\scripts\state tomography\state simulation.py"

matrices = [sigmax,sigmay,sigmaz]

projectors = map(lambda x:createMeasurement(x),matrices)

outcomes = [1,-1]
labels = ["0","1"]

measurements = []
measurementLabels = []

for projector_i in projectors:
	for projector_j in projectors:
		for outcome_i in outcomes:
			for outcome_j in outcomes:
				measurements.append(tensor(projector_i[outcome_i],projector_j[outcome_j]))

matrices = [sigmax,sigmay,sigmaz,idatom]

measurements = generateCombinations(matrices,lambda x,y:tensor(x,y),2)

from numpy.linalg import norm
import random

state = tensor(es+1j*gs,es+1j*gs)

state = state/norm(state)

originalDensityMatrix = adjoint(state)*state

densityMatrix = originalDensityMatrix

measuredValues = []

for m in measurements:
	v = trace(originalDensityMatrix*m)
	var = 0.05+(v+1.0)/2.0*0.3*0
	measuredValues.append(v+random.gauss(0,var))

reconstructedRho = reconstructDensityMatrix(measurements,measuredValues)

print reconstructedRho

bestParams = None
minError = None

for i in range(0,20):

	print i

	paramsGuess = parametrizeRho(originalDensityMatrix)
	
	fittedParams = fitDensityMatrix(measurements,measuredValues,paramsGuess)
	matrixParameters = vectorizeRho(buildRho(fittedParams))
	
	error = numpy.linalg.norm(error_function(fittedParams,measurements,measuredValues))

	if bestParams == None or error < minError:
		bestParams = fittedParams
		minError = error
		print error
		densityMatrix = buildRho(bestParams)

print "After ML fitting:"
print densityMatrix

##3D plotting of density matrix
#densityMatrix = densityMatrices[0]

fig = figure("3D density matrix")
clf()
cla()
from mpl_toolkits.mplot3d import Axes3D

import numpy as np

ax = Axes3D(fig)

dim = densityMatrix.shape[0]

xpos = []
ypos = []
zpos = [0]*dim*dim

dx = [0.5]*dim*dim
dy = [0.5]*dim*dim
dz = []


for x in range(0,dim):
	for y in range(0,dim):
		xpos.append(x)
		ypos.append(y)
		dz.append(abs(densityMatrix[x,y]))


#ax.set_xticklabels(["00","10","01","11"])
ax.bar3d(xpos, ypos, zpos, dx,dy,dz, color='b')
#ax.set_xticks([0,1,2,3])
#ax.set_xlabel("test")

draw()

##Plot and print the results

#densityMatrix = (densityMatrices[0]+densityMatrices[1]+densityMatrices[2])/3
#densityMatrix = densityMatrices[0]

rcParams["font.size"] = 10

labels = []
texts = ['0','1']


labels = generateCombinations(texts,lambda x,y:x+y,4)

figure("results new",figsize = (8,2))
subplot(111)
cla()
title("Real component")
l = range(0,len(vectorizeRho(densityMatrix)))
l2 = map(lambda x: x+0.5,l)
#bar(l,real(vectorize(rho0)),color = 'r',width = 0.5)
bar(l,real(vectorizeRho(densityMatrix)),color = 'g',align = 'edge',width = 0.5,label = 'real')
bar(l2,imag(vectorizeRho(densityMatrix)),color = 'r',align = 'edge',width = 0.5,label = 'imaginary')
legend()
#ylim(-1,1)
xticks(l2,labels)
