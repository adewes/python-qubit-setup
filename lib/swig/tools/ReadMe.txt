Acqiris Data Processing Library, v0.1, Dec. 2009

Author: Andreas Dewes, andreas.dewes@gmail.com

---Introduction:
A C++ library that interfaces with Python via SWIG (the Simplified Wrapped and Interface generator) and handles the data processing of the Acqiris card.
The main purpose of this library is to speed up the processing of numerical data during the acquisition process which would be much slower if done purely in Python.

---Compiling the library:
To copmpile this library, you need to have a copy of Visual C++, SWIG and Python installed on your system. You can get these here:

Visual C++: Google for "Visual C++ Express" (as of 2010, the Express version can be downloaded for free)
SWIG:   http://www.swig.org/
Python: http://www.python.org/

Before building the library make sure that you have added the following directories to your Visual C++ configuration (Tools -> Options -> Projects and Solutions -> VC++ Directories):
	Include files:
		- [path to your python installation]\include    e.g. c:\python26\include
	Library files:
		- [path to your python installation]\lib        e.g. c:\python26\lib

Also make sure that the directory containing the file "swig.exe" is included in your PATH environment variable (check via "Control panel -> System -> Advanced -> Environment Variables").

If everything is set up correctly the build process should generate the files acqiris.py and _acqiris.pyd which can be used from Python via "import lib.swig.acqiris.acqiris". Have fun!