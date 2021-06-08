# GLOBALS
VIDEO_W, VIDEO_H = (800,600)
NUM_ROWS, NUM_COLS = 22, 41 # Pegboard is 22 x 41
CAMERA_ID = 0
INTENSITY_THRESHOLD = 0.3
cv2_video_capture = None
last_frame = None

selected_row = None
selected_col = None
rect_array = [ [None]*NUM_COLS for _ in range(NUM_ROWS) ]