import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf  # эта библиотека нужна для обучения и проверки сети
from tensorflow.keras import datasets, layers, models
import pyedflib
#import mne
import os
import re
import pandas as pd
from pandas import DataFrame
from read_input_data import ANN_examples_3channels_markup # Это нужно для корректного считывания файлов по 3-ем каналам
from read_input_data import ANN_examples_2channels_markup # Это нужно для корректного считывания файлов по 3-ем каналам
import statistics
from scipy.signal import butter, lfilter

#--------------
# Some funny little buggers by L.
##------------
import math

def time_to_secs_local(time):
    if ',' in time:
        time = time[:-1]
    parts = time.split(':')
    return (int(parts[0])*3600 + int(parts[1])*60 + int(parts[2]))

def fancy(time, length = 2):
    time = str(time)
    nuls = '0'*(length-len(time))
    return f'{nuls}{time}'

def get_number(image_name):
    return int(re.search(r'\d+.png', image_name)[0][:-4])

def cool_name(image_name):
    m = int(image_name)#get_number(image_name)
    return f'{fancy(m//3600)}:{fancy((m%3600)//60)}:{fancy(m%3600%60)}'

def logistic(x):
    e = 1/(1+math.exp(-x))
    if e > 0.5:
        return e#round(x, 2)
    else:
        return e#round(x, 2)

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
        #print (freq_spectrum)
        result.append(round(statistics.stdev(signal_filt), 3)) #stdev
        result.append(round(abs(freqs[np.argmax(np.abs(freq_spectrum[1:]))]), 2)) #freq
    return result

def magic2(a):
    return logistic(a[0]*(-0.1037)+a[1]*3.591+a[2]*(-0.842)+a[3]*6.288+a[4]*(-1.242)+a[5]*(-2.783)-2.67012)

################
# Параметры :::
################
def find_sleep(edf_file, filt = True):
    input_size=6 # Количество входных нейронов = число каналов * 2

    dt_average_s=1         # сдвиг окна усреднения в секундах
    window_average_s=10    # размер окна усреднения в секундах
    extra_metrics = True
    if filt:
        min_sleep_len = 16#минимальная продолжительность сна (в секундах)
        len_thresh = 80#нижний порог интервала между двумя событиями (в секундах)
    else:
        min_sleep_len = 0
        len_thresh = 0


    # Обработка edf-файла

    print("Extracting sleep data: ", edf_file)
    f = pyedflib.EdfReader(edf_file)
    signal_labels = f.getSignalLabels()
    #print(signal_labels)
    n = f.signals_in_file
    T0=f.getStartdatetime()
    sT0 = time_to_secs_local(re.search(r'\d+:\d{2}:\d{2}', str(T0))[0])
    sT0 = 0 #COMMENT ME TO ENABLE ASTRONOMY TIME
    freq = int(f.getSampleFrequency(0))
    #print(sT0, freq)
    #print("Frequency = ",freq," Hz")
    f_len = np.size(f.readSignal(0),0) # Число точек в каждом канале
    #print(str(f_len) + " points")
    imported_data = np.zeros((f_len,4))
    use_corrected_data = False #True = будет использован сглаженный сигнал, где значения >0.2 и <-0.2 заменены на 0,2 и -0,2 соответсвенно
                            #а так же band-path фильтрация в диапазоне 0,5-100Hz


    # 1 столбец время в секундах
    imported_data[:,0] = np.arange(0,f_len/freq,1/freq)
    # 2 столбец FrL = канал 1
    imported_data[:,1] = np.array(f.readSignal(0))
    # 3 столбец FrR = канал 2
    imported_data[:,2] = np.array(f.readSignal(1))
    # 4 столбец OcR = канал 3
    imported_data[:,3] = np.array(f.readSignal(2))
    # Файл в разметкой Насти и Максима. Если его нет, задать = None
    #file_markup = "Result_time_AW_BS.dat"
    file_markup = None


    #if use_corrected_data:
    #    info = mne.create_info(signal_labels, freq, ch_types='eeg')
    #    corrected_data = np.where(imported_data[:,1:]>0.2, 0.2,imported_data[:,1:])
    #    corrected_data = np.where(corrected_data<-0.2, -0.2,corrected_data)
    #    corrected_data = (mne.io.RawArray(corrected_data.T, info, verbose = False).filter(0.5,100, phase='zero-double', verbose = False)).get_data(picks='eeg')

    #    imported_data = np.concatenate((imported_data[:,0][None].T, corrected_data.T),1)





    # Импорт файлов и вычисление среднего и стандартного отклонения по 3-ем каналам:
    Time_average_test, x_test, y_test = ANN_examples_3channels_markup(imported_data,file_markup,-1,-1,dt_average_s,window_average_s,input_size)


    ANN_predictions_test = np.array([magic2(tur) for tur in x_test])

    # Оформление предсказания в бинарном виде 1-спит, 0-бодрствует
    ANN_predictions_test_bool = np.zeros(np.shape(ANN_predictions_test))
    ANN_predictions_test_bool[ANN_predictions_test>=0.5] = 1


    # Выводим в промежуточный dat-файл в формате 1 - время, 2 - ответ ИНС в вещественном виде, 3 - ответ ИНС в бинарном виде (сон=1, бодрствование=0)
    np.savetxt("ann_output.dat",np.array([Time_average_test[:,0], ANN_predictions_test_bool]).T,fmt='%.5f')
    #, ANN_predictions_test[:,0]


    total = np.concatenate((Time_average_test[:,0][None].T,ANN_predictions_test_bool[None].T) ,1)
    points = []
    intervals_s = []
    intervals_e = []
    SD1 = []
    rt1 = []
    SD2 = []
    rt2 = []
    SD3 = []
    rt3 = []

    for i in range(1, total.shape[0]):
        if (total[i,1] != total[i-1,1] and total[i,1]==1) or \
                total[i,1] != total[i-1,1] and total[i,1]==0:
            points.append(total[i,0])

    to_delete = []
    for i in range(1, len(points)-2,2):
        if points[i+1] - points[i]<len_thresh:
            to_delete.append(points[i])
            to_delete.append(points[i+1])

    for i in to_delete:
        points.remove(i)

    events = np.ones(shape=[1,3])

    for i in range(0, len(points)-1, 2):
        if points[i+1] - points[i]>min_sleep_len:
            event_start = np.array([[points[i]*freq, 0, 0]])
            event_end = np.array([[points[i+1]*freq, 0, 1]])
            event = np.concatenate((event_start, event_end),0)
            events = np.concatenate((events, event),0)
            intervals_s.append(cool_name(points[i]+sT0))
            intervals_e.append(cool_name(points[i+1]+sT0))
            #print(freq, points[i])
            [S1, r1, S2, r2, S3, r3] = extract_stuff(imported_data[int(points[i]*freq):int(points[i+1]*freq)], freq)
            
            SD1.append(S1)
            rt1.append(r1)
            SD2.append(S2)
            rt2.append(r2)
            SD3.append(S3)
            rt3.append(r3)

    #with open('results/' + edf_file[4:] + '_intervals.txt', 'w') as file:
    #    for i in intervals:
    #        file.write(i)
    #        file.write('\n')
    #    file.close()
    #print(intervals)
    df = DataFrame({'Start': intervals_s, 'End': intervals_e, 'Ch1 SD': SD1, 'Ch1 FR': rt1, 'Ch2 SD': SD2, 'Ch2 FR': rt2, 'Ch3 SD': SD3, 'Ch3 FR': rt3})
    out_name = 'results/' + edf_file[4:] + '.xlsx'# + '_warning.txt'
    out_name_warn = 'results/' + edf_file[4:] + '_warning.xlsx'
    excel_mode = 'a'
    if not os.path.exists(out_name): #Check if there is a file to write to; adding a sheet if there is, making a new one if there isn't
        if not os.path.exists(out_name_warn):
            excel_mode = 'w'
            print (f'File {out_name} not found, creating...')
        else:
            out_name = out_name_warn
            print (f'File {out_name_warn} found, appending Sleep sheet...')
    else:
        print (f'File {out_name} found, appending Sleep sheet...')
    try:
        with pd.ExcelWriter(out_name_warn, engine='openpyxl', mode=excel_mode) as writer:
            df.to_excel(writer, sheet_name='Sleep')
    except Exception as e:
        print (f'Failed to make Sleep sheet, reason: {e}')

def sleep_mark_everyone():
    files = []
    for file in os.listdir("EDF/"):
        if file.endswith(".edf"):
            files.append('EDF/' + file)
    print ("Found files: ", files)

    for edf_file in files:
        find_sleep(edf_file)

if __name__ == '__main__':
    sleep_mark_everyone()

