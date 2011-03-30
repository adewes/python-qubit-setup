// numerical.h

#pragma once

int awg_pack_real_data(int len,float *values,unsigned char *markers,unsigned char *output);
int awg_pack_int_data(int len,unsigned short *values,unsigned char *markers,unsigned char *output);