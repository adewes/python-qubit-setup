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

##The simulation...

state = tensor(gs,es)

state = state/norm(state)

rho = vectorizeRho(adjoint(state)*state)

cube = Datacube("master equation simulation")
cube.parameters()["defaultPlot"]=[["t","zzp00"],["t","zzp01"],["t","zzp10"],["t","zzp11"]]

dataManager.addDatacube(cube)

dt = 1.0

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

for i in range(0,200.0/dt):

	if t < 0:
	
		extra = 	0.5/math.pi*(tensor(sigmax,idatom)*cos(Delta*t/math.pi/2.0)+tensor(sigmay,idatom)*sin(Delta*t/math.pi/2.0))
	else:
		extra = 0
		g = 0.1/math.pi*2.0

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
			cube.set(**{stateLabels[a]+stateLabels[b]:abs(rhomat[a,b])})
	cube.commit()

	t += dt

##Test some measurement operators:

figure("state measurement")
cla()

data = Datacube()

for phi in arange(0,2*math.pi,0.1):

	data.set(phi = phi)

	state = tensor((es+exp(1j*phi)*gs)/sqrt(2),(es+gs*0)/sqrt(2))

	state = state/norm(state)

	rho = vectorize(adjoint(state)*state)

	mx = createMeasurement(tensor(sigmax,idatom))
	my = createMeasurement(tensor(sigmay,idatom))

	data.set(x = trace(devectorize(rho)*mx[-1]),y = trace(devectorize(rho)*my[-1]))
	
	data.commit()

plot(data.column("phi"),data.column("x"),data.column("phi"),data.column("y"))

##
cube = Datacube("XY measurement vs state")

dataManager.addDatacube(cube)
for phi in arange(0,360,1):
	state = eg+exp(1j*phi/180.0*math.pi)*ge
	
	state = state/norm(state)
	
	rho = adjoint(state)*state
	cube.set(phi = phi)
	cube.set( xy = trace(rho*tensor(sigmay,sigmax)))
	cube.set( yx = trace(rho*tensor(sigmax,sigmay)))
	cube.commit()