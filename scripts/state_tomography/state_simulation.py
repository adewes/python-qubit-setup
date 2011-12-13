#Some function definitions...

import numpy

class Dict:
	
	def __init__(self,dict):
		self.__dict__ = dict

globals()["state_simulation"] = Dict(locals())
from qulib import *
from numpy.linalg import *
from scripts.state_tomography.plot_density_matrix import *
import scipy.optimize
import random
import cmath

#We define the measurement operators...

def densityMatrixErrorFunction(x,measurements,measured,diagonalElements = None):
	if diagonalElements == None:
		rho = buildRho(x)
	else:
		rho = buildRho(diagonalElements+list(x))
	errorsum = 0		
	v = zeros(len(measurements))
	for i in range(0,len(measurements)):
		measurement = measurements[i]
		expected = real(trace(rho*measurement))
		p = (expected+1.0)/2.0
		var = 1.0
		var = abs(pow(trace(rho*measurement),2.0)-trace(rho*measurement*measurement))+0.01
		v[i]=pow(expected-measured[i],2.0)/var
	return v

def optimizeDensityMatrix(measurements,measuredValues,initialGuess,diagonalElements = None):
	result = scipy.optimize.leastsq(densityMatrixErrorFunction,initialGuess,args=(measurements,measuredValues,diagonalElements),xtol = 1e-9,ftol = 1e-9,maxfev=10000)
	return result[0]

def convertToSpins(tomographyData,inverseDetectorFunction,indices1=["x","y","z","i"],indices2=["x","y","z","i"],prefix = ''):

	
	if len(tomographyData.children(name = prefix+"spins")) > 0:
		measuredSpins = tomographyData.children(name = prefix+"spins")[0]
		measuredSpins.clear()
		measuredSpins.setName(prefix+"spins")
	else:
		measuredSpins = Datacube("spins")
		tomographyData.addChild(measuredSpins,name = prefix+"spins")
	if len(tomographyData.children(name = prefix+"probabilities")) > 0:
		measuredProbabilities = tomographyData.children(name = prefix+"probabilities")[0]
		measuredProbabilities.clear()
		measuredProbabilities.setName("probs")
	else:
		measuredProbabilities = Datacube("probs")
		tomographyData.addChild(measuredProbabilities,name = prefix+"probabilities")

	for t in range(0,len(tomographyData)):
	
		row = t
	
		for name in tomographyData.names():
			if len(name) < 2 or (len(name) >= 2 and name[2]!="p"):
				measuredSpins.set(**{name:tomographyData.column(name)[t]})
				measuredProbabilities.set(**{name:tomographyData.column(name)[t]})
	
	
		for i in indices1:
			for j in indices2:
				if i == "i" and j == "i":
					measuredSpins.set(**{i+j:1})
				elif i == "i":
					if not "z"+j+"p00" in tomographyData.names():
						continue
					probs = matrix([tomographyData.column("z"+j+"p00")[row],tomographyData.column("z"+j+"p10")[row],tomographyData.column("z"+j+"p01")[row],tomographyData.column("z"+j+"p11")[row]])	
					mapping = matrix([1,1,-1,-1])
				elif j == "i":			
					if not i+"z"+"p00" in tomographyData.names():
						continue
					probs = matrix([tomographyData.column(i+"z"+"p00")[row],tomographyData.column(i+"z"+"p10")[row],tomographyData.column(i+"z"+"p01")[row],tomographyData.column(i+"z"+"p11")[row]])
					mapping = matrix([1,-1,1,-1])
				else:
					if not i+j+"p00" in tomographyData.names():
						continue
					mapping = matrix([1,-1,-1,1])
					probs = matrix([tomographyData.column(i+j+"p00")[row],tomographyData.column(i+j+"p10")[row],tomographyData.column(i+j+"p01")[row],tomographyData.column(i+j+"p11")[row]])
				realProbs = inverseDetectorFunction*transpose(probs)
				if i != "i" and j != "i":
					probs = transpose(realProbs)[0].tolist()[0]
					values = ["00","10","01","11"]
					measuredProbabilities.set(**{i+j+"1x":probs[1]+probs[3],i+j+"x1":probs[2]+probs[3]})
					for k in range(0,len(values)):
						measuredProbabilities.set(**{i+j+values[k]:probs[k]})
				expectation = (mapping*realProbs)[0,0]
				if i != "i" or j != "i":
					measuredSpins.set(**{i+j:expectation})
		measuredSpins.commit()
		measuredProbabilities.commit()

	return (measuredSpins,measuredProbabilities)


def sqrtm(A):
	(eigenvals,eigenvecs) = eigh(A)
	return (eigenvecs)*diag(sqrt(eigenvals))*adjoint(eigenvecs)
	
def quantumFidelity(measuredRho,targetRho):
	return trace(sqrtm(measuredRho)*targetRho*sqrtm(measuredRho))


def simulateMeasurements(state,samples = 200):
	"""
	Simulates a set of measurement on a given quantum state
	"""
	
	qubits = int(log(float(state.shape[1]))/log(2.0))
	rho0 = adjoint(state)*state
	measurements = [sigmax,sigmay,sigmaz,-sigmax,-sigmay,-sigmaz,idatom]
	labels = ["x","y","z","mx","my","mz","i"]
	
	measuredSpins = Datacube()
	measuredProbabilities = Datacube()
	
	cs = map(lambda x:[x,createMeasurement(x)],generateCombinations(measurements,lambda x,y:tensor(x,y),2))
	measuredLabels = generateCombinations(labels,lambda x,y:x+y,2)
	
	for j in range(0,len(cs)):
		sum = 0
		measurement = cs[j]
		for i in range(0,samples):
			(value,rho) = measure(rho0,measurement[1])
			sum+=value+random.gauss(0,0.1)*0
		sum/=float(samples)
		measuredSpins.set(**{measuredLabels[j]:sum})
	measuredSpins.commit()
	return measuredSpins

def convertDatacubeToSpins(data,saveValues = False,indices1=["x","y","z","i"],indices2=["x","y","z","i"],correctDetectorErrors = True,detectorFunction=None,prefix = ''):
	if correctDetectorErrors:
		print "Correcting detector errors..."
		if detectorFunction==None:
			detector1 = matrix([[data.parameters()["qubit1"]["readout.p00"],1.0-data.parameters()["qubit1"]["readout.p11"]],[1.0-data.parameters()["qubit1"]["readout.p00"],data.parameters()["qubit1"]["readout.p11"]]])
			detector2 = matrix([[data.parameters()["qubit2"]["readout.p00"],1.0-data.parameters()["qubit2"]["readout.p11"]],[1.0-data.parameters()["qubit2"]["readout.p00"],data.parameters()["qubit2"]["readout.p11"]]])
			detectorFunction = tensor(detector1,detector2)
		inverseDetectorFunction = numpy.linalg.inv(detectorFunction)
	else:
		inverseDetectorFunction = matrix(eye(4))
	(measuredSpins,measuredProbabilities) = convertToSpins(data,inverseDetectorFunction,indices1=indices1,indices2=indices2,prefix = prefix)
	
	if saveValues:
		data.savetxt()

	return (measuredSpins,measuredProbabilities)


def fitDensityMatrix(measuredSpins,measuredProbabilities,hot = False,row = None,rounds = 10,initialGuess = None):

	if measuredSpins.column("mxmx") != None and False:
		matrices = [sigmax,sigmay,sigmaz,-sigmax,-sigmay,-sigmaz,idatom]
		labels = ["x","y","z","mx","my","mz","i"]
	else:
		matrices = [sigmax,sigmay,sigmaz,idatom]
		labels = ["x","y","z","i"]
	
	measurements = generateCombinations(matrices,lambda x,y:tensor(x,y),2)
	measuredLabels = generateCombinations(labels,lambda x,y:x+y,2)
	
	if row == None:
		measuredValues = map(lambda x: mean(measuredSpins.column(x)),measuredLabels)
	else:
		measuredValues = map(lambda x: measuredSpins.column(x)[row],measuredLabels)
	
	densityMatrix = matrix(zeros((4,4)))
	
	bestValue = None

	for j in range(0,rounds):
		print "Round %d" % j
		rhoGuess = (numpy.random.rand(4,4)+1j*numpy.random.rand(4,4)-numpy.random.rand(4,4)-1j*numpy.random.rand(4,4))*0.5
		if initialGuess != None:
			rhoGuess =initialGuess+rhoGuess*0.1
		if row != None:
			rhoGuess[0,0] = measuredProbabilities.column("zz00")[row]
			rhoGuess[1,1] = measuredProbabilities.column("zz10")[row]
			rhoGuess[2,2] = measuredProbabilities.column("zz01")[row]
			rhoGuess[3,3] = measuredProbabilities.column("zz11")[row]
		else:
			rhoGuess[0,0] = mean(measuredProbabilities.column("zz00"))
			rhoGuess[1,1] = mean(measuredProbabilities.column("zz10"))
			rhoGuess[2,2] = mean(measuredProbabilities.column("zz01"))
			rhoGuess[3,3] = mean(measuredProbabilities.column("zz11"))
		paramsGuess = parametrizeRho(rhoGuess)
	
		diagonalElements = list(paramsGuess[:3])
		
		fittedParams = optimizeDensityMatrix(measurements,measuredValues,paramsGuess[3:],diagonalElements)
		matrixParameters = vectorizeRho(buildRho(diagonalElements+list(fittedParams)))
	
		value = numpy.linalg.norm(densityMatrixErrorFunction(fittedParams,measurements,measuredValues,diagonalElements))

		if bestValue == None or value < bestValue:
			print "New best value: %g " % value
			bestValue = value
			densityMatrix = buildRho(diagonalElements+list(fittedParams))
			try:
				measuredSpins.parameters()["densityMatrix"] = densityMatrix.tolist()
				measuredSpins.savetxt(forceSave = True)
				if hot:
					plotDensityMatrix(densityMatrix,"rho")
					show()
			except:
				import traceback
				traceback.print_exc()
				print sys.exc_info()
	return densityMatrix	

def calculateCHSH(tomographyData,fit_data=True,detectorFunction = None):

	"""
	Calculates the value of the CHSH operator of a given dataset.
	"""

	print "CHSH..."

	(measuredSpins,measuredProbabilities) = convertDatacubeToSpins(tomographyData,indices1=["q","r"], indices2=["s","t"],saveValues = False,correctDetectorErrors = True,detectorFunction=detectorFunction)
	
	(measuredSpinsUncorrected,measuredProbabilitiesUncorrected) = convertDatacubeToSpins(tomographyData,indices1=["q","r"], indices2=["s","t"],saveValues = False,correctDetectorErrors = False,detectorFunction=detectorFunction,prefix = 'uncorrected_')

	measuredProbabilities.parameters()["defaultPlot"] = [("duration","zzp00"),("duration","zzp01"),("duration","zzp10"),("duration","zzp11")]
	
	chsh = measuredSpins["qs"]+measuredSpins["rs"]+measuredSpins["rt"]-measuredSpins["qt"]
	chsh_uncorrected = measuredSpinsUncorrected["qs"]+measuredSpinsUncorrected["rs"]+measuredSpinsUncorrected["rt"]-measuredSpinsUncorrected["qt"]
	
	measuredSpins.createColumn("chsh",chsh)
	measuredSpins.createColumn("chsh_uncorrected",chsh_uncorrected)
	measuredSpins.createColumn("sqrt(2)",[sqrt(2)]*len(measuredSpins))
	measuredSpins.createColumn("-sqrt(2)",[-sqrt(2)]*len(measuredSpins))
	measuredSpins.parameters()["defaultPlot"] = [["phi","chsh",{'ls':'','marker':'o'}]]

	#Make a fit of the CHSH data...
	if fit_data:
		fitfunc = lambda p,x: p[0]*sin(x/180.0*math.pi-p[1])
		errfunc = lambda p, x, y,ff: numpy.linalg.norm((ff(p,x)-y))
		
		ps = [(max(measuredSpins["chsh"])-min(measuredSpins["chsh"]))/2.,0]
		p1s = scipy.optimize.fmin(errfunc, ps,args=(measuredSpins["phi"],measuredSpins["chsh"],fitfunc),maxfun = 1e5,maxiter = 1e5)
		
		if p1s[0] < 0:
			p1s[0] = -p1s[0]
			p1s[1]+=math.pi
		measuredSpins.createColumn("chsh_fit",fitfunc(p1s,measuredSpins["phi"]))
		measuredSpins.createColumn("(2)",[2]*len(measuredSpins))
		
		measuredSpins.parameters()["defaultPlot"].append(["phi","chsh_fit"])
		measuredSpins.parameters()["defaultPlot"].extend([["phi","sqrt(2)"],["phi","-sqrt(2)"]])
		measuredSpins.parameters()["defaultPlot"].extend([["phi","(2)"]])
		
		measuredSpins.sortBy("phi")	
		measuredSpins.parameters()["chsh_fit"] = p1s.tolist()

	return measuredSpins

def calculateWs(tomographyData):

	(measuredSpins,measuredProbabilities) = convertDatacubeToSpins(tomographyData,indices1=["x","y","z","i"], indices2=["x","y","z","i"],saveValues = False)
	measuredProbabilities.parameters()["defaultPlot"] = [("duration","zzp00"),("duration","zzp01"),("duration","zzp10"),("duration","zzp11")]
	
	for i in range(0,len(measuredSpins)):
		
		w_psi_plus = 1./4.*(1-measuredSpins.column("xx")[i]+measuredSpins.column("yy")[i]-measuredSpins.column("zz")[i])
		w_psi_minus = 1./4.*(1+measuredSpins.column("xx")[i]-measuredSpins.column("yy")[i]-measuredSpins.column("zz")[i])
		w_phi_plus = 1./4.*(1-measuredSpins.column("xx")[i]-measuredSpins.column("yy")[i]+measuredSpins.column("zz")[i])
		w_phi_minus = 1./4.*(1+measuredSpins.column("xx")[i]+measuredSpins.column("yy")[i]+measuredSpins.column("zz")[i])
	
		measuredSpins.setAt(i,w_psi_minus = w_psi_minus,w_psi_plus = w_psi_plus,w_phi_minus = w_phi_minus,w_phi_plus = w_phi_plus)
		measuredSpins.setAt(i,maxv = 0.5,minv = -0.5)
	
	#Make a fit of the data...
	
	fitfunc = lambda p,x: p[0]+p[1]*sin(p[2]+x/180.0*math.pi)
	errfunc = lambda p, x, y,ff: numpy.linalg.norm((ff(p,x)-y))
	
	ps = [0,0.5,0]
	p1s = scipy.optimize.fmin(errfunc, ps,args=(measuredSpins["phi"],measuredSpins["w_phi_plus"],fitfunc),maxfun = 1e5,maxiter = 1e5)
	measuredSpins.createColumn("w_phi_plus_fit",fitfunc(p1s,measuredSpins["phi"]))
	p1s[2]+=math.pi
	measuredSpins.createColumn("w_phi_minus_fit",fitfunc(p1s,measuredSpins["phi"]))
	
	measuredSpins.parameters()["defaultPlot"] = [["phi","w_phi_plus",{'ls':'','marker':'o'}],["phi","w_phi_minus",{'ls':'','marker':'o'}],["phi","w_phi_plus_fit"],["phi","w_phi_minus_fit"],["phi","w_psi_plus",{'ls':'','marker':'o'}],["phi","w_psi_minus",{'ls':'','marker':'o'}],["phi","maxv"],["phi","minv"]]
	
	measuredSpins.sortBy("phi")


print "State simulation loaded..."