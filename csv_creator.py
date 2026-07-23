import os
from datetime import datetime, timedelta
import re

def time_to_times(time):
    #print(time)
    time = str(time).split(':')
    #print(time)
    if len(time) == 1:
        return int(time[0]), 0, 0
    if len(time) == 2:
        return int(time[0]), int(time[1]), 0
    if len(time) == 3:
        return int(time[0]), int(time[1]), int(time[2])

def sum_times(time1, time2, minus = False):
    #print(time1, time2)
    h1, m1, s1 = time_to_times(time2)
    h2, m2, s2 = time_to_times(time1)
    if minus:
        total = timedelta(hours=h2, minutes=m2, seconds=s2) - timedelta(hours=h1, minutes=m1, seconds=s1)
    else:
        total = timedelta(hours=h1, minutes=m1, seconds=s1) + timedelta(hours=h2, minutes=m2, seconds=s2)
    result = re.findall(r'\d+:\d{2}:\d{2}', str(total))[0]
    if result[1] == ':':
        result = '0'+ result
    return result

def create_csvs (key):
    for filename in os.listdir(os.getcwd() + '/results/MESD/'):
        if 'MESD.txt' in filename:
            create_csv(os.getcwd() + '/results/MESD/' + filename, key) #not CSV
    return 0

def transform(line, start):
    parts = line.split(' ')
    result = f'{sum_times(parts[0].split("-")[0], start)}, {parts[0].split("-")[0]}, {sum_times(parts[0].split("-")[1], parts[0].split("-")[0], minus = True)}, {parts[-1]}'
    return result
    

def create_csv(file, key):
    with open(file, "r") as f:
        splitted = f.read().split('\n')
        start = splitted[0].split(' ')[1]
        with open(key['Folder'] + '/' + os.path.basename(file)[:-3] + 'csv', 'w') as out:
            output = [transform(line, start) for line in splitted if "CERT" in line]
            out.write("\n".join(output))


