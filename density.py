#version 001
import re
import os
import pandas as pd
import additional_metrics
import pyedflib
from pandas import DataFrame
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.plotarea import DataTable
#import datetime

def histogram(total_duration, values, durations_base, writer):
    durations = []
    for time in durations_base:
        durations.append(sum(x * int(t) for x, t in zip([3600, 60, 1], time.split(":"))))
    values.append(0)
    #print(total_duration)
    #print(sum(durations))
    durations.append(total_duration - sum(durations))
    sheet_name = 'Histogram'
    capped_values = [min(v, 10) for v in values]
    
    # Create DataFrame
    df = pd.DataFrame({'Value': capped_values, 'Duration': durations})
    
    # Group by Value and sum durations
    grouped = df.groupby('Value', as_index=False)['Duration'].sum()
    
    # Calculate percentage of total duration
    grouped['Percentage'] = my_formatted_list = [round(elem, 2) for elem in ((grouped['Duration'] / total_duration) * 100)]
    
    # Ensure all values from 1 to 10 are present
    full_range = pd.DataFrame({'Value': range(0, 11)})
    grouped = full_range.merge(grouped, on='Value', how='left').fillna(0)
    
    # Create chart object
    chart = BarChart()
    chart.type = "col"
    chart.style = 10
    chart.title = "Percentage of Total Duration by Cert"
    chart.legend = None
    #chart.x_axis = TextAxis(delete=True)
    chart.x_axis.title = None
    chart.y_axis.title = "Percentage (%)"
    chart.x_axis.delete = False
    chart.y_axis.delete = False
    chart.plot_area.dTable = DataTable()
    chart.plot_area.dTable.showHorzBorder = True
    chart.plot_area.dTable.showVertBorder = True
    #chart.plot_area.dTable.showOutline = True
    chart.plot_area.dTable.showKeys = True


    grouped.to_excel(writer, sheet_name=sheet_name, index=False)
    
    worksheet = writer.sheets[sheet_name]
    
    # Add chart to worksheet
    data_ref = Reference(worksheet, min_col=3, min_row=3, max_row=12)  # Percentage column
    categories_ref = Reference(worksheet, min_col=1, min_row=3, max_row=12)  # Value column
    
    chart.add_data(data_ref, titles_from_data=False)
    chart.set_categories(categories_ref)
    
    # Add chart to worksheet
    worksheet.add_chart(chart, "E2")
    #worksheet.to_excel(writer, sheet_name=sheet_name, index = False)

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

def time_between_old(num1, bool1, num2, bool2, key):
    if num2 < num1:
        num2 += 24 #to account for possible midnight holes
    # Initialize an empty list to store our pairs
    pairs = []
    if bool1 == 0 and key['Bins'] == 'half' and num1 != num2:
        pairs.append([num1, '30'])
    # Loop through the numeric range
    for num in range(num1+1, num2):
        pairs.append([num%24, '00'])
        if key['Bins'] == 'half':
            pairs.append([num%24, 3])
    if bool2 == 30 and key['Bins'] == 'half' and num1 != num2:
        pairs.append([num2%24, '00'])
    return pairs

def time_between(start_hour, start_minute, end_hour, end_minute, key):
    output = []
    start_hour = 23 if start_hour == -1 else start_hour #to check if it's "just before recording
    start_time = datetime(1900, 1, start_hour//24+1, start_hour%24, start_minute)
    if end_hour < start_hour or (end_hour == start_hour and start_minute > end_minute):
        end_time = datetime(1900, 1, end_hour//24+2, end_hour%24, end_minute)
    else:
        end_time = datetime(1900, 1, end_hour//24+1, end_hour%24, end_minute)
    if key['Bins'] == 'hour':
        current = start_time.replace(minute=0, second=0)
    else:
        current = start_time
    #print(start_time, end_time)
    while current < end_time:
        #print(current)
        if key['Bins'] == 'hour':
            if current.hour != start_time.hour or current.minute == 0:  # Skip start time unless it's on the hour
                output.append(current.strftime("%H:%M"))
            current += timedelta(hours=1)    
        if key['Bins'] == 'half': 
            if current.minute in [0, 30]:
                output.append(current.strftime("%H:%M"))
            current += timedelta(minutes=30)   
        if key['Bins'] == 'quarter':
            if current.minute in [0, 15, 30, 45]:
                output.append(current.strftime("%H:%M"))
            current += timedelta(minutes=15)
    #print(output[1:])
    return output[1:]


def parse_timestamp_pairs(pairs, day_long, start_time="00:00:00", end_time="23:59:59"):
    # Define the overall time range
    start_datetime = datetime.strptime(start_time, "%H:%M:%S") #MAKE A CHECK ITS SAME OR DIFFERENT DAYS!!
    end_datetime = datetime.strptime(end_time, "%H:%M:%S")
    #print(end_time, start_time)

    # Initialize the time series with zeros
    time_series = [0] * ((end_datetime - start_datetime).seconds + 1 + day_long*86400) 
    start_next_day, end_next_day = 0, 0
    old_end, old_start = 0, 0
    # Process each pair
    for pair in pairs:
        start, end = pair
        #print(start, end)
        start_datetime_pair = datetime.strptime(start, "%H:%M:%S")
        end_datetime_pair = datetime.strptime(end, "%H:%M:%S")
        #print(start_datetime_pair, start_datetime)

        # Calculate the indices for the start and end times of the pair
        ###OLD
        start_index = int((start_datetime_pair - start_datetime).total_seconds())
        #if start_index < 0:
        #    start_index = 86400 + start_index
        end_index = int((end_datetime_pair - start_datetime).total_seconds())
        #if end_index < 0:
        #    end_index = 86400 + end_index
        if start_index < old_start:
            start_next_day += 1
        if end_index < old_end:
            end_next_day += 1
        old_start = start_index
        old_end = end_index
        start_index += 86400 * start_next_day
        end_index += 86400 * end_next_day
        

        # Mark the covered seconds
        #print (len(time_series), start_index, end_index)
        for i in range(start_index, end_index + 1):
            time_series[i] = 1

    return time_series

#this functions finds timestamps and parses their stats to corr. hours
def find_sd (filename, output, start, key): #also returns SWDs for excel
    file = open(filename, 'r').read()
    lines = re.findall(r'\d{2}:\d{2}:\d{2}-\d{2}:\d{2}:\d{2} SD \d+.\d+ CERT \d+', file)
    result = []
    excel = []
    #count, sd, cert = 0, 0, 0
    old_hour = int(re.match(r'\d+', start)[0]) - 1#'999' #to fail
    if key['Bins'] == 'quarters':    
        old_minute = int(re.search(r':\d+:', start)[0][1:3])//15*15 #2
    else:    
        old_minute = int(re.search(r':\d+:', start)[0][1:3])//30*30 #2

    if key['Bins'] == 'half':
        if old_minute == 30:
            old_minute = 0
            old_hour += 1
        else:
            old_minute = 30
    if key['Bins'] == 'quarter':
        if old_minute == 45:
            old_minute = 0
            old_hour += 1
        else:
            old_minute += 45
    count = 0
    #print(lines)
    for line in lines:
        x = line.split()
        excel.append(x)
        hour = int(re.match(r'\d+', sum_times(start, x[0][:8]))[0])
        if key['Bins'] == 'quarter':
            minutes = int(re.search(r':\d+:', sum_times(start, x[0][:8]))[0][1:3])//15*15 #same but for 0-15...
        if key['Bins'] == 'half':
            minutes = int(re.search(r':\d+:', sum_times(start, x[0][:8]))[0][1:3])//30*30 #acutally checks if it is 0-30 or 30-59, as 0-1 respectively
        else:
            minutes = 0
            
        
        if hour == old_hour and (key['Bins'] == 'hour' or minutes == old_minute):
            sd += float(x[2])
            count += 1
            cert += float(x[4])
        else:
            if count != 0:
                result.append([str(old_hour) + ':' + str(old_minute // 10) + str(old_minute % 10), count, round(sd/count, 3), round(cert/count, 1)]) #str(old_minute // 10) + '0'
                #print(result[-1])

                
            #else:
            #    result.append([old_hour + ':' + str(old_minute // 10) + '0', count, 0, 0])
            for skipped in time_between(old_hour, old_minute, hour, minutes, key):
                result.append([skipped, 0, 0, 0])
            old_hour = hour
            old_minute = minutes
            sd = float(x[2])
            count = 1
            cert = float(x[4])
        #print(x)
    df = DataFrame({'Start': [row[0][:8] for row in excel], 'End':[row[0][9:] for row in excel], 'SD': [float(row[2]) for row in excel], 'Cert': [int(row[4]) for row in excel], 'Duration': [sum_times(row[0][9:], row[0][:8], minus = True) for row in excel]})
    #df['Duration'] = (pd.to_datetime(df['End'], format = "%H:%M:%S") - pd.to_datetime(df['Start'], format = "%H:%M:%S")).astype(str).map(lambda x: x[7:])
    if key['Astronomical']:
        df['Start'] = (pd.to_datetime(df['Start'], format = "%H:%M:%S") + datetime.strptime(start, "%H:%M:%S")).astype(str).map(lambda x: x[7:])
        df['End'] = (pd.to_datetime(df['End'], format = "%H:%M:%S") + datetime.strptime(start, "%H:%M:%S")).astype(str).map(lambda x: x[7:])                                                                     
    if count == 0: #in case of an empty file
        result.append([0, 0, 0, 0, 0, 0, 0])
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
    if key['Astronomical']:
        start = times[0]
    else:
        start = '00:00:00'
    filtered = [int(i) for i in (re.search(r'\d+VS\d+', file)[0].split('VS'))]
    bad_time = int(re.search(r'y: \d+', file)[0].split(' ')[-1])
    dur = int(re.search(r'Duration: \d+', file)[0].split(' ')[-1])#total duration
    #print ('BT: ', bad_time)
    #print(filtered)
    misc = DataFrame({'Filtered': filtered[0], 'Passed': filtered[1], 'Artefacts Duration': bad_time}, index = [0])#, '% of filtered': round(int(filtered[0])/(int(filtered[0])+int(filtered[1]))*100, 3)})
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
    #print(index)
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
        if real_start_hour.total_seconds():
            hourly_counts.iloc[0] = hourly_counts.iloc[0] * 3600 / real_start_hour.total_seconds()
        if real_end_hour.total_seconds():
            hourly_counts.iloc[-1] = hourly_counts.iloc[-1] * 3600 / ((real_end_hour.total_seconds() - bad_time)) #REMOVE
        hours = hourly_counts.axes[0].hour
    if key['Bins'] == 'half':
        hourly_time = series.resample('30min').sum()
        hourly_counts = hourly_time / 1800
        real_start_hour = datetime.strptime(start, "%H:%M:%S") - datetime.strptime(f'{start[0]}{start[1]}:{int(start[3:5])//30*30}:00', "%H:%M:%S")
        #print (real_start_hour)
        real_end_hour = datetime.strptime(times[-1], "%H:%M:%S") - datetime.strptime(f'{times[-1][0]}{times[-1][1]}:{int(times[-1][3:5])//30*30}:00', "%H:%M:%S") #not safe
        #print (real_end_hour)
        if real_start_hour.total_seconds():
            hourly_counts.iloc[0] = hourly_counts.iloc[0] * 1800 / real_start_hour.total_seconds()
        if real_end_hour.total_seconds():
            hourly_counts.iloc[-1] = hourly_counts.iloc[-1] * 1800 / ((real_end_hour.total_seconds()))
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
    if key['Bins'] == 'quarter': #DOESNT WORK WITH ASTRO
        hourly_time = series.resample('15min', origin = 'start').sum()
        #print(series)
        #print(hourly_time)
        hourly_counts = hourly_time / 900
        real_start_hour = datetime.strptime(start, "%H:%M:%S") - datetime.strptime(f'{start[0]}{start[1]}:{int(start[3:5])//15*15}:00', "%H:%M:%S")
        #print (real_start_hour)
        real_end_hour = datetime.strptime(times[-1], "%H:%M:%S") - datetime.strptime(f'{times[-1][0]}{times[-1][1]}:{int(times[-1][3:5])//15*15}:00', "%H:%M:%S") #not safe
        #print (real_end_hour)
        if real_start_hour.total_seconds():
            hourly_counts.iloc[0] = hourly_counts.iloc[0] * 900 / real_start_hour.total_seconds()
        if real_end_hour.total_seconds():
            hourly_counts.iloc[-1] = hourly_counts.iloc[-1] * 900 / ((real_end_hour.total_seconds()))
        hours_bad = hourly_counts.axes[0].hour
        if len(hours_bad) < 2:
            hours = hours_bad
        else:
            hours = []#check for astronomy if starts at quarter
            quarter = 3
            for hour in hours_bad:
                quarter = (quarter+1)%4
                quarter_min = 15*quarter if quarter else '00'
                hours.append(f'{hour}:{quarter_min}')
    if info[0] == [0, 0, 0, 0, 0, 0, 0]: #TO BE REMOVED
        df = DataFrame({'Hour': ['NO SWD'], 'SWD time': [0], 'SWD time percentage': [0], 'SWD amount': [0], "mean SD": [0], "mean CERT": [0], "mean SWD": [0], "Max SWD": [0]})
    else:
        #('Hour', hours, '\nHours', [row[0] for row in info], '\nSWD time', list(hourly_time), '\nSWD time percentage', [round(elem, 2) for elem in list(hourly_counts.iloc)], '\nSWD amount', [row[1] for row in info], "\nmean SD", [row[2] for row in info], "\nmean CERT", [row[3] for row in info])
        #print('Hour', len(hours), '\nHours', len([row[0] for row in info]), '\nSWD time', len(list(hourly_time)), '\nSWD time percentage', len([round(elem, 2) for elem in list(hourly_counts.iloc)]), '\nSWD amount', len([row[1] for row in info]), "\nmean SD", len([row[2] for row in info]), "\nmean CERT", len([row[3] for row in info]))
        times_2 = [sum_times(a, times[0]) for a in hours]
        df = DataFrame({'Time': times_2, 'Hour': hours, 'SWD time': list(hourly_time), 'SWD time percentage': [round(elem, 2) for elem in list(hourly_counts.iloc)], 'SWD amount': [row[1] for row in info], "mean SD": [row[2] for row in info], "mean CERT": [row[3] for row in info]})
        ###TEST###

        df['Mean SWD'] = df['SWD time'] / df['SWD amount']
        df['Mean SWD'] = df['Mean SWD'].fillna(0)
        df['Mean SWD'] = df['Mean SWD'].round(decimals=2)
        time_priods = [list(row) for row in zip(*[swds['Start'].tolist(), swds['End'].tolist()])]
        dict_periods = additional_metrics.check_periods(time_priods, len(df), start, key)
        periods = list(dict_periods.values())
        df['Max SWD'] = periods
    with pd.ExcelWriter(output[:-9] + warning_filtered + '.xlsx', engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Properties', index=False)
        swds.to_excel(writer, sheet_name='SWDs')
        misc.to_excel(writer, sheet_name='Misc', index=False)
        #print(bad_time)
        #print(real_end_hour)
        #print(real_end_hour.total_seconds())
        if real_end_hour.total_seconds():
            chart_page = histogram(dur - bad_time, swds['Cert'].tolist(), swds['Duration'].tolist(), writer)        

    #file_out.close()
    print('Excel file created succesfully:', output[:-9] + '.xlsx')
    #print(datetime.now())

def extract_stats (key):
    #if not os.path.exists(os.getcwd() + '/results/CSV/'):
    #    os.makedirs(os.getcwd() + '/results/CSV/')
    for filename in os.listdir(os.getcwd() + '/results/MESD/'):
        if '.txt' in filename:
            describe_csv(os.getcwd() + '/results/MESD/' + filename, key['Folder'] + '/' + filename, key) #not CSV
    return 0


if __name__ == '__main__':
    extract_stats({'Bins': 'hour', 'SR': 1000, 'verbose': 3, 'Channel': 0, 'Rename': 1, 'Sleep': 0,  'Astronomical': 0, 'Marker': 1})
