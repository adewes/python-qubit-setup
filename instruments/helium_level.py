import sys
import getopt

from pyview.lib.classes import *

class Instr(Instrument):

      def heliumLevel(self):
        try:
        	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        	sock.settimeout(0.5)
        	sock.connect((self.host, self.port))
        	return float(sock.recv(1024))
        except:
          return None
          
      def parameters(self):
        params = dict()
        params['heliumLevel'] = self.heliumLevel()
        return params

      def initialize(self,address = "132.166.16.116", port = 449):
        try:
          self._name = "Helium level meter"
          self.host = address
          self.port = port
        except:
          self.statusStr("An error has occured. Cannot initialize Helium level meter.")        
