from numerical import *

from numpy import *

import struct
import ctypes
import time

data = zeros(1000000,dtype = float32)+1
markers = zeros(1000000,dtype = int32)

buf = ctypes.create_string_buffer(len(data)*5)

start = time.time()

awg_pack_real_data(len(data),data.ctypes.data,markers.ctypes.data,ctypes.addressof(buf))

print time.time()-start," seconds elapsed."

start = time.time()

output = ''
for i in range(0,len(data)):
  marker = int(markers[i])
  output+=struct.pack("f",float(data[i]))
  output+=struct.pack("B",(marker & 3) << 6)

print time.time()-start," seconds elapsed."

if output != buf.raw:
  print "Error!"
else:
  print "It works!"