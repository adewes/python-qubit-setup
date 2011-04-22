##Imports...
import sys
from qulib import *
from numpy.linalg import norm
from pyview.helpers.datamanager import DataManager
dataManager = DataManager() 
##Parameter definitions...
Delta = 0.0
g = 0.01*2.0*math.pi

gamma1 = 1.0/303.4
gamma2 = 1.0/368.7
gammaphi1 = 1.0/500.0
gammaphi2 = 1.0/650.0

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


def simulate(rho,cube,times):
	dt = 0.1
	order = 3
	rho0 = 0 
	coeffs = (5./12.,2./3.,-1./12.)
	rho_vector = matrix(zeros(order))
	t = 0
	Delta = 0.
	g = 0.0
	
	detector1 = matrix([[0.9,0.05],[0.1,0.95]])
	detector2 = matrix([[0.9,0.05],[0.1,0.95]])
	
	detectorFunction = tensor(detector2,detector1)
	detectorFunction = eye(4)
	
	stateLabels = ["00","10","01","11"]
	
	for i in times:
	
		if t < 1000:
		
			extra = 	1/math.pi*(tensor(sigmax,idatom)*cos(Delta*t/math.pi/2.0)+tensor(sigmay,idatom)*sin(Delta*t/math.pi/2.0))
		else:
			extra = 0
			g = 0.092/math.pi*2.0
	
		H = -Delta/2.0*sz1+Delta/2.0*sz2+g/2.0*(sp1*sm2+sm1*sp2)+extra
		LH = -1.j*(spre(H)-spost(H))
		
		drho = (L+LH)*rho	
		rho = rho+dt*(drho*1.5-0.5*rho0)
		rho0 = drho
		rhomat = devectorizeRho(rho)
	
		#Now the calculate all kinds of variables...
	
		cube.set(t = t)
		ms1 = [sigmaz]
		ms2 = [sigmaz]
	#	ms1 = [sigmax,sigmay,sigmaz,idatom]
	#	ms2 = [sigmax,sigmay,sigmaz,idatom]
	#	labels = ["x","y","z","i"]
		labels = ["z"]
		result_labels = {-1:"1",1:"0"}
		
		phi = math.pi*t/100.0
	
		for a in range(0,len(ms1)):
			for b in range(0,len(ms2)):
				realVector = zeros(4)
				mlabel = labels[a]+labels[b]
				ma = createMeasurement(ms1[a])
				mb = createMeasurement(ms2[b])
				results = []
				keys = []
				for result_a in ma:
					for result_b in mb:
						if not result_a in ma or not result_b in mb:
							continue
						m = tensor(ma[result_a],mb[result_b])
	#Rotate the state along z:
	#					r1 = matrix([[cos(phi/2.0)-1j*sin(phi/2.0),0],[0,cos(phi/2.0)+1j*sin(phi/2.0)]])
	#					r2 = matrix([[cos(-phi/3.0)-1j*sin(-phi/3.0),0],[0,cos(-phi/3.0)+1j*sin(-phi/3.0)]])
	#					r = tensor(r1,r2)
	#					realVector[cnt] = trace((r*rhomat*adjoint(r))*m)
						E = trace(rhomat*m)
						results.append(E)
						keys.append(mlabel+"p"+result_labels[result_a]+result_labels[result_b])
	#					cube.set(**{mlabel+"p"+result_labels[result_a]+result_labels[result_b] : E})	
				cube.set(**{mlabel:trace(rhomat*tensor(ms1[a],ms1[b]))})
				if len(results) < 4:
					continue
				results = transpose(matrix(results))
				detectedResults = detectorFunction*results
				for i in range(0,len(keys)):
					cube.set(**{keys[i]:detectedResults[i,0]})
	
		for a in range(0,4):
			for b in range(0,4):
				cube.set(**{str(a)+str(b):rhomat[a,b]})
		cube.commit()
	
		t += dt
		
##The simulation...

state = tensor(es,gs)
state = state/norm(state)
rho = vectorizeRho(adjoint(state)*state)

cube = Datacube("master equation simulation")
cube.parameters()["defaultPlot"]=[["t","zzp00"],["t","zzp01"],["t","zzp10"],["t","zzp11"]]

dataManager.addDatacube(cube)
simulate(rho,cube,range(0,2000.0))
##Simulate a quantum process

states = generateCombinations([gs,es,(gs+es)/sqrt(2),(gs+1j*es)/sqrt(2)],lambda x,y:tensor(x,y),2)

tomography = Datacube("simulation of quantum process tomography")
densityMatrices = Datacube("density matrices",dtype =complex128)
tomography.addChild(densityMatrices,name = "density matrices")
dataManager.addDatacube(tomography)
#We store the parameters of the simulation in the datacube
tomography.parameters()["gamma1"] = gamma1
tomography.parameters()["gamma2"] = gamma2
tomography.parameters()["gammaphi1"] = gammaphi1
tomography.parameters()["gammaphi2"] = gammaphi2
tomography.parameters()["g"] = g

for i in range(0,len(states)):
	cube = Datacube("state no %d" % i,dtype = complex128)
	tomography.addChild(cube,i = i)
	rho = vectorizeRho(adjoint(states[i])*states[i])
	cube.parameters()["defaultPlot"]=[["t","zzp00"],["t","zzp01"],["t","zzp10"],["t","zzp11"]]
	simulate(rho,cube,range(0,250.0))
	for a in range(0,4):
		for b in range(0,4):
			densityMatrices.setAt(i,**{str(a)+str(b):cube[str(a)+str(b)][25]})
