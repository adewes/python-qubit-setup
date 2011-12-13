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
process_matrix = matrix([[1,0,0,0],[0,1./sqrt(2),-1j/sqrt(2),0],[0,-1.j/sqrt(2),1./sqrt(2),0],[0,0,0,1]])
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

epsilon_states_theory = []

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
			epsilon_states_theory.append(process(states_theory[i]))
			mapping_matrix[i,:] = array(states[i].ravel())[0,:]
	else:
		states_theory = states
		for i in range(0,len(gv.densityMatrices)):
			epsilon_states_theory.append(process(states_theory[i]))
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
			
	rho_final_2 = state.ravel()*lambda_matrix

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
plotChi(chi,"chi_experimental")
plotChi(chi_ideal,"chi_theory")
if gv.densityMatrices.parent().filename() != None:
	figtext(0,0,gv.densityMatrices.parent().filename()[:-4])
show()
fidelity = trace(chi*chi_ideal)

print "Process fidelity: %g " % fidelity

S = lambda_matrix

##We plot the eigenvalues of the lambda matrix

(evl,evtl) = eig(S)

fidelity = trace(chi*chi_ideal)

figure("eigenvalues")
clf()
angles = arange(0,math.pi*2.0,0.01)
plot(cos(angles),sin(angles),'r')
plot(fidelity*cos(angles),fidelity*sin(angles))
scatter(real(evl),imag(evl))
xlabel(r"$\mathbb{Re}(\lambda_i)$")
ylabel(r"$\mathbb{Im}(\lambda_i)$")
xlim(-1.1,1.1)
ylim(-1.1,1.1)
show()
show()
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
#	output_fidelities.append(float(abs(quantumFidelity(epsilon_states[i],process(states[i])))))
	output_fidelities.append(float(trace(epsilon_rhos[i]*adjoint(process(rhos[i])) )/ sqrt(trace(process(rhos[i])*adjoint(process(rhos[i])))*trace(rhos[i]*adjoint(rhos[i])) ) ))
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

state_titles = generateCombinations([r"$|0>$",r"$|1>$",r"$\frac{|0>+i|1>}{\sqrt{2}}$",r"$\frac{|0>+|1>}{\sqrt{2}}$"],lambda x,y:x+y,2)

filename = None

if gv.densityMatrices.parent().filename() != None:
	filename = gv.densityMatrices.parent().filename()

#plots = [states,epsilon_states,epsilon_rhos]
#titles = [state_titles,state_titles,titles]

def plotInputOutputMatrices(input,output,name = "matrices",filename = None,titles = None,**kwargs):
	figure(name)
	clf()
	ioff()
	i = 1
	if filename != None:
		figtext(0,0,filename)
	subplots_adjust(hspace=0.01,wspace=0.05) 
	for (inp,out) in zip(input,output):
		if i <= 8:
			j = 0
		else:
			j = 8
		subplot(4,8,i+j)
		plotDensityMatrix(inp,annotate = False,**kwargs)
		if not titles == None:
			title(titles[i-1],fontsize = 6,verticalalignment = 'bottom')
		ax = gca()
		a = Arrow(x = 1.5,y = -1,dx = 0,dy = -1,zorder = 10,width = 2,lw = 0,color = 'black',clip_on = False)
		ax.add_artist(a)
		subplot(4,8,i+j+8)
		plotDensityMatrix(out,annotate = False,**kwargs)

		i+=1
	show()


plotInputOutputMatrices(states,epsilon_states,titles = state_titles,filename = filename,name = "rho_exp_2")
plotInputOutputMatrices(states_theory,epsilon_states_theory,titles = state_titles,filename = filename,name = "rho_theory")
show()
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

##Plot the optimized chi matrix
plotChi(best_chi,"best")
if gv.densityMatrices.parent().filename() != None:
	figtext(0,0,chiMatrix.filename()[:-4])
show()

print trace(best_chi*chi_ideal)

chiMatrix.parameters()["fidelity"] = float(trace(best_chi*chi_ideal))
chiMatrix.savetxt(forceSave = True)

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
##Load the chi matrix and plot it...
chi = matrix(zeros((16,16),dtype = complex128))
for i in range(0,16):
	for j in range(0,16):
		chi[i,j] = gv.chiMatrix[str(i)+","+str(j)][1]
plotDensityMatricesContour([chi],figureName = "original")
show()
##We plot a chi matrix
importModule("scripts.state_tomography.plot_density_matrix")
from scripts.state_tomography.plot_density_matrix import *
figure("rho")
cla()
state = tensor(es,gs)+tensor(gs,es)
state = state / norm(state)
rho = adjoint(state)*state
import numpy
idealChi = matrix(zeros((16,16),dtype = complex128))

coeffs = []

process_matrix = matrix([[1,0,0,0],[0,0,1j,0],[0,1j,0,0],[0,0,0,1]])

m = 0

for e in E:
	vec = e.ravel()
	vec = vec / pow(norm(vec),2.0)
	coeffs.append((vec*adjoint(process_matrix.ravel()).tolist())[0,0])
	m += coeffs[-1]*e
	
	
for i in range(0,16):
	for j in range(0,16):
		idealChi[i,j] = coeffs[i]*adjoint(coeffs[j])

labels = generateCombinations([r"\mathbb{1}",r"\sigma_x",r"i\sigma_y",r"\sigma_z"],lambda x,y:r"$ "+x+r"\times "+y+r" $",2)

chiMatrix = matrix(zeros((16,16),dtype = complex128))
for i in range(0,16):
	for j in range(0,16):
		chiMatrix[i,j] = gv.chiMatrix[str(i)+","+str(j)][0]
rho2 = rho+numpy.random.normal(0,0.1,(4,4))+1j*numpy.random.normal(0,0.1,(4,4))-1j*numpy.random.normal(0,0.1,(4,4))
clf()
plotDensityMatricesContour([chiMatrix,chi_ideal],figureTitle = "chi matrix vs. theory",labels = labels)
show()

##
plotDensityMatricesContour([tensor(conjugate(As[-1]),As[-1]),tensor(conjugate(As[-2]),As[-2]),S],figureName = "S")
show()
##
figure("eigenvals")
cla()
phis = arange(0,math.pi*2.0,0.001)
xs = cos(phis)
ys = sin(phis)
(eigenvalsS,eigenvecsS) = eig(S)
scatter(real(eigenvalsS),imag(eigenvalsS))
plot(xs,ys)
plot(xs*0.92,ys*0.92)
xlim(-1,1)
ylim(-1,1)
axhline(0)
axvline(0) 	
show()
##
f = 0
for i in range(0,len(As)):
	f+=pow(abs(trace(adjoint(process_matrix)*As[i]*sqrt(eigenvals[i]))/4.),2.)
print f
##
plotChi(chiMatrix,name = "test")
show()
print trace(chiMatrix*adjoint(chiMatrix))
##QR decomposition
(q,r) = qr(As[-1])
figure("qr")
subplot(121)
cla()
plotDensityMatrix(q,figureName = None)
title("Q")
subplot(122)
cla()
plotDensityMatrix(r,figureName = None)
title("R")
show()
##Calculation of Choi's matrix based on chi

(ev,evv) = eigh(chi)

As = []

for i in range(0,len(evv)):
	eigenvec = transpose(evv)[i,:]
	A = 0
	for j in range(0,16):
		A+=E[j]*eigenvec[0,j]
	As.append(A*sqrt(ev[i]))
	
importModule("scripts.state_tomography.plot_density_matrix")
from scripts.state_tomography.plot_density_matrix import *

plotDensityMatrices(map(lambda x:qr(x)[0],reversed(As[-4:])),name = "As",titles = map(lambda x:"%.1f %%" % (x*100),reversed(ev[-4:])))

show()

S = 0 

for i in range(0,len(As)):
	S+=tensor(As[i].conj(),As[i])

plotDensityMatricesContour([S],figureName = "S")
show()
##Check that the lambda and chi representations match...

for state in states:

	epsilon_state = devectorizeRho(transpose(lambda_matrix)*transpose(state.ravel()))
	
	epsilon_state_2 = 0
	
	for i in range(0,16):
		epsilon_state_2+=As[i]*state*adjoint(As[i])
	
	if not allclose(epsilon_state,epsilon_state_2):
		print "Error!"
		print norm(epsilon_state-epsilon_state_2)
	else:
		print "It worked!"

##

def choi(S):
	T = 0

	id = matrix(eye(4,dtype = complex128))
	for i in range(0,4):
		for j in range(0,4):
			Eij = matrix(zeros((4,4),dtype = complex128))
			Eij[i,j] = 1
			T+=tensor(Eij,id)*S*tensor(id,Eij)
	return T

T = choi(lambda_matrix)

plotDensityMatricesContour([T],figureName = "T")
show()
print eigh(T)[0]
##
(evt,evvt) = eigh(T)
Ass = []
TT = 0
for i in range(0,16):
	TT+=evt[i]*evvt[:,i]*adjoint(evvt[:,i])
	A = sqrt(evt[i])*(evvt[:,i].reshape((4,4)))
	Ass.append(A)
Lambda = 0
Lambda2 = 0
for i in range(0,16):
	if evt[i] > 0 or True:
		Lambda+=tensor(conjugate(Ass[i]),Ass[i])
	Lambda2+=tensor(conjugate(As[i]),As[i])

print norm(Lambda-Lambda2)
plotDensityMatricesContour([Lambda,Lambda2],figureName = "Lambda")
show()
##

Tprime = T

for i in range(0,10):

	(evt,evtt) = eigh(Tprime)
	
	Tprime = reduce(lambda x,y:x+y,map(lambda x: evvt[:,x]*(evt[x] > 0 and evt[x] or 0.)*adjoint(evvt[:,x]),range(0,len(evvt))))
	
	Sprime = choi(Tprime)

	dS = 1./4.*(adjoint(id.ravel())*id.ravel()*Sprime-tensor(id,id))

	Sprime-=dS

	Tprime = choi(Sprime)

print evt
chiprime = calculateChi(beta,Sprime)
print trace(chiprime)

plotDensityMatricesContour([lambda_matrix,Sprime],figureName = "Lambda")
##
Tpp = 0
id = matrix(eye(4,dtype = complex128))
for i in range(0,4):
	for j in range(0,4):
		Eij = matrix(zeros((4,4),dtype = complex128))
		Eij[i,j] = 1
		T+=tensor(Eij,id)*S*tensor(id,Eij)

dS = 1./4.*(adjoint(id.ravel())*id.ravel()*Sprime)-tensor(id,id)
print trace(choi(Sprime))
print trace(choi(Sprime-dS))
#Sprime = Sprime-dS
##Plot some density matrices
rho = matrix(zeros((4,4)),dtype = complex128)
stateIdeal = tensor(es,gs)-1j*tensor(gs,es)
stateIdeal = stateIdeal/norm(stateIdeal)
stateIdeal = tensor(gs,gs)
rhoIdeal = adjoint(stateIdeal)*stateIdeal
for i in range(0,4):
	for j in range(0,4):
		rho[i,j] = gv.densityMatrices[str(i)+str(j)][1]
plotDensityMatricesContour([rhoIdeal,rho],figureName = "density matrix",labels = ["|11>","|01>","|10>","|00>"])
show()
##We calculate the eigenvalues and eigenoperators of the chi matrix
(ev,evv) = eigh(chi)
figure("eigenvalues")
cla()
bar(range(0,len(ev)),ev)
show()
##
figure("operator")
clf()
plotDensityMatrix(As[-1]/sqrt(ev[-1]),figureName = "operator")
show()

output_states = []

for state in states:
	i = -1
	output_state = As[i]*state*adjoint(As[i])/ev[i]
	output_states.append(output_state)

plotDensityMatrices(output_states,name = "output_states")
plotDensityMatrices(map(lambda x:x,map(lambda x:qr(x[0]/sqrt(x[1]))[0],zip(As,ev))),name = "operators_Q")
plotDensityMatrices(map(lambda x:x,map(lambda x:qr(x[0]/sqrt(x[1]))[1],zip(As,ev))),name = "operators_H")
##Calculating the log of the S matrix

Sideal = tensor(conjugate(process_matrix),process_matrix)

(evs,evvs) = eig(S)
(evsIdeal,evvsIdeal) = eig(Sideal)

logevs = map(lambda x:log(x),evs)
logevsIdeal = map(lambda x:log(x),evsIdeal)

logS = evvs*diag(logevs)*adjoint(evvs)
logSIdeal = evvsIdeal*diag(logevsIdeal)*adjoint(evvsIdeal)

plotChi(logS,name = "logS")
plotDensityMatricesContour([logS,logSIdeal],figureName = "logSd")
plotDensityMatricesContour([logS-logSIdeal],figureName = "logSdiff",labels = generateCombinations(["0","1"],lambda x,y:x+y,4) )
show()
##Simulation of process matrix with relaxation...
idtot = tensor(idatom,idatom)
drive1 = tensor(sigmax,idatom)
sm1 = tensor(sigmam,idatom)
sm2 = tensor(idatom,sigmam)
sp1 = tensor(sigmap,idatom)
sp2 = tensor(idatom,sigmap)
sz1 = tensor(sigmaz,idatom)
sz2 = tensor(idatom,sigmaz)

sx1 = tensor(sigmax,idatom)
sx2 = tensor(idatom,sigmax)
sy1 = tensor(sigmay,idatom)
sy2 = tensor(idatom,sigmay)

def generateL(params):

	(Delta,g,gamma1,gamma2,gammaphi1,gammaphi2,t,dz1,dz2) = params
	
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
	
	H = -Delta/2.0*sz1+Delta/2.0*sz2+g/2.0*(sp1*sm2+sm1*sp2)+dz1*sz1+dz2*sz2
	LH = -1.j*(spre(H)-spost(H))
	
	Ltot = (LH+L)*t
	
	return Ltot
	
p1 = (1.0/800.*0,1.0/800.*0,31,0.00,0.0)
p1fixed = (0,0.0082*math.pi*2.0,1./450.,1./450.)

LT1 = generateL((0,0.0082*math.pi*2.0*0,1./450.,1./450.*0,1.0/800.*0,1.0/800.*0,31,0.00,0.0))

plotDensityMatricesContour([logS-generateL(p1fixed+p1),LT1],figureName = "logSdiff",labels = generateCombinations(["00","10","01","11"],lambda x,y:x+y,2) )
show()
##Make a fit of 
p1s = scipy.optimize.fmin(lambda p: norm(generateL(list(p1fixed)+list(p))-logS),p1,	maxfun = 1e5,maxiter = 1e5)
##
plotDensityMatricesContour([-(logSIdeal-logS),-(logSIdeal-generateL(list(p1fixed)+list(p1s)))],figureName = "logSoptimized",labels = generateCombinations(["0","1"],lambda x,y:x+y,4) )
figtext(0,0,gv.tomographyData.filename()[:-4])
show()

##Simulate the L and chi matrices of some processes...

Lphi1 = generateL((0,0.0082*math.pi*2.0*0,1./450.*0,1./450.*0,1.0/800.,1.0/800.,31,0.00,0.0))
LT11 = generateL((0,0.0082*math.pi*2.0*0,1./450.,1./450.*0,1.0/800.*0,1.0/800.*0,31,0.00,0.0))
p1 = (3.23201963e-03,0.0082*math.pi*2.0,1./450.,1./450.,1.0/800.,1.0/800.,31,0.00,0.0)

Lswap = generateL(p1)
LswapIdeal = generateL((0,0.0082*math.pi*2.0,1./450.*0,1./450.*0,1.0/800.*0,1.0/800.*0,31,0.00,0.0))

state = tensor(gs+es,gs)

state = state / norm(state)

rho = adjoint(state)*state

expLT11 = scipy.linalg.expm(LT11)
expLphi1 = scipy.linalg.expm(Lphi1)
expLswap = scipy.linalg.expm(Lswap)
expLswapIdeal = scipy.linalg.expm(LswapIdeal)

#plotDensityMatricesContour([expLT11,expLphi1,expLswap],figureName = "logSrelax",labels = generateCombinations(["00","10","01","11"],lambda x,y:x+y,2) )
#show()

def errorFunction(p):
	chiSwap = calculateChi(p)
	return norm(chiSwap-chi)
	
def completeParams(p):
	ps = list(p1)
	ps[0] = p[0]
	ps[4] = p[1]
	ps[5] = p[2]
	ps[-2]= p[3]
	ps[-1]= p[4]
	return ps
	
def calculateChi(p):

	ps = completeParams(p)
	
	L = generateL(ps)
	expL = scipy.linalg.expm(L)
	chi = tensorsolve(beta,expL)
	return chi

p1s = scipy.optimize.fmin(errorFunction,(0,0,0,0,0))

savetxt("i_swap_fit_real.txt",real(calculateChi(p1s)))
savetxt("i_swap_fit_imag.txt",imag(calculateChi(p1s)))

rhop = (expLswap*transpose(rho.ravel())).reshape((4,4))

chiT11 = tensorsolve(beta,expLT11)
chiPhi1 = tensorsolve(beta,expLphi1)
chiSwap = tensorsolve(beta,expLswap)
chiSwapIdeal = tensorsolve(beta,expLswapIdeal)
##
importModule("scripts.state_tomography.plot_density_matrix")
from scripts.state_tomography.plot_density_matrix import *

labels = generateCombinations([r"\mathbb{1}",r"\sigma_x",r"i\sigma_y",r"\sigma_z"],lambda x,y:r"$ "+x+r"\times "+y+r" $",2)
plotDensityMatricesContour([chi,chi_ideal],figureName = "chirelax",labels = labels,show = "lowerTriangular" )
show()
##Calculate the corresponding eigenoperators

(ev,evv) = eigh(array(chi))

As = []

for i in range(0,len(evv)):
	eigenvec = transpose(evv)[i,:]
	A = 0
	for j in range(0,16):
		A+=E[j]*eigenvec[j]
	As.append(A*sqrt(ev[i]))

plotDensityMatrices(As,name = "ops")
show()

i = 1
for A in As:
	savetxt("a_%d_real.txt" % i,real(A))
	savetxt("a_%d_imag.txt" % i,imag(A))
	i+=1

S = 0 

for i in range(0,len(As)):
	S+=tensor(conjugate(As[i]),As[i])

savetxt("s matrix real.txt",real(S))
savetxt("s matrix imag.txt",imag(S))
##
figure("krass")
clf()
subplot(321)
cla()
plotDensityMatricesContour([-As[-1],process_matrix],figureName = None,labels = [r"$|00\rangle$",r"$|01\rangle$",r"$|10\rangle$",r"$|11\rangle$"])
subplot(322)
plotDensityMatricesContour([As[-2]],figureName = None)
subplot(323)
plotDensityMatricesContour([As[-3]],figureName = None)
subplot(324)
plotDensityMatricesContour([As[-4]],figureName = None)
subplot(325)
plotDensityMatricesContour([As[-5]],figureName = None)
show()
subplot(326)
cla()
bar(arange(1,6)-0.5,list(reversed(list(ev)))[:5],color = 'red',log = False)
xticks(arange(1,6),("A","B","C","D","E"))
ylim(0,1)
xlim(0.4,5.5)
yticks(arange(0,1.2,0.2))
show()

##savefig("kraus_operator_1.eps")
show()
##
##
importModule("scripts.state_tomography.plot_density_matrix")
from scripts.state_tomography.plot_density_matrix import *
rho = zeros((4,4))
rho[0,1] = 1
rho[0,0] = 1

plotDensityMatricesContour([rho],figureName = "testrho",labels = generateCombinations(["00","10","01","11"],lambda x,y:x+y,2) )
plotDensityMatrix(rho,figureName = "testrho")
show()

##

for rho in [rhos[5]]:

	epsilon_rho = 0
	
	for i in range(0,16):
		for j in range(0,16):
			epsilon_rho+=chi[i,j]*E[i]*rho*adjoint(E[j])
	
	epsilon_rho_kraus = 0
	
	for k in range(0,16):
		epsilon_rho_kraus+=As[k]*rho*adjoint(As[k])
		
	if not allclose(epsilon_rho_kraus,epsilon_rho):
		print "error!"
	else:
		print "success!"
		
	print rho,"\n",epsilon_rho
		