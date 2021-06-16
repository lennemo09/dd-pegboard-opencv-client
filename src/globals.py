from peg_tile import PegTile
from cv2 import COLOR_BGR2GRAY, COLOR_BGR2RGB

# GLOBALS
VIDEO_W, VIDEO_H = (800,600)
NUM_ROWS, NUM_COLS = 22, 41 # Pegboard is 22 x 41
CAMERA_ID = 0
PORT = 8080

PEG_CHECK_REFRESH_RATE = 1

using_greyscale = True
using_mask = True

CV_GRAY_FORMAT = COLOR_BGR2GRAY
CV_RGB_FORMAT = COLOR_BGR2RGB

cv2_video_capture = None
last_frame = None

mask_threshold = 180
gamma = 10
intensity_threshold = 1

selected_row = None
selected_col = None
rect_array = [ [None]*NUM_COLS for _ in range(NUM_ROWS) ]

tile_array = []
for _ in range(NUM_ROWS):
    new_row = []
    for _ in range(NUM_COLS):
        new_tile = PegTile()
        new_row.append(new_tile)
    tile_array.append(new_row)

output_bit_array = [ [0]*NUM_COLS for _ in range(NUM_ROWS) ]
