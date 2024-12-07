from datetime import datetime, timedelta
import datetime as dt
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


def sum_times_am(times):
    total_seconds = 0
    for t in times:
        total_seconds += int(t[0]) * 3600 + int(t[1]) * 60 + int(t[2])
    
    # Convert total_seconds to hours, minutes, and seconds
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    #a = datetime.
    return [hours, minutes, seconds]#dt.time(hour=hours, minute=minutes, second=seconds)

def return_next(moment):
    tim = moment.split(':')
    if int(tim[1]) > 29:
        tim[1] = '00'
        tim[0] = int(tim[0]) + 1
    else:
        tim[1] = '30'
    #if int(tim[0]) > 23:
    #    tim[0] -= 24
    if len(str(tim[0])) < 2:
        tim[0] = '0'+str(tim[0])
    return str(tim[0]) + ':' + str(tim[1])

def fancy(time):
    result = f"{time//2}:{time%2*3}0"
    if result[1] == ':':
        result = '0'+result
    return result

def make_dick_time(lim, hour):
    result = {}
    for x in range(lim):
        result[hour] = '0:00:00'
        hour = return_next(hour)
    return result

# Function to parse time period strings into start and end datetimes
def parse_time_period(tp, start):
    start_str, end_str = tp
    start_ar = sum_times_am([start_str.split(':'), start.split(':')])
    end_ar = sum_times_am([end_str.split(':'), start.split(':')])
    #print(start_dt, end_dt)
    return start_ar, end_ar#.time()

# Function to calculate duration between two times
def calculate_duration(start_time, end_time):
    start_time = int(start_time[0]) * 3600 + int(start_time[1]) * 60 + int(start_time[2])
    end_time = int(end_time[0]) * 3600 + int(end_time[1]) * 60 + int(end_time[2])
    return dt.timedelta(seconds = end_time - start_time)

def check_periods(time_periods, record_len, delta): #TODO: check for per hour basis
    grouped_by_half_hour = {}
    for tp in time_periods:
        start_time, end_time = parse_time_period(tp, delta)
        print(start_time)
        start_half_hour = start_time[0] * 2 + (start_time[1] // 30)  # Convert hour and minute to half-hour index
        if start_half_hour not in grouped_by_half_hour:
            grouped_by_half_hour[start_half_hour] = []
        grouped_by_half_hour[start_half_hour].append((start_time, end_time))
    #print(grouped_by_half_hour.items())


    longest_durations = make_dick_time(record_len, round_time(delta))
    #print(longest_durations.keys())
    for half_hour, time_periods in grouped_by_half_hour.items():
        #print ('#', half_hour)
        max_duration = timedelta()
        for start_time, end_time in time_periods:
            duration = calculate_duration(start_time, end_time)
            if duration > max_duration:
                max_duration = duration
        longest_durations[fancy(half_hour)] = str(max_duration)
    print(longest_durations.keys())
    return longest_durations





# Print the longest durations for each half-hour
#for half_hour, duration in dict_periods.items():
#    print(f"Half-Hour {half_hour//2}:{half_hour%2*3}0: Longest duration is {duration}")


def max_add(file, time_file):
    if time_file == 0:
        time_file = input(os.path.basename(file)+', Time not found\n')
    if time_file == '':
        print('Pass')
        return 0
    dfs = pd.read_excel(file, sheet_name=None)
    dfs = pd.read_excel(file, sheet_name=None)
    starts = [list(row) for row in zip(*[dfs['SWDs']['Start'].tolist(), dfs['SWDs']['End'].tolist()])]
    dict_periods = check_periods(starts, len(dfs['Properties']), time_file)
    periods = list(dict_periods.values())
    dfs['Properties']['Max SWD'] = periods

    starts = [list(row) for row in zip(*[dfs['SWDs']['Start'].tolist(), dfs['SWDs']['End'].tolist()])]
    dict_periods = check_periods(starts, len(dfs['Properties']), '00:00')
    periods = list(dict_periods.values())
    dfs['Properties']['Max SWD Relative'] = periods
    
    with pd.ExcelWriter(file, engine='openpyxl') as writer:
        for sheet in dfs:
            if sheet == 'SWDs':
                del dfs[sheet]['Unnamed: 0']
                dfs[sheet].to_excel(writer, sheet_name = sheet, index=True)
            else:
                dfs[sheet].to_excel(writer, sheet_name = sheet, index=False)
