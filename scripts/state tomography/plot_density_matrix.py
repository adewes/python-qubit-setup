def plotDensityMatrix(densityMatrix,figureName = "rho"):
	from pyview.ide.mpl.backend_agg import figure
	fig = figure(figureName)
	from matplotlib.patches import Ellipse
	import matplotlib.cm
	
	NUM = 250
	
	cmap = get_cmap('jet')
	clf()
	cla()
	ells = dict()
	
	ax = subplot(111, aspect='equal')
	for i in range(0,4):
		ells[i] = dict()
		ax.add_artist(Line2D([-1,4],[0.5+i,0.5+i],ls = '--',color = 'grey'))
		ax.add_artist(Line2D([0.5+i,0.5+i],[-1,4],ls = '--',color = 'grey'))
		for j in range(0,4):
	
			v = abs(densityMatrix[i,j])
			r = sqrt(v)*0.9
			phi = angle(densityMatrix[i,j])
	
			ells[i][j] =Ellipse(xy=(i,j), width=r, height=r, angle=0)
			e = ells[i][j]
	
			fc = cmap((phi+math.pi)/2.0/math.pi)
			t = Text(x = i+0.5-0.04,va = 'top',ha = 'right',y = j+0.5-0.04,text = "%.2f" % v,size = 'medium' )
			e2 =Ellipse(xy=[i,j], width=1.0, height=1.0, angle=0,fill = False,zorder = -1)
			a = Arrow(x = i,y = j,dx = 0.5*r*cos(phi),dy = 0.5*r*sin(phi),zorder = 10,width = 0.5*v,fc = map(lambda x:x*0.5,fc),lw = 0)
	
			e.set_clip_box(ax.bbox)
			e.set_alpha(1.0)
			e.set_facecolor(fc)
	
			if v > 0.01:
				ax.add_artist(a)
				ax.add_artist(e)
				ax.add_artist(t)
	
	
	rcParams['font.size'] = 10
	yticks([0,1,2,3],["|00>","|10>","|01>","|11>"])
	xticks([0,1,2,3],["<00|","<10|","<01|","<11|"])
	xlim(-0.5, 3.5)
	ylim(-0.5, 3.5)
	#grid()
	
	