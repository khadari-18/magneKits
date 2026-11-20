import cv2
import os
import trackpy as tp
import pandas as pd


row_limit = 1048576 - 1

data_folder = input("Enter the path to the data folder(e.g., G:\\RESEARCH-UNC\\): ")            # video and signal data path
excel_name = input("Enter the excel data file name (include extension): ")                      # update output excel file name here
img_name = "img.jpg"                                                                            # update output image file name here

excel_path = os.path.join(data_folder, excel_name)
image_path = os.path.join(data_folder, img_name)

def fix_background_drift_in_data(data, frame):

    # This is a velocity (= displacement/time) vector based approach. The actual vector = measured vector - drift vector. The time (1/fps) is cosntant for all vector, thus ignored in the calculations. 
    # A nonlinear approach can be tried: First moving average of drifts in zero volt windows calculated. Then it can be spanned along all frames. This will subtract drifts based on time. Spatial variation could be also considered. Clean experiments help.  
    # Drift is usually larger away from the pole thus a drift(distance from pole) approach can be tried as well.
    corrected = data.copy()                                 # Create a copy of the original data to avoid modifying it directly
    velocity_drift_x = []
    velocity_drift_y = []

    is_zero = corrected['voltages(V)'].eq(0)                # Create a boolean series for zero voltage for the entire volatge column
    run_id = is_zero.ne(is_zero.shift()).cumsum()           # Create a unique identifier for each contiguous block of zero voltage

    for _, zero_v_data in corrected[is_zero].groupby(run_id[is_zero]):                        # _ can be replaced by group number
        drift_0V = tp.compute_drift(zero_v_data, pos_columns=['x', 'y'], smoothing = 20)      # Compute drift using trackpy
        velocity_drift_x.append(drift_0V['x'].diff().mean())                                  # Mean drift in x-direction for this zero voltage block, mean() ignores NaN at diff() first row 
        velocity_drift_y.append(drift_0V['y'].diff().mean())                                  # Mean drift in y-direction for this zero voltage block, mean() ignores NaN at diff() first row

    velocity_drift_mean_x = sum(velocity_drift_x) / len(velocity_drift_x)                     # Overall mean drift in x-direction
    velocity_drift_mean_y = sum(velocity_drift_y) / len(velocity_drift_y)                     # Overall mean drift in y-direction

    print(f"Mean drift velocity in x-direction: {velocity_drift_mean_x}, Mean drift velocity in y-direction: {velocity_drift_mean_y}")

    # velocity_drift_mean_x, velocity_drift_mean_y = -150, -30  # Initialize drift velocities
    try:
        tp.plot_traj(data, label=True, superimpose=frame, title='Before synching')
    except Exception as e:
        print(f"Error occurred while plotting before synching: {e}")

    velocity_measured_x = corrected['x'].diff().copy()                                         # Calculate the measured velocity in x-direction                                          
    velocity_measured_y = corrected['y'].diff().copy()                                           

    corrected.iloc[1:-1, corrected.columns.get_loc('x')] = corrected.iloc[0:-2, corrected.columns.get_loc('x')].values + velocity_measured_x.iloc[1:-1].values - velocity_drift_mean_x
    corrected.iloc[1:-1, corrected.columns.get_loc('y')] = corrected.iloc[0:-2, corrected.columns.get_loc('y')].values + velocity_measured_y.iloc[1:-1].values - velocity_drift_mean_y

    try:
        tp.plot_traj(corrected, label=True, superimpose=frame, title='After synching')
    except Exception as e:
        print(f"Error occurred while plotting after synching: {e}")

    corrected = corrected.drop(columns=['frame'], errors='ignore')  # Remove the displacement column if it exists
    corrected['dx_measured'] = velocity_measured_x
    corrected['dy_measured'] = velocity_measured_y

    return corrected, (velocity_drift_mean_x, velocity_drift_mean_y)


excel_file = pd.ExcelFile(excel_path, engine='openpyxl')
tracked_sheets = [sheet for sheet in excel_file.sheet_names if sheet.startswith('Synched Tracked')]
data = pd.concat([excel_file.parse(sheet) for sheet in tracked_sheets], ignore_index=True)
parameters = pd.read_excel(excel_path, sheet_name='Parameters', engine='openpyxl')  
frame = cv2.imread(image_path)              

data, drift_avg = fix_background_drift_in_data(data, frame)                                             
parameters[['drift_x', 'drift_y']] = [drift_avg[0], drift_avg[1]]

with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer: 
# # Save tracked data, splitting into multiple sheets if it exceeds the row limit
    if len(data) <= row_limit:
        data.to_excel(writer, index=False, sheet_name='Synched-no-drift', engine='openpyxl')         # saving the tracked data to excel
    else:
        num_chunks = (len(data) + row_limit - 1) // row_limit
        for i in range(num_chunks):
            chunk = data.iloc[i * row_limit : (i + 1) * row_limit]
            sheet_name = f'Synched-no-drift {i+1}' 
            chunk.to_excel(writer, index=False, sheet_name=sheet_name)
with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer: 
    parameters.to_excel(writer, index=False, sheet_name='Parameters', engine='openpyxl')            # saving the tracking parameters to excel
