import cv2
import numpy as np
from globals import *

def checkIntensity(greyscale_frame,coords,intensity_threshold):
    greyscale_frame = cv2.resize(greyscale_frame,(VIDEO_W, VIDEO_H))
    _, mask2 = cv2.threshold(greyscale_frame, thresh=180, maxval=255, type=cv2.THRESH_BINARY)
    img_thresh_gray = cv2.bitwise_and(greyscale_frame, mask2)
    selection = img_thresh_gray[coords[1]:coords[0], coords[3]:coords[2]]
    intensity = np.mean(selection)
    print(f"{selection.shape},{coords[1]}:{coords[0]}, {coords[3]}:{coords[2]}",intensity)
    if intensity>intensity_threshold:
        return True
    else:
        return False
