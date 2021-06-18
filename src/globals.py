from peg_tile import PegTile
from cv2 import COLOR_BGR2GRAY, COLOR_BGR2RGB
import pickle

# GLOBALS
VIDEO_W, VIDEO_H = (1200,700)
NUM_ROWS, NUM_COLS = 22, 41 # Pegboard is 22 x 41
CAMERA_ID = 0
PORT = 8080
RECT_DATA_FILE = "rectangles_data.pegdata"
TILE_DATA_FILE = "tile_data.pegdata"

PEG_CHECK_REFRESH_RATE = 1

using_greyscale = False
using_mask = False
using_adaptive_thresholding = False
using_vignette = True

CV_GRAY_FORMAT = COLOR_BGR2GRAY
CV_RGB_FORMAT = COLOR_BGR2RGB

cv2_video_capture = None
last_frame = None

mask_threshold = 180
gamma = 10
intensity_threshold = 1
scale = 50
mirrored = False

use_red = True
use_green = True
use_blue = True

selected_row = None
selected_col = None

# Try to load saved rectangles data. If it fails, create a clean array.
try:
    with open(RECT_DATA_FILE, 'rb') as rectangle_data_file:
        rect_array = pickle.load(rectangle_data_file)
        print("Loaded rects.")
except FileNotFoundError:
    print("No rects data file found.")
    rect_array = [ [None]*NUM_COLS for _ in range(NUM_ROWS) ]

try:
    with open(TILE_DATA_FILE, 'rb') as tile_data_file:
        tile_array = pickle.load(tile_data_file)
        print("Loaded tiles.")
except FileNotFoundError:
    print("No tiles data file found.")
    tile_array = []
    for _ in range(NUM_ROWS):
        new_row = []
        for _ in range(NUM_COLS):
            new_tile = PegTile()
            new_row.append(new_tile)
        tile_array.append(new_row)



output_bit_array = [ [0]*NUM_COLS for _ in range(NUM_ROWS) ]
