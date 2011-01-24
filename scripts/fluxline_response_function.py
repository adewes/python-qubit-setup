##Initialize the Acqiris card (make sure to launch the server on the Acqiris machine before...)
acqiris2 = instrumentManager.initInstrument("rip://192.168.0.19:8000/acqiris2","acqiris")
import math
import numpy.linalg
import numpy.fft

def filter(x,cutoff = 0.5):
	return exp(-pow(fabs(x)/cutoff,2.0) )

##Generate the target waveform:

samplingInterval = 0.5e-9

#Waveform length
waveformLength = 2048*2

waveform = zeros(waveformLength)
waveformDiff = zeros(waveformLength)
afgWaveform = zeros(waveformLength*3.0)

diff = True

#Set to False if you want to measure the response of the AFG alone...
measureWholeLine = True

waveform[waveformLength/2:] = (2<<13)-1

waveformDiff[:] = waveform

if diff:
	for i in range(0,len(waveform)-1):
		waveformDiff[i] = waveform[i]-waveform[i+1]
		waveformDiff[-1] = 0

afgWaveform[:waveformLength] = waveform
afgWaveform[waveformLength:] = waveform[-1]
afgWaveform[waveformLength+100:] = 0

waveformDiff = (waveformDiff - mean(waveformDiff))
waveformDiff /= numpy.linalg.norm(waveformDiff)

waveformFFT = numpy.fft.rfft(waveformDiff)
waveformFFT2 = numpy.fft.rfft(list(waveformDiff)*4)

figure("waveform")
cla()
plot(absolute(waveformFFT))

##Transfer the waveform the the AFG and configure the Acqiris card:

afg1.writeWaveform("USER1",afgWaveform)
afg1.setWaveform("USER1")
afg1.write("SOURCE1:BURST:STATE OFF")
afg1.write("TRIG:SEQ:SOURCE TIM")
afg1.write("TRIG:SEQ:TIM 0.01 ms")
afg2.write("SOURCE1:BURST:TDELAY 0 ns")
afg1.setPeriod(len(afgWaveform)*samplingInterval*1e9)

fullScales = acqiris2.parameters()["fullScales"]
if measureWholeLine:
	fullScales[0] = 0.025
else:
	fullScales[0] = 1.0

bandwidths = acqiris2.parameters()["bandwidths"]
bandwidths[0] = 0

acqiris2.ConfigureV2(**{'bandwidths':bandwidths, 'fullScales':fullScales,'numberOfPoints':waveformLength,'sampleInterval':samplingInterval,'delayTime':0,'numberOfSegments':1,'triggerSlope':2})

##Measure the returning waveform:

afg1.turnOff()
averaging = 32000*4
acqiris2.bifurcationMap(ntimes = averaging)
signalOff = acqiris2.averages()[0,:]
afg1.turnOn()
acqiris2.bifurcationMap(ntimes = averaging)
signalOn = acqiris2.averages()[0,:]

signal = signalOn-signalOff

if diff:
	for i in range(0,len(signal)-1):
		signal[i]-=signal[i+1]
	signal[-1] = 0
signal = (signal - mean(signal))
signal /= numpy.linalg.norm(signal)
figure("signal")
clf()
plot(list(signal)*3)
plot(signalOff)

signalFFT = numpy.fft.rfft(signal)

freqs = linspace(0,1.0/samplingInterval/1e9,len(signalFFT))

signalReverse = numpy.fft.irfft(signalFFT,len(signal))

plot(signalReverse)

##Calculate the response function:
responseFunction = zeros((len(signalFFT)),dtype = complex128)
modifiedFFT = zeros(len(waveformFFT),complex128)
for i in range(0,len(signalFFT)):
	responseFunction[i] = signalFFT[i] /waveformFFT[i]
responseFunction/=absolute(responseFunction[1])

for i in range(1,len(responseFunction)):
	modifiedFFT[i] = waveformFFT[i]/responseFunction[i]*exp(-pow(fabs(i)/320.0,2.0) )

compensatedWaveform = numpy.fft.irfft(modifiedFFT,len(waveform))
##Or load it from a datcube instead...
data = Datacube()
data.loadtxt("response function - whole line-7")
responseFunction = data.column("response")
##Load the acqiris response function
import scipy.interpolate
acqirisData = Datacube()
acqirisData.loadtxt("acqiris_response_function-1")
acqirisData.commit()
responseFunctionAcqiris = zeros(len(signalFFT))
response = acqirisData.column("response")
responseSmooth = zeros(len(response))
s = 5
for i in range(0,len(response)):
	cnt = 0
	integral = 0
	for j in range(-s,s+1):
		k = i+j
		if k > 0 and k < len(response):
			integral += response[k]
			cnt+=1
	integral/=float(cnt)
	responseSmooth[i] = integral	

f = scipy.interpolate.interp1d(acqirisData.column("f"),responseSmooth)
for i in range(0,len(signalFFT)):
	responseFunctionAcqiris[i] = f(freqs[i])	
responseFunctionAcqiris/= responseFunctionAcqiris[0]
##
if measureWholeLine:
	data = Datacube()
	data.loadtxt("response function - afg alone-2")
	responseFunctionAfg = data.column("response")
responseFunctionInputSample = zeros(len(responseFunction),dtype = complex128)
responseFunctionXSample = zeros(len(responseFunction),dtype = complex128)
offset = 0
phase = zeros(len(responseFunction))
for i in range(0,len(responseFunction)):
	value = responseFunction[i]/responseFunctionAfg[i]/responseFunctionAcqiris[i]
	alpha =angle(value)
	if i > 0:
		if fabs(alpha - lastAlpha) > math.pi:
			if fabs(alpha - lastAlpha-2.0*math.pi) < math.pi:
				offset-=2.0*math.pi
			else:
				offset+=2.0*math.pi
	phase[i] = alpha+offset
	responseFunctionInputSample[i] = sqrt(absolute(value))*exp(1j*phase[i]/2.0)
	responseFunctionXSample[i] = responseFunctionInputSample[i]*responseFunctionAfg[i]
	lastAlpha = alpha
if measureWholeLine:
	name = "response function - whole line"
else:
	name = "response function - afg alone"
data = Datacube(name,dtype = complex128)
data.createColumn("frequency",freqs)
data.createColumn("response_full",responseFunction)
data.createColumn("response_dac",responseFunctionAfg)
data.createColumn("response_input_sample",responseFunctionInputSample)
data.createColumn("response_waveform_sample",responseFunctionXSample)
data.createColumn("response_adc",responseFunctionAcqiris)
data.savetxt()
##
rcParams['font.size'] = 12
figure("response function")
subplot(211)
cla()
if measureWholeLine:
	titlestr = 'whole line'
else:
	titlestr = 'DAC only'
from pylab import title
title("Response function, %s" % titlestr)

if measureWholeLine:
	plot(freqs,numpy.absolute((responseFunction)))
	plot(freqs,numpy.absolute(responseFunctionAfg))
	plot(freqs,numpy.absolute(responseFunctionInputSample))
	plot(freqs,numpy.absolute(responseFunctionXSample))
	plot(freqs,numpy.absolute((responseFunctionAcqiris)))
	legend((r"$\tilde{r}_{full}(\omega)$",r"$\tilde{r}_{DAC}(\omega)$",r"$\tilde{r}_{input \to sample}(	\omega)$",r"$\tilde{r}_{x \to sample}(\omega)$",r"$\tilde{r}_{ADC}(\omega)$"))
else:
	plot(freqs,numpy.absolute((responseFunction)))
	legend([r"$\tilde{r}_{DAC}(\omega)$"])
ylim(0,1.1)
subplot(212)
cla()
if measureWholeLine:
	plot(freqs,numpy.angle((responseFunction)))
	plot(freqs,numpy.angle(responseFunctionAfg))
	plot(freqs,numpy.angle(responseFunctionInputSample))
	plot(freqs,numpy.angle(responseFunctionXSample))
	legend((r"$\tilde{r}_{full}(\omega)$",r"$\tilde{r}_{DAC}(\omega)$",r"$\tilde{r}_{input \to sample}	(\omega)$",r"$\tilde{r}_{x \to sample}(\omega)$"))
else:
	plot(freqs,numpy.angle((responseFunction)))
	legend([r"$\tilde{r}_{DAC}(\omega)$"])
ylabel("fourier coefficients")
xlabel("frequency [GHz]")

figure("compensation")
cla()

plot(linspace(0,len(signal)*0.5,len(compensatedWaveform)),compensatedWaveform)
plot(linspace(0,len(signal)*0.5,len(signal)),signal)
plot(linspace(0,len(signal)*0.5,len(waveformDiff)),waveformDiff)

xlabel("time [ns]")
ylabel("voltage")

##TESTING


##Generate a waveform and calculate the correction:

testWaveform = zeros(waveformLength)
testWaveform[waveformLength/2:waveformLength/2+100] = 1.0
testWaveformFFT = numpy.fft.rfft(testWaveform)
testWaveformSampleFFT = numpy.fft.rfft(testWaveform)
cutoff = 0

for i in range(0,len(testWaveformFFT)):
	if i < len(responseFunction):
		testWaveformFFT[i]/=responseFunctionXSample[i]/filter(freqs[i],cutoff = 0.40)
		testWaveformSampleFFT[i] = testWaveformFFT[i]*responseFunctionXSample[i]
	else:
		testWaveformFFT[i] = 0

correctedWaveform = numpy.fft.irfft(testWaveformFFT)
correctedWaveformSample = numpy.fft.irfft(testWaveformSampleFFT)
testWaveform = (testWaveform-min(testWaveform))/(max(testWaveform)-min(testWaveform))

figure("correction test")
clf()
plot(testWaveform)
plot(correctedWaveform)
plot(correctedWaveformSample)

##Write the corrected waveform to the AFG and measure the returning signal:
target = correctedWaveform
afg1.writeWaveform("USER1",(target-min(target))/(max(target)-min(target))*(2<<13)-1)
afg1.setWaveform("USER1")
afg1.setPeriod(len(correctedWaveform)/2.0)
afg1.turnOff()
acqiris2.bifurcationMap(ntimes = 5000)
noise = acqiris2.averages()[0]
afg1.turnOn()
acqiris2.bifurcationMap(ntimes = 5000)
output = acqiris2.averages()[0]-noise
##Plot the results:

figure("correction test")
clf()
output = (output-min(output))/(max(output)-min(output)) 
times = linspace(0,len(output)*0.5,len(output))
plot(times,output)
plot(times,(target-min(target))/(max(target)-min(target)))
plot(times,testWaveform)
plot(times,noise)
xlim(0,times[-1])
ylim(-0.1,1.1)
xlabel('time [ns]')
ylabel('voltage [arb.]')
title("response function compensation")
##
data = Datacube("Acqiris - frequency response")
dataManager.addDatacube(data)
for i in arange(0.0101,3.0001,0.01):
	qubit2_mwg.setFrequency(i)
	acqiris2.bifurcationMap(ntimes = 1)
	signal = acqiris2.averages()[0]
#	bin = int(qubit2_mwg.frequency()*(0.5*float(len(signal))))
#	fft = numpy.fft.rfft(signal)
	signalCube = Datacube("Signal at %g GHz" % i)
	data.addChild(signalCube)
	signalCube.createColumn("signal",signal)
	signalCube.createColumn("time",linspace(0,len(signal)*0.5,len(signal)))
	data.set(f = i, response = max(signal)-min(signal))
	data.commit()
