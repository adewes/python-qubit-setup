import sys
import getopt
import re
import struct
import math
import random

from pyview.lib.classes import *
from pyview.lib.datacube import *


class Instr(Instrument):
  
  def measureSomething(self,params):
    result = Datacube("Measurement results")
    for i in range(0,100):
      result.set(x = i , y = math.sin(math.pi*i*0.1)+random.random())
      result.commit()
    return result
  
  def initialize(self):
    """
    Put initialization code here...
    """
    print "Hello, world!"
