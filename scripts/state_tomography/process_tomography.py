from scripts.qulib import *
from numpy.linalg import *
from config.startup import importModule
importModule("scripts.state_tomography.plot_density_matrix")
from scripts.state_tomography.plot_density_matrix import *
import scipy.optimize
import random
import cmath
import numpy.linalg

E = []
rhos = []

sigmas = [idatom,sigmax,1j*sigmay,sigmaz]

for i in range(0,4):
	for j in range(0,4):
		rho = matrix(zeros((4,4)))
		rho[i,j] = 1
		rhos.append(rho)
		E.append(tensor(sigmas[i],sigmas[j]))
		
A = 	matrix(zeros((16,16),dtype = complex128))

for i in range(0,len(E)):
	A[:,i] = transpose(E[i].ravel())

#We calculate the mapping between the basis matrices rho and a set of matrices rho' that we actually measure...

states = map(lambda x:adjoint(x)*x,generateCombinations([gs,es,(gs-1j*es)/sqrt(2),(gs+es)/sqrt(2)],lambda x,y:tensor(x,y),2))

mapping_matrix = matrix(zeros((16,16),dtype = complex128))

for i in range(0,len(states)):
	mapping_matrix[i,:] = array(states[i].ravel())[0,:]

#A SWAP matrix...
process_matrix = 1./2*matrix([[2,0,0,0],[0,1+1j,1-1j,0],[0,1-1j,1+1j,0],[0,0,0,2]])
rotation = tensor(rotz(0),idatom)
process_matrix = rotation*process_matrix
beta = zeros((16,16,16,16))

#process_matrix = eye(4)

#We calculate the beta matrix
for m in range(0,len(E)):
	for n in range(0,len(E)):
		for j in range(0,len(rhos)):
			rhop = (E[m]*rhos[j]*adjoint(E[n]))
			beta[j,:,m,n]=array(rhop.ravel())

epsilon_rhos = []

def process(rho,ideal = True):
	rhop = process_matrix*rho*adjoint(process_matrix)
	if not ideal:
		#We introduce some errors...
		angle1 = random.random()*10.*math.pi/180.0*0
		angle2 = random.random()*10.*math.pi/180.0*0
		rotation = tensor(rotz(angle1),rotz(angle2))
		rhop = rotation*rhop*adjoint(rotation)
	return rhop
#We calculate Epsilon(rho)
epsilon_rhos_direct = []
for rho in rhos:
	epsilon_rhos_direct.append(process(rho,ideal = False))

#We calculate Epsilon(rho)
epsilon_rhos_ideal = []
for rho in rhos:
	epsilon_rhos_ideal.append(process(rho,ideal = True))

#We calculate Epsilon(rho')
simulate = False
if simulate:
	epsilon_states = []
	for state in states:
		epsilon_states.append(process(state,ideal = False))
else:
	print "Loading experimental data..."
	epsilon_states = []
	if len(gv.densityMatrices) == 16*2:
		states_theory = states
		states = []
		print "Loading with initial matrices..."
		for i in range(0,len(gv.densityMatrices)/2):
			rho = matrix(zeros((4,4),dtype = complex128))
			rho_initial = matrix(zeros((4,4),dtype = complex128))
			for a in range(0,4):
				for b in range(0,4):
					rho_initial[a,b] = gv.densityMatrices[str(a)+str(b)][i*2]
					rho[a,b] = gv.densityMatrices[str(a)+str(b)][i*2+1]
			rotation = tensor(rotz(0),rotz(0))
			epsilon_states.append(rotation*rho*adjoint(rotation))		
			states.append(rho_initial)	
			mapping_matrix[i,:] = array(states[i].ravel())[0,:]
	else:
		for i in range(0,len(gv.densityMatrices)):
			rho = matrix(zeros((4,4),dtype = complex128))
			for a in range(0,4):
				for b in range(0,4):
					rho[a,b] = gv.densityMatrices[str(a)+str(b)][i]
			rotation = tensor(rotz(0),rotz(0))
			epsilon_states.append(rotation*rho*adjoint(rotation))		

m_inv = inv(transpose(mapping_matrix))
#We map Epsilon(rho') to Epsilon(rho)
for i in range(0,len(rhos)):
	epsilon_rho= matrix(zeros((4,4),dtype = complex128))
	for j in range(0,len(states)):
		epsilon_rho+=m_inv[j,i]*epsilon_states[j]
	epsilon_rhos.append(epsilon_rho)

#We verify that Epsilon(rho) found by direct calculation equals Epsilon(rho) found by mapping from Epsilon(rho')
failed = False
for i in range(0,len(epsilon_rhos)):
	if not allclose(epsilon_rhos[i],epsilon_rhos_direct[i]):
		failed = True

if failed:
	print "Error: Epsilon(rho) != M^-1*Epsilon(rho')"
	
#We calculate the lambda matrix
lambda_matrix = zeros((16,16),dtype = complex128)
lambda_matrix_ideal = zeros((16,16),dtype = complex128)
for i in range(0,len(epsilon_rhos)):
	lambda_matrix[i,:] = array(epsilon_rhos[i].ravel())
	lambda_matrix_ideal[i,:] = array(epsilon_rhos_ideal[i].ravel())

def parametrizeChi(chi):
	"""
	Parametrizes a chi matrix and returns a list of real parameters that contain the diagonal elements and the real and imaginary parts of the upper-diagonal elements of the matrix.
	"""
	params = []
	n = len(chi)
	for i in range(0,n):
		params.append(float(real(chi[i,i])))
	for i in range(0,n):
		for j in range(i+1,n):
			params.append(float(real(chi[i,j])))
			params.append(float(imag(chi[i,j])))
	return params
	
def reconstructChi(params):
	"""
	Reconstructs a complex, symmetric matrix of dimensions nxn from n^2 real parameters, where the first n values in the parameter list
	give the real diagonal elements of the matrix and the remaining n^2-n elements the real and imaginary values of the upper-diagonal elements.
	"""
	n = int(sqrt(len(params)))
	chi = matrix(zeros((n,n),dtype = complex128))
	for i in range(0,n):
		chi[i,i] = params[i]
	cnt = 0
	for i in range(0,n):
		for j in range(i+1,n):
			chi[i,j] = params[n+cnt]+1j*params[n+cnt+1]
			chi[j,i] = conjugate(complex(chi[i,j]))
			cnt+=2
	return chi

def correctChi(chi):
	"""
	Renders a given matrix chi physical by assuring that for the eigenvalues \lambda_i we have
		- \sum_i \lambda_i = 1
		- \lambda_i > 0 \forall i
	"""
	(eigenvals,eigenvecs) = eigh(chi)
	Q = matrix(eigenvecs)
	LL = diag(eigenvals)
	for i in range(0,len(LL)):
		LL[i,i] = max(0,LL[i,i])
	LL = LL / trace(LL)
	return Q*LL*adjoint(Q)

def calculateChi(beta,lambdas):
	import numpy.linalg
	chi = numpy.linalg.tensorsolve(beta,lambdas)
	return matrix(chi)
	
chi = calculateChi(beta,lambda_matrix)
chi_ideal = calculateChi(beta,lambda_matrix_ideal)

#We apply the process matrix to all initially measured density matrices and compare the result to the density matrices obtained when directly applying the process matrices to each of them
failed = False
for state in states:

	rho_final_calculated = process(state)

	rho_final = matrix(zeros((4,4),dtype = complex128))

	for m in range(0,len(E)):
		for n in range(0,len(E)):
			rho_final+=chi[m,n]*E[m]*state*adjoint(E[n])

	if not allclose(rho_final,rho_final_calculated):
		failed = True

if failed:
	print "The precise reconstruction of the chi matrix failed!"	
(eigenvals,eigenvecs) = eigh(chi)

if len(gv.densityMatrices.parent().children(name = "chi")) > 0:
	chiMatrix = gv.densityMatrices.parent().children(name = "chi")[0]
else:
	chiMatrix = Datacube("chi matrix",dtype = complex128)
	gv.densityMatrices.parent().addChild(chiMatrix,name = "chi")

for i in range(0,16):
	for j in range(0,16):
		chiMatrix.setAt(0,**{str(i)+","+str(j):chi[i,j]})

plotChi(chi,"original")
if gv.densityMatrices.parent().filename() != None:
	figtext(0,0,gv.densityMatrices.parent().filename()[:-4])
show()
print trace(chi*chi_ideal)

##We calculate the fidelities of the input states:
from scripts.state_tomography.state_simulation import quantumFidelity

print "Fidelity of input states:"

input_fidelities = []

for i in range(0,len(states)):
	input_fidelities.append(float(abs(quantumFidelity(states[i],states_theory[i]))))
	print i+1,input_fidelities[i]

print "Average input fidelity: %g" % mean(input_fidelities) 

from scripts.state_tomography.state_simulation import quantumFidelity

print "Fidelity of output states:"

output_fidelities = []

for i in range(0,len(states)):
	output_fidelities.append(float(abs(quantumFidelity(epsilon_states[i],process(states_theory[i])))))
	print i+1,output_fidelities[i]

print "Average output fidelity: %g" % mean(output_fidelities) 

gv.densityMatrices.parameters()["inputFidelities"] = input_fidelities
gv.densityMatrices.parameters()["outputFidelities"] = output_fidelities

gv.densityMatrices.savetxt(forceSave = True)

##We plot the density matrices corresponding to the process

titles = []
labels = ["00","10","01","11"]
for i in range(0,len(epsilon_rhos)):
	titles.append(r"$|%s><%s|$" % (labels[i/4],labels[i%4]) )	

state_titles = generateCombinations([r"$|0>$",r"$|1>$",r"$\left(|0>+i|1>\right)/\sqrt{2}$",r"$\left(|0>+|1>\right)/\sqrt{2}$"],lambda x,y:x+y,2)

filename = None

if gv.densityMatrices.parent().filename() != None:
	filename = gv.densityMatrices.parent().filename()

#plots = [states,epsilon_states,epsilon_rhos]
#titles = [state_titles,state_titles,titles]

plotDensityMatrices(epsilon_states,titles = titles,filename = filename)

##We plot the eigenvalues

chi_corrected = correctChi(chi)

print trace(chi_corrected*chi_ideal)

figure("eigh")
cla()
bar(range(0,16),eigh(chi)[0])
bar(range(0,16),eigh(best_chi)[0],color = 'red')
show()
ylim(-1,1)

##Calculate the eigenoperators of the process...

Ms = []
titles = []

for i in range(0,16):
	titles.append(str(i+1))
	M = reduce(lambda x,y:x+y,map(lambda x:x[1]*x[0],zip(list(array(eigh(chi)[1][:,i])[:,0]),E)))
	M = exp(-1j*angle(M[0,0]))*M
	print M*adjoint(M)
	Ms.append(M)

plotDensityMatrices(Ms,name = "operators",titles = titles)	

##Optimize the analytical solution that has been found...

def errorFunction(ps,chi):
	chi_candidate = correctChi(reconstructChi(ps))
	error = numpy.linalg.norm(chi_candidate-chi)
	return error

ps = parametrizeChi(chi)
	
p1s = scipy.optimize.fmin(errorFunction,ps,args = [chi],maxiter = 1e5,maxfun = 1e5)

best_chi = correctChi(reconstructChi(p1s))

for i in range(0,16):
	for j in range(0,16):
		chiMatrix.removeColumn(str(i)+str(j))
		chiMatrix.setAt(1,**{str(i)+","+str(j):best_chi[i,j]})


##
importModule("scripts.state_tomography.plot_density_matrix")
from scripts.state_tomography.plot_density_matrix import *

plotChi(best_chi,"best",filename = filename)
suptitle("best $\chi$ matrix obtained - 66 % fidelity")
show()
print norm(-chi)

(eigenvals,eigenvecs) = eigh(best_chi)

print norm(chi-best_chi),norm(chi-correctChi(chi))

print trace(best_chi*chi_ideal)

##
figure("eigenvalues")
cla()
plot(eigh(chi)[0])
plot(eigh(best_chi)[0])
plot(eigh(chi_ideal)[0])
show()
##Generate the chi matrix of an arbitrary process
n = 50
fidelity = zeros((n,n))

i = 0
j = 0

angles = linspace(0,math.pi*2.0,n)

AI = inv(transpose(A))

for alpha in angles:
	j = 0
	for beta in angles:
		rotation = tensor(rotz(alpha),rotz(beta))
		M = rotation*process_matrix
		
		coeffs = M.ravel()*AI
		chi_theory = matrix(zeros((16,16),dtype = complex128))
		
		for k in range(0,16):
			for l in range(0,16):
				chi_theory[k,l] = coeffs[0,k]*conjugate(coeffs[0,l])

		fidelity[i,j] = trace(chi*chi_theory)
		j+=1
	i+=1
##
figure("fidelity")
clf()	
imshow(transpose(fidelity),aspect = 'auto',interpolation = 'nearest',origin = 'lower',extent = (0,360,0,360))
colorbar()
xlabel("Qubit 1 z rotation angle")
ylabel("Qubit 2 z rotation angle")
show()
print max(map(lambda x:max(fidelity[x,:]),range(0,len(fidelity))))
figtext(0,0,gv.densityMatrices.filename()[:-4])