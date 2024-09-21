import tensorflow as tf
import numpy as np

#!!!!!!!!!!!!!
# MArkup + window_average_s/2
#!!!!!!!!!!!!!

def ANN_examples_3channels_markup(imported_data,file_markup,Tmin,Tmax,dt_average_s,window_average_s,input_size) :
 N_average, Time_average, Channel1_mean, Channel1_std, Channel2_mean, Channel2_std, Channel3_mean, Channel3_std, Markup_realization = import_3channels_mean_std_markup(imported_data,file_markup,Tmin,Tmax,dt_average_s,window_average_s)

 ######## Prepare ANN examples :::
 x_test = np.zeros((N_average, input_size))
 x_test[:, 0] = Channel1_mean[:, 0]
 x_test[:, 1] = Channel1_std[:, 0]
 x_test[:, 2] = Channel2_mean[:, 0]
 x_test[:, 3] = Channel2_std[:, 0]
 x_test[:, 4] = Channel3_mean[:, 0]
 x_test[:, 5] = Channel3_std[:, 0]
 y_test = Markup_realization

 return Time_average, x_test, y_test

def import_3channels_mean_std_markup(imported_data,file_markup,Tmin,Tmax,dt_average_s,window_average_s) :

 ######## Import realization :::

 #print("###############################################")
 Channel1 = imported_data[:,1] # np.loadtxt(file_channel1, dtype=float)
 Channel2 = imported_data[:,2] # np.loadtxt(file_channel2, dtype=float)
 Channel3 = imported_data[:,3]  # np.loadtxt(file_channel3, dtype=float)

 #print("Input realization's shape: ", np.shape(Channel1))
 dt_real_s = imported_data[1, 0] - imported_data[0, 0]
 #print("Input realization's step: ", dt_real_s)
 if Tmin==-1 :
  Tmin = imported_data[0, 0]
 if Tmax==-1 :
  Tmax = imported_data[np.size(imported_data, 0) - 1, 0]


 ###### Average characteristics :::
 dt_average_n = int(dt_average_s / dt_real_s)  # in numbers
 window_average_n = int(window_average_s / dt_real_s)  # in numbers
 N_average = int((Tmax - Tmin) / dt_real_s / dt_average_n)  # number of points in new realizations

 Time_average = np.zeros((N_average, 1))
 Channel1_mean = np.zeros((N_average, 1))
 Channel1_std = np.zeros((N_average, 1))
 Channel2_mean = np.zeros((N_average, 1))
 Channel2_std = np.zeros((N_average, 1))
 Channel3_mean = np.zeros((N_average, 1))
 Channel3_std = np.zeros((N_average, 1))

 #print("Average realization's shape: ", np.shape(Channel1_mean))
 #print("###############################################")

 for i in range(N_average):
  Time_average[i, 0] = Tmin + i * dt_average_s
  Channel1_mean[i, 0] = np.mean(Channel1[int(Tmin / dt_real_s + i * dt_average_n):int(Tmin / dt_real_s + i * dt_average_n + window_average_n)])
  Channel1_std[i, 0] = np.std(Channel1[int(Tmin / dt_real_s + i * dt_average_n):int(Tmin / dt_real_s + i * dt_average_n + window_average_n)])
  Channel2_mean[i, 0] = np.mean(Channel2[int(Tmin / dt_real_s + i * dt_average_n):int(Tmin / dt_real_s + i * dt_average_n + window_average_n)])
  Channel2_std[i, 0] = np.std(Channel2[int(Tmin / dt_real_s + i * dt_average_n):int(Tmin / dt_real_s + i * dt_average_n + window_average_n)])
  Channel3_mean[i, 0] = np.mean(Channel3[int(Tmin / dt_real_s + i * dt_average_n):int(Tmin / dt_real_s + i * dt_average_n + window_average_n)])
  Channel3_std[i, 0] = np.std(Channel3[int(Tmin / dt_real_s + i * dt_average_n):int(Tmin / dt_real_s + i * dt_average_n + window_average_n)])

 ############ Normalizations :::
 Channel1_mean = Channel1_mean - np.min(Channel1_mean[:, 0])
 mean_val = np.mean(Channel1_mean[:, 0])
 Channel1_mean = Channel1_mean / mean_val * 0.5
 #
 Channel1_std = Channel1_std - np.min(Channel1_std[:, 0])
 mean_val = np.mean(Channel1_std[:, 0])
 Channel1_std = Channel1_std / mean_val * 0.5
 #
 Channel2_mean = Channel2_mean - np.min(Channel2_mean[:, 0])
 mean_val = np.mean(Channel2_mean[:, 0])
 Channel2_mean = Channel2_mean / mean_val * 0.5
 #
 Channel2_std = Channel2_std - np.min(Channel2_std[:, 0])
 mean_val = np.mean(Channel2_std[:, 0])
 Channel2_std = Channel2_std / mean_val * 0.5
 #
 Channel3_mean = Channel3_mean - np.min(Channel3_mean[:, 0])
 mean_val = np.mean(Channel3_mean[:, 0])
 Channel3_mean = Channel3_mean / mean_val * 0.5
 #
 Channel3_std = Channel3_std - np.min(Channel3_std[:, 0])
 mean_val = np.mean(Channel3_std[:, 0])
 Channel3_std = Channel3_std / mean_val * 0.5

 #
 #print("Импорт файлов и построение среднего и стандартного отклонения прошли успешно")
 ############ Read markup :::
 Markup_realization = np.zeros((N_average, 1))



 return N_average, Time_average, Channel1_mean, Channel1_std, Channel2_mean, Channel2_std, Channel3_mean, Channel3_std, Markup_realization


##############################################
##############################################
########## 2 канала ##########################
##############################################
##############################################

def ANN_examples_2channels_markup(imported_data,file_markup,Tmin,Tmax,dt_average_s,window_average_s,input_size) :
 N_average, Time_average, Channel1_mean, Channel1_std, Channel2_mean, Channel2_std, Markup_realization = import_2channels_mean_std_markup(imported_data,file_markup,Tmin,Tmax,dt_average_s,window_average_s)

 ######## Prepare ANN examples :::
 x_test = np.zeros((N_average, input_size))
 x_test[:, 0] = Channel1_mean[:, 0]
 x_test[:, 1] = Channel1_std[:, 0]
 x_test[:, 2] = Channel2_mean[:, 0]
 x_test[:, 3] = Channel2_std[:, 0]
 y_test = Markup_realization

 return Time_average, x_test, y_test

def import_2channels_mean_std_markup(imported_data,file_markup,Tmin,Tmax,dt_average_s,window_average_s) :

 ######## Import realization :::

 #print("###############################################")
 Channel1 = imported_data[:,1] # np.loadtxt(file_channel1, dtype=float)
 Channel2 = imported_data[:,2] # np.loadtxt(file_channel2, dtype=float)

 #print("Input realization's shape: ", np.shape(Channel1))
 dt_real_s = imported_data[1, 0] - imported_data[0, 0]
 #print("Input realization's step: ", dt_real_s)
 if Tmin==-1 :
  Tmin = imported_data[0, 0]
 if Tmax==-1 :
  Tmax = imported_data[np.size(imported_data, 0) - 1, 0]


 ###### Average characteristics :::
 dt_average_n = int(dt_average_s / dt_real_s)  # in numbers
 window_average_n = int(window_average_s / dt_real_s)  # in numbers
 N_average = int((Tmax - Tmin) / dt_real_s / dt_average_n)  # number of points in new realizations

 Time_average = np.zeros((N_average, 1))
 Channel1_mean = np.zeros((N_average, 1))
 Channel1_std = np.zeros((N_average, 1))
 Channel2_mean = np.zeros((N_average, 1))
 Channel2_std = np.zeros((N_average, 1))

 #print("Average realization's shape: ", np.shape(Channel1_mean))
 #print("###############################################")

 for i in range(N_average):
  Time_average[i, 0] = Tmin + i * dt_average_s
  Channel1_mean[i, 0] = np.mean(Channel1[int(Tmin / dt_real_s + i * dt_average_n):int(Tmin / dt_real_s + i * dt_average_n + window_average_n)])
  Channel1_std[i, 0] = np.std(Channel1[int(Tmin / dt_real_s + i * dt_average_n):int(Tmin / dt_real_s + i * dt_average_n + window_average_n)])
  Channel2_mean[i, 0] = np.mean(Channel2[int(Tmin / dt_real_s + i * dt_average_n):int(Tmin / dt_real_s + i * dt_average_n + window_average_n)])
  Channel2_std[i, 0] = np.std(Channel2[int(Tmin / dt_real_s + i * dt_average_n):int(Tmin / dt_real_s + i * dt_average_n + window_average_n)])

 ############ Normalizations :::
 Channel1_mean = Channel1_mean - np.min(Channel1_mean[:, 0])
 mean_val = np.mean(Channel1_mean[:, 0])
 Channel1_mean = Channel1_mean / mean_val * 0.5
 #
 Channel1_std = Channel1_std - np.min(Channel1_std[:, 0])
 mean_val = np.mean(Channel1_std[:, 0])
 Channel1_std = Channel1_std / mean_val * 0.5
 #
 Channel2_mean = Channel2_mean - np.min(Channel2_mean[:, 0])
 mean_val = np.mean(Channel2_mean[:, 0])
 Channel2_mean = Channel2_mean / mean_val * 0.5
 #
 Channel2_std = Channel2_std - np.min(Channel2_std[:, 0])
 mean_val = np.mean(Channel2_std[:, 0])
 Channel2_std = Channel2_std / mean_val * 0.5
 #
 #print("Импорт файлов и построение среднего и стандартного отклонения прошли успешно")
 ############ Read markup :::
 Markup_realization = np.zeros((N_average, 1))



 return N_average, Time_average, Channel1_mean, Channel1_std, Channel2_mean, Channel2_std, Markup_realization



