##############################################
# This file is used for general purpose launch
# of the SWAN stuff; practically what happens
# after you hit START button - it's all there
##############################################

import ann
import MESD
import density
import csv_creator
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
                failure_xls, failure_csv = 0, 0
                if key['Output'] == 'xls' or key['Output'] == 'csvxls':
                    failure_xls = density.extract_stats(key)
                if key['Output'] == 'csv' or key['Output'] == 'csvxls':
                    failure_csv = csv_creator.create_csvs(key)  
                if failure_xls == 0 and failure_csv == 0:            
                    print('All steps passed succesfully!\n')
            except Exception as e:
                print(f"Statistical data and Excel/CSV file formation failed: {e}")

            #Removing directory with MESD stuff
        for root, dirs, files in os.walk(os.getcwd()+'/results/MESD'):
            for file in files:
                print(file)
                if "_MESD" in file:
                    file_path = os.path.join(root, file)
                    os.remove(file_path)
    ''' REMOVED UNTIL SARATOV SENDS THEIR REGARDS
    if key['Sleep']:
        import sleep
        print('Moving to sleep markdown...')
        sleep.sleep_mark_files(key['Files'])
    '''
    if key['Markdown'] != 'None':
        import add_markers
        print('Moving to EDF markers...')
        add_markers.mark_files(key['Files'], key['Markdown'], key['Folder'])
        
    if key['Rename']:            
        rename_folder_to_unique(os.getcwd() + '/results/', "result")
    else:
        print('Results were saved in results folder')
    return 0

if __name__ == '__main__':
    key = {'Bins': 'half', 'SR': 400, 'verbose': 3, 'Model': 'short', 'Channel': 0, 'Rename': 1, 'Sleep': 0,  'Astronomical': 0, 'Markdown': 0}
    SR = input ('The program will attempt to parse all files in EDF folder. Enter Sampling Rate (or press enter to use 400)\n')
    if SR != '':
        key['SR'] = SR
    launch(key)
    input('')

