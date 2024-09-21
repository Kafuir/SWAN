#version 0.01

import ann
import MESD
import density
import os

#Bin - using hours or half-hours for excel file index
#SR - sampling rate of the record
#verbose - how much of the process should be shown, codified binary: 0 - nothing, 1 - files, 2 - overall information, 4 - swds found
#model - name of the model used, 'short' for default one, 'compact' for 8-neuron one

def rename_folder_to_unique(original_path, base_name):
    i = 0
    try:
        while True:
            new_name = f"{base_name}_{i}"
            if not os.path.exists(new_name):
                break
            i += 1
        os.rename(original_path, new_name)
        print(f"Results saved in '{new_name}'")
    except Exception as e:
        print(f'Folder renaming failure: {e}')

def launch(key):
    try:
        failure = ann.swd(key)
    except Exception as e:
        print(f"ANN failure: {e}")
        return 0
    if failure == 0:
        try:
            failure = MESD.calculate_ME_SD(key)
        except Exception as e:
            print(f"Deviation filtration and/or SD calculation failure: {e}")
            return 0
        if failure == 0:
            try:
                failure = density.extract_stats(key)  
                if failure == 0:            
                    print('All steps passed succesfully!\n')
            except Exception as e:
                print(f"Statistical data and Excel file formation failed: {e}")
                return 0
    if key['Sleep']:
        import sleep
        print('Moving to sleep markdown...')
        sleep.sleep_mark_everyone()  
    if key['Rename']:            
        rename_folder_to_unique(os.getcwd() + '/results/', "result")
    else:
        print('Results were saved in results folder')
    return 0

if __name__ == '__main__':
    key = {'Bins': 'half', 'SR': 400, 'verbose': 3, 'Model': 'short', 'Channel': 0}
    SR = input ('The program will attempt to parse all files in EDF folder. Enter Sampling Rate (or press enter to use 400)\n')
    if SR != '':
        key['SR'] = SR
    launch(key)
    input('')

