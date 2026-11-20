import os, sys
import cv2
import glob

from pathlib import Path

import magneKits as go


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
            cv2.destroyAllWindows()

            edge_h = int(input('Crop at what "%" of original height from top edge? Input a number between 0-100:'))
            length_h = int(input('Crop how much "%" of original height? Input a number between 0-100:'))
            if edge_h + length_h > 100:
                length_h = 100 - edge_h
                print('Adjusted cropping height to fit within image frame.')
            top = int(h*0.01*edge_h)
            bottom = int(h*0.01*(edge_h+length_h))
            edge_w = int(input('Crop at what "%" of original width from left edge? Input a number between 0-100:'))
            length_w = int(input('Crop how much "%" of original width? Input a number between 0-100:'))
            if edge_w + length_w > 100:
                length_w = 100 - edge_w
                print('Adjusted cropping width to fit within image frame.')
            left = int(w*0.01*edge_w)  
            right = int(w*0.01*(edge_w+length_w))                   

            cv2.namedWindow('This is the cropped image. Press any key ...', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('This is the cropped image. Press any key ...', 600, 600)  # Resize the window to fit the screen
            cv2.imshow('This is the cropped image. Press any key ...', frame[top:bottom, left:right]) # Could use try-except here to ease the customer experience with erroneous inputs
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            cropped = input('Was the cropping good? (y/n) :')

        print('Cropped frame size is (h x w):', bottom-top, 'x', right-left)

        return top, bottom, left, right

lines = []    # to store line coordinates to find origin
line = ((0, 0), (0, 0))

lines.append(line)

