#version 02

import pyedflib
import os
import statistics
import datetime
import scipy.stats as st
import numpy as np



def create_artefact_series (signal, SR, tlow, thigh):
    num_seconds = len(signal) // SR
    
    series = []
    
    for i in range(num_seconds):
        start_idx = i * SR
        end_idx = start_idx + SR
        segment = signal[start_idx:end_idx]
        diff1 = np.diff(signal) #probably not a good idea, but it will do
        abs_diff1 = np.abs(diff1)
        max_d1 = np.max(abs_diff1)
        
        if len(segment) > 0:
            sd = np.std(segment)
            if max_d1 < tlow or sd > thigh:
                series.append(1)
            else:
                series.append(0)
    
    return sum(series)

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
    


    

    SR = key['SR']
    #for filename in os.listdir(os.getcwd() + '/results/'):
    if key['Files'] == []:
        key['Files'] = [os.getcwd() + '/EDF/' + os.path.basename(x)[:-3] + 'edf' for x in os.listdir(os.getcwd() + '/results/') if '.txt' in x]
    for filename in key['Files']:
        #if '.txt' in filename:
        #print('Found a file, ', filename)
        with open(os.getcwd() + '/results/' + os.path.basename(filename)[:-3] + 'txt') as file:
            eeg = pyedflib.highlevel.read_edf(filename, ch_nrs = key['Channel'])[0][0]
            if int(SR) == 0:
                SR = int(pyedflib.highlevel.read_edf(filename, ch_nrs = key['Channel'])[1][0]['sample_frequency'])
                
            if key['Model'] != 'physio': #physio recordings are more noisy
                threshold_low, threshold_high = 0.1, 0.45 #should be 10 times smaller
                bad_time = 0
            else:
                threshold_low, threshold_high = 1, 10000
                bad_time = create_artefact_series(eeg, SR, threshold_low, threshold_high) #how many of the record is compromosed
                                                  
            file_out = open(os.getcwd() + '/results/MESD/' + os.path.basename(filename[:-4]) + '_MESD.txt', 'w')
            filtered = 0
            passed = 0
            for line in file:
                parts = line.split()
                if parts[2] != 'at':
                    time1 = time_to_secs(parts[2], SR)
                    time2 = time_to_secs(parts[4], SR)
                    (line, stdev) = extract_from_chunk(eeg[time1:time2], parts[2], parts[4], parts[-1])
                    if stdev >= threshold_low and stdev < threshold_high:
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
            file_out.write(f'Artefacts physio only: {bad_time}\n')
            file_out.write(f'Duration: {int(pyedflib.highlevel.read_edf_header(filename)["Duration"])}')
            file_out.close()
        os.remove(os.getcwd() + '/results/' + os.path.basename(filename)[:-3] + 'txt')
    return 0 #TODO fileless transition

if __name__ == "__main__":
    calculate_ME_SD({'Model': 'short', 'SR': 400, 'Channel': 0, 'Files': []})

