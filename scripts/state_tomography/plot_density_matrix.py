from qulib import *

def plotChi(chi,name = None,filename = None):
	if name != None:
		fig = figure(name)
		clf()
		cla()
	else:
		fig = gcf()
	jet()
	subplot(131)

	if filename != None:
		figtext(0,0,filename)
	
	minv = round(min(min(array(imag(chi)).ravel()),min(array(real(chi)).ravel() )),1)
	maxv = round(max(max(array(imag(chi)).ravel()),max(array(real(chi)).ravel() )),1)
	
	if int((maxv-minv)*10)%2 == 1:
		maxv+=0.1
	
	ticks = linspace(minv,maxv,(int((maxv-minv)*10))/2+1)
	
	print ticks
	
	title("$\chi$ - real part")
	v1 = imshow(array(real(chi)),interpolation = 'nearest',origin = 'lower',vmin = minv,vmax = maxv)
	subplot(132)
	title("$\chi$ - imaginary part")
	v2 = imshow(array(imag(chi)),interpolation = 'nearest',origin = 'lower',vmin = minv,vmax = maxv)	
	subplot(133)
	title("$\chi$ - absolute value")
	v3 = imshow(array(abs(chi)),interpolation = 'nearest',origin = 'lower',vmin = minv,vmax = maxv)	
	
	ax = fig.add_axes([0.12, 0.15, 0.78, 0.05])

	fig.colorbar(v2,cax = ax,orientation = 'horizontal',ticks = ticks)
	draw()

def plotPauliSet(measuredSpins = None,densityMatrix = None,row = None,fill = False,lw = 1,ls = 'solid'):

	operators = ["x","y","z"]
	
	allOperators = ["xi","yi","zi","ix","iy","iz"]+generateCombinations(operators,lambda x,y:x+y,2)

	realOperators = [tensor(sigmax,idatom),tensor(sigmay,idatom),tensor(sigmaz,idatom),tensor(idatom,sigmax),tensor(idatom,sigmay),tensor(idatom,sigmaz)]+generateCombinations([sigmax,sigmay,sigmaz],lambda x,y:tensor(x,y),2)	

	values = []
	
	if measuredSpins != None:
		for operator in allOperators:
			if row == None:	
				values.append(mean(measuredSpins.column(operator)))
			else:
				values.append(measuredSpins.column(operator)[row])	
	elif densityMatrix != None:
		for operator in realOperators:
			values.append(trace(densityMatrix*operator))
	bar(arange(0,len(values),1),values,edgecolor = (0.4,0.4,0.4),lw = lw,color = ["#AA0000"]*3+["#00AA00"]*3+["#0000AA"]*9,fill = fill,ls = ls)
	ylabel("mean value")
	xlim(0,len(values))
	axhline(1,color = 'black',ls = ':')
	axhline(-1,color = 'black',ls = ':')
	axvline(2.9,color = 'black',ls = ':')
	axvline(5.9,color = 'black',ls = ':')
	xticks(arange(0,len(values),1)+0.5,allOperators)

def plotDensityMatrix(densityMatrix,figureName = None,export=None,figureTitle = None,annotate = True):
	from numpy import angle
	from pyview.ide.mpl.backend_agg import figure
	if figureName != None:
		fig = figure(figureName)
	from matplotlib.patches import Ellipse
	import matplotlib.cm
	
	NUM = 250

	#cmap = get_cmap('jet')

	sat = 0.8

	cdict = {'blue': ((0.0, sat, sat),(0.5, 1-sat, 1-sat),(1.0, sat, sat)),'green': ((0.0, 0,0),(0.5, 0,0),(1.0, 0,0)),'red': ((0.0, 1-sat, 1-sat),(0.5,sat,sat),(1,1-sat,1-sat))}
	my_cmap = matplotlib.colors.LinearSegmentedColormap('my_colormap',cdict,256)
	cmap = my_cmap

	if figureName != None:
		clf()
		cla()

	if figureTitle != None:
		title(figureTitle)
	
	ells = dict()
	
	n = densityMatrix.shape[0]

	ax = gca()
	ax.set_aspect('equal')	
	for i in range(0,n):
		ells[i] = dict()
		ax.add_artist(Line2D([-1,4],[0.5+i,0.5+i],ls = '--',color = 'grey'))
		ax.add_artist(Line2D([0.5+i,0.5+i],[-1,4],ls = '--',color = 'grey'))
		for j in range(0,n):
	
			v = abs(densityMatrix[3-j,i])
			r = sqrt(v)*0.9
			phi = angle(densityMatrix[3-j,i])
	
#			ells[i][j] =Ellipse(xy=(i,j), width=r, height=r, angle=0)
			ells[i][j] = Rectangle(xy=(i-r/2,j-r/2),width = r,height = r,lw = 0.5)
			e = ells[i][j]
	
			fc = cmap((phi+math.pi)/2.0/math.pi)
			t = Text(x = i+0.5-0.04,va = 'top',ha = 'right',y = j+0.5-0.04,text = "%.2f" % v,size = 'medium' )
			if i == 3-j:
				rect = Rectangle(xy = [i-0.5,j-0.5],width = 1.0,height = 1.0)
				rect.set_facecolor([0.9,0.9,0.9])
				ax.add_artist(rect)
			a = Arrow(x = i-0.45*r*cos(phi),y = j-0.45*r*sin(phi),dx = r*cos(phi)*0.9,dy = r*sin(phi)*0.9,zorder = 10,width = 1*sqrt(v),fc = map(lambda x:x*0.3,fc),lw = 0)
	
			e.set_clip_box(ax.bbox)
			e.set_alpha(1.0)
			e.set_facecolor(fc)
	
			if v > 0.01 or True:
				ax.add_artist(a)
				ax.add_artist(e)
			if annotate:
				ax.add_artist(t)
	if annotate:
		yticks([0,1,2,3],["|11>","|01>","|10>","|00>"])
		xticks([0,1,2,3],["<00|","<10|","<01|","<11|"])
	else:
		yticks([0,1,2,3],["","","",""])
		xticks([0,1,2,3],["","","",""])

	xlim(-0.5, 3.5)
	ylim(-0.5, 3.5)
	
	if export!=None:
		print "exporting"
		fig.savefig(export)
		
def plotDensityMatricesContour(densityMatrices,figureName = None,export=None,figureTitle = None,annotate = True,labels = [],show = "all"):
	from numpy import angle
	from pyview.ide.mpl.backend_agg import figure
	if figureName != None:
		fig = figure(figureName)
	from matplotlib.patches import Ellipse
	import matplotlib.cm
	
	NUM = 250

	#cmap = get_cmap('jet')

	sat = 0.8

	cdict = {'blue': ((0.0, sat, sat),(0.5, 1-sat, 1-sat),(1.0, sat, sat)),'green': ((0.0, 0,0),(0.5, 0,0),(1.0, 0,0)),'red': ((0.0, 1-sat, 1-sat),(0.5,sat,sat),(1,1-sat,1-sat))}
	my_cmap = matplotlib.colors.LinearSegmentedColormap('my_colormap',cdict,256)
	cmap = my_cmap

	if figureName != None:
		clf()
		cla()

	if figureTitle != None:
		title(figureTitle)
	
	n = densityMatrices[0].shape[0]

	ax = gca()
	ax.set_aspect('equal')	
	
	styles = ["solid","solid"]
	widths = [0.5,1]
	colors = ["black",'red',"blue","magenta","green"]
	
	for i in range(0,n):
		if show == "lowerTriangular":
			ax.add_artist(Line2D([-1,n-i-0.5],[0.5+i,0.5+i],ls = '--',color = 'grey'))	
			ax.add_artist(Line2D([0.5+i,0.5+i],[-1,n-i-0.5],ls = '--',color = 'grey'))
		elif show == "upperTriangular":
			ax.add_artist(Line2D([-1,n],[0.5+i,0.5+i],ls = '--',color = 'grey'))	
			ax.add_artist(Line2D([0.5+i,0.5+i],[-1,n],ls = '--',color = 'grey'))
		else:
			ax.add_artist(Line2D([-1,n],[0.5+i,0.5+i],ls = '--',color = 'grey'))	
			ax.add_artist(Line2D([0.5+i,0.5+i],[-1,n],ls = '--',color = 'grey'))
		for j in range(0,n):
			
			if show == "lowerTriangular":
				if j > n-i:
					continue
			elif show == "upperTriangular":
				if j < i:
					continue
			
			if i == n-j-1:
				rect = Rectangle(xy = [i-0.5,j-0.5],width = 1.0,height = 1.0)
				rect.set_facecolor([0.9,0.9,0.9])
				ax.add_artist(rect)
	
			plotted = False
			
			k = 0
	
			for densityMatrix in densityMatrices:
	
				v = abs(densityMatrix[n-j-1,i])
				r = sqrt(v)*0.9
				phi = angle(densityMatrix[n-j-1,i])
		
				e = Ellipse(xy=(i,j), width=r, height=r, angle=0,ls = styles[k%len(styles)],lw = widths[k%len(widths)])
			
				fc = cmap((phi+math.pi)/2.0/math.pi)
				
				t = Text(x = i+0.5-0.04,va = 'top',ha = 'right',y = j+0.5-0.04,text = "%.2f" % v,size = 'medium' )
				a = Arrow(x = i-0.45*r*cos(phi)*0,y = j-0.45*r*sin(phi)*0,dx = r*cos(phi)*0.5,dy = r*sin(phi)*0.5,zorder = 10,width = 0.1,fc = colors[k%len(colors)],lw = 0)
		
				e.set_clip_box(ax.bbox)
				e.set_alpha(1.0)
				e.set_facecolor('none')
				e.set_edgecolor(colors[k%len(colors)])
		
				if v > 0.01:
					ax.add_artist(a)
					ax.add_artist(e)
					plotted = True
					
				k+=1

			if plotted:
				e2 	= Ellipse(xy=(i,j), width=0.025, height=0.025, angle=0)
				e2.set_facecolor('black')
				e2.set_zorder(n*n*10)
				ax.add_artist(e2)
				

	if annotate and labels != []:
		yticks(arange(n-1,-1,-1),labels,rotation = -45)
		xticks(arange(0,n,1),labels,rotation = -45)
	else:
		yticks([0,1,2,3],["","","",""])
		xticks([0,1,2,3],["","","",""])

	xlim(-0.5, n-0.5)
	ylim(-0.5, n-0.5)
	
	if export!=None:
		print "exporting"
		fig.savefig(export)

def plotDensityMatrices(matrices,name = "matrices",filename = None,titles = None,**kwargs):
	figure(name)
	clf()
	ioff()
	i = 1
	if filename != None:
		figtext(0,0,filename)
	for rho in matrices:
		subplot(4,4,i)
		plotDensityMatricesContour([rho],annotate = False,**kwargs)
		if not titles == None:
			title(titles[i-1],fontsize = 6,verticalalignment = 'bottom')
		i+=1
	show()