Python Qubit Data Acquisition Setup
===================================

Here you find all Python data acquisition and processing script that I've using for my PhD thesis in Experimental Quantum Computing at the CEA Saclay.

##Summary

The repository is organized in the following way:

* *config*: Contains configuration scripts and settings for the setup.
* *doc*: Contains the (still incomplete) documentation of the instrument classes and methods
* *frontpanels*: Contains the graphical frontpanels of all instruments used in the setup, which were realized using PyQT.
* *instruments*: Contains the instrument classes for all real and virtual instruments used in the measurement setup.
* *lib*: Contains several libraries used for acquiring and processing data and interfacing Python and C++ libraries.
* *macros*: (Obsolete) measurement macros
* *scripts*: Measurement and data processing scripts.
* *test*: (Largeley incomplete) test scripts for the instrument classes.

##Requirements

Besides *numpy*, *scipy*, *PyQt* and *PyYaml*, the scripts here make use of the classes defined in the *pyview* repository (http://github.com/adewes/pyview), which contains all generic, reusable classes and functions that are not specific to the qubit setup.

##Further Reading

For more information on the data acquisition software and my PhD work, check out my PhD thesis (http://www.andreas-dewes.de/en/publications) and have a look at the pyview source code (http://github.com/adewes/pyview). 
