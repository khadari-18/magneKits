import os 
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

# from scipy.ndimage import gaussian_filter1d
datasets = []   # list of (shear_rate, eta) arrays
n = 0
check = 'n'
while check != 'y': 
    n += 1
    data_folder = input("Enter data folder name (e.g., G:\\Research Data\\) : ")           # result saving path  
    data_file = input("Enter excel file name (include extension) : ")
    data_path = os.path.join(data_folder, data_file)

    sr_col = f"shear rate(1/s) set{n}"
    eta_col = f"eta(Pa*s) set{n}"
    try:
        temp = pd.read_excel(data_path, sheet_name='Viscosity Datapoints', engine='openpyxl')
        temp = temp[['shear rate(1/s)', 'eta(Pa*s)']].dropna()
        temp = temp.sort_values('shear rate(1/s)')   # np.interp needs sorted x
        datasets.append((temp['shear rate(1/s)'].to_numpy(), temp['eta(Pa*s)'].to_numpy()))
    
    except Exception as e:
        print("Error opening file.")

    check = input("Done selecting files? (y/n) : ")

sr_min = min(sr.min() for sr, _ in datasets)    # sr is read as the first column
sr_max = max(sr.max() for sr, _ in datasets)

sr_interp = np.logspace(np.log10(sr_min), np.log10(sr_max), num=20)
eta_list = []
for sr_data, eta_data in datasets:
    # mask points outside each set's range so they don't distort the average
    f = interp1d(sr_data, eta_data, kind='linear', fill_value='extrapolate')    # handles extrapolation as well
    # eta = np.interp(sr_interp, sr_data, eta_data, left=np.nan, right=np.nan)
    eta_list.append(f(sr_interp))

eta_interp = np.nanmean(np.asarray(eta_list), axis=0)   # unpacks each interpolated dataset separately and avergaes them 

eta_df = pd.DataFrame({'shear rate(1/s)': sr_interp, 'eta(Pa*s)': eta_interp})

results_folder = input("Enter results folder : ")
results_file = input("Enter output excel name : ")
results_path = os.path.join(results_folder, results_file)

with pd.ExcelWriter(results_path, engine='openpyxl', mode='w') as writer:
    eta_df.to_excel(writer, index=False, sheet_name='Avg Viscosity')

print("Task completed.")
    