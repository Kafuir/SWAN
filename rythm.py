import pyedflib
import numpy as np
import statistics
import matplotlib.pyplot as plt

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y

def extract_stuff(signal, sample_rate):
    #print(signal)
    result = []
    for x in range(1,4):
        signal_filt = butter_bandpass_filter(signal[:,x], 0.5, 50, sample_rate)
        #print (len(signal[:,x]))
        freq_spectrum = np.fft.fft(signal_filt)
        freqs = np.fft.fftfreq(len(signal_filt), d=1/sample_rate)
        print (freq_spectrum)
        result.append(abs(freqs[np.argmax(np.abs(freq_spectrum[1:]))]):.2f) #freq
        result.append(round(statistics.stdev(signal_filt), 3)) #stdev
    return result



f = pyedflib.EdfReader("res_short.edf")

n = f.signals_in_file
freq = int(f.getSampleFrequency(0))
print(freq)
f_len = np.size(f.readSignal(0),0) # Число точек в каждом канале
imported_data = np.zeros((f_len,4))
# 1 столбец время в секундах
imported_data[:,0] = np.arange(0,f_len/freq,1/freq)
# 2 столбец FrL = канал 1
imported_data[:,1] = np.array(f.readSignal(0))
# 3 столбец FrR = канал 2
imported_data[:,2] = np.array(f.readSignal(1))
# 4 столбец OcR = канал 3
imported_data[:,3] = np.array(f.readSignal(2))
f.close()

inp = '5'
while inp != '':
    inp = int(input('Time1 '))
    iny = int(input('Time2 '))
    extract_stuff(imported_data[inp*freq:iny*freq], freq)


# Close the file
