import cv2 as cv
import numpy as np
import threading

xCord1 = 0
yCord1 = 0
xCord2 = 0
yCord2 = 0
THRESHOLD = 1
loopArray = []

def do_every (interval, worker_func, iterations = 0):
  if iterations != 1:
    t=threading.Timer (
      interval,
      do_every, [interval, worker_func, 0 if iterations == 0 else iterations-1]
    )
    t.setDaemon(True)
    t.start()
    worker_func ()

def mousePoints(event, x, y, flags, params):
    if event == cv.EVENT_LBUTTONDOWN:
        xCord1 = x
        yCord1 = y
        xCord2 = xCord1 + 50
        yCord2 = yCord1 + 50
        coords =[(yCord1, yCord2), (xCord1, xCord2)]
        loopArray.append(coords)

        cv.rectangle(img, (xCord1, yCord1), (xCord2, yCord2), (0, 0, 255), thickness=0)
        cv.imshow('Pegboard', img)
        
        checkIntensity()

def checkIntensity():
    newCords = []
    for i in range(len(loopArray)):
        for j in range(len(loopArray[i])):
                newCords.append(loopArray[i][j])

    for i in range(0,len(newCords),2):
        selection = img_thresh_gray[newCords[i][0]:newCords[i][1], newCords[i+1][0]:newCords[i+1][1]]
        intensity = np.mean(selection)
        if intensity>THRESHOLD:
            print("Peg with intensity:", intensity)
        else:
            print("No peg with intensity:", intensity)

img = cv.imread('pegboard.png')
gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
_, mask2 = cv.threshold(gray, thresh=180, maxval=255, type=cv.THRESH_BINARY)
img_thresh_gray = cv.bitwise_and(gray, mask2)
do_every (5.0, checkIntensity)
cv.imshow('Pegboard', img)
cv.setMouseCallback('Pegboard', mousePoints)

cv.waitKey(0)