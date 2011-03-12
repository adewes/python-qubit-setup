#Some function definitions...
from qulib import *
from numpy.linalg import *
import scipy.optimize
import random

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

def convertToSpins(tomographyData,inverseDetectorFunction,indices1=["x","y","z","i"],indices2=["x","y","z","i"]):

	measuredSpins = Datacube("Measured spins")
	measuredProbabilities = Datacube("Measured probabilities")


	for t in range(0,len(tomographyData)):
	
		row = t
	
		print "row = %g " % t
	
		for name in tomographyData.names():
			if name[2]!="p":
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

def convertDatacubeToSpins(data,saveValues = False,deleteOldData = False,indices1=["x","y","z","i"],indices2=["x","y","z","i"]):

	detector1 = matrix([[data.parameters()["qubit1"]["readout.p00"],1.0-data.parameters()["qubit1"]["readout.p11"]],[1.0-data.parameters()["qubit1"]["readout.p00"],data.parameters()["qubit1"]["readout.p11"]]])
	detector2 = matrix([[data.parameters()["qubit2"]["readout.p00"],1.0-data.parameters()["qubit2"]["readout.p11"]],[1.0-data.parameters()["qubit2"]["readout.p00"],data.parameters()["qubit2"]["readout.p11"]]])
	
	detectorFunction = tensor(detector1,detector2)
	inverseDetectorFunction = numpy.linalg.inv(detectorFunction)
	
	(measuredSpins,measuredProbabilities) = convertToSpins(data,inverseDetectorFunction,indices1=indices1,indices2=indices2)
	if "cnt" in data.names():
		measuredSpins.createColumn("cnt",data.column("cnt"))

	if deleteOldData:
		data.removeChildren(data.allChildren())

	data.addChild(measuredSpins)
	data.addChild(measuredProbabilities)
	if saveValues:
		data.savetxt()

	return (measuredSpins,measuredProbabilities)


def fitDensityMatrix(measuredSpins,measuredProbabilities,hot = False,row = None,rounds = 10):

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
			except:
				print sys.exc_info()
	return densityMatrix	

##Renormalize a set of measured data.

(measuredSpins,measuredProbabilities) = convertDatacubeToSpins(tomographyData,indices1=["x","y","z","i"], indices2=["x","y","z","i"],saveValues = False,deleteOldData = True)
measuredProbabilities.parameters()["defaultPlot"] = [("duration","zzp00"),("duration","zzp01"),("duration","zzp10"),("duration","zzp11")]
######
#densityMatrices = Datacube("Density matrices")
#densityMatrices.createColumn("phi",measuredSpins.column("phi"))
#densityMatrices.goTo(0)
#measuredSpins.goTo(0)
#measuredSpins.addChild(densityMatrices)

densityMatrix = fitDensityMatrix(measuredSpins,measuredProbabilities,hot = True,row =None,rounds = 20)
##
for i in range(0,4):
	for j in range(0,4):
		densityMatrices.set(**{str(i)+str(j):densityMatrix[i,j]})
densityMatrices.commit()

##Plot a given density matrix that has been fitted before.

densityMatrix = matrix(zeros((4,4)),dtype =complex128)

for i in range(0,4):
	for j in range(0,4):
		densityMatrix[i,j] = densityMatrices.column(str(i)+str(j))[0]

plotDensityMatrix(densityMatrix)

##Plot a Pauli set

from pyview.ide.mpl.backend_agg import *
ion()
figure("pauli set")
cla()
rcParams["font.size"] = 18
plotPauliSet(measuredSpins = measuredSpins)
plotPauliSet(densityMatrix = rho,fill = False,lw = 2,ls = "dashed")
ylim(-1.2,1.2)

##Calculate the quantum fidelity of a given state

state = tensor(gs+1j*es,gs+1j*es)
state = state/norm(state)
rho = adjoint(state)*state
plotDensityMatrix(rho,figureName = "ideal")
print quantumFidelity(rho,densityMatrix)

##Calculate the entanglement witnesses using the measured values of XX, XY, etc...

(measuredSpins,measuredProbabilities) = convertDatacubeToSpins(tomographyData,indices1=["x","y","z","i"], indices2=["x","y","z","i"],saveValues = False,deleteOldData = True)
measuredProbabilities.parameters()["defaultPlot"] = [("duration","zzp00"),("duration","zzp01"),("duration","zzp10"),("duration","zzp11")]

for i in range(0,len(measuredSpins)):
	
	w_psi_plus = 1./4.*(1-measuredSpins.column("xx")[i]+measuredSpins.column("yy")[i]-measuredSpins.column("zz")[i])
	w_psi_minus = 1./4.*(1+measuredSpins.column("xx")[i]-measuredSpins.column("yy")[i]-measuredSpins.column("zz")[i])
	w_phi_plus = 1./4.*(1-measuredSpins.column("xx")[i]-measuredSpins.column("yy")[i]+measuredSpins.column("zz")[i])
	w_phi_minus = 1./4.*(1+measuredSpins.column("xx")[i]+measuredSpins.column("yy")[i]+measuredSpins.column("zz")[i])

	measuredSpins.setAt(i,w_psi_minus = w_psi_minus,w_psi_plus = w_psi_plus,w_phi_minus = w_phi_minus,w_phi_plus = w_phi_plus)
	measuredSpins.setAt(i,maxv = 0.5,minv = -0.5)

measuredSpins.parameters()["defaultPlot"] = [["phi","w_phi_plus"],["phi","w_phi_minus"],["phi","w_psi_plus"],["phi","w_psi_minus"],["phi","maxv"],["phi","minv"]]

measuredSpins.sortBy("phi")

##Calculate the entanglement witnesses using the reconstructed density matrices

w_psi_plus = 1./4.*(tensor(idatom,idatom)-tensor(sigmax,sigmax)+tensor(sigmay,sigmay)-tensor(sigmaz,sigmaz))
w_psi_minus = 1./4.*(tensor(idatom,idatom)+tensor(sigmax,sigmax)-tensor(sigmay,sigmay)-tensor(sigmaz,sigmaz))
w_phi_plus = 1./4.*(tensor(idatom,idatom)-tensor(sigmax,sigmax)-tensor(sigmay,sigmay)+tensor(sigmaz,sigmaz))
w_phi_minus = 1./4.*(tensor(idatom,idatom)+tensor(sigmax,sigmax)+tensor(sigmay,sigmay)+tensor(sigmaz,sigmaz))


p_relax = 0.12


wData = Datacube("Simulation of entanglement witnesses - %g %% relaxation" % p_relax)

dataManager.addDatacube(wData)

for psi in arange(0,360,1):
	state = tensor(es,gs)-tensor(gs,es)*exp(1j*psi/180.0*math.pi)
	state = state/norm(state)
	rho = adjoint(state)*state*(1.0-p_relax)+p_relax*adjoint(tensor(gs,gs))*tensor(gs,gs)
	wData.set(psi = psi)
	wData.set(w_phi_minus = trace(w_phi_minus*rho),w_phi_plus = trace(w_phi_plus*rho),w_psi_plus = trace(w_psi_plus*rho),w_psi_minus = trace(w_psi_minus*rho))
	wData.commit()
	

##

witnesses = Datacube("Entanglement Witnesses")
tomographyData.addChild(witnesses)
#witnesses.createColumn("height",tomographyData.column("height"))
witnesses.goTo(0)

densityMatrices = Datacube("Density Matrices",dtype = complex128)
#densityMatrices.createColumn("duration",tomographyData.column("duration"))
densityMatrices.goTo(0)

tomographyData.addChild(densityMatrices)

for row in range(0,len(measuredSpins)):
	densityMatrix = fitDensityMatrix(measuredSpins,measuredProbabilities,hot = False,row = row)
	for i in range(0,4):
		for j in range(0,4):
			densityMatrices.set(**{str(i)+str(j):densityMatrix[i,j]})
	densityMatrices.set(row = row)
	densityMatrices.commit()
	witnesses.set(angle = angle(densityMatrix[3,0]))
	witnesses.set(psi_plus = trace(densityMatrix*w_psi_plus))
	witnesses.set(psi_minus = trace(densityMatrix*w_psi_minus))
	witnesses.set(phi_plus = trace(densityMatrix*w_phi_plus))
	witnesses.set(phi_minus = trace(densityMatrix*w_phi_minus))
	witnesses.set(row = row)
	witnesses.commit()
		
##

densityMatrices = Datacube("Density Matrices",dtype = complex128)
densityMatrices.createColumn("index",measuredSpins.column("index"))
densityMatrices.goTo(0)
measuredSpins.addChild(densityMatrices)
for row in range(0,len(measuredSpins)):
	densityMatrix = fitDensityMatrix(measuredSpins,measuredProbabilities,hot = True,row = row)
	for i in range(0,4):
		for j in range(0,4):
			densityMatrices.set(**{str(i)+str(j):densityMatrix[i,j]})
	densityMatrices.commit()
measuredSpins.savetxt()
##

##Example of Density Matrix Plotting
kappa = -3.14*2
state = tensor(gs,es)+tensor(es,gs)*exp(1j*math.pi*1.1)
groundState = tensor(gs,gs)
state = state/norm(state)
rho = adjoint(state)*state*0.9+adjoint(groundState)*groundState*0.1
gate = tensor(rotx(-180.0/180.0*math.pi),idatom)
rho = gate*rho*adjoint(gate)
print quantumFidelity(rho,densityMatrix)
plotDensityMatrix(rho)
##Simulate the effect of a quantum gate on a given state
state = tensor(es,gs)
state = state/norm(state)
rho = adjoint(state)*state
psi = math.pi*2.2/3.0
gate = sqrtm(matrix([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]]))*tensor(rotz(-0.0/180.0*math.pi),rotz(135.0/180.0*math.pi))
finalState = gate*rho*adjoint(gate)
ion()
rcParams["font.size"] = 14
figure("rho3",figsize=(8,8))
clf()
cla()
#subplot(121)
#plotDensityMatrix(densityMatrix,figureName = None)
#savefig("test.png")
#subplot(122)
plotPauliSet(measuredSpins)
#plotDensityMatrix(matrix(tomographyData.childrenAt(0)[12].allChildren()[0].parameters()["densityMatrix"]),figureName = None)
##Simulate a set of measurements on a given state
state = tensor(gs,es)-1j*tensor(es,gs)
state = state/norm(state)
simulateMeasurements(state)
##
for child in tomographyData.allChildren():
	(measuredSpins,measuredProbabilities) = convertDatacubeToSpins(child,saveValues = True,deleteOldData = True)
	densityMatrix = fitDensityMatrix(measuredSpins,measuredProbabilities,hot = True)