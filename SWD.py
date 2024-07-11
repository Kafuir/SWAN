#version 0.01

import ann
import MESD
import density
import os

def rename_folder_to_unique(original_path, base_name):
    i = 0
    while True:
        new_name = f"{base_name}_{i}"
        if not os.path.exists(new_name):
            break
        i += 1
    os.rename(original_path, new_name)
    input(f"Results saved in '{new_name}'")

SR = input ('The program will attempt to parse all files in EDF folder. Enter Sampling Rate (or press enter to use 400)\n')
if SR == '':
    SR = 400

if not ann.swd(SR): #TODO: replace with Exceptions
    if not MESD.calculate_ME_SD(SR):
        if not density.extract_stats():            
            print('All steps passed succesfully!\n')
        else:   
            input('Failed to extract information to CSV!\n')
    else:   
        input('Failed to compute SD!\n')
else:   
    input('ANN failure!\n')
            
rename_folder_to_unique(os.getcwd() + '/results/', "result")



