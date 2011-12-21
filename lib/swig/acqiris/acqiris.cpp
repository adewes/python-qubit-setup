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
		if ((activeChannels & 3) == 3)
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
		if ((activeChannels & 12) == 12)
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


Averager::Averager()
{

}

Averager::~Averager()
{

}
void Averager::init()
{

	for (n=0;n<nSegments;n++)
	{
		for(nf=0;nf<nFrequencies;nf++)
		{
			for(channel=0;channel<4;channel++)
			{
				components[channel+4*nf+4*nFrequencies*n]=0;
				averages[channel+4*nf]=0;

			}
		}
	}
}


void Averager::add(double *matrix)
{

	//Loop over all segments
	for(n=0;n<nSegments;n++)
	{
		//Loop over all channels
		for(channel=0;channel<4;channel+=2)
		{
			//Loop over all frequencies
			for(nf=0;nf<nFrequencies;nf++)
			{
				//cp=cos(phicorretion[nf]);
				//sp=sin(phicorretion[nf]);
				indexComponents=nf+nFrequencies*(n+nSegments*channel);
				indexAverages=nf+nFrequencies*(channel);
				for(point=0;point<nPoints;point++)
				{
					double t = (double)point*sampleInterval;
					indexMatrix=point+nPoints*(n+nSegments*channel);
					c=cos(2*PI*t*frequencies[nf]-phicorrection[nf]); 
					s=sin(2*PI*t*frequencies[nf]);

					components[indexComponents]+=matrix[indexMatrix]*c/(double)nPoints*Icorrection[nf];
					components[indexComponents+nFrequencies*nSegments]+=matrix[indexMatrix+nFrequencies*nSegments]*s*Qcorrection[nf]/(double)nPoints;
				}
				averages[indexAverages]+=components[indexComponents]/(double)nSegments;
				averages[indexAverages+nFrequencies]+=components[indexComponents+nFrequencies*nSegments]/(double)nSegments;
			}
		}
	}
}

void Averager::finish()
{
	// ECRIRE QUELQUE CHOSE ICI (UTILE, DE PREFERENCE) --- > rien trouve d'interessant ....
}


/*multiplexed bifurcation map*/


 MultiplexedBifurcationMap::MultiplexedBifurcationMap()
{
	int dimensionF=1;
}

MultiplexedBifurcationMap::~MultiplexedBifurcationMap()
{
}

//This initializes the bifurcation class...
void MultiplexedBifurcationMap::initF(double f)
{
}


//Sets the rotation angles for the bifurcation map procedure.
void MultiplexedBifurcationMap::setRotation(double r, double Io, double Qo, double f)
{
	int found = 0;
	for (int i=0;i<dimensionF;i++)
	{
	if (fTable[i] == f)
		{
			Ioffset[i] = Io;
			Qoffset[i] = Qo;
			CosTable[i] = cos(r);
			SinTable[i] = sin(r);
			found = 1;
			cout << "ligne : " << i << "Io,Qo,r" << Io << Qo << r << endl;
		}
	}
	if (found == 0)
	{
		dimensionF++;
		fTable.push_back(f);
		Ioffset.push_back(Io);
		Qoffset.push_back(Qo);
		CosTable.push_back(cos(r));
		SinTable.push_back(sin(r));
		cout << "adding new line, number of lines = " << dimensionF << endl;
	}

}

//This finishes the data treatment.
void MultiplexedBifurcationMap::finish()
{
	//Finish the data processing by normalizing the probabilities and averages.
	probabilities[0]/=(double)index;
	probabilities[1]/=(double)index;

	for(int i = 0;i++;i< 4)
		crossProbabilities[i]/=(double)index;

	for(int k = 0;k< 4;k++)
	{
		for(int i=0;i<nPoints;i++)
		{
			averages[i+k*nPoints]/=(double)index;
		}
	}
}

void MultiplexedBifurcationMap::add(double *f, double *trends, int numberOfFrequencies, int numberOfSegments,double *results)
{
	double Io,Qo,c,s;
	int nf, i, ns;
	int indexTrends;
	double point;
	// for each frequencie sent
	for(nf=0; nf<numberOfFrequencies; nf++)
	{
		// find the good parameters for this frequency
		int found = 0;
		for (i=0;i<dimensionF;i++)
		{
			if (fTable[i] == f[nf])
			{
				Io=Ioffset[i];
				Qo=Qoffset[i];
				c=CosTable[i];
				s=SinTable[i];
				found = 1;
				cout << "frequency found : " << "Io : " << Io << " Qo : " << Qo << " cos : " << c << " sin : " << s << endl;
			}
		}
		if (found == 1)
		{
			//loop over all segments
			for(ns=0; ns<numberOfSegments;ns++)
			{
				int ch=0;
				indexTrends=nf+numberOfFrequencies*(ns+numberOfSegments*ch);
				point = (trends[indexTrends]-Io)*c+(trends[indexTrends+numberOfFrequencies*numberOfSegments]-Qo)*s;
				if (point>0)
					results[indexTrends]=1;
				else results[indexTrends]=0;
				}

		}

	}
}
void MultiplexedBifurcationMap::convertToProbabilities(int nbQB, int nbSegments, double *r, double *proba)
{
	int i;
	int qb;
	for(i =0; i<nbSegments, i++)
	{
		value=0;
		for(qb=0; qb<nbQb; qb++)
		{
			value+=pow(2,(nbQb-qb))*r[qb+i*nbQb]
		}
		proba[value]+=1./nSegments
	}
}