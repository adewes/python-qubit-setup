from numpy.fft import *
from numpy import *
from instruments.qubit import gaussianFilter
from config.startup import *

figure("calibration data")
cla()
plot(calibration1.column("t"),calibration1.column("flux"),'rd')
from scipy.interpolate import *
rep = interp1d(calibration1.column("t"),calibration1.column("flux"))
interpolatedX = arange(200,225,0.5)
interpolatedFlux = rep(interpolatedX)
plot(interpolatedX,interpolatedFlux,'bo')
##Deconvolution of our signal
testSignal = zeros(1000)
testSignal[500:] = 1.0
convolutor = exp(-power(linspace(-100,100,len(testSignal)),2.0))
convolutor/=sum(convolutor)

convolvedSignal = irfft(rfft(testSignal)*rfft(convolutor))

convolutorFFT = rfft(convolutor)
signalFFT = rfft(testSignal)
signalFFT[:100]/=convolutorFFT[:100]/gaussianFilter(linspace(0,2.0,len(convolutorFFT[:100])),cutoff = 0.001)
deconvolvedSignal = irfft(signalFFT)
figure("deconvolution")
cla()
plot(abs(convolutorFFT))
figure("calibration data")
cla()
#plot(convolutor)
#plot(testSignal)
#plot(convolvedSignal)
plot(deconvolvedSignal)
##Loading of the derivative data
derivative = loadtxt("FourierDerivative-measured with previous correction.txt")
print derivative
figure("fft data")
cla()
times = derivative[:,0]
fluxes = derivative[:,1]  
testWaveform = zeros(len(fluxes))
testWaveform[40] = 1.0

testWaveformFFT = rfft(testWaveform)
fluxFFT = rfft(fluxes)

responseFunction = fluxFFT/testWaveformFFT

responseFunction/=absolute(responseFunction[0])

figure("fft")
cla()

freqs = linspace(0,2.0,len(fluxFFT))

plot(freqs,absolute(testWaveformFFT))
plot(freqs,absolute(fluxFFT))
plot(freqs,absolute(responseFunction))

figure("angles")
cla()
plot(freqs,angle(testWaveformFFT))
plot(freqs,angle(fluxFFT))
plot(freqs,angle(responseFunction))

##Calculation of the corrected waveform

newTest = zeros(len(fluxes))
newTest[len(newTest)/2:] = 1.0

filter = gaussianFilter(freqs,cutoff = 0.20)

correctedWaveformFFT = rfft(newTest)/responseFunction*filter

correctedWaveform = irfft(correctedWaveformFFT)

correctedWaveformOutput = irfft(correctedWaveformFFT*responseFunction)

figure("correction")
cla()
plot(correctedWaveformOutput)
plot(correctedWaveform)
plot(flux)

##

fluxFFT = rfft(interpolatedFlux) 
filter2 = gaussianFilter(linspace(0,2.0,len(fluxFFT)),cutoff = 0.51)
figure("fft")
cla()
smoothedFlux = irfft(fluxFFT)
diffs = zeros(len(smoothedFlux)-1)
waveform = zeros(len(smoothedFlux))
waveform[20:] =50
diffsWaveform = zeros(len(waveform)-1)
for i in range(1,len(smoothedFlux)):
	diffs[i-1] = smoothedFlux[i]-smoothedFlux[i-1]
	diffsWaveform[i-1] = waveform[i]-waveform[i-1]
reload(sys.modules["macros.qubit_functions"])
from macros.qubit_functions import *
ps = [0.05,213,5,0]
result = fitGaussian(interpolatedX[:-1],diffs,ps = ps)
print result
plot(interpolatedX[:-1],diffs,interpolatedX,interpolatedFlux)
plot(interpolatedX,result[1](result[0],interpolatedX))
##
figure("response function")
responseFunction = rfft(result[1](result[0],linspace(interpolatedX[0],interpolatedX[-1],len(waveform))))
cla()
freqs = linspace(0,2,len(responseFunction))
plot(freqs,real(responseFunction))
plot(freqs,imag(responseFunction))
plot(freqs,abs(responseFunction))
plot(freqs,filter)
waveformFFT = rfft(waveform)
correctedWaveform = irfft(waveformFFT/responseFunction* gaussianFilter(linspace(0,2.0,len(waveformFFT)),cutoff = 0.22))
figure("corrected waveform")
cla()
plot(correctedWaveform)
plot(waveform)