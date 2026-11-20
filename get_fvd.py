import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


row_limit = 1048576 - 1

data_folder = input("Enter the path to the data folder(e.g., G:\\RESEARCH-UNC\\): ")            # video and signal data path
excel_name = input("Enter the excel data file name (include extension): ")                      # update output excel file name here
img_name = "img.jpg"                                                                            # update output image file name here

excel_path = os.path.join(data_folder, excel_name)
image_path = os.path.join(data_folder, img_name)


def get_force_vs_distance_relationships(data, signal, parameters): # Assuming data is sorted in time and has ('t', 'x', 'y', 'PID', 'voltage')

    viscosity = float(input('Enter viscosity of the calibration fluid in Pa·s? (e.g., 0.14 for 2.5M sucrose): '))  # 2.5M sucrose viscosity checked creep with Button DHR3
    
    origin = parameters[['origin_x', 'origin_y']].iloc[0].values
    dia_m = parameters['dia_um'].values[0] * 1e-6
    dia_px = parameters['dia_px'].values[0]


    voltages = signal['voltages(V)'].values
    intervals = signal['intervals(s)'].values
    num_runs = int(signal['num_sigcycles'].values[0])

    Coeff_at_Voltages = []   # coefficients (m,c) go into log(force) = m*log(distance) + c
    distance = [] 
    force = []

    # Loop through each voltage value, includes multiple PID and pulsewidth (repeated signal based) information
    ind = 0
    for voltiter in voltages: # voltages are unique in DJC's recommended unit signal block for calibration  
        data_at_fixedvolt = data[data['voltages(V)'] == voltiter].copy() # data at this voltage, includes multiple runs and PIDs, should be sorted by time already     

        # Loop through each run (repeatd signals) for this pulsewidth under this voltage 
        for run in range(num_runs):
            if ind == 0:
                runinit_time = run * sum(intervals)
                runfinal_time = run * sum(intervals) + intervals[0]
            else: 
                runinit_time = run * sum(intervals) + np.cumsum(intervals[0:ind])[-1]
                runfinal_time = run * sum(intervals) + np.cumsum(intervals[0:ind+1])[-1]
            data_at_fixedvolt_fixedrun = data_at_fixedvolt[(data_at_fixedvolt['time(s)'] >= runinit_time) & (data_at_fixedvolt['time(s)'] < runfinal_time)] # data in this voltage interval

            # Loop through each PID available in this pulswidth run under this voltage   
            for PID in data_at_fixedvolt_fixedrun['particle'].unique(): # PID at this time stamp should be unique anyway  
                data_at_fixedvolt_fixedrun_fixedPID = data_at_fixedvolt_fixedrun[data_at_fixedvolt_fixedrun['particle'] == PID].copy() # note this is already sorted by time, has one PID at one voltage only

                dt_for_PID = data_at_fixedvolt_fixedrun_fixedPID.iloc[-1]['time(s)'] - data_at_fixedvolt_fixedrun_fixedPID.iloc[0]['time(s)'] # particle specific interval 
                (y1, x1) = data_at_fixedvolt_fixedrun_fixedPID.iloc[0][['y', 'x']]          # particle location at start of a voltage run
                (y2, x2) = data_at_fixedvolt_fixedrun_fixedPID.iloc[-1][['y', 'x']]         # particle location at end of a voltage run

                distance.append(np.sqrt((origin[0] - np.mean([x1,x2]))**2 + (origin[1] - np.mean([y1,y2]))**2) * dia_m/dia_px)      # distance = origin to midpoint of a particle's trajcetory under this voltage run 
                force.append(3 * np.pi * viscosity * dia_m * np.sqrt((x2 - x1)**2 + (y2 - y1)**2) * (dia_m/dia_px) / dt_for_PID)    # Stokes' drag force calculation. SI units throughout            

        df = pd.DataFrame({'distance': distance, 'force': force})                           # distance and force values 
        check = 'n'
        while check.lower()!='y':
            quant = float(input('Enter lower threshold quantile for data filtering (between 0-1): '))
            threshold = df['force'].quantile(quant)
            filtered_df = df[df['force'] >= threshold]                                      # Filter rows below lower
            filtered_d = filtered_df['distance'].tolist()
            filtered_f = filtered_df['force'].tolist()

            log_d = np.log(filtered_d)
            log_f = np.log(filtered_f)
            m , c = np.polyfit(log_d, log_f, 1)                     # fit log(force)-log(distance) eqn to all the points found at this voltage for all runs to get the coefficients
            
            plt.figure(figsize=(10, 5))
            plt.scatter(filtered_d, filtered_f, label= f'Volts: {voltiter}', color="blue")
            plt.plot(filtered_d, np.exp(m*np.log(filtered_d + c)), label= f"Fit (m= {m:.2f}, c= {c:.2f})", color="red")
            plt.xlabel("distance (m)")
            plt.ylabel("Force (N)")
            plt.legend()
            plt.show()

            check = input('Filtering and fitting good enough? (y/n) :')
        Coeff_at_Voltages.append((voltiter, m, c)) # saving (m,c) coefficients of log-log fit

        # prepare for next iteration 
        distance = []       # emptying 
        force = []          # emptying 
        ind += 1            # for next voltage and pulsewidth in the unit/original signal block
    
    coefficients_df = pd.DataFrame(Coeff_at_Voltages, columns=['voltages(V)', 'm', 'c'])  # dataframe with final coefficients for all voltages

    return coefficients_df


excel_file = pd.ExcelFile(excel_path, engine='openpyxl')
tracked_sheets = [sheet for sheet in excel_file.sheet_names if sheet.startswith('Synched Tracked')]
data = pd.concat([excel_file.parse(sheet) for sheet in tracked_sheets], ignore_index=True)
signal = pd.read_excel(excel_path, sheet_name='Signal', engine='openpyxl')
parameters = pd.read_excel(excel_path, sheet_name='Parameters', engine='openpyxl')
    
coefficients = get_force_vs_distance_relationships(data, signal, parameters)

with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    coefficients.to_excel(writer, index=False, sheet_name='Force vs Distance Coefficients')