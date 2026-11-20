import cv2
import os
import matplotlib.pyplot as plt
import pandas as pd
import trackpy as tp

from scipy.io import loadmat

row_limit = 1048576 - 1

data_folder = input("Enter the path to the data folder(e.g., G:\\RESEARCH-UNC\\): ")           # video and signal data path
results_folder = input("Enter the path to the output folder(e.g., D:\\WORK\\): ")              # result saving path  
vid_name = input("Enter the video/image file name (include extension): ")                      # update video/image file name(s) here (e.g., vid.mp4 or img_%04d.jpg)
mat_name = input("Enter the matlab file name (include extension): ")                           # update .mat file name here
out_excel = input("What should be the output excel file name (include extension): ")           # update output excel file name here
out_img = "img.jpg"                                                                            # update output image file name here

vid_path = os.path.join(data_folder, vid_name)
mat_path = os.path.join(data_folder, mat_name)
excel_path = os.path.join(results_folder, out_excel)
image_path = os.path.join(results_folder, out_img)


# Context manager to suppress print statements temporarily.
def get_raw_tracking_data(vid_path, mat_path):
    # function to set cropping parameters
    def crop(frame):
        h = frame.shape[0]
        w = frame.shape[1]
        print('Original frame size is (h x w):', h, 'x', w)
        cropped = 'n'
        while cropped != 'y':
            cv2.namedWindow('This is the original size. Press any key ...', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('This is the original size. Press any key ...', 800, 600)  # Resize the window to fit the screen
            cv2.imshow('This is the original size. Press any key ...', frame)
            cv2.waitKey(0)  
            cv2.destroyWindow('This is the original size. Press any key ...')

            edge_h = int(input('Crop at what "%" of original height from top edge? Input a number between 0-100:'))
            length_h = int(input('Crop (keep) how much "%" of original height? Input a number between 0-100:'))
            if edge_h + length_h > 100:
                length_h = 100 - edge_h
                print('Adjusted cropping height to fit within image frame.')
            top = int(h*0.01*edge_h)
            bottom = int(h*0.01*(edge_h+length_h))
            edge_w = int(input('Crop at what "%" of original width from left edge? Input a number between 0-100:'))
            length_w = int(input('Crop (keep) how much "%" of original width? Input a number between 0-100:'))
            if edge_w + length_w > 100:
                length_w = 100 - edge_w
                print('Adjusted cropping width to fit within image frame.')
            left = int(w*0.01*edge_w)  
            right = int(w*0.01*(edge_w+length_w))                   

            cv2.namedWindow('This is the cropped image. Press any key ...', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('This is the cropped image. Press any key ...', 800, 600)  # Resize the window to fit the screen
            cv2.imshow('This is the cropped image. Press any key ...', frame[top:bottom, left:right]) # Could use try-except here to ease the customer experience with erroneous inputs
            cv2.waitKey(0)
            cv2.destroyWindow('This is the cropped image. Press any key ...')
            cropped = input('Was the cropping good? (y/n) :')

        print('Cropped frame size is (h x w):', bottom-top, 'x', right-left)

        return top, bottom, left, right

    def bead_check(frame):      # checking for bead size and min_mass, the color density parameter, interactively    
        check = 'n'
        while check != 'y':
            plt.close('all')  # Close any existing plots to avoid overlap
            search_px = int(input('What should be the search size of the bead in pixels?: '))
            min_mass = int(input('What is the minimum mass for trackpy locate function?: '))
            noise = int(input('What is the background noise size for trackpy locate function?: '))
            f = tp.locate(frame, diameter=search_px, minmass=min_mass, invert=True, noise_size=noise)  # separation is the minimum distance between two particles.
            tp.annotate(f, frame)
            f['mass'].hist()                    # set minmass=0 and look for the 2nd peak in the histogram
            plt.title('Mass histogram of detected beads')
            plt.xlabel('Mass')
            plt.ylabel('Frequency')
            plt.show()
            check = input('Was the bead detection good? (y/n) :')

        return search_px, min_mass

    # READING VIDEO/IMAGE DATA FROM FILE
    cap = cv2.VideoCapture(vid_path)                           # can load either video or images. for images, use cv2.capImages flag 
    if not cap.isOpened():
        raise ValueError('Could not open video/image file')

    sensor_ratio = float(input('What is the sensor um/pixel ratio of the camera (e.g., 3.45um/px for the GS3-U3-51S5 camera)?: '))
    mag = float(input('What is the magnification (number) of the lens used (e.g., 20x, 40x, 60x)?: '))
    um_per_px = sensor_ratio / mag
    bead_um = float(input('What is the bead diameter in microns (e.g., 2.8um)?: '))
    bead_px = round(bead_um / um_per_px) + 3                                        # overestimating by 3px for product variations  
    print(f"Estimated bead size in pixels is: {bead_px} px")    

    frames=[]                                                   # a temp list to store video frames         
    counter = 0
    while True:                                                 # reading frames from the cap object  
        returned, frame = cap.read()
        if not returned:
            break
        
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)         # Convert BGR to grayscale for consistency with matplotlib
        # frame = cv2.bitwise_not(frame)                        # Invert colors for better visibility of beads                
        if counter == 0:
            counter += 1
            top, bottom, left, right = crop(frame)              # set cropping parameters to keep only area near the pole in images
            search_px, min_mass = bead_check(frame)             # set bead size and min_mass for trackpy locate function 
        
        frame = frame[top:bottom, left:right]                   # cropping the frame
        frames.append(frame)                                    # storing frame to the list
    cap.release()                                               # releasing the VideoCapture object
    
    f = tp.batch(frames, diameter = search_px, minmass = min_mass, invert=True, processes=0) # process <= 1 multiprocessing disabled
    t = tp.link(f, search_range=2*search_px, adaptive_stop=search_px, adaptive_step=0.9, memory=0)  # there'll be 14 step breakdown of linking subnets before stopping if search range yields large calculations. 

    try:    
        # READING VOLTAGE AND TIME FROM .mat FILE
        matfile_path = os.path.join(mat_path)
        voltmat_data = loadmat(matfile_path)

        voltages = voltmat_data['voltages'][0]                      # voltage values in volts stored in a row vector in the .mat file
        intervals = voltmat_data['pulse_widths'][0]                 # pulse widths in seconds stored in a row vector in the .mat file
        num_runs  = voltmat_data['NSequences'][0][0] + 1              # adding 1 assuming the first run was not counted in NRepeats

        parameters = pd.DataFrame({'sensor_ratio': [sensor_ratio], 'mag': [mag], 'um_per_px': [um_per_px], 'dia_um': [bead_um], 'dia_px': [bead_px], 'search_px': [search_px], 'min_mass': [min_mass]}) # storing the parameters in a dataframe to save to excel later
        signal = pd.DataFrame({'voltages(V)': voltages, 'intervals(s)': intervals}) # storing the signal in a dataframe to save to excel later
        signal.loc[0, 'num_sigcycles'] = num_runs
    except KeyError as e:
        print(f"Error: Encountered while handling .mat file - {e}")
        parameters = pd.DataFrame({'sensor_ratio': [], 'mag': [], 'um_per_px': [], 'dia_um': [], 'dia_px': [], 'search_px': [], 'min_mass': []}) # storing the parameters in a dataframe to save to excel later
        signal = pd.DataFrame({'voltages(V)': [], 'intervals(s)': [], 'num_sigcycles': []}) # storing the signal in a dataframe to save to excel later

    return t, parameters, signal, frames[-1]




# BLOCK 1: TRACK VIDEO/IMAGES

data, parameters, signal, frame = get_raw_tracking_data(vid_path, mat_path)              # for image sequences, use "img_%04.jpg" for names with 000# format. Set overestimated bead dia. Set minmass=0 and find a 2nd peak in the histogram to set the minmass. 

with pd.ExcelWriter(excel_path, engine='openpyxl', mode='w') as writer: 
# Save tracked data, splitting into multiple sheets if it exceeds the row limit
    if len(data) <= row_limit:
        data.to_excel(writer, index=False, sheet_name='Raw Tracked', engine='openpyxl')     # saving the tracked data to excel
    else:
        num_chunks = (len(data) + row_limit - 1) // row_limit
        for i in range(num_chunks):
            chunk = data.iloc[i * row_limit : (i + 1) * row_limit]
            sheet_name = f'Raw Tracked {i+1}' 
            chunk.to_excel(writer, index=False, sheet_name=sheet_name)
with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a') as writer: 
    parameters.to_excel(writer, index=False, sheet_name='Parameters', engine='openpyxl')    # saving the tracking parameters to excel
with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a') as writer:
    signal.to_excel(writer, index=False, sheet_name='Signal', engine='openpyxl')            # saving the signal parameters to excel

cv2.imwrite(image_path, frame) 




