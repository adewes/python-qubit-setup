#Some function definitions...
from qulib import *
from numpy.linalg import *
import scipy.optimize
import random

w_psi_plus = 1./4.*(tensor(idatom,idatom)-tensor(sigmax,sigmax)+tensor(sigmay,sigmay)-tensor(sigmaz,sigmaz))
w_psi_minus = 1./4.*(tensor(idatom,idatom)+tensor(sigmax,sigmax)-tensor(sigmay,sigmay)-tensor(sigmaz,sigmaz))
w_phi_plus = 1./4.*(tensor(idatom,idatom)-tensor(sigmax,sigmax)-tensor(sigmay,sigmay)+tensor(sigmaz,sigmaz))
w_phi_minus = 1./4.*(tensor(idatom,idatom)+tensor(sigmax,sigmax)+tensor(sigmay,sigmay)+tensor(sigmaz,sigmaz))



#CHSH Measurement
def CHSH(phi,i=1):
	Q=sigmaz
	R=sigmax
	S=-cos(phi)*sigmaz-sin(phi)*sigmax
	T=sin(phi)*sigmaz-cos(phi)*sigmax
	CHSHMat=tensor(Q,S)+tensor(R,S)+i*tensor(R,T)-i*tensor(Q,T)
	return CHSHMat

densityMatrix=matrix(zeros((4,4),dtype=complex128))

chshdata=Datacube()
chshdata.setName("CHSH from rhoMat")
rhoMatData.addChild(chshdata)

do_w_calculation=False
do_chsh_calculation=False
for i in range(0,len(rhoMatData)):
	print "row %s" %str(i)
	for row in range(0,4):
		for column in range(0,4):
			densityMatrix[row,column]=rhoMatData.column(str(row)+str(column))[i] #rhoMatData._table[i,rhoMatData._map[str(row)+str(column)]]
			#zPulseLength=rhoMatData._table[i,rhoMatData._map[zPulseLength]]
	if do_w_calculation:
		for row in range(0,4):
			for column in range(0,4):
				phibell=angle(densityMatrix[2,1])
				rhoMatData.setAt(i,w_psi_plus = trace(densityMatrix*w_psi_plus))
				rhoMatData.setAt(i,w_psi_minus = trace(densityMatrix*w_psi_minus))
				rhoMatData.setAt(i,w_phi_plus = trace(densityMatrix*w_phi_plus))
				rhoMatData.setAt(i,w_phi_minus = trace(densityMatrix*w_phi_minus))
				rhoMatData.setAt(i,phibell = phibell)
	if do_chsh_calculation:
		for phichsh in [math.pi/4.]:#arange(-math.pi,math.pi,0.01):
			chshdata.set(phichsh=phichsh)
			chshdata.set(zPulseLength=rhoMatData.column("zPulseLength")[i])
			chshdata.set(phibell=rhoMatData.column("phibell")[i])
			chshdata.set(chsh1=trace(densityMatrix*CHSH(phichsh)))
			chshdata.commit()
		chshdata.savetxt()

#plotDensityMatrix(densityMatrix)#,export="rhomats/rhomat_"+str(i)+".png")
	rhoMatData.setAt(i,errorimage=0)
	if rhoMatData.column("errorimage")[i]!=1:
		print "Plotting..."
		try:
			plotDensityMatrix(densityMatrix,export="film of swap/rhomats/rhomat_%.3d.png" % i,figureTitle = "t = %g ns" % rhoMatData.column("duration")[i])#,figureName="phibell = %s" % str(phibell))
		except:
			print "Failed!"
			print sys.exc_info()
			rhoMatData.setAt(i,errorimage=1)
rhoMatData.savetxt()

##

##
from pyview.helpers.datamanager import DataManager
dataManager = DataManager()3
##
phi_wit=Datacube()
dataManager.addDatacube(phi_wit)
phi_wit.setName("phi_wit")
phi_wit.createColumn("zPulseLength",real(rhoMatData.column("zPulseLength")))
phi_wit.createColumn("phibell",real(rhoMatData.column("phibell")))
phi_wit.createColumn("w_phi_minus",real(rhoMatData.column("w_phi_minus")))
phi_wit.createColumn("w_phi_plus",real(rhoMatData.column("w_phi_plus")))
phi_wit.savetxt()


##

#chshdata=Datacube()
#chshdata.setName("CHSH from rhoMat theory")
#rhoMatData.addChild(chshdata)

state=tensor(gs,es)-tensor(es,gs)
state=state/norm(state)
densityMatrix=adjoint(state)*state
chshdata.goTo(0)
for i in range(0,len(chshdata)):
	state=tensor(gs,es)+exp(1j*chshdata.column("phibell")[i])*tensor(es,gs)
	state=state/norm(state)
	densityMatrix=adjoint(state)*state
	for phichsh in [math.pi/4.]:#arange(-math.pi,math.pi,0.01):
		chshdata.set(phichsh=phichsh)
		chshdata.set(chsh_th=trace(densityMatrix*CHSH(phichsh)))
		chshdata.commit()
chshdata.savetxt()	