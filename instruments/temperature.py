import sys
import getopt

from pyview.lib.classes import *

class Instr(Instrument):

      def temperature(self):
        try:
        	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        	sock.settimeout(0.5)
        	sock.connect((self.host, self.port))
        	return float(sock.recv(1024))
        except:
          return None
          
      def parameters(self):
        params = dict()
        params['temperature'] = self.temperature()
        return params

      def initialize(self,address = "132.166.16.116", port = 444):
        try:
          self._name = "Temperature sensor"
          if DEBUG:
            print "Initializing temperature sensor"
          self.host = address
          self.port = port
        except:
          self.statusStr("An error has occured. Cannot initialize FSP.")        
