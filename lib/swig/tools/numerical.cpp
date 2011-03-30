// This is the main DLL file.

#include "stdafx.h"
#include <iostream>

using namespace std;

#include <cmath>
#include "numerical.h"

int awg_pack_real_data(int len,float *values,unsigned char *markers,unsigned char *output)
{
	for(int i=0;i<len;i++)
	{
		memcpy(output+i*5,(void *)(values+i),4);
		memcpy(output+i*5+4,(void *)(markers+i),1);
	}
	return len;
}

int awg_pack_int_data(int len,unsigned short *values,unsigned char *markers,unsigned char *output)
{
	for(int i=0;i<len;i++)
	{
		output[i*2]   = (char)values[i] & 0xFF;
		output[i*2+1] = (char)(values[i] >> 8) & (0xFF >> 2) ;
		output[i*2+1] += (char)(markers[i] << 6);
	}
	return len;
}
