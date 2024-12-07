#version 02

import pyedflib
import os
import statistics
import datetime
import scipy.stats as st
import numpy as np

def extract_from_chunk (chunk, hour1, hour2, sev):
    stdev = round(statistics.stdev(chunk), 3)
    #mean = round(statistics.mean(chunk), 3)
    #amp = round(chunk.max()-chunk.min(), 3)
    filtered = [num for num in chunk if abs(num) > 1.5]
    #hal = round(len(filtered) / len(chunk), 4)*100
    return (f'{hour1}-{hour2[:-1]} SD {stdev} CERT {sev}', stdev)# Cool Metric {int(sev)/stdev}')#{amp} high and lows percentage')

def time_to_secs(time, SR):
    if ',' in time:
        time = time[:-1]
    parts = time.split(':')
    return (int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])) * SR

def calculate_ME_SD(key): 
    if not os.path.exists(os.getcwd() + '/results/MESD/'):
        os.makedirs(os.getcwd() + '/results/MESD/')
    stdevs = []
    means = []
    #file_out_global = open(os.getcwd() + '/results/MESD/' + '_GLOBAL_ME.txt', 'a')


    for filename in os.listdir(os.getcwd() + '/results/'):
        if '.txt' in filename:
            print('Found a file, ', filename)
            with open(os.getcwd() + '/results/' + filename) as file:
                eeg = pyedflib.highlevel.read_edf(os.getcwd() + '/EDF/' + filename[:-3] + 'edf', ch_nrs = key['Channel'])[0][0]
                file_out = open(os.getcwd() + '/results/MESD/' + os.path.basename(filename[:-4]) + '_MESD.txt', 'w')
                filtered = 0
                passed = 0
                for line in file:
                    parts = line.split()
                    if parts[2] != 'at':
                        time1 = time_to_secs(parts[2], key['SR'])
                        time2 = time_to_secs(parts[4], key['SR'])
                        (line, stdev) = extract_from_chunk(eeg[time1:time2], parts[2], parts[4], parts[-1])
                        if stdev >= 0.0 and stdev < 0.45:
                            file_out.write(line + '\n')
                            #***#print (line)
                            passed += 1
                        else:
                            #***#print ('FILETERED: ', line)
                            filtered += 1
                        ##stdevs.append(stdev)
                        ##means.append(mean)
                        #file_out_global.write(f'{stdev} {mean}\n')
                    else:
                        file_out.write(f'Start: {parts[4]}\n')
                file_out.write(f'Filtered/passed rate: {filtered}VS{passed}\n') 
                file_out.close()
            os.remove(os.getcwd() + '/results/' + filename)
    return 0

if __name__ == "__main__":
    calculate_ME_SD({'SR': 400, 'Channel': 0})
    
##stats1 = (f'STDEV:\n68%: {st.t.interval(0.68, len(stdevs)-1, loc=np.mean(stdevs), scale=st.sem(stdevs))}\n 90%: {st.t.interval(0.90, len(stdevs)-1, loc=np.mean(stdevs), scale=st.sem(stdevs))}\n 99.7%: {st.t.interval(0.997, len(stdevs)-1, loc=np.mean(stdevs), scale=st.sem(stdevs))}')
##stats2 = (f'MEAN:\n68%: {st.t.interval(0.68, len(means)-1, loc=np.mean(means), scale=st.sem(means))}\n 90%: {st.t.interval(0.90, len(means)-1, loc=np.mean(means), scale=st.sem(means))}\n 99.7%: {st.t.interval(0.997, len(means)-1, loc=np.mean(means), scale=st.sem(means))}')
##file_out_global.write(stats1)
##print (stats1)
##file_out_global.write(stats2)
##print (stats2)
##file_out_global.close()


#for 
