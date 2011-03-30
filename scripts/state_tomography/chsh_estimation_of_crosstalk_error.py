state = tensor(es,gs)+tensor(gs,es)
state = tensor(es+gs,es+gs)
state = state / norm(state)
relax = 0.12
rho = adjoint(state)*state*(1-relax)+relax*adjoint(tensor(gs,gs))*tensor(gs,gs)

def sigma_ij(rho,i,j,C,C_inv):
	"""
	Calculates the value of <sigma_i,sigma_j> on rho simulating a crosstalk modeled by a matrix C and a linear compensation of visibility modeled by a matrix C
	"""

	sigmas = {"x":sigmax,"y":sigmay,"z":sigmaz,"i":idatom}
	Proj_i = createMeasurement(sigmas[i])
	Proj_j = createMeasurement(sigmas[j])

	ps = zeros(4)

	ps[0] = trace(tensor(Proj_i[+1],Proj_j[+1])*rho) #p_00
	ps[1] = trace(tensor(Proj_i[-1],Proj_j[+1])*rho) #p_10
	ps[2] = trace(tensor(Proj_i[+1],Proj_j[-1])*rho) #p_01
	ps[3] = trace(tensor(Proj_i[-1],Proj_j[-1])*rho) #p_11

	clicks = C_inv*(C*transpose(matrix(ps)))

	m = matrix([1,-1,-1,1])

	return (m*clicks)[0,0]

visibility_1 = 0.74
visibility_2 = 0.75

C = eye(4)

C_lin_1 = matrix([[0.5+visibility_1/2.,0.5-visibility_1/2.0],[0.5-visibility_1/2.,0.5+visibility_1/2.]])
C_lin_2 = matrix([[0.5+visibility_2/2.,0.5-visibility_2/2.0],[0.5-visibility_2/2.,0.5+visibility_2/2.]])

C_lin = tensor(C_lin_1,C_lin_2)

C_crosstalk = matrix([[1.04,0.02,0.02,0],[0.05,0.95,0.0,0.0],[0.02,0.01,0.99,0.0],[0,0.1,0.03,0.88]])

C_crosstalk = eye(4)

alpha = 0.05
beta = 0.03

#C_crosstalk = matrix([[1,0,0,0],[0,1-alpha,0,0],[0,0,1-beta,0],[0,alpha,beta,1]])

C = C_lin*C_crosstalk

C_inv = inv(C_lin)

data = Datacube("simu")

from pyview.helpers.datamanager import DataManager

dataManager = DataManager()

dataManager.addDatacube(data)

s = lambda i:sigma_ij(rho,i[0],i[1],C,C_inv)

for phi in linspace(0,math.pi*2.0,100):
	chsh = cos(phi)*(s("yx")+s("xx")-s("xy")+s("yy"))+sin(phi)*(s("yy")+s("xy")+s("xx")-s("yx"))
	data.set(phi = phi*180.0/math.pi)
	data.set(chsh = chsh)
	data.commit()

print max(data["chsh"])
##
print trace(tensor(sigmay,sigmay)*rho),sigma_ij(rho,"y","y",C,C_inv)