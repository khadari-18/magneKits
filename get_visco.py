import os 
import pandas as pd
import cv2
import numpy as np
import matplotlib.pyplot as plt
# from scipy.interpolate import CubicSpline
# from scipy.interpolate import PchipInterpolator
import trackpy as tp

# from scipy.ndimage import gaussian_filter1d

data_folder = '/Volumes/Data Drive/RESEARCH-UNC/Backup - D drive/WORK/Processed data/uRheo/3DFM/Viscosity/Mucus+HA/2026-09-25/0925_calib/2pctM+0.3pctHA/Set4'           # result saving path  
source_file = "visc_20260925_2HBE_0.3HA_5v30s_4.xlsx"               # name of the excel file containing tracked data
results_file = "results_visc_20260925_2HBE_0.3HA_5v30s_4new.xlsx"                # name of the excel file to save results
out_img = "img.jpg"  

m = -2.81                                                          # F-d fitting parameter
c = -51.5                                                          # F-d fitting parameter

source_path = os.path.join(data_folder, source_file)
results_path = os.path.join(data_folder, results_file)
image_path = os.path.join(data_folder, out_img)

frame = cv2.imread(image_path)  
duration = float(input("Enter the duration of the video in seconds (check vid file name) : "))          
total_frames = int(input("Enter number of frames in the video (check frame no. of 'Raw Tracked') : ")) 
fps = total_frames / duration
print(f"fps is: {fps}")


def get_pole_axis(image): 
    def click_event(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # print(f"Clicked at: x={x}, y={y}")
            # Save the coordinates to a file
            param["point"] = (x,y)

    def capture_point(window_title):
        cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)        
        cv2.resizeWindow(window_title, 800, 600)
        container = {"point": None}
        while container["point"] is None:
            cv2.imshow(window_title, image)
            cv2.setMouseCallback(window_title, click_event, param=container)
            key = cv2.waitKey(20) & 0xFF
            if key == 27:  # Esc to cancel
                break
        cv2.destroyWindow(window_title)

        return container["point"]

    poleTip = capture_point("Click on the approximate pole tip in the image.")
    axis_ref = capture_point("Click on an approximate origin of the magnetic field.")

    return poleTip, axis_ref

def drop_groups(t, frame):
    fig , ax = plt.subplots(figsize=(8, 6))
    tp.plot_traj(t, label = True, superimpose=frame, ax=ax)                               
    plt.show()
    # Brushing up based on cutoff 
    check = 'n'
    while check != 'y':
        fig , ax = plt.subplots(figsize=(8, 6))
        bad_groups = input('Enter the particles IDs that are to be dropped (separated by spaces or tabs):')
        bad_groups = [int(x) for x in bad_groups.split()]
        t1 = t[~t['particle'].isin(bad_groups)]   
        tp.plot_traj(t1, label = True, superimpose=frame, ax=ax)                               
        plt.show()
        check = input('Satisfied with the selected particles? (y/n) :')

    return t1 

def set_cutoff(t, frame):
    fig , ax = plt.subplots(figsize=(8, 6))
    tp.plot_traj(t, label = True, superimpose=frame, ax=ax)                               
    plt.show()
    # Brushing up based on cutoff 
    check = 'n'
    while check != 'y':
        fig , ax = plt.subplots(figsize=(8, 6))
        l_cutoff = int(input('Enter distance from origin below which tracking will be excluded (in px):'))
        u_cutoff = int(input(f'Enter distance above which tracking will be excluded (in px, the image is {frame.shape[0]}x{frame.shape[1]} :'))
        t1 = t[t['distances'].between(l_cutoff, u_cutoff)]   
        tp.plot_traj(t1, label = True, superimpose=frame, ax=ax)                               
        plt.show()
        check = input('Is the cutoff acceptable? (y/n) :')

    return t1 

df = pd.read_excel(source_path, sheet_name='Filtered Tracked', engine='openpyxl')

# Finding origin 
poleTip, axisRef = get_pole_axis(frame)
dx = -poleTip[0]+axisRef[0]     # Tip is the reference
dy = -poleTip[1]+axisRef[1]     # Tip is the reference
theta = np.arctan2(dy,dx)       # angle between +ve horizontal axis and the tip-to-origin axis 
print(f"theta: {theta*180/np.pi}")
tip_to_org = float(input("Enter the distance between tip to origin in pixels (check calibration file): ")) 
origin = np.zeros(2)
origin[0] = poleTip[0] + tip_to_org*np.cos(theta)
origin[1] = poleTip[1] + tip_to_org*np.sin(theta)
origin = origin.astype(int)
window_name = "Close window to continue ..."
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, 800, 600) 
cv2.circle(frame, (origin[0], origin[1]), radius=10, color=(255, 255, 255), thickness=-1)
cv2.putText(frame, 'Origin', (origin[0]+50, origin[1]), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 10)
while True:
    cv2.imshow(window_name, frame)
    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC key to exit
        break
cv2.destroyWindow(window_name)
  
df = drop_groups(df, frame)

dia_um = pd.read_excel(source_path, sheet_name='Parameters', engine='openpyxl')['dia_um'].iloc[0]
dia_px = pd.read_excel(source_path, sheet_name='Parameters', engine='openpyxl')['dia_px'].iloc[0]                                         

df['distances'] = 0.0                                                                       # adding a new column for distances from origin
df['distances'] = ((df['x'] - origin[0])**2 + (df['y'] - origin[1])**2)**0.5  

df = set_cutoff(df, frame)                                                        # filtering data within the cutoff distance from origin

df = df.rename(columns={'frame':'time(s)'})
df['time(s)'] = df['time(s)'] / fps                                       
df = df.sort_values(by=['time(s)'], ascending=[True])                                           # sorting data by time if not already sorted

df = df.rename(columns={'distances':'distances(um)'})
df['distances(um)'] = df['distances(um)'] * (dia_um / dia_px) 

df = df.rename(columns={'displacement':'displacement(um)'})
df['displacement(um)'] = df['displacement(um)'] * (dia_um / dia_px) 
                                      
df['forces(pN)'] = 0.0
df['forces(pN)'] = 1e12 * np.exp(m * np.log((df['distances(um)']) * 1e-6) + c)

# # Viscosity by Stoke's law: eta = F(t) / 3 pi d v(t)
df['velocity(um/s)'] = 0.0
df['shear rate(1/s)'] = 0.0
df['eta(Pa*s)'] = 0.0

df['dt(s)'] = df.groupby('particle')['time(s)'].diff()
df['dt(s)'] = df['dt(s)'].fillna(1/fps)

df.loc[df['dt(s)'] <= 0, 'dt(s)'] = np.nan

df['velocity(um/s)'] = df['displacement(um)'] / df['dt(s)']
df['shear rate(1/s)'] = df['velocity(um/s)'] / dia_um
df['eta(Pa*s)'] = df['forces(pN)'] / (3 * np.pi * dia_um * df['velocity(um/s)']) 

df.replace([np.inf, -np.inf], np.nan, inplace=True)
df.loc[df['velocity(um/s)'] <= 0, 'eta(Pa*s)'] = np.nan

# brushing up for invalid values
valid = df.dropna(subset=['shear rate(1/s)', 'eta(Pa*s)']).copy()       
valid = valid[valid['shear rate(1/s)'] >= 0]                            
# ranges = valid.groupby('particle')['shear rate(1/s)'].agg(['min', 'max'])

# sr_min = ranges['min'].max()
# sr_max = ranges['max'].min()

sr_min = valid['shear rate(1/s)'].min()
sr_max = valid['shear rate(1/s)'].max()

sr_interp = np.logspace(np.log10(sr_min), np.log10(sr_max), 100)
eta_list = []

for PID, particle_df in valid.groupby('particle'):
    particle_df = particle_df.sort_values('shear rate(1/s)')

    # Average duplicate shear-rate measurements before interpolation
    particle_df = (
        particle_df.groupby('shear rate(1/s)', as_index=False)['eta(Pa*s)'].mean()
    )
    eta_list.append(np.interp(sr_interp, particle_df['shear rate(1/s)'], particle_df['eta(Pa*s)']))
    # cs = CubicSpline(particle_df['shear rate(1/s)'], particle_df['eta(Pa*s)'])    
    # eta_list.append(cs(sr_interp))
    # pchip = PchipInterpolator(particle_df['shear rate(1/s)'], particle_df['eta(Pa*s)'])    
    # eta_list.append(pchip(sr_interp))

eta_interp = np.nanmean(np.asarray(eta_list), axis=0)       # this line unpacks the list for different sets and nanmean then averages them 

valid_df = pd.DataFrame({'shear rate(1/s)': valid['shear rate(1/s)'], 'eta(Pa*s)': valid['eta(Pa*s)']})
eta_df = pd.DataFrame({'shear rate(1/s)': sr_interp, 'eta(Pa*s)': eta_interp})

with pd.ExcelWriter(results_path, engine='openpyxl', mode='w') as writer:
    df.to_excel(writer, index=False, sheet_name='Raw Data', engine='openpyxl')
    eta_df.to_excel(writer, index=False, sheet_name='Viscosity Interpolated', engine='openpyxl')
    valid_df.to_excel(writer, index=False, sheet_name='Viscosity Datapoints', engine='openpyxl')
        

print("Analysis completed.")


