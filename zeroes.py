import pandas as pd
import os

def find_all_files(what):
    result = []
    for i in os.walk(os.getcwd()):
        for x in i[2]:
            if what in x: 
                result.append(i[0] + '/' + x)
    print (f'Found {len(result)} files')
    return result

def round_time(moment):
    tim = moment.split(':')
    if int(tim[1]) > 30:
        tim[1] = '30'
    else:
        tim[1] = '00'
    return str(tim[0]+':'+tim[1])

def read_times(file):
    dick = {}
    with open(file, 'r') as file:
    # Iterate over each line in the file
        for line in file:
            line = line.strip()
            key, value1, value2, value3 = line.split(" ")  # Assuming there's only one space separating key and value
            #print (value2)
            
            # Add the key-value pair to the dictionary
            dick[key] = [value1, value2, value3]
    return dick

def fh(num):
    num = str(num%24)
    if len(num) < 2:
        num = '0'+num
    return num

def time_between(time1, time2):
    if len(str(time1)) < 3:
        time1 = str(time1)+':00'
    [num1, bool1] = map(int, time1.split(':'))
    [num2, bool2] = map(int, time2.split(':'))
    #print (num1, ':', bool1, ' ', num2, ':', bool2)
    if num2 < num1:
        num2 += 24 #to account for possible midnight holes
    # Initialize an empty list to store our pairs
    pairs = []
    if bool1 == 0 and num1 != num2:
        pairs.append(f'{fh(num1)}:30')
    # Loop through the numeric range
    for num in range(num1+1, num2):
        pairs.append(f'{fh(num)}:00')
        pairs.append(f'{fh(num)}:30')
    if bool2 == 30 and num1 != num2:
        pairs.append(f'{fh(num2)}:00')
    if num1 != num2:
        pairs.append(time2)
    return pairs

#file = 'my_file.xlsx'
def zeros_add(file, time_file):
    start = time_file[0]
    #print(start)
    time_file = time_file[1]
    if time_file == 0:
        time_file = input(os.path.basename(file)+', Time not found\n')
    if time_file == '':
        print('Pass')
        return 0
    else:
        delta = round_time(time_file)
    dfs = pd.read_excel(file, sheet_name=None)
    end_hour = dfs['Properties'].iloc[-1, 0]
    if end_hour == 'NO SWD':
        end_hour = start
    x = time_between(end_hour, round_time(time_file))
    for hour in x:
        dfs['Properties'] = dfs['Properties']._append({'Hour': hour, 'SWD time': 0.0, 'SWD time percentage': 0.0, 'SWD amount': 0.0, 'mean SD': 0.0, 'mean CERT': 0.0}, ignore_index = True)
    dfs['Properties']['Mean SWD'] = dfs['Properties']['SWD time'] / dfs['Properties']['SWD amount']
    dfs['Properties']['Mean SWD'] = dfs['Properties']['Mean SWD'].fillna(0)
    dfs['Properties']['Mean SWD'] = dfs['Properties']['Mean SWD'].round(decimals=2)
