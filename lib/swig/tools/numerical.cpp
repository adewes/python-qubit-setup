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
