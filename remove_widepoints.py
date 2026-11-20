import cv2
import os
import numpy as np
import pandas as pd


row_limit = 1048576 - 1

data_folder = input("Enter the path to the data folder(e.g., G:\\RESEARCH-UNC\\): ")            # video and signal data path
excel_name = input("Enter the excel data file name (include extension): ")                      # update output excel file name here
img_name = "img.jpg"                                                                            # update output image file name here

excel_path = os.path.join(data_folder, excel_name)
image_path = os.path.join(data_folder, img_name)

def delete_wide_angled_points(df, parameters):
    """
    Deletes points from a DataFrame that have angles with origin and poletip axis wider than the specified threshold.

    Args:
        df (DataFrame): DataFrame containing 'x', 'y', and 'frame' columns.
        parameters (DataFrame): DataFrame containing 'origin_x', 'origin_y', 'poleTip_x', 'poleTip_y', and 'angle_threshold' columns.
    """
    origin = parameters[['origin_x', 'origin_y']].iloc[0].values
    poletip = parameters[['poleTip_x', 'poleTip_y']].iloc[0].values

    angle_threshold = float(input('Enter the angle threshold in degrees (e.g., 30): '))  # User-defined angle threshold

    vec_axis =  np.array(poletip) - np.array(origin)

    df_narrow = []
    for _, row in df.iterrows():
        vec_point = np.array([row['x'], row['y']]) - np.array(origin)
        cos_theta = np.dot(vec_point, vec_axis) / (np.linalg.norm(vec_point) * np.linalg.norm(vec_axis))
        theta = np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0)))               
        if theta <= angle_threshold:
            df_narrow.append(row)

    if len(df_narrow) != 0:
        df_narrow = pd.DataFrame(df_narrow, columns=['time(s)','particle','y','x','displacement','voltages(V)'])
    else:
        raise ValueError("All points were deleted; no points remain within the specified angle threshold.")
    
    print('Particle left after angle filtering:', df_narrow['particle'].nunique())

    return df_narrow, angle_threshold


data = pd.read_excel(excel_path, sheet_name='Synched Tracked', engine='openpyxl')
parameters = pd.read_excel(excel_path, sheet_name='Parameters', engine='openpyxl')
frame = cv2.imread(image_path)

data, angle_threshold = delete_wide_angled_points(data, parameters)  # delete wide angle particles if needed
parameters['angle_threshold'] = angle_threshold

with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    data.to_excel(writer, index=False, sheet_name='Angle Filtered Tracked')
