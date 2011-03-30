/* File : numerical.i */
%module numerical

%{
#include "numerical.h"
%}

/*Yippie!!! This typemap converts any incoming variable (that is supposed to be a long integer pointing to some memory location) to a double pointer... */
%typemap (in) float*
{
	$1 = (float *)PyInt_AsLong($input);
}

/*Yippie!!! This typemap converts any incoming variable (that is supposed to be a long integer pointing to some memory location) to a double pointer... */
%typemap (in) unsigned short*
{
	$1 = (unsigned short *)PyInt_AsLong($input);
}


/*Yippie!!! This typemap converts any incoming variable (that is supposed to be a long integer pointing to some memory location) to a double pointer... */
%typemap (in) double*
{
	$1 = (double *)PyInt_AsLong($input);
}

/*Yippie!!! This typemap converts any incoming variable (that is supposed to be a long integer pointing to some memory location) to a double pointer... */
%typemap (in) unsigned char*
{
	$1 = (unsigned char *)PyInt_AsLong($input);
}

/* Let's just grab the original header file here */
%include "numerical.h"

