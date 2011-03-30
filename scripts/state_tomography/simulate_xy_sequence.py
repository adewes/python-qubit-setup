from qulib import *

sangles = linspace(-15,15,20)

ms = zeros((len(sangles),len(sangles)),dtype = complex128)

cx = 0
angle = (90)/180.0*math.pi
for a in sangles:
	cy = 0
	for b in sangles:
		values = []
		for c in arange(0,360,10):
			state = gs
			state = state*pauliRotation(math.pi/2.0+a/180.0*math.pi,cos(b/180.0*math.pi),sin(b/180.0*math.pi),0)*pauliRotation(c,cos(angle),sin(angle),0)
			values.append (abs(state[0,1]))
		ms[cx,cy] = numpy.var(values)
		cy+=1
	cx+=1
figure("matrix (theory)")
cla()
imshow(real(ms),interpolation = 'nearest',extent = (0,360,0,360))

xlabel("x angle")
ylabel("y angle")