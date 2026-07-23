import pyedflib
import numpy as np
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
  
def time_to_seconds(time_str):
    dt = time_str.split(':')
    return int(dt[0]) * 3600 + int(dt[1]) * 60 + int(dt[2])

def mark(source_path, markers, what, output):
    y1 = pyedflib.highlevel.read_edf(source_path)
    for n in range(len(y1[1])):
        y1[1][n]['physical_max'] = max(y1[0][n])
        y1[1][n]['physical_min'] = min(y1[0][n])
    y1[2]['annotations'] = markers
    if what == 'mrk_copy':
        pyedflib.highlevel.write_edf(output + '/' + os.path.basename(source_path)[:-3] + '_marked.edf', *y1)
    if what == 'mrk_orig':
        pyedflib.highlevel.write_edf(source_path, *y1)

def get_marks(ex):
    df = pd.read_excel(ex, sheet_name='SWDs')
    return[[int(df['Start'].apply(time_to_seconds)[i]), int(df['Duration'].apply(time_to_seconds)[i]), str(df['Cert'][i])] for i in range(len(df))]

# Define markers

def mark_files(edfs, what, output):
    xls = []
    if edfs == []:
        for file in os.listdir(output):
            if file.endswith(".xlsx"):
                xls.append(output + file)
                edfs.append(xl_file.replace('_warning', '')[:-4].replace('results/', 'EDF/') + 'edf')
    else:
        for file in edfs:
            filename = os.path.splitext(os.path.basename(file))[0] + ".xlsx"
            filename = os.path.join(output, filename)
            if not Path(filename).is_file():
                filename = filename[:-5] + '_warning.xlsx'
            xls.append(filename)
            #else:
            #    xls.append(os.path.join(os.getcwd(), "results", filename))
    print ("Found files: ", edfs)
    for xl_file, edf_file in zip(xls, edfs):
        #print (edf_file)
        mark(edf_file, get_marks(xl_file), what, output)


# Specify the output file path
if __name__ == '__main__':
    mark_files([])
