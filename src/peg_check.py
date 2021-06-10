import cv2
import numpy as np
from globals import *

def check_intensity(greyscale_frame,coords):
    """
    Checks the intensity of the pixel chunk defined by coords in the given greyscale frame by comparing its mean intensity
    to a set intensity threshold.

    @param greyscale_frame: a Numpy 2-D array representing an OpenCV frame in cv2.COLOR_BGR2GRAY format.
    @param coords: a 4-tuple representing the coordinates for the pixel chunk: (topLeft.x, topLeft.y, bottomRight.x, bottomRight.y)
    @return: True if the mean intensity > intensity threshold. False otherwise.
    """
    greyscale_frame = cv2.resize(greyscale_frame,(VIDEO_W, VIDEO_H))

    if using_mask:
        _, mask2 = cv2.threshold(greyscale_frame, thresh=180, maxval=255, type=cv2.THRESH_BINARY)
        final_image = cv2.bitwise_and(greyscale_frame, mask2)
    else:
        final_image = greyscale_frame
        
    selection = final_image[coords[1]:coords[3], coords[0]:coords[2]]
    intensity = np.mean(selection)
    #print(f"{greyscale_frame.shape},{selection.shape},{coords[1]}:{coords[3]}, {coords[0]}:{coords[2]}",intensity)
    #cv2.imwrite("selection.jpg", selection)
    if intensity>INTENSITY_THRESHOLD:
        return True
    else:
        return False
