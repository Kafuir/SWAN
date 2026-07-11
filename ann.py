import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import matplotlib.pyplot as plt
import matplotlib.image as img
import tensorflow as tf
import numpy as np
import pyedflib
import scipy as sp
from tensorflow.keras import datasets, layers, models
import re
from io import BytesIO
import math
from multiprocessing import Pool, current_process, Manager
#print(tf.__version__)

def butterlord (eeg, sr):
    eeg = np.clip(eeg, -150, 150)
    nyquist = 1
    low = 0.2 / nyquist
    high = 32 / nyquist
    #print (sr)

    # Butterworth avoids ripple in passband (better than Chebyshev for EEG)
    b, a = sp.signal.butter(4, [low, high], btype='band', fs = sr)

    # Apply forward-backward (zero-phase) filtering
    eeg_filtered = sp.signal.filtfilt(b, a, eeg)
    return eeg_filtered

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
    return files


#@tf.function(reduce_retracing=True) #this is old but seem to work
#def make_spectrogram(signal, size, spectro_cut):
#    frame_length = size*128
#    frame_step = size*8
#    spectrogram = tfio.audio.spectrogram(processed_signal,nfft=frame_length, window=frame_length, stride=frame_step)
#    return spectrogram.numpy()[:,:spectro_cut]

def create_image_chunks(total_items, num_processes, images):
    base_size = math.floor(total_items / num_processes)
    remainder = total_items % num_processes
    
    chunks = []
    start = 0
    
    for i in range(num_processes):
        # Add 1 to chunk size for first 'remainder' processes
        chunk_size = base_size + (1 if i < remainder else 0)
        end = start + chunk_size
        chunks.append(images[start:end])
        start = end
        
    return chunks


def predict_spectrogram(image_chunk, model, vmax):
    pid = current_process().pid
    predictions = []
    for x in image_chunk:
        image = x.T   
        with BytesIO() as img_buffer:#str(pid) + '.png'
            plt.imsave(img_buffer, image, vmin = 0, vmax = vmax) #TODO
            img_buffer.seek(0)
            input_arr = np.array([tf.keras.utils.img_to_array(tf.keras.utils.load_img(img_buffer))])
        try:
            predictions.append(model.predict(input_arr, verbose = 0))
        except Exception as e:
            if "Graph execution error" in str(e):
                print("Cutting... size: ", input_arr.shape)

            else:
                print (f'Failure parsing data for fitting (this is likely not an actual error, reason: {e}')
        #TODO ADD  CHECK FOR TAILS
        #if os.path.exists(img_buffer):
        #    os.unlink(img_buffer)
    return predictions

def swd(key):
    print ('Attempting to find SWDs in EDF files...')
    if not os.path.exists(os.getcwd() + '/results/'):
        os.makedirs(os.getcwd() + '/results/')

    #HERE BE SETTINGS
    if key['Model'] == 'compact':
        model = tf.keras.models.load_model('model-compact02.keras', compile = False)
        frame_length = 256
        frame_step = 16
        vmax = 32
        spectro_cut = 65
        cert_threshold = 2
    elif key['Model'] == 'short':
        model = tf.keras.models.load_model('model_short.keras', compile = False)
        frame_length = 256
        frame_step = 16
        vmax = 32
        spectro_cut = 65
        cert_threshold = 2
    elif key['Model'] == 'physio':
        model = tf.keras.models.load_model('model_quality.keras', compile = False)
        frame_length = 512
        frame_step = 50
        vmax = 2048
        spectro_cut = 32
        cert_threshold = 1
    elif key['Model'] == 'piter':
        model = tf.keras.models.load_model('model_piter.keras', compile = False)
        frame_length = 512
        frame_step = 25
        vmax = 32
        spectro_cut = 16
        cert_threshold = 0
    else:
        print('Model not found')
        return 1
    if key['Files'] != []:
        filelist = key['Files']
    else:
        filelist = find_all_files('.edf') #NO LONGER SUPPORTed
    print (f'Found {len(filelist)} files')
    count = 0
    for filename in filelist:
        count += 1
        print (f'\n----------\n{count}/{len(filelist)}')
        print (filename)
        eeg = pyedflib.highlevel.read_edf(filename, ch_nrs = key['Channel'])[0][0]
        SR = key['SR']
        if int(SR) == 0:
            SR = int(pyedflib.highlevel.read_edf(filename, ch_nrs = key['Channel'])[1][0]['sample_frequency'])
        #if int(SR) != 400:
        #    eeg = sp.signal.resample(eeg, num=len(eeg) // int(SR) * 400) #IMPLEMENT IN THE MAIN BRANCH AND AUTOMATE
        #    SR = 400
        if key['Model'] == 'physio':
            eeg = butterlord(eeg, SR)
        start_time = pyedflib.highlevel.read_edf_header(filename)['startdate'] #01
        processed_signal = np.array(eeg).astype(float)
        swd_len = 0
        certainty = 0 
            
        name_num = 0
        open(os.getcwd() + '/results/' + os.path.basename(filename[:-4]) + '.txt', 'w').close() #to avoid older records being added to
        file_out = open(os.getcwd() + '/results/' + os.path.basename(filename[:-4]) + '.txt', 'a')
        file_out.write(f'Record started at {start_time}\n') #01
        print (f'Record started at {start_time}') #01
        spectrogram = tf.signal.stft(processed_signal,fft_length=frame_length, frame_length=frame_length, frame_step=frame_step)
        spectrogram = tf.abs(spectrogram)
        spectrogram = spectrogram.numpy()[:,:spectro_cut]

        carrot_size = SR//frame_step
        image_chunks = chunks(spectrogram, carrot_size)
        del(spectrogram)
        vmin = 0
        
        seconds = int(len(processed_signal)/SR)
        EOF = cool_name(seconds) ##version03\
        processes = os.cpu_count() if key['Multi'] else 1
        preproc_chunks = create_image_chunks(seconds, processes, list(image_chunks))
        print(f'Using {len(preproc_chunks)} processes...')
        with Manager() as manager:
            lock = manager.Lock()
            with Pool(processes) as pool:
                results = pool.starmap(predict_spectrogram, zip(preproc_chunks, [model]*processes, [vmax]*processes))
        predictions_list = [item for sublist in results for item in sublist]
            
        for predictions in predictions_list:
            #print (predictions[0][1] - predictions[0][0])
            name_num += 1
            if predictions[0][1] > predictions[0][0]: #SWD
                certainty += (predictions[0][1] - predictions[0][0]) #a very rough approximation
                if swd_len == 0:
                    start_time = name_num
                swd_len += 1
                oldname = name_num
                not_len = 0
            if predictions[0][0] >= predictions[0][1] and swd_len > 0: #not SWD
                not_len += 1
                if swd_len < 2: #too short for SWD
                    certainty = 0
                    not_len = 0
                    swd_len = 0
                if swd_len > 1 and not_len > 1: #to check if it is a hole
                    if (round(certainty / swd_len)) > cert_threshold: #seems that such swds with cert less than 3 are mostly not swds ##version03
                        file_out.write(f'SWD status: {cool_name(max(0, start_time-1))} - {cool_name(oldname)}, certainty: {round(certainty / swd_len)}\n')
                        #print (f'SWD status: {cool_name(start_time-1)} - {cool_name(oldname)}, certainty: {round(certainty / swd_len)}')
                    certainty = 0
                    not_len = 0
                    swd_len = 0
        if swd_len > 0 and (round(certainty / swd_len)) > cert_threshold:
            #print (f'SWD status: {cool_name(start_time-1)} - {EOF}, certainty: {round(certainty / swd_len)}')
            file_out.write(f'SWD status: {cool_name(start_time-1)} - {EOF}, certainty: {round(certainty / swd_len)}\n')
        file_out.close()
    print('SWD parsing Done!')
    return 0

if __name__ == '__main__':
    swd({'SR': 0, 'Channel': 0, 'Model': 'physio', 'Files': [], 'Multi': 1})
