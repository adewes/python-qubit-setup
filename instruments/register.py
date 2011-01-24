import sys
import getopt
import struct
import shelve
import os.path

from pyview.lib.classes import *
import yaml

class Instr(Instrument):
  
  """
  A persistent paramter register.
  """
  
  def parameters(self):
    """
    Return the register as a dictionary.
    """
    return dict(self._register)
  
  def __getitem__(self,key):
    """
    Get a variable from the register.
    """
    if not hasattr(self,"_register"):
      self._register = dict()
    if key in self._register:
      return self._register[key]
    raise IndexError("No such key: %s" % key)
    
  def hasKey(self,key):
    if key in self._register:
      return True
    return False
  
  def __setitem__(self,key,value):
    """
    Store a variable in the register.
    """
    self._register[key] = value
    self._register.sync()
    
  def __len__(self):
    return len(self._register)
    
  def load(self,params):
    """
    Load the register from a dictionary.
    """
    self._register.clear()
    for key in params:
      self._register[key] = params[key]
  
  def loadFromFile(self,filename):
    """
    Loads the register from a file.
    """
    path = os.path.dirname(__file__)+"/"+filename
    if os.path.exists(path) and os.path.isfile(path):
      self.load(yaml.load(open(path, 'r')))
      
  def saveToFile(self,filename):
    """
    Save the register to a file.
    """
    path = os.path.dirname(__file__)+"/"+filename
    stream = open(path,"w")
    yaml.dump(self.parameters(),stream)
      
  def __delitem__(self,key):
    """
    Delete an item from the register.
    """
    if key in self._register:
      del self._register[key]
  
  def initialize(self,name = "Parameter register",filename = "register.par"):
    """
    Initialize the register.
    """
    path = os.path.dirname(__file__)+"/"+filename
    print "Opening register with filename %s" % path
    self._register = shelve.open(path)
  
  def __del__(self):
    self._register.close()