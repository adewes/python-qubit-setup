##Imports...
import sys
reload(sys.modules["qulib"])
from qulib import *
from numpy.linalg import norm
from pyview.helpers.datamanager import DataManager
dataManager = DataManager() 
##Parameter definitions...
Delta = 0.0
g = 0.01*2.0*math.pi

gamma1 = 1.0/390.
gamma2 = 1.0/450.
gammaphi1 = 1.0/800.
gammaphi2 = 1.0/800.

##Some more definitions...

idtot = tensor(idatom,idatom)
drive1 = tensor(sigmax,idatom)
sm1 = tensor(sigmam,idatom)
sm2 = tensor(idatom,sigmam)
sp1 = tensor(sigmap,idatom)
sp2 = tensor(idatom,sigmap)
sz1 = tensor(sigmaz,idatom)
sz2 = tensor(idatom,sigmaz)
##The Lindblad operators...
Delta = 0.0
g = 0.01*2.0*math.pi

gamma1 = 1.0/390.
gamma2 = 1.0/450.
gammaphi1 = 1.0/800.
gammaphi2 = 1.0/800.


C1T1 = sqrt(gamma1)*sm1
C2T1 = sqrt(gamma2)*sm2
C1Phi = sqrt(gammaphi1/2.0)*sz1
C2Phi = sqrt(gammaphi2/2.0)*sz2

C1T1dC1T1 = adjoint(C1T1)*C1T1
C2T1dC2T1 = adjoint(C2T1)*C2T1
C1PhidC1Phi = adjoint(C1Phi)*C1Phi
C2PhidC2Phi = adjoint(C2Phi)*C2Phi


L1 = spre(C1T1)*spost(adjoint(C1T1))-0.5*spre(C1T1dC1T1)-0.5*spost(C1T1dC1T1)
L2 = spre(C2T1)*spost(adjoint(C2T1))-0.5*spre(C2T1dC2T1)-0.5*spost(C2T1dC2T1)
L3 = spre(C1Phi)*spost(adjoint(C1Phi))-0.5*spre(C1PhidC1Phi)-0.5*spost(C1PhidC1Phi)
L4 = spre(C2Phi)*spost(adjoint(C2Phi))-0.5*spre(C2PhidC2Phi)-0.5*spost(C2PhidC2Phi)
L = L1+L2+L3+L4

def integrate(rho,L,ts,dt = 0.1):

	t = 0
	
	rhos = zeros((len(ts),rho.shape[0],rho.shape[1]),dtype = complex128)

	def integrateStep(rho,L,t,dt,sections = 1):
		step = dt/float(sections)
		for i in range(0,sections):
			Lrho = L(t+step*i)*rho
			rho = rho+step*Lrho
		return rho

	def adaptiveIntegrate(rho,L,t,dt,epsilon = 0.00001,epsilonTrace = 0.0001):
		rho1 = integrateStep(rho,L,t,dt,sections = 1)
		rhon = rho1
		sections  = 2
		while True:
			rhon = integrateStep(rho,L,t,dt,sections = sections)
			e1 = norm(rho1-rhon)
			e2 = abs(sum(rhon[range(0,len(rhon),sqrt(len(rhon))+1),0])-1)
			if e1 > epsilon or e2 > epsilonTrace:
				rho1 = rhon
				sections += 1
			else:
				break
		return rhon

	i = 0
	
	ts = list(ts)

	while len(ts) > 0:
		tt = ts.pop(0)
		print "t = %g " % tt
		dtt = dt
		while t < tt:
			if tt-t > dt:
				rho = adaptiveIntegrate(rho,L,t,dt)
				t+=dt
			else:
				rho = adaptiveIntegrate(rho,L,t,tt-t)
				t+=tt-t
		rhos[i] = rho
		i+=1
	return rhos


##Adaptive timestep simulation of Grover's algorithm

"""
Pulse lengths and coupling strengths
"""
coupling = 0.082/math.pi*2.0
t1 = 2.5
t2 = 4./coupling-15.
t3 = 1.25*2.
t4 = t2
t5 = 2.5

def LL(t,signs = [-1,-1]):

	"""
	This function returns the Lindblad operator for the Grover search algorithm
	"""

	Delta = 0.

	drive1 = 0
	drive2 = 0
	g = 0	
	
	if t < t1:
		drive1 = 1./math.pi*tensor(sigmay,idatom)
		drive2 = 1./math.pi*tensor(idatom,sigmay)
	elif t < t1+t2:
		g = coupling
	elif t < t1+t2+t3:
		drive1 = 1./math.pi*tensor(signs[0]*sigmaz,idatom)
		drive2 = 1./math.pi*tensor(idatom,sigmaz*signs[1])
	elif t < t1+t2+t3+t4:
		g = coupling
	elif t < t1+t2+t3+t4+t5:
		drive1 = 1./math.pi*tensor(sigmax,idatom)
		drive2 = 1./math.pi*tensor(idatom,sigmax)
	
	H = -Delta/2.0*sz1+Delta/2.0*sz2+g/2.0*(sp1*sm2+sm1*sp2)+drive1+drive2
	LH = -1.j*(spre(H)-spost(H))
	return LH+L

state = tensor(gs,gs)
state = state/norm(state)
rho = vectorizeRho(adjoint(state)*state)

times = arange(0,t1+t2+t3+t4+t5+1.,1.)
data = Datacube("simulation",dtype = complex128)
data.parameters()["t1_I"] = gamma1
data.parameters()["t1_II"] = gamma2
data.parameters()["tphi_I"] = gammaphi1
data.parameters()["tphi_II"] = gammaphi2
data.parameters()["g"] = coupling

dataManager.addDatacube(data)

rhosvec = []
#We simulate the Grover algorithm for all possible oracle functions
for signs in generateCombinations([-1,1],lambda x,y:[x,y],2):
	child = Datacube("state %d,%d" % (signs[0],signs[1]))
	data.addChild(child,signs = signs)

	state = tensor(gs,gs)
	state = state/norm(state)
	rho = vectorizeRho(adjoint(state)*state)

	rhos = integrate(rho,lambda t:LL(t,signs = signs),times,dt = 0.01)
	for i in range(0,len(rhos)):
		child.set(t = times[i])
		rho = devectorizeRho(rhos[i])
		for j in range(0,len(rho)):
			for k in range(0,len(rho)):
				child.set(**{str(j)+str(k) : rho[j,k]})
		child.commit()
	child.parameters()["defaultPlot"]=[["t","11"],["t","22"],["t","33"],["t","44"]]
	rhosvec.append(rhos)
##We plot the results of the simulation...
from config.startup import importModule
importModule("scripts.state_tomography.plot_density_matrix")
from scripts.state_tomography.plot_density_matrix import *
figure("grover simulation")
clf()
k = 0
for rhos in rhosvec:
	subplot(4,4,1+k*4)
	plotDensityMatrix(devectorizeRho(rhos[0]),figureName = None,annotate = False)
	subplot(4,4,2+k*4)
	plotDensityMatrix(devectorizeRho(rhos[t1+1]),figureName = None,annotate = False)
	subplot(4,4,3+k*4)
	plotDensityMatrix(devectorizeRho(rhos[t1+t2+t3+1]),figureName = None,annotate = False)
	subplot(4,4,4+k*4)
	plotDensityMatrix(devectorizeRho(rhos[-1]),figureName = None,annotate = False)
	show()
	k+=1
figtext(0.05,0.05,data.filename()[:-4])

##Simulate a quantum process

states = generateCombinations([gs,es,(gs-1j*es)/sqrt(2),(gs+es)/sqrt(2)],lambda x,y:tensor(x,y),2)

tomography = Datacube("simulation of quantum process tomography")
densityMatrices = Datacube("density matrices",dtype =complex128)
tomography.addChild(densityMatrices,name = "density matrices")
dataManager.addDatacube(tomography)
#We store the parameters of the simulation in the datacube

g = 0.082/math.pi*2.0

times = arange(0,500,1)

Delta = 0.0

states = [tensor(es,gs)]

gamma1 = 1.0/560.
gamma2 = 1.0/530.
gammaphi1 = 1.0/1600.
gammaphi2 = 1.0/1400.

C1T1 = sqrt(gamma1)*sm1
C2T1 = sqrt(gamma2)*sm2
C1Phi = sqrt(gammaphi1/2.0)*sz1
C2Phi = sqrt(gammaphi2/2.0)*sz2

C1T1dC1T1 = adjoint(C1T1)*C1T1
C2T1dC2T1 = adjoint(C2T1)*C2T1
C1PhidC1Phi = adjoint(C1Phi)*C1Phi
C2PhidC2Phi = adjoint(C2Phi)*C2Phi

L1 = spre(C1T1)*spost(adjoint(C1T1))-0.5*spre(C1T1dC1T1)-0.5*spost(C1T1dC1T1)
L2 = spre(C2T1)*spost(adjoint(C2T1))-0.5*spre(C2T1dC2T1)-0.5*spost(C2T1dC2T1)
L3 = spre(C1Phi)*spost(adjoint(C1Phi))-0.5*spre(C1PhidC1Phi)-0.5*spost(C1PhidC1Phi)
L4 = spre(C2Phi)*spost(adjoint(C2Phi))-0.5*spre(C2PhidC2Phi)-0.5*spost(C2PhidC2Phi)
L = L1+L2+L3+L4

tomography.parameters()["gamma1"] = gamma1
tomography.parameters()["gamma2"] = gamma2
tomography.parameters()["gammaphi1"] = gammaphi1
tomography.parameters()["gammaphi2"] = gammaphi2
tomography.parameters()["g"] = g

def Lswap(t):

	"""
	This function returns the Lindblad operator for the Grover search algorithm
	"""
	H = -Delta/2.0*sz1+Delta/2.0*sz2+g/2.0*(sp1*sm2+sm1*sp2)
	LH = -1.j*(spre(H)-spost(H))
	return LH+L

for i in range(0,len(states)):
	cube = Datacube("state no %d" % i)
	tomography.addChild(cube,i = i)
	rho = vectorizeRho(adjoint(states[i])*states[i])
	cube.parameters()["defaultPlot"]=[["t","zzp00"],["t","zzp01"],["t","zzp10"],["t","zzp11"]]
	rhos = integrate(rho,Lswap,times,dt = 0.01)
	for j in range(0,len(times)):
		rho = devectorizeRho(rhos[j])
		cube.set(t = times[j])
		cube.set(zzp00 = rho[0,0],zzp10 = rho[1,1],zzp01 = rho[2,2],zzp11 = rho[3,3])
		cube.commit()
	for a in range(0,4):
		for b in range(0,4):
			densityMatrices.setAt(i,**{str(a)+str(b):devectorizeRho(rhos[-1])[a,b]})
	figure("swap")
	subplot(121)
	cla()
	plotDensityMatrix(devectorizeRho(rhos[0]),figureName = None,annotate = True)
	subplot(122)
	cla()
	plotDensityMatrix(devectorizeRho(rhos[1]),figureName = None,annotate = True)
	show()
