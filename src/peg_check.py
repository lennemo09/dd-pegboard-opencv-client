import cv2 as cv
import numpy as np
import threading

def checkIntensity(greyscale_frame,coords,intensity_threshold):
    _, mask2 = cv.threshold(greyscale_frame, thresh=180, maxval=255, type=cv.THRESH_BINARY)
    img_thresh_gray = cv.bitwise_and(greyscale_frame, mask2)
    selection = greyscale_frame[coords[1]:coords[0], coords[3]:coords[2]]
    intensity = np.mean(selection)
    if intensity>intensity_threshold:
        return True
    else:
        return False
