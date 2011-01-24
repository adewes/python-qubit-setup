// Acqiris Data Processing.h

#pragma once

using namespace System;

#define DllExport extern "C" __declspec( dllexport ) 

class Tester
{
public:
	Tester();
	~Tester();
	void sayHello();
};

DllExport void *createClass();
DllExport void add(int channels,int len,double *source,double *destination);
DllExport void rotate(double angle,int len,double *source,double *destination);
DllExport void means(int channels,int len,double *data,double *means,int *dataStrides);