from scripts.qulib import *
from numpy.linalg import *
from scripts.state_tomography.plot_density_matrix import *
import scipy.optimize
import random
import cmath

E = []
rhos = []

sigmas = [idatom,sigmax,1j*sigmay,sigmaz]

for i in range(0,4):
	for j in range(0,4):
		rho = matrix(zeros((4,4)))
		rho[i,j] = 1
		rhos.append(rho)
		E.append(tensor(sigmas[i],sigmas[j]))

#A SWAP matrix...
process_matrix = 1./2*matrix([[2,0,0,0],[0,1+1j,1-1j,0],[0,1-1j,1+1j,0],[0,0,0,2]])
rotation = tensor(rotz(0.5)*roty(-0.8),rotx(-0.4))
process_matrix = rotation*process_matrix*adjoint(rotation)
beta = zeros((16,16,16,16))

#We calculate the beta matrix
for m in range(0,len(E)):
	for n in range(0,len(E)):
		for j in range(0,len(rhos)):
			rhop = (E[m]*rhos[j]*adjoint(E[n]))
			beta[j,:,m,n]=array(rhop.ravel())

epsilon_rhos = []

def process(rho):
	rhop = process_matrix*rho*adjoint(process_matrix)
	angle1 = random.random()*0.2*0
	angle2 = random.random()*0.2*0
	rotation = tensor(rotz(angle1),rotz(angle2))
	rhop = rotation*rhop*adjoint(rotation)
	return rhop

#We calculate Epsilon(rho_i)
for rho in rhos:
	epsilon_rhos.append(process(rho))
	
#We calculate the lambda matrix
lambda_matrix = zeros((16,16),dtype = complex128)
for i in range(0,len(epsilon_rhos)):
	lambda_matrix[i,:] = array(epsilon_rhos[i].ravel())
			
#We solve the tensor equation for chi
import numpy.linalg
chi = numpy.linalg.tensorsolve(beta,lambda_matrix)

state = tensor(es+gs,gs+es)
state = state/norm(state)

rho = adjoint(state)*state
rho_final_calculated = process(rho)

print "Original:\n",rho_final_calculated

rho_final = matrix(zeros((4,4),dtype = complex128))

for m in range(0,len(E)):
	for n in range(0,len(E)):
			rho_final+=chi[m,n]*E[m]*rho*adjoint(E[n])
						
print "Reproduction:\n",rho_final

if not allclose(rho_final,rho_final_calculated):
	print "Failed!"
else:
	print "Success!"
	
(eigenvals,eigenvecs) = eigh(chi)

def errorFunction(ps,chi,Q):
	LL = abs(diag(ps))
	LL = LL / trace(LL)
	return numpy.linalg.norm(chi-Q*LL*adjoint(Q))

ps = eigenvals

Q = matrix(eigenvecs)

p1s = scipy.optimize.fmin(errorFunction,ps,args = (chi,Q))

LL = abs(diag(p1s))
LL = LL / trace(LL)
print numpy.linalg.norm(Q*LL*adjoint(Q)-chi)