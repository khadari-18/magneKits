import cv2
import os
import matplotlib.pyplot as plt
import pandas as pd
import trackpy as tp


row_limit = 1048576 - 1

data_folder = input("Enter the path to the data folder(e.g., G:\\RESEARCH-UNC\\): ")            # video and signal data path
excel_name = input("Enter the excel data file name (include extension): ")                      # update output excel file name here
img_name = "img.jpg"                                                                            # update output image file name here

excel_path = os.path.join(data_folder, excel_name)
image_path = os.path.join(data_folder, img_name)


def synch_data_with_signal(data, signal, frame):

    def plot_func(*args):
        num_args = len(args)
        if num_args == 1:
            data_PID = args[0]
            plt.figure(figsize=(10, 5))
            plt.plot(data_PID['time(s)'], data_PID['displacement'], label= f'PID: {PID}', color="blue")
            plt.xlabel('Time (s)')
            plt.ylabel('Displacement')
            plt.legend()
            plt.show()

        elif num_args == 2:
            data_PID, flat_idx = args[0], args[1]
            plt.figure(figsize=(10, 5))
            plt.plot(data_PID['time(s)'], data_PID['displacement'], label= f'PID: {PID}', color="blue")
            plt.plot(data_PID.iloc[flat_idx]['time(s)'], data_PID.iloc[flat_idx]['displacement'], "x", label="Flats", color="red", markersize=10, mew=2)
            plt.xlabel('Time (s)')
            plt.ylabel('Displacement')
            plt.legend()
            plt.show()

        return None

    # READING SIGNAL INFORMATION
    voltages = signal['voltages(V)'].values
    intervals = signal['intervals(s)'].values
    num_runs = int(signal['num_sigcycles'].values[0])
    print(f"Signal has {len(voltages)} voltage values and {len(intervals)} pulse widths, repeated for {num_runs} runs.")

    # THIS PART CHECKS FOR FPS FOR VIDEO DATA WHICH SHOULD CORRESPOND TO SIGNAL BLOCK PERIODS (THUS DISPLACEMENT PEAKS). JUST NEED THE FPS VALUE HERE. SYNCHING DONE LATER.
    fps = 60                                                        # default frame rate in Hz, will be changed by user input
    part_check = 'y'
    while part_check != 'n': 
        PID = data['particle'].sample(n=1).values[0]                # Sample a random particle ID
        data_PID = data[data['particle'] == PID].copy()             # Important: use .copy() to avoid SettingWithCopyWarning
        data_PID = data_PID.reset_index(drop=True)                  # Reset index for proper plotting

        data_PID['time(s)'] = data_PID['frame'] /fps                  # Convert frame numbers to time in seconds, note the column name is still unchanged
        plot_func(data_PID)                                         # Plot the displacement vs time for the sampled particle

        fps_check = input('Is this particle good for the fps analysis (proceed if there are at least 5 clean peaks) ? (y/n): ')
        if fps_check == 'y':
            fps_check = 'n'
            while fps_check != 'y':
                fps = float(input(f'What should be the fps in Hz? (current fps = {fps}):'))
                data_PID['time(s)'] = data_PID['frame'] / fps          # Convert frame numbers to time in seconds, note the column name is still unchanged
                t0 = float(input(f"Where to set the starting time of signal here (t0 in data = {data_PID['time(s)'].min()})?: "))
                flat_idx = []
                for i in range(5):
                    t_i = t0 + sum(intervals) * i
                    idx_i = (data_PID['time(s)'] - t_i).abs().idxmin()
                    flat_idx.append(idx_i)

                plot_func(data_PID, flat_idx)                       # Plot the displacement vs time for the sampled particle with flats marked
                fps_check = input('Does the fps look good (Try placing crosses on peaks)? (y/n): ')
            part_check = input('Check another particle for fps? (y/n): ')

    data['time(s)'] = data['frame']                                     # Creating a 'time' column 
    data['time(s)'] = data['frame'] / fps                               # Adding time values with final fps, should go from 0s to total signal time

    # THIS PART COUPLES/SYNCHS THE DISPLACEMENTS WITH THE SIGNAL BLOCKS.
    good_PIDs = data['particle'].unique().tolist()              # Initialize good_PIDs with all unique particle IDs
    number_blcks_PID = []
    t_zero_PID = []

    for PID in data['particle'].unique():
        data_PID = data[data['particle']==PID].copy()               # Important: use .copy()
        data_PID = data_PID.reset_index(drop=True)                  # Reset index for proper plotting
        plot_func(data_PID)                                         # Plot the displacement vs time for the sampled particle

        part_check = input('Keep this particle? (y/n): ')
        if part_check == 'y':
            para_check = 'n'
            while para_check != 'y':
                nblck = int(input(f"How many good signal blocks are there for this PID? (2 if unsure): "))
                nflt = nblck + 1                                    # Number of 0v flats correspondingly
                t0 = float(input(f"Where to set the starting time of the signal here (t0 in data = {data_PID['time(s)'].min()}?: "))
                flat_idx = []
                for i in range(nflt):
                    t_i = t0 + sum(intervals) * i 
                    idx_i = (data_PID['time(s)'] - t_i).abs().idxmin()
                    flat_idx.append(idx_i)

                plot_func(data_PID, flat_idx)                       # Plot the displacement vs time for the sampled particle with flats marked
                para_check = input('Was the synching good? (y/n): ')
                if para_check == 'y': 
                    number_blcks_PID.append(nblck)
                    t_zero_PID.append(t0)

        elif part_check == 'n':
            good_PIDs.remove(PID) 

    sync_list = []

    for PID in good_PIDs:
        data_PID = data[data['particle'] == PID].copy()             # Important: use .copy()
        trunc_data = data_PID[(data_PID['time(s)'] >= t_zero_PID[good_PIDs.index(PID)]) & (data_PID['time(s)'] <= t_zero_PID[good_PIDs.index(PID)] * number_blcks_PID[good_PIDs.index(PID)] * sum(intervals))] # trimming data to the signal duration
        trunc_data['time(s)'] = trunc_data['time(s)'] - trunc_data['time(s)'].iloc[0]  # shifting time to start from zero for each particle
        sync_list.append(trunc_data)

    try:
        tp.plot_traj(data, label=True, superimpose=frame, title='Before synching')
    except Exception as e:
        print(f"Error occurred while plotting before synching: {e}")

    data = pd.concat(sync_list, ignore_index=True)  # pd.concat overwrites the original data with the sliced synched data 
    print(f"Synched data contains {len(data)} rows for {data['particle'].nunique()} particles")

    try:
        tp.plot_traj(data, label=True, superimpose=frame, title='After synching')
    except Exception as e:
        print(f"Error occurred while plotting after synching: {e}")

    # data = data.drop(columns=['frame'], errors='ignore')        # drift calc needs frame column      
    data = data.sort_values(by=['time(s)', 'particle'], ascending=[True, True])     # sorting data by time and then PID to add corresponding voltages

    # THIS PART ADDS VOLTAGE VALUES AT SYNCHED SPOTS
    data['voltages(V)'] = 0.0                                     # adding voltage column, to be updated next 
    entire_volt_list = voltages.tolist() * num_runs               # creating the entire voltage list from the unit block for the number of runs
    entire_pulsewidth_list = intervals.tolist() * num_runs        # creating the entire pulsewidth list from the unit block for the number of runs
    counter = 0                                                   # for counting row numbers
    for i in range(len(entire_volt_list)):                               # inputting the corresponding voltage values 
        time_covered = sum(entire_pulsewidth_list[0:i+1]) 
        while counter < len(data['time(s)']) and data.iloc[counter]['time(s)'] <= time_covered: # while time value in dataframe column is less than covered time
            data.loc[counter, 'voltages(V)'] = entire_volt_list[i]
            counter += 1

    return data, fps



excel_file = pd.ExcelFile(excel_path, engine='openpyxl')
tracked_sheets = [sheet for sheet in excel_file.sheet_names if sheet.startswith('Filtered Tracked')]
data = pd.concat([excel_file.parse(sheet) for sheet in tracked_sheets], ignore_index=True)
parameters = pd.read_excel(excel_path, sheet_name='Parameters', engine='openpyxl')
signal = pd.read_excel(excel_path, sheet_name='Signal', engine='openpyxl')    
frame = cv2.imread(image_path)              
                                      
data, fps = synch_data_with_signal(data, signal, frame)         # try putting crosses on the peaks of the displacements for better synching                                    
parameters['fps'] = fps

with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer: 
# # Save tracked data, splitting into multiple sheets if it exceeds the row limit
    if len(data) <= row_limit:
        data.to_excel(writer, index=False, sheet_name='Synched Tracked', engine='openpyxl')         # saving the tracked data to excel
    else:
        num_chunks = (len(data) + row_limit - 1) // row_limit
        for i in range(num_chunks):
            chunk = data.iloc[i * row_limit : (i + 1) * row_limit]
            sheet_name = f'Synched Tracked {i+1}' 
            chunk.to_excel(writer, index=False, sheet_name=sheet_name)
with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer: 
    parameters.to_excel(writer, index=False, sheet_name='Parameters', engine='openpyxl')  # saving the tracking parameters to excel


