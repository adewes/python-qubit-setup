// This is the main DLL file.

#include "stdafx.h"
#include <iostream>

using namespace std;

#include <cmath>
#include "acqiris.h"


BifurcationMap::BifurcationMap()
{
	setRotation(0,0);
}

BifurcationMap::~BifurcationMap()
{
}

//This initializes the bifurcation class...
void BifurcationMap::init()
{
	index = 0;
	//Set all the averages to 0
	for(int k=0;k<4;k++)
		for(int i = 0;i<nPoints;i++)
			averages[i+k*nPoints]=0;
	
	probabilities[0]=0;
	probabilities[1]=0;

	for(int i = 0;i< 4;i++)
		crossProbabilities[i]=0;
}

//This processes "waveform" and calculates probabilities, averages, etc...
void BifurcationMap::add(double *matrix)
{
	//Loop over all segments
	for(int j=0;j<nSegments;j++)
	{
		//Loop over all channels
		for(int k=0;k<4;k++)
		{
			int trendind = index+k*nSegments*nLoops;
			trends[trendind]= 0;
			for(int i=0;i<nPoints;i++)
			{
				int ind = i+j*nPoints+k*nPoints*nSegments;
				trends[trendind]+=matrix[ind];
				averages[i+k*nPoints]+=matrix[ind];
			}
			trends[trendind]/=(double)nPoints;
		}
		bool switched1 = false;
		bool switched2 = false;
		if (activeChannels & 3 == 3)
		{
			//Rotate the trend information to obtain the bifurcation criterion.
			double c = trends[index+0*nSegments*nLoops]*costable[0]+trends[index+1*nSegments*nLoops]*sintable[0];
			//Check the bifurcation criterion for channels 1 & 2.
			if (c>0)
			{
				switched1 = true;
				probabilities[0]+=1.0;
			}
		}
		if (activeChannels & 12 == 12)
		{
			//Rotate the trend information to obtain the bifurcation criterion.
			double c = trends[index+2*nSegments*nLoops]*costable[1]+trends[index+3*nSegments*nLoops]*sintable[1];
			//Check the bifurcation criterion for channels 3 & 4.
			if (c>0)
			{
				switched2 = true;
				probabilities[1]+=1.0;
			}
		}
		//Add the switching event to the joint probability table containing P(00),P(10),P(01),P(11)
		if (activeChannels == 15)
			crossProbabilities[(switched1 == true ? 2:0)+(switched2 == true ? 1:0)]+=1.0;
		index++;
	}
}

//Sets the rotation angles for the bifurcation map procedure.
void BifurcationMap::setRotation(double r1,double r2)
{
	rotation[0] = r1;
	rotation[1] = r2;
	costable[0] = cos(r1);
	sintable[0] = sin(r1);
	costable[1] = cos(r2);
	sintable[1] = sin(r2);
}

//This finishes the data treatment.
void BifurcationMap::finish()
{
	//Finish the data processing by normalizing the probabilities and averages.
	probabilities[0]/=(double)index;
	probabilities[1]/=(double)index;

	for(int i = 0;i< 4;i++)
		crossProbabilities[i]/=(double)index;

	for(int k = 0;k< 4;k++)
	{
		for(int i=0;i<nPoints;i++)
		{
			averages[i+k*nPoints]/=(double)index;
		}
	}
}
