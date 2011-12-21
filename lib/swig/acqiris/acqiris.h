// acqiris.h

#pragma once
#include "nr3.h"
#define PI 3.14159268
#include <vector>
/*
The BifurcationMap class.
All the parameters have to be initialized from Python, usually with a ctypes pointer:

Example:

        bm = acqirislib.BifurcationMap()
        bm.activeChannels = 15

        bm.nLoops = 20
        trends = zeros((4,params["numberOfSegments"]*bm.nLoops))
        bm.trends = trends.ctypes.data

		#...

After initializing all the variables, call init() to initialize the data processing routine itself.
Then call add(waveform) to process a single waveform.
Call finish() to finish the data processing.
*/
class BifurcationMap
{
public:
	~BifurcationMap();
	BifurcationMap();

	double rotation[2];
	double costable[2],sintable[2];
	double* rotatedWaveform;
	double *means,*trends,*averages,*probabilities,*crossProbabilities;
	unsigned int nPoints,nSegments,activeChannels;
	int index,nLoops;


	void setRotation(double r1,double r2);
	void init();
	void add(double *matrix);
	void finish();
};


class Averager
{
public:
	Averager();
	~Averager();

	int n, nf, channel, point, indexComponents, indexAverages, indexMatrix;


	double *averages;
	double *components;
	double *frequencies;
	double *Icorrection, *Qcorrection, *phicorrection;
	//	unsigned int params[10];
	unsigned int nPoints, nSegments, activeChannels, index, nFrequencies;
	double sampleInterval,c,s,cp,sp,ic,qc;
	void finish();
	void add(double *matrix);
	void init();

};


class MultiplexedBifurcationMap
{
public:
	~MultiplexedBifurcationMap();
	MultiplexedBifurcationMap();

	double *rotations;
	double costable[2],sintable[2];
	double *rotatedWaveform;
	double *means,*trends,*averages,*probabilities,*crossProbabilities;
	unsigned int nPoints,nSegments,activeChannels;
	int index,nLoops;

	int dimensionF;

	vector <double> fTable;
	vector <double> Ioffset;
	vector <double> Qoffset;
	vector <double> CosTable;
	vector <double> SinTable;


	void setRotation(double r,double Io, double Qo, double f);
	void initF(double f);
	void add(double *frequencies, double *trends, int numberOfFrequencies, int numberOfsegments,double *results);
	void finish();
	void convertToProbabilities(int nbQB, int nbSegments, double *r, double *proba);
};
