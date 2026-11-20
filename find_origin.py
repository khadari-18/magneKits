import os
import numpy as np
import pandas as pd


row_limit = 1048576 - 1

data_folder = input("Enter the path to the data folder(e.g., G:\\RESEARCH-UNC\\): ")            # video and signal data path
excel_name = input("Enter the excel data file name (include extension): ")                      # update output excel file name here

excel_path = os.path.join(data_folder, excel_name)


def find_origin_from_lines(lines):
    """
    Finds the best-fit origin (point) from a set of radially distributed lines
    using a least-squares solution.

    Args:
        lines (list of tuples): Each tuple contains the start and end
                                points of a line, e.g., ((x1, y1), (x2, y2)).

    Returns:
        tuple: The (x, y) coordinates of the best-fit origin.
    """
    if len(lines) < 2:
        print("At least two lines are required to find an origin.")
        return None  # At least two lines are required.

    # Build the system of linear equations A * p = b
    # where p is the point (x, y) we want to find.
    A = []
    b = []

    for line in lines:
        (x2, y2), (x1, y1) = line

        # Calculate the direction vector of the line.
        dx = x2 - x1
        dy = y2 - y1

        # Compute the Hessian normal form of the line.
        # This is a robust way to handle vertical lines.
        # The equation of the line is a*x + b*y + c = 0.
        a = dy
        b_coeff = -dx
        c = -dy * x1 + dx * y1

        # Append to our matrix and vector.
        A.append([a, b_coeff])
        b.append(-c)

    A_matrix = np.array(A)
    b_vector = np.array(b)

    # Solve the overdetermined system of linear equations using least squares.
    # The result is the point (x, y) that minimizes the sum of squared distances.
    try:
        origin, _, _, _  = np.linalg.lstsq(A_matrix, b_vector, rcond=None)
        return tuple(float(coord) for coord in origin)
    except np.linalg.LinAlgError:
        # Handle case where lines are all parallel or have issues.
        print("Could not find a valid origin.") 
        return None


excel_file = pd.ExcelFile(excel_path, engine='openpyxl')
tracked_sheets = [sheet for sheet in excel_file.sheet_names if sheet.startswith('Filtered Tracked')]
data = pd.concat([excel_file.parse(sheet) for sheet in tracked_sheets], ignore_index=True)
parameters = pd.read_excel(excel_path, sheet_name='Parameters', engine='openpyxl')
# frame = cv2.imread(image_path)

lines = []    
for PID in np.sort(data['particle'].unique()):
    particle_data = data[data['particle'] == PID].copy()                        # data[logic]
    try:
        (y1,x1) = particle_data.iloc[0,[2,3]] 
        (y2,x2) = particle_data.iloc[-1,[2,3]]    
        line = (x2, y2), (x1, y1)
        lines.append(line)
    except:
        print('Could not extract line trajectories of the particle:', PID)
print("Number of lines found:", len(lines))
origin = find_origin_from_lines(lines)                                # Finding the magnetic field origin from the trajectories of the particles (x,y)
print("Origin: ", origin)
parameters[['origin_x', 'origin_y']] = (origin[0], origin[1])

with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    parameters.to_excel(writer, sheet_name='Parameters', index=False)


