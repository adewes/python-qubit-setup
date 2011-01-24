import sys
import getopt
import re
import struct
import time
import math

from pyview.lib.classes import VisaInstrument

class Trace:
      pass

class Instr(VisaInstrument):

      """
      The Yokogawa instrument class
      """

      def voltage(self):
        """
        Returns the voltage
        """
        string = self.ask("od;")
        string = re.sub(r'^(NDCV|EDCV)',r'',string)
        self.notify("voltage",float(string))
        return float(string)
      
      def setVoltage(self,value,slewRate = None):
        """
        Sets the voltage to a given value with a given slew rate
        """
        if slewRate == None:
          slewRate = self.slewRate        
        if math.fabs(value) > 50.0: 
          raise "Error! Voltage is too high!"
        if slewRate == None:
          self.write("S%g;E" % value)
        else:
          v = self.voltage()
          while math.fabs(v - value)>0.001:
            time.sleep(0.1)
            if v > value:
              if v-value > slewRate*0.1:
                v-=slewRate*0.1
              else:
                v=value
              self.write("S%g;E" % v)
              v = self.voltage()
            elif v < value:
              if value-v > slewRate*0.1:
                v+=slewRate*0.1
              else:
                v = value
              self.write("S%g;E" % v)
              v = self.voltage()
                
        return self.voltage()
        
      def output(self):
        """
        Returns the output status of the device (ON/OFF)
        """
        match = re.search("STS1=(\d+)",self.ask("OC;"))
        status = int(match.groups(0)[0])
        isOn = status & 16
        if isOn:
          isOn = True
        else:
          isOn = False
        self.notify("output",isOn)
        return isOn
        
      def turnOn(self):
        """
        Turns the device on.
        """
        self.write("E;O1;E;")
        return self.output()
        
      def turnOff(self):
        """
        Turns the device off.
        """
        self.write("E;O0;E;")
        return self.output()
        
      def saveState(self,name):
        """
        Saves the state of the device to a dictionary.
        """
        return self.parameters()
        
      def restoreState(self,state):
        """
        Restores the state of the device from a dictionary.
        """
        self.setVoltage(state['voltage'])
        if state['output'] == True:
          self.turnOn()
        else:
          self.turnOff()
        
      def parameters(self):
        """
        Returns the parameters of the device.
        """
        params = dict()
        params['voltage'] = self.voltage()
        params['output'] = self.output()
        return params

      def initialize(self, name = "Yoko", visaAddress = "GPIB0::9",slewRate = None):
        """
        Initializes the device.
        """
        try:
          self.slewRate = slewRate
          self._name = name
          self._visaAddress = visaAddress
        except:
          self.statusStr("An error has occured. Cannot initialize Yoko(%s)." % visaAddress)        
