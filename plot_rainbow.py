import matplotlib.pyplot as plt
import cv2
from matplotlib.patches import Circle, Wedge
import os

from numpy import cos, sin

img_path = 'D:\\WORK\\Processed data\\uRheo\\3DFM\\Compliance\\20260824\\4pctOsHBE\\Load1_1\\img.jpg'
save_dir = os.path.dirname(img_path)
save_path = os.path.join(save_dir, 'rainbow_overlay.png')


# Load your background image
img = cv2.imread(img_path)
img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Get image dimensions
height, width = img.shape

# Define center and radii based on your image dimensions (in pixels)
center = (211.25, 1638.11)
radii = [
    423.2390897,
    466.8879962,
    524.3601431,
    604.4147463,
    725.917256,
    939.7437881,
    1461.113238
]

colors = ['violet', 'indigo', 'blue', 'green', 'yellow', 'orange', 'red']
labels = ['350', '300', '250', '200', '150', '100', '50pN']

fig, ax = plt.subplots(figsize=(10, 10))

# 1. Display the background image first
ax.imshow(img, cmap='gray', origin='upper')

# 2. Overlay the semicircles
# theta1 and theta2 define the arc angles (in degrees)
# 0° = right, 90° = bottom, 180° = left, 270° = top
theta1 = 270      # Start angle
theta2 = 10    # End angle (this makes a semicircle)

counter = 0
for r, color, label in zip(radii, colors, labels):
    # Create semicircular wedge (arc with thickness)
    wedge = Wedge(center, r, theta1, theta2, 
                  width=3,  # thickness of the arc
                  color=color, fill=False, linewidth=10, alpha=0.6)
    ax.add_patch(wedge)

    # # 2. Overlay the concentric rainbow circles
    # for r, color, label in zip(radii, colors, labels):
    #     # Set fill=False and use lw (linewidth) to make transparent ring arches if desired
    #     circle = Circle(center, r, color=color, fill=False, linewidth=15)
    #     ax.add_patch(circle)

    if counter % 2 == 0:
        k = 1
    else:
        k = 1
    # Position text on the left side of each semicircle
    ax.text(center[0] - 4.25*r/5, center[1] + r/10, label, 
        color='white', fontsize=15, ha='right', va='center', 
        weight='bold')
    # Position text on the right side of each semicircle
    ax.text(center[0] + r*cos(45), center[1] - k*r*sin(45), label, 
        color='white', fontsize=15, ha='left', va='center', 
        weight='bold')    
 
    counter += 1

# 3. Mark the center point
# Option 1: Simple marker
ax.plot(center[0], center[1], 'r+', markersize=15, markeredgewidth=2)

# Set limits based on image dimensions (in pixels)
ax.set_xlim(0, width)
ax.set_ylim(height, 0)  # Inverted for image coordinates (0,0 at top-left)

# Keep aspect ratio matching the image
ax.set_aspect('equal')
ax.axis('off')  # Optional: hide axes for cleaner look
plt.title('Force Calibration Overlay', fontsize=14, pad=20)
plt.tight_layout()
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.show()