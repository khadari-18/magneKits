import cv2
import os
import pandas as pd


row_limit = 1048576 - 1

data_folder = input("Enter the path to the data folder(e.g., G:\\RESEARCH-UNC\\): ")            # video and signal data path
excel_name = input("Enter the excel data file name (include extension): ")                      # update output excel file name here
img_name = "img.jpg"                                                                            # update output image file name here

excel_path = os.path.join(data_folder, excel_name)
image_path = os.path.join(data_folder, img_name)


def get_pole_tip(image, origin): 
    poleTip = [] 
    def click_event(event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONDOWN:
            # print(f"Clicked at: x={x}, y={y}")
            # Save the coordinates to a file
            poleTip.append(x)
            poleTip.append(y)

    origin = int(origin[0]), int(origin[1]) # rounding off to nearest pixel
    window_name = "Click on the image to select the tip of the cantilever and then press esc to proceed."
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 800, 600) 
    cv2.circle(image, (origin[0], origin[1]), radius=10, color=(255, 255, 255), thickness=-1)
    cv2.putText(image, 'Origin', (origin[0]+50, origin[1]), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 10)
    while True:
        cv2.imshow(window_name, image)
        cv2.setMouseCallback(window_name, click_event)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC key to exit
            break
    cv2.destroyAllWindows()

    return tuple(poleTip)


parameters = pd.read_excel(excel_path, sheet_name='Parameters', engine='openpyxl')
origin = pd.read_excel(excel_path, sheet_name='Parameters', engine='openpyxl')[['origin_x', 'origin_y']].iloc[0].values
print("Origin: ", origin)
frame = cv2.imread(image_path)

poleTip = get_pole_tip(frame, origin)
if len(poleTip) > 2:
    poleTip = (poleTip[-2], poleTip[-1])                                # taking the last two clicks as the pole tip coordinates
    print("Multiple points detected, taking the last click as the pole tip.")

print("Pole Tip Coordinates: ", poleTip)
parameters[['poleTip_x', 'poleTip_y']] = (poleTip[0], poleTip[1])

with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    parameters.to_excel(writer, index=False, sheet_name='Parameters', engine='openpyxl')  # saving the tracking parameters to excel

