#version 001
import re
import os
import pandas as pd
from pandas import DataFrame
from datetime import datetime, timedelta

def sum_times(time1, time2):
    time_list = [time1, time2]
    total = timedelta()
    for time_str in time_list:
        h, m, s = map(int, time_str.split(':'))
        total += timedelta(hours=h, minutes=m, seconds=s)
    return re.findall(r'\d+:\d{2}:\d{2}', str(total))[0]

def time_between(num1, bool1, num2, bool2, key):
    #print (num1, ':', bool1, ' ', num2, ':', bool2)
    if num2 < num1:
        num2 += 24 #to account for possible midnight holes
    # Initialize an empty list to store our pairs
    pairs = []
    if bool1 == 0 and key['Bins'] == 'half' and num1 != num2:
        pairs.append([num1, 3])
    # Loop through the numeric range
    for num in range(num1+1, num2):
        pairs.append([num%24, 0])
        if key['Bins'] == 'half':
            pairs.append([num%24, 3])
    if bool2 == 30 and key['Bins'] == 'half' and num1 != num2:
        pairs.append([num2%24, 0])
    return pairs


def parse_timestamp_pairs(pairs, day_long, start_time="00:00:00", end_time="23:59:59"):
    # Define the overall time range
    start_datetime = datetime.strptime(start_time, "%H:%M:%S") #СДЕЛАЙ ПРОВЕРКУ ЧТО ЭТО ТОТ ЖЕ ИЛИ РАЗНЫЕ ДНИ!!
    end_datetime = datetime.strptime(end_time, "%H:%M:%S")
    #print(end_time, start_time)

    # Initialize the time series with zeros
    time_series = [0] * ((end_datetime - start_datetime).seconds + 1 + day_long*86400) 

    # Process each pair
    for pair in pairs:
        start, end = pair
        #print(start, end)
        start_datetime_pair = datetime.strptime(start, "%H:%M:%S")
        end_datetime_pair = datetime.strptime(end, "%H:%M:%S")
        #print(start_datetime_pair, start_datetime)

        # Calculate the indices for the start and end times of the pair
        start_index = int((start_datetime_pair - start_datetime).total_seconds())
        if start_index < 0:
            start_index = 86400 + start_index
        end_index = int((end_datetime_pair - start_datetime).total_seconds())
        if end_index < 0:
            end_index = 86400 + end_index

        # Mark the covered seconds
        #print (len(time_series), start_index, end_index)
        for i in range(start_index, end_index + 1):
            time_series[i] = 1

    return time_series

#this functions finds timestamps and parses their stats to corr. hours
def find_sd (filename, output, start, key): #also returns SWDs for excel
    file = open(filename, 'r').read()
    lines = re.findall(r'\d{2}:\d{2}:\d{2}-\d{2}:\d{2}:\d{2} SD 0.\d+ CERT \d+', file)
    result = []
    excel = []
    #count, sd, cert = 0, 0, 0
    old_hour = int(re.match(r'\d+', start)[0]) - 1#'999' #to fail
    old_minute = int(re.search(r':\d+:', start)[0][1:3])//30*30 #2
    #making sure its less than the first observed bin
    #print (old_hour, old_minute)
    if key['Bins'] == 'half':
        if old_minute == 30:
            old_minute = 0
            old_hour += 1
        else:
            old_minute = 30
    #print('HAHAS', old_hour, old_minute)
    count = 0
    for line in lines:
        x = line.split()
        excel.append(x)
        hour = int(re.match(r'\d+', sum_times(start, x[0][:8]))[0])
        minutes = int(re.search(r':\d+:', sum_times(start, x[0][:8]))[0][1:3])//30*30 #acutally checks if it is 0-30 or 30-59, as 0-1 respectively
        #print (x)
        if hour == old_hour and not (key['Bins'] == 'half' and minutes != old_minute):
            sd += float(x[2])
            count += 1
            cert += float(x[4])
        else:
            if count != 0:
                result.append([str(old_hour) + ':' + str(old_minute // 10) + '0', count, round(sd/count, 3), round(cert/count, 1)])
            #else:
            #    result.append([old_hour + ':' + str(old_minute // 10) + '0', count, 0, 0])
            for skipped in time_between (old_hour, old_minute, hour, minutes, key):
                result.append([str(skipped[0]) + ':' + str(skipped[1]) + '0', 0, 0, 0])
            old_hour = hour
            old_minute = minutes
            sd = float(x[2])
            count = 1
            cert = float(x[4])
    df = DataFrame({'Start': [row[0][:8] for row in excel], 'End':[row[0][9:] for row in excel], 'SD': [float(row[2]) for row in excel], 'Cert': [int(row[4]) for row in excel]})
    if count == 0: #in case of an empty file
        result.append([0, 0, 0, 0, 0])
    else:
        result.append([old_hour, count, round(sd/count, 3), round(cert/count, 1)])
        if old_hour != int(re.match(r'\d+', sum_times(start, x[0][9:17]))[0]): #raplce with actually checking if seconds overflow
            result.append([old_hour, 'Tail of above', round(sd/count, 3), round(cert/count, 1)])      
    #print (result)
    return (result, df)
            
    
def describe_csv (filename, output, key):
    #print (filename)
    file = open(filename, 'r').read()
    times = re.findall(r'\d{2}:\d{2}:\d{2}', file)

    warning_filtered = ''
    start = times[0]
    filtered = [int(i) for i in (re.search(r'\d+VS\d+', file)[0].split('VS'))]
    #print(filtered)
    misc = DataFrame({'Filtered': filtered[0], 'Passed': filtered[1]}, index = [0])#, '% of filtered': round(int(filtered[0])/(int(filtered[0])+int(filtered[1]))*100, 3)})
    if sum(filtered):
        if filtered[0] > (filtered[1]+filtered[0])/10:
            warning_filtered = '_warning'
            print (f'\nWARNING! File {os.path.basename(filename)} has {round(filtered[0]/(filtered[1]+filtered[0])*100, 2)}% SWDs filtered: it might indicate poor quality of the record.\nIt is recommended to check the record and/or use another channel (current: {key["Channel"]}) for parsing.')
    (info, swds) = find_sd(filename, output, start, key)
    timestamp_pairs = []
    for x in range(1, len(times), 2):
        timestamp_pairs.append((sum_times(times[x], start), sum_times(times[x+1], start)))

    day_long = (int(times[-1].split(':')[0]) > 23) #boolean var to check if record goes for 24+ hours
    time_series = parse_timestamp_pairs(timestamp_pairs, start_time = start, end_time = sum_times(start, times[-1]), day_long = day_long)
    index = pd.date_range(start=start, periods=len(time_series), freq='s')
    series = pd.Series(time_series, index=index)
    if day_long:
        times[-1] = sum_times(times[-1], "00:00:00")
        if times[-1][1] == ':':
            times[-1] = '0'+times[-1]
    #print (times[-1])

    if key['Bins'] == 'hour': #dividing in hourly bins
        hourly_time = series.resample('h').sum()
        hourly_counts = hourly_time / 3600
        real_start_hour = datetime.strptime(start, "%H:%M:%S") - datetime.strptime(f'{start[0]}{start[1]}:00:00', "%H:%M:%S")
        #print (real_start_hour)
        real_end_hour = datetime.strptime(times[-1], "%H:%M:%S") - datetime.strptime(f'{times[-1][0]}{times[-1][1]}:00:00', "%H:%M:%S") #not safe
        #print (real_end_hour)
        hourly_counts.iloc[0] = hourly_counts.iloc[0] * 3600 / real_start_hour.total_seconds()
        hourly_counts.iloc[-1] = hourly_counts.iloc[-1] * 3600 / (3600-(real_end_hour.total_seconds()))
        hours = hourly_counts.axes[0].hour
    if key['Bins'] == 'half':
        hourly_time = series.resample('30min').sum()
        hourly_counts = hourly_time / 1800
        real_start_hour = datetime.strptime(start, "%H:%M:%S") - datetime.strptime(f'{start[0]}{start[1]}:{int(start[3:5])//30*30}:00', "%H:%M:%S")
        #print (real_start_hour)
        real_end_hour = datetime.strptime(times[-1], "%H:%M:%S") - datetime.strptime(f'{times[-1][0]}{times[-1][1]}:{int(times[-1][3:5])//30*30}:00', "%H:%M:%S") #not safe
        #print (real_end_hour)
        hourly_counts.iloc[0] = hourly_counts.iloc[0] * 1800 / real_start_hour.total_seconds()
        hourly_counts.iloc[-1] = hourly_counts.iloc[-1] * 1800 / (1800-(real_end_hour.total_seconds()))
        hours_bad = hourly_counts.axes[0].hour
        if len(hours_bad) < 2:
            hours = hours_bad
        else:
            start_at_half = -1 if hours_bad[0] == hours_bad[1] else 1
            hours = []
            for hour in hours_bad:
                half = 3 if start_at_half == 1 else 0
                hours.append(f'{hour}:{half}0')
                start_at_half *= -1
    if info[0] == [0, 0, 0, 0, 0]:
        df = DataFrame({'Hour': ['NO SWD'], 'SWD time': [0], 'SWD time percentage': [0], 'SWD amount': [0], "mean SD": [0], "mean CERT": [0]})
    else:
        #print('Hour', hours, '\nHours', [row[0] for row in info], '\nSWD time', list(hourly_time), '\nSWD time percentage', [round(elem, 2) for elem in list(hourly_counts.iloc)], '\nSWD amount', [row[1] for row in info], "\nmean SD", [row[2] for row in info], "\nmean CERT", [row[3] for row in info])
        #print('Hour', len(hours), '\nHours', len([row[0] for row in info]), '\nSWD time', len(list(hourly_time)), '\nSWD time percentage', len([round(elem, 2) for elem in list(hourly_counts.iloc)]), '\nSWD amount', len([row[1] for row in info]), "\nmean SD", len([row[2] for row in info]), "\nmean CERT", len([row[3] for row in info]))
        df = DataFrame({'Hour': hours, 'SWD time': list(hourly_time), 'SWD time percentage': [round(elem, 2) for elem in list(hourly_counts.iloc)], 'SWD amount': [row[1] for row in info], "mean SD": [row[2] for row in info], "mean CERT": [row[3] for row in info]})
    with pd.ExcelWriter(output[:-9] + warning_filtered + '.xlsx', engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Properties', index=False)
        swds.to_excel(writer, sheet_name='SWDs')
        misc.to_excel(writer, sheet_name='Misc', index=False)

    #file_out.close()
    print('Excel file created succesfully:', output[:-9] + '.xlsx')

def extract_stats (key):
    #if not os.path.exists(os.getcwd() + '/results/CSV/'):
    #    os.makedirs(os.getcwd() + '/results/CSV/')
    for filename in os.listdir(os.getcwd() + '/results/MESD/'):
        if '.txt' in filename:
            describe_csv(os.getcwd() + '/results/MESD/' + filename, os.getcwd() + '/results/' + filename, key) #not CSV
            os.remove(os.getcwd() + '/results/MESD/' + filename)
    os.rmdir(os.getcwd() + '/results/MESD/')
    return 0


if __name__ == '__main__':
    extract_stats({'Bins': 'half', 'Channel': 0})
