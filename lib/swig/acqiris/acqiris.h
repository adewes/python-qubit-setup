// acqiris.h

#pragma once

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