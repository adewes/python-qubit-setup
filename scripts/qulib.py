from numpy import *
from scipy import *
from pyview.lib.datacube import *
from matplotlib.pyplot import *
from pyview.ide.mpl.backend_agg import figure
from numpy.linalg import *

def adjoint(m):
	return m.conj().transpose()

def tensor(a,b):
	return kron(b,a)

def vectorizeRho(A):
	v = A.copy()
	v.shape = (A.shape[0]*A.shape[1],1)
	return v

def devectorizeRho(v):
	A = v.copy()
	n	= sqrt(v.shape[0])
	A.shape = (n,n)
	return A

def spost(A):
	n = A.shape[0]
	N = n*n
	AA = matrix(zeros((N,N)))
	for i in range(0,n):
		AA[i*n:(i+1)*n,i*n:(i+1)*n] = A.transpose()
	return AA

def spre(A):
	n = A.shape[0]
	N = n*n
	AA = matrix(zeros((N,N)))
	for i in range(0,n):
		for j in range(0,n):
			for k in range(0,n):
				AA[k*n+i,j*n+i] = A[k,j] 
	return AA

def rotx(angle):
	return matrix([[cos(angle/2.0),-1j*sin(angle/2.0)],[-1j*sin(angle/2.0),cos(angle/2.0)]])

def roty(angle):
	return matrix([[cos(angle/2.0),-sin(angle/2.0)],[sin(angle/2.0),cos(angle/2.0)]])

def rotz(angle):
	return matrix([[exp(-1j*angle/2.0),0],[0,exp(1j*angle/2.0)]])

def createMeasurement(tensor,verbose = False):

	(eigenvalues,eigenvectors) = eigh(tensor)

	vals = dict()
	projs = dict()

	if verbose:
		print eigenvalues
		print eigenvectors

	for i in range(0,len(eigenvalues)):
		e = eigenvalues[i]
		ev = eigenvectors[:,i]

		if e in projs:
			projs[e] += ev*adjoint(ev)
		else:
			projs[e] = matrix(zeros((ev.shape[0],ev.shape[0]),dtype = complex128))
			projs[e] += ev*adjoint(ev)
	return projs

def generateMeasurementCombinations(qubit,measurement,measurements,nqubits):
	"""
	Generates all possible combinations in a set of measurements for "nqubits" qubits.
	"""
	ms = []
	if qubit >= nqubits:
		return [[measurement,createMeasurement(measurement)]]
	for m in measurements:
		if measurement == None:
			ms.extend(generateMeasurementCombinations(qubit+1,m,measurements,nqubits))
		else:
			ms.extend(generateMeasurementCombinations(qubit+1,tensor(measurement,m),measurements,nqubits))
	return ms

def generateCombinations(things,combiner,dim,i = 1):
	"""
	Generates a list of all possible combinations of "things", using the function "combiner" to combine two things togeter. For example, generateCombinations(["x","y","z"],lambda x,y : x+y,2) will generate the list ['xx', 'xy', 'xz', 'yx', 'yy', 'yz', 'zx', 'zy', 'zz']

	"""
	combinations = []
	if i < dim:
		newCombinations = generateCombinations(things,combiner,dim,i+1)
		for thing in things:
			for combination in newCombinations:
				combinations.append(combiner(thing,combination))
		return combinations
	else:
		return things

def measure(rho0,m):
	p = random.random()
	psum = 0
	for value in m:
		projector = m[value]
		p0 = (projector*rho0).trace()
		psum+=p0
		if psum >= p:
			rho = projector*rho0*projector
			rho = rho/rho.trace()
			return (value,rho)

def buildRho(params):
	"""
	This function reconstructs a density matrix using an array of real-valued parameters as produced by parametrizeRho.
	This function will correct parameters that could produce an unphysical density matrix, i.e. a density matrix with
		- A trace > 1
		- An off-diagonal element at position (i,j) whose absolute value is larger than the square root of product of the absolute values of the diagonal elements i,i and (j,j)
	"""
	dim = sqrt(1/4+2*(len(params)/2+1))-1/2
	rho = matrix(zeros((dim,dim),dtype =complex128))
	cnt = 0
	for i in range(0,dim-1):
		rho[i,i] = abs(params[cnt])
		cnt+=1
	for i in range(0,dim-1):
		for j in range(i+1,dim):
			rho[i,j] = params[cnt]*exp(1j*params[cnt+1])
			if i != j:
				rho[j,i] = conjugate(rho[i,j])
			cnt += 2
	tr = trace(rho)
	if tr > 1:
		for i in range(0,dim):
			rho[i,i]/=tr
	rho[-1,-1] = 1-trace(rho)
	for i in range(0,dim):
		for j in range(0,dim):
			mv = sqrt(abs(rho[i,i])*abs(rho[j,j]))
			if i != j:
				if abs(rho[i,j]) > mv:
					rho[i,j] = mv
				if abs(rho[j,i]) > mv:
					rho[j,i] = mv
	return rho

def parametrizeRho(rho):
	"""
	This functions stores a density matrix as an array of real-valued parameters.
	The output array contains:
		-All but the last diagonal elements of the density matrix
		-The real and imaginary parts of the rows above the diagonal.

	An example:
		
		The density matrix

		( 0.5   0.25j )
		( -0.25j 0.5  )
		
		will get stored as

		(0.5,0,0.25)
	
	Use buildRho(rho) to reconstruct the density matrix from these parameters.

	"""
	dim = rho.shape[0]
	params = list()
	for i in range(0,dim-1):
		params.append(abs(rho[i,i]))
	for i in range(0,dim-1):
		for j in range(i+1,dim):
			params.append(real(rho[i,j]))
			params.append(imag(rho[i,j]))
	return params

def pauliRotation(phi,x,y,z):
	return matrix(
		[
			[cos(phi/2.0)-1j*z*sin(phi/2.0),(-1j*x-y)*sin(phi/2)],
			[(-1j*x+y)*sin(phi/2),cos(phi/2)+1j*z*sin(phi/2)]
		]
	)

def reconstructDensityMatrix(measurements,values):
	cm = matrix(zeros((len(measurements),len(measurements))))
	for i in range(0,len(measurements)):
		for j in range(i,len(measurements)):
			tr = trace(measurements[i]*measurements[j])
			cm[i,j] = tr
			cm[j,i] = tr
	print cm
	x = solve(cm,values)

	rho = matrix(zeros(measurements[0].shape))	
	for i in range(0,len(x)):
		rho+= x[i]*measurements[i]
	return rho


def determineDensityMatrixAnalytical(baseMatrices,baseLabels,measurements):
	dim = len(measurements.shape)
	n = len(baseMatrices)
	A = zeros(tuple([n]*dim*2),dtype = complex128)
	indices = range(0,n)

	rho = zeros((pow(2,dim),pow(2,dim)),dtype = complex128)

	indices = [0]*dim*2
	for i in range(0,pow(n,dim*2)):

		l1 = []
		l2 = []
		l1.extend(indices[len(indices)/2:])
		l2.extend(indices[:len(indices)/2])

		m1 = reduce(lambda x,y:tensor(x,y),map(lambda x:baseMatrices[x],l1))
		m2 = reduce(lambda x,y:tensor(x,y),map(lambda x:baseMatrices[x],l2))

		A[tuple(indices)] = trace(m1*m2)

		ci = -1
		indices[ci]+=1
		while indices[ci] >= n:
			indices[ci] = 0
			indices[ci-1]+=1
			ci-=1
			if ci <= -dim*2:
				break

	x = tensorsolve(A,measurements)

	indices = [0]*dim
	for i in range(0,pow(n,dim)):

		m = reduce(lambda x,y:tensor(x,y),map(lambda x:baseMatrices[x],indices))

		rho += x[tuple(indices)]*m

		ci = -1
		indices[ci]+=1
		while indices[ci] >= n:
			indices[ci] = 0
			indices[ci-1]+=1
			ci-=1
			if ci <= -dim:
				break

	rho = rho/trace(rho)
	
	return rho

sigmam = matrix([[0,1],[0,0]])
sigmap = matrix([[0,0],[1,0]])
sigmax = matrix([[0,1],[1,0]])
sigmay = matrix([[0,-1j],[1j,0]])
sigmaz = matrix([[1,0],[0,-1]])
idatom = matrix(eye(2))

gs = matrix([1,0])
es = matrix([0,1])
gg = matrix([1,0,0,0])
eg = matrix([0,1,0,0])
ge = matrix([0,0,1,0])
ee = matrix([0,0,0,1])

proj_gg = gg.transpose()*gg
proj_eg = eg.transpose()*eg
proj_ge = ge.transpose()*ge
proj_ee = ee.transpose()*ee
