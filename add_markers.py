import pyedflib
import numpy as np
import os
import pandas as pd
from datetime import datetime
  
def time_to_seconds(time_str):
    dt = time_str.split(':')
    return int(dt[0]) * 3600 + int(dt[1]) * 60 + int(dt[2])

def mark(source_path, markers):
    y1 = pyedflib.highlevel.read_edf(source_path)
    for n in range(len(y1[1])):
        y1[1][n]['physical_max'] = max(y1[0][n])
        y1[1][n]['physical_min'] = min(y1[0][n])
    y1[2]['annotations'] = markers
                         
    pyedflib.highlevel.write_edf(source_path, *y1)

def get_marks(ex):
    df = pd.read_excel(ex, sheet_name='SWDs')
    return[[int(df['Start'].apply(time_to_seconds)[i]), int(df['Duration'].apply(time_to_seconds)[i]), str(df['Cert'][i])] for i in range(len(df))]

# Define markers

def mark_files():
    files = []
    for file in os.listdir("results/"):
        if file.endswith(".xlsx"):
            files.append('results/' + file)
    print ("Found files: ", files)

    for xl_file in files:
        edf_file = xl_file.replace('_warning', '')[:-4].replace('results/', 'EDF/') + 'edf'
        print (edf_file)
        mark(edf_file, get_marks(xl_file))


# Specify the output file path
if __name__ == '__main__':
    mark_files()
