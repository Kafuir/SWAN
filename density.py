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
    #print (total.days)
    #print(total)
    return re.findall(r'\d+:\d{2}:\d{2}', str(total))[0]




def parse_timestamp_pairs(pairs, start_time="00:00:00", end_time="23:59:59"):
    # Define the overall time range
    start_datetime = datetime.strptime(start_time, "%H:%M:%S")
    end_datetime = datetime.strptime(end_time, "%H:%M:%S")

    # Initialize the time series with zeros
    time_series = [0] * ((end_datetime - start_datetime).seconds + 1)

    # Process each pair
    for pair in pairs:
        start, end = pair
        start_datetime_pair = datetime.strptime(start, "%H:%M:%S")
        end_datetime_pair = datetime.strptime(end, "%H:%M:%S")

        # Calculate the indices for the start and end times of the pair
        start_index = int((start_datetime_pair - start_datetime).total_seconds())
        end_index = int((end_datetime_pair - start_datetime).total_seconds())

        # Mark the covered seconds
        for i in range(start_index, end_index + 1):
            time_series[i] = 1

    return time_series

def find_sd (filename, start):
    file = open(filename, 'r').read()
    lines = re.findall(r'\d{2}:\d{2}:\d{2}-\d{2}:\d{2}:\d{2} SD 0.\d{3} CERT \d{1}', file)
    result = []
    #count, sd, cert = 0, 0, 0
    old_hour = '999' #to fail
    for line in lines:
        x = line.split()
        hour = re.match(r'\d+', sum_times(start, x[0][:8]))[0]
        #print (x)
        if hour == old_hour:
            sd += float(x[2])
            count += 1
            cert += float(x[4])
        else:
            if old_hour != '999':
                result.append([old_hour, count, round(sd/count, 3), round(cert/count, 1)])
            old_hour = hour
            sd = float(x[2])
            count = 1
            cert = float(x[4])
    result.append([old_hour, count, round(sd/count, 3), round(cert/count, 1)])
    #print (result)
    return result
            
    
def describe_csv (filename, output): 
    file = open(filename, 'r').read()
    times = re.findall(r'\d{2}:\d{2}:\d{2}', file)

    ##severity = re.findall(r'certainty: [\d+]')
    start = times[0]
    info = find_sd(filename, start)
    timestamp_pairs = []
    for x in range(1, len(times), 2):
        timestamp_pairs.append((sum_times(times[x], start), sum_times(times[x+1], start)))

    # Example usage
    #timestamp_pairs = [("16:27:53", "16:28:01"), ("17:45:32", "17:46:10")]
    time_series = parse_timestamp_pairs(timestamp_pairs, start_time = start, end_time = sum_times(start, times[-1]))

    # Create a datetime index starting from a specific time (e.g., midnight)
    #start_time = "00:00:00"#datetime.now()  # Or any specific start time
    index = pd.date_range(start=start, periods=len(time_series), freq='s')

    # Convert the list to a pandas Series with the datetime index
    series = pd.Series(time_series, index=index)

    # Resample the series to hourly frequency and count the occurrences of '1'
    hourly_counts = series.resample('h').sum() / 3600
    real_start_hour = datetime.strptime(start, "%H:%M:%S") - datetime.strptime(f'{start[0]}{start[1]}:00:00', "%H:%M:%S")
    print (real_start_hour)
    real_end_hour = datetime.strptime(times[-1], "%H:%M:%S") - datetime.strptime(f'{times[-1][0]}{times[-1][1]}:00:00', "%H:%M:%S") #not safe
    print (real_end_hour)
    hourly_counts[0] = hourly_counts[0] * 3600 / real_start_hour.total_seconds()
    hourly_counts[-1] = hourly_counts[-1] * 3600 / (3600-(real_end_hour.total_seconds()))
    hours = hourly_counts.axes[0].hour
    count = 0
    file_out = open(output[:-3] + 'csv', 'w')
    file_out.write('Hour; SWD time percentage; SWD amount; mean SD; mean CERT\n')
    for number in range(len(hours)):
        x = f'{hours[number]}; {round(hourly_counts.iloc[number], 2)}; {info[count][1]}; {info[count][2]}; {info[count][3]}\n'
        #print(x)
        file_out.write(x)
        count += 1 #ugly but effective)

    file_out.close()
    print('CSV file created succesfully:', filename[:-3] + 'csv')
    return 0

def extract_stats ():
    if not os.path.exists(os.getcwd() + '/results/CSV/'):
        os.makedirs(os.getcwd() + '/results/CSV/')
    for filename in os.listdir(os.getcwd() + '/results/MESD/'):
        if '.txt' in filename:
            describe_csv(os.getcwd() + '/results/MESD/' + filename, os.getcwd() + '/results/CSV/' + filename)

if __name__ == '__main__':
    extract_stats()

#df = DataFrame({'Hour': hours, 'SWD time percentage': hourly_counts.iloc, 'SWD amount': info[:][0], "mean SD": info[:][2], "mean CERT": info[:][3]})
#df.to_excel('test.xlsx', sheet_name='sheet1', index=False)
