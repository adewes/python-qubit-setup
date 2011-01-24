// Il s'agit du fichier DLL principal.

#include "stdafx.h"
#include <cmath>
#include <iostream>
using namespace std;

#include "data_processing.h"

Tester::Tester()
{
	cout << "Creating new tester class...\n";
}

Tester::~Tester()
{

}

void Tester::sayHello()
{
	cout << "Hello, world!\n";
}

void *createClass()
{
	Tester *MyTester = new Tester();
	return (void *)MyTester;
}

//Adds to multi-channel signals together
void add(int channels,int len,double *source,double *destination)
{
	for(int k = 0;k< channels;k++)
		for (int i = 0;i <len ; i++)
		{
			destination[k*len+i]+=source[k*len+i];
		}
}

void means(int channels,int len,double *data,double *means,int *dataStrides)
{
	int ix = dataStrides[0]/8;
	int iy = dataStrides[1]/8;
	for(int k = 0 ;k<channels;k++)
	{
		means[k] = 0;
		for(int i = 0;i<len;i++)
			means[k]+=data[k*ix+i*iy];
		means[k]/=(double)len;
	}
}

//Rotates the waveform source with an angle of "angle" and stores it in destination.
//Assumes that the first channel is stored in source[0:len] and the second in source[len:2*len], same for destination
void rotate(double angle,int len,double *source,double *destination)
{
	double *s1 = source;
	double *s2 = source +len;
	double *d1 = destination;
	double *d2 = destination +len;
	double cosa = cos(angle);
	double sina = sin(angle);
	for (int i = 0;i <len ; i++)
	{
		d1[i]=s1[i]*cosa+s2[i]*sina;
		d2[i]=-s1[i]*sina+s2[i]*cosa;
	}
		
}