import cv2
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import trackpy as tp

from pandas import DataFrame


row_limit = 1048576 - 1

data_folder = input("Enter the path to the data folder(e.g., G:\\RESEARCH-UNC\\): ")            # video and signal data path
excel_name = input("Enter the excel data file name (include extension): ")                      # update output excel file name here
img_name = "img.jpg"                                                                            # update output image file name here

excel_path = os.path.join(data_folder, excel_name)
image_path = os.path.join(data_folder, img_name)


def brushup_raw_data(t, frame):

    # Brushing up based on trajectory life and stage 
    check = 'n'
    while check != 'y':
        fig , ax = plt.subplots(figsize=(8, 6))
        stub_t = int(input('What must be the minimum life of the tracked beads(in number of frames)?:'))
        ecc = float(input('What is the eccentricity threshold for the beads (0 for perfectly round beads)?:'))        
        t1 = tp.filter_stubs(t, stub_t)                         # helps with anomalous short-lived trajectories and trackpy errors 
        t1 = t1[(t1['ecc'] < ecc)]                              # ecc also helps filter out frames of beads after they reached the pole-tip  
        # tp.annotate(t1[t1['frame'] == 0], frame, ax=ax)
        tp.plot_traj(t1, label = True, superimpose=frame, ax=ax)                               
        plt.show()
        check = input('Does the tracking look good? (y/n) :')

    t = t1
    t.index.name = None    
    t = t.loc[:,['frame','particle','y','x']] 

    # Brushing up based on trajectory length 
    check = 'n'
    while check != 'y':
        fig , ax = plt.subplots(figsize=(8, 6))
        # ax.clear()  # Clear the axes to avoid overlapping plots
        stub_d = float(input('What must be the minimum distance of the tracked beads(in percentage of frame width )? Input between 0 and 1:'))        
        id_list = [] 
        for PID in t['particle'].unique():                          # going by each PID in the dataframe
            data_PID = t[t['particle']==PID]          

            y1 = data_PID.iloc[0, 2]                                # consecutive locations     
            x1 = data_PID.iloc[0, 3]
            y2 = data_PID.iloc[-1, 2] 
            x2 = data_PID.iloc[-1, 3]
            if np.sqrt((x2 - x1)**2 + (y2 - y1)**2) > frame.shape[1]*stub_d:  # distance covered filter (based on init and final locations). For 2Msucrose and 2.8um beads, a 0.4 pixel jump expected for each pN force. 
                id_list.append(PID) 
        t1 = t[t['particle'].isin(id_list)]                          # deleting beads that had damped motion or were stuck. 
        # tp.annotate(t1[t1['frame'] == t1['frame'].max()], frame, ax=ax)
        tp.plot_traj(t1, label = True, superimpose=frame, ax=ax)
        plt.show()                             
        check = input('Does the tracking look good? (y/n) :')    
    
    t = t1

    # CALCULATING DISPLACEMENTS AND STORING THEM IN A COLUMN IN THE DATAFRAME
    t = t.sort_values(by=['particle','frame'], ascending=[True, True]) # sorting data by PID and then frame numbers to find particle jumps
    t['displacement'] = 0.0                                     # adding a displacement between consecutive frames to help find jump frames later
    d_list = []                                                 # a temp list to store displacements 
    for PID in t['particle'].unique():                          # going by each PID in the dataframe
        data_PID = t[t['particle']==PID]          
        rows_PID = len(data_PID) 
        if rows_PID > 1:
            for index in range(rows_PID):                       # Note python indices start from 0 and range subtracts last number 
                if index == 0: 
                    d_list.append(0.0)                          # first frame displacement is zero
                else:
                    # print('PID, index :', PID, index)
                    y1 = data_PID.iloc[index-1, 2]              # consecutive locations     
                    x1 = data_PID.iloc[index-1, 3]
                    y2 = data_PID.iloc[index, 2] 
                    x2 = data_PID.iloc[index, 3]  
                    d_list.append(np.sqrt((x2 - x1)**2 + (y2 - y1)**2)) # distance logging

        elif rows_PID == 1:
            d_list.append(0.0)                                  # if only one frame for a particle, no displacement

    t.iloc[:, 4] = d_list                                       # adding displacement values to the dataframe        
    t = t.sort_values(by=['frame','particle'], ascending= [True, True]) # sorting data back by frame no. first 

    parameters2 = pd.DataFrame([[stub_t, stub_d, ecc]], columns=['stub_t', 'stub_d', 'ecc'])
    return t, parameters2




excel_file = pd.ExcelFile(excel_path, engine='openpyxl')
tracked_sheets = [sheet for sheet in excel_file.sheet_names if sheet.startswith('Raw Tracked')]
data = pd.concat([excel_file.parse(sheet) for sheet in tracked_sheets], ignore_index=True)
parameters = pd.read_excel(excel_path, sheet_name='Parameters', engine='openpyxl') 
frame = cv2.imread(image_path)              

data, parameters2 = brushup_raw_data(data, frame)                                         # Filters data, adds displacements, converts frmaes to times 

new_cols = ['stub_t', 'stub_d', 'ecc']
for col in new_cols:
    if col not in parameters.columns:
        parameters[col] = pd.NA

parameters[new_cols] = parameters2.iloc[0][new_cols].to_numpy()

with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer: 
# # Save tracked data, splitting into multiple sheets if it exceeds the row limit
    if len(data) <= row_limit:
        data.to_excel(writer, index=False, sheet_name='Filtered Tracked', engine='openpyxl')         # saving the tracked data to excel
    else:
        num_chunks = (len(data) + row_limit - 1) // row_limit
        for i in range(num_chunks):
            chunk = data.iloc[i * row_limit : (i + 1) * row_limit]
            sheet_name = f'Filtered Tracked {i+1}' 
            chunk.to_excel(writer, index=False, sheet_name=sheet_name)
with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer: 
    parameters.to_excel(writer, index=False, sheet_name='Parameters', engine='openpyxl')  # saving the tracking parameters to excel

