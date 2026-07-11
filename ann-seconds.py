#version 004
#modification to be used on second-by-second basis

import matplotlib.pyplot as plt
import matplotlib.image as img
import tensorflow as tf
import numpy as np
import pyedflib
import tensorflow_io as tfio 
from tensorflow.keras import datasets, layers, models
import os
import re
from io import BytesIO
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
    files = []
    for file in os.listdir("EDF/"):
        if file.endswith(".edf"):
            files.append('EDF/' + file)
    print (f'Found {len(files)} files')
    return files


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

    filelist = find_all_files('.edf')
    count = 0
    for filename in filelist:
        count += 1
        print (f'\n----------\n{count}/{len(filelist)}')
        print (filename)
        eeg = pyedflib.highlevel.read_edf(filename, ch_nrs = key['Channel'])[0][0]
        start_time = pyedflib.highlevel.read_edf_header(filename)['startdate'] #01
        processed_signal = np.array(eeg).astype(float)
        swd_len = 0
        certainty = 0 
            
        name_num = 0
        open(os.getcwd() + '/results/' + os.path.basename(filename[:-4]) + '.txt', 'w').close() #to avoid older records being added to
        file_out = open(os.getcwd() + '/results/' + os.path.basename(filename[:-4]) + '.txt', 'a')
        file_out.write(f'Record started at {start_time}\n') #01
        print (f'Record started at {start_time}') #01
        frame_length = size*128
        frame_step = size*8
        spectrogram = tfio.audio.spectrogram(processed_signal,nfft=frame_length, window=frame_length, stride=frame_step)
        spectrogram = spectrogram.numpy()[:,:65]

        frame_step = size*8
        num_frames = -(-len(processed_signal) // frame_step)

        carrot_size = num_frames // round(len(processed_signal)//key['SR'])
        image_chunks = chunks(spectrogram, carrot_size)
        del(spectrogram)
        vmin = 0
        vmax = 32
        EOF = cool_name(len(processed_signal)/key['SR']) ##version03\
        #***#print('Len of part: ', EOF)
        

        for x in image_chunks:
            if x.min() == 0 and x.max() == 0:
                break
            name_num += 1
            image = x.T
            
            img_buffer = BytesIO()
            plt.imsave(img_buffer, image, vmin = vmin, vmax = vmax)
            img_buffer.seek(0)
            input_arr = np.array([tf.keras.utils.img_to_array(tf.keras.utils.load_img(img_buffer))])

            
            try:
                predictions = model.predict(input_arr, verbose = 0)
            except Exception as e:
                print (f'Failure parsing data for fitting (this is likely not an actual error, reason: {e}')
                file_out.close()
                
            file_out.write(f'{cool_name(name_num)}: {predictions[0][1] - predictions[0][0]}\n')

        file_out.close()
    print('SWD parsing Done!')
    return 0

if __name__ == '__main__':
    swd({'SR': 400, 'Channel': 0, 'Model': 'compact'})
