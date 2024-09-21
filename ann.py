#version 004

import matplotlib.pyplot as plt
import matplotlib.image as img
import tensorflow as tf
import numpy as np
import pyedflib
import tensorflow_io as tfio 
from tensorflow.keras import datasets, layers, models
import os
import re
#print(tf.__version__)

def fancy(time, length = 2):
    time = str(time)
    nuls = '0'*(length-len(time))
    return f'{nuls}{time}'

def get_number(image_name):
    return int(re.search(r'\d+.png', image_name)[0][:-4])

def cool_name(image_name):
    m = int(image_name)#get_number(image_name)
    return f'{fancy(m//3600)}:{fancy((m%3600)//60)}:{fancy(m%3600%60)}'

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def find_all_files(what):
    result = []
    for i in os.walk(os.getcwd()):
        for x in i[2]:
            if what in x: 
                result.append(i[0] + '/' + x)
    print (f'Found {len(result)} files')
    return result


@tf.function(reduce_retracing=True) #this is old but seem to work
def make_spectrogram(signal, size):
    frame_length = size*128
    frame_step = size*8
    spectrogram = tfio.audio.spectrogram(processed_signal,nfft=frame_length, window=frame_length, stride=frame_step)
    return spectrogram.numpy()[:,:65]

def swd(key):
    print ('Attempting to find SWDs in EDF files...')
    if not os.path.exists(os.getcwd() + '/results/'):
        os.makedirs(os.getcwd() + '/results/')

    #HERE BE SETTINGS
    if key['Model'] == 'compact':
        model = tf.keras.models.load_model('model-compact02.keras', compile = False)
    elif key['Model'] == 'short':
        model = tf.keras.models.load_model('model_short.keras', compile = False)
    else:
        print('Model not found')
        return 1
    size = 2
    threshold = 120 #5 days for memes; USED TO PREVENT HUNGRY SNAKE FROM EATING ALL YOUR MEMORY

    filelist = find_all_files('.edf')
    count = 0
    for filename in filelist:
        count += 1
        print (f'\n----------\n{count}/{len(filelist)}')
        print (filename)
        eeg = pyedflib.highlevel.read_edf(filename, ch_nrs = key['Channel'])[0][0]
        start_time = pyedflib.highlevel.read_edf_header(filename)['startdate'] #01
        signal = np.array(eeg).astype(float)
        swd_len = 0
        certainty = 0 

        if len(signal) > key['SR']*3600*threshold: #completely arbitrary threshold of 12 hours
            signal_parted = [signal[:len(signal)//2], signal[len(signal)//2:]]
            print ('The original recording is too long to proceed safely, dividing it in two...')
        else:
            signal_parted = [signal]
            
        name_num = 0
        open(os.getcwd() + '/results/' + os.path.basename(filename[:-4]) + '.txt', 'w').close() #to avoid older records being added to
        file_out = open(os.getcwd() + '/results/' + os.path.basename(filename[:-4]) + '.txt', 'a')
        file_out.write(f'Record started at {start_time}\n') #01
        print (f'Record started at {start_time}') #01
        for processed_signal in signal_parted:
            frame_length = size*128
            frame_step = size*8
            spectrogram = tfio.audio.spectrogram(processed_signal,nfft=frame_length, window=frame_length, stride=frame_step)
            spectrogram = spectrogram.numpy()[:,:65]

            frame_step = size*8
            num_frames = -(-len(processed_signal) // frame_step)
            #***#print('Spec length: ', num_frames)
            #***#print(spectrogram.shape)

            carrot_size = num_frames // round(len(processed_signal)//key['SR'])
            image_chunks = chunks(spectrogram, carrot_size)
            vmin = 0
            vmax = 32
            EOF = cool_name(len(processed_signal)/key['SR']) ##version03\
            #***#print('Len of part: ', EOF)
            

            for x in image_chunks:
                if x.min() == 0 and x.max() == 0:
                    break
                name_num += 1
                image = x.T
                img.imsave('image.png', image, vmax = vmax, vmin = vmin) #sloppy stuff, TODO - do it in mem
                image = tf.keras.utils.load_img('image.png')
                input_arr = tf.keras.utils.img_to_array(image)
                input_arr = np.array([input_arr])  # Convert single image to a batch.
                #name = cool_name(name_num) ##version03
                try:
                    predictions = model.predict(input_arr, verbose = 0)
                except Exception as e:
                    print (f'Failure parsing data for fitting (this is likely not an actual error, current time: {name}')
                    file_out.close()
                if predictions[0][1] > predictions[0][0]: #SWD
                    certainty += (predictions[0][1] - predictions[0][0]) #a very rough approximation
                    if swd_len == 0:
                        start_time = name_num
                    swd_len += 1
                    oldname = name_num
                    not_len = 0
                if predictions[0][0] >= predictions[0][1] and swd_len > 0: #not SWD
                    not_len += 1
                    if swd_len < 3: #too short for SWD
                        certainty = 0
                        not_len = 0
                        swd_len = 0
                    #print (not_len, swd_len)
                    if swd_len > 2 and not_len > 1: #to check if it is a hole
                        if (round(certainty / swd_len)) > 2: #seems that such swds with cert less than 3 are mostly not swds ##version03
                            file_out.write(f'SWD status: {cool_name(start_time-1)} - {cool_name(oldname)}, certainty: {round(certainty / swd_len)}\n')
                            #***#print (f'SWD status: {cool_name(start_time-1)} - {cool_name(oldname)}, certainty: {round(certainty / swd_len)}')
                        certainty = 0
                        not_len = 0
                        swd_len = 0
            if swd_len > 0 and (round(certainty / swd_len)) > 2:
                #***#print (f'SWD status: {cool_name(start_time-1)} - {EOF}, certainty: {round(certainty / swd_len)}')
                file_out.write(f'SWD status: {cool_name(start_time-1)} - {EOF}, certainty: {round(certainty / swd_len)}\n')
        file_out.close()
    print('SWD parsing Done!')
    return 0

if __name__ == '__main__':
    swd({'SR': 400, 'Channel': 0, 'Model': 'short'})
