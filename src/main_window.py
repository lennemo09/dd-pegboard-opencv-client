import sys
from PyQt5.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QWidget, QToolBar, QVBoxLayout, QMenu, QMenuBar, QCheckBox, QSlider
from PyQt5.QtCore import QThread, Qt, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QIntValidator
import numpy as np

from peg_check import check_intensity
from globals import *
from peg_tile import PegTile

import cv2
import pickle

class Tile(QCheckBox):
    """
    Currently unused classed.
    Intended for a selection grid, which allows selection of tile visually instead of typing in row/column numbers.
    """
    def __init__(self, pos):
        QCheckBox.__init__(self)
        self.pos = pos
        self.has_peg = False


class MainWindow(QMainWindow):
    """
    The main Application window instance.
    """
    def __init__(self, parent=None):
        """
        Initializer.
        """
        super().__init__(parent)
        self.setWindowTitle("DD Interactive Pegboard")
        self.window = QWidget() # The window's content bounding box is a blank widget where we will add components inside of it.

        # A vertical box layout as the main layout.
        self.layout_main = QVBoxLayout()
        self.layout_widget = QWidget()
        self.layout_main.addWidget(self.layout_widget)

        # A horizontal box layout to split the first row of the vertical box layout into 2 halfs (intended for a selection grid which is currently disabled).
        self.split_layout = QHBoxLayout()
        self.layout_widget.setLayout(self.split_layout)

        # The main content box
        self.setCentralWidget(self.window)

        # The main layout type of the box
        self.window.setLayout(self.layout_main)

        # A menu bar which is currently unused
        #menuBar = QMenuBar(self)
        #self.setMenuBar(menuBar)
        #self._createMenuBar()

        # A toolbar to house the row/column selection fields and columns.
        self._createToolBars()

        # Status bar to display current drawing mouse's coordinates.
        self._createStatusBar()

        # Video feed component stored in a label
        # IMPORTANT: This IS the video feed's container. It is stored in an empty label for scaling and positioning convenience.
        # If you need to resize or reposition the video feed, do it via this label.
        self.feed_label = QLabel()
        self.feed_label.setScaledContents = True
        self.split_layout.addWidget(self.feed_label,0)

        # Disable stretching of layout's rows so the video feed stays in a fixed position.
        self.layout_main.addStretch(1)

        # A thread to update the video feed using OpenCV's VideoCapture.
        self.camera_thread_worker = CameraThreadWorker()
        self.camera_thread_worker.start()
        # The thread's signal handler to update the video frames. Check CameraThreadWorker's documentation on how this works.
        self.camera_thread_worker.thread_image_update.connect(self._imageUpdateSlot)
         # The thread's signal handler to store the previous frame. This is used for sharing frame data between threads for peg detection.
        self.camera_thread_worker.thread_last_frame_update.connect(self._lastFrameUpdateSlot)

        # A thread to detect pegs from the current video feed.
        self.peg_check_thread_worker = PegCheckThreadWorker()
        self.peg_check_thread_worker.start()

        # The UI Widget to house the drawing canvas for selection rectangles
        self.selectionCanvasApp = SelectionCanvasApp(self.feed_label)
        self.selectionCanvasApp.setMainWindow(self)
        #self.layout.addWidget(self.selectionCanvasApp)

        # The row selection field's label
        self.selected_row_label = QLabel()
        self.selected_row_label.setText("Selected row:")
        self.editToolBar.addWidget(self.selected_row_label)

        # The row selection input field
        self.row_select_field = QLineEdit(str(selected_row))
        #self.row_select_field.setValidator(QIntValidator(0,NUM_ROWS,self))
        self.row_select_field.setFixedWidth(80) # Set fixed width so it doesn't stretch on window resize.
        self.row_select_field.editingFinished.connect(self._rowSelectionEnterPressed) # Enter/mouse clicked on something else handler.
        self.editToolBar.addWidget(self.row_select_field)

        # Increment row button
        self.next_row_button = QPushButton("Next Row(+1)")
        self.editToolBar.addWidget(self.next_row_button)
        self.next_row_button.clicked.connect(self._incrementRow)

        self.editToolBar.addSeparator()

        # The column selection input field's label
        self.selected_col_label = QLabel()
        self.selected_col_label.setText("Selected column:")
        self.editToolBar.addWidget(self.selected_col_label)

        # The column selection input field
        self.col_select_field = QLineEdit(str(selected_col))
        #self.col_select_field.setValidator(QIntValidator(0,NUM_COLS,self))
        self.col_select_field.setFixedWidth(80) # Set fixed width so it doesn't stretch on window resize.
        self.col_select_field.editingFinished.connect(self._colSelectionEnterPressed) # Enter/mouse clicked on something else handler.
        self.editToolBar.addWidget(self.col_select_field)

        # Increment column button
        self.next_col_button = QPushButton("Next Column(+1)")
        self.editToolBar.addWidget(self.next_col_button)
        self.next_col_button.clicked.connect(self._incrementCol)

        self.editToolBar.addSeparator()

        # Toggle greyscale button
        self.toggle_greyscale_button = QPushButton("Toggle Greyscale")
        self.editToolBar.addWidget(self.toggle_greyscale_button)
        self.toggle_greyscale_button.clicked.connect(self._toggleGreyscale)

        # Toggle masking button
        self.toggle_masking_button = QPushButton("Toggle Masking")
        self.editToolBar.addWidget(self.toggle_masking_button)
        self.toggle_masking_button.clicked.connect(self._toggleMasking)

        self.editToolBar.addSeparator()

        # The column selection input field's label
        self.mask_threshold_label = QLabel()
        self.mask_threshold_label.setText("Masking threshold:")
        self.editToolBar.addWidget(self.mask_threshold_label)

        # Masking threshold slider
        global mask_threshold
        self.mask_slider = QSlider(Qt.Horizontal)
        self.mask_slider.setMinimum(0)
        self.mask_slider.setMaximum(255)
        self.mask_slider.setValue(mask_threshold)
        self.mask_slider.setTickPosition(QSlider.TicksBelow)
        self.mask_slider.setTickInterval(5)

        self.editToolBar.addWidget(self.mask_slider)
        self.mask_slider.valueChanged.connect(self._maskSliderChange)

        self.editToolBar.addSeparator()

        # The column selection input field's label
        self.gamma_label = QLabel()
        self.gamma_label.setText("Gamma:")
        self.editToolBar.addWidget(self.gamma_label)

        # Gamma slider
        global gamma
        self.gamma_slider = QSlider(Qt.Horizontal)
        self.gamma_slider.setMinimum(1)
        self.gamma_slider.setMaximum(50)
        self.gamma_slider.setValue(gamma)
        self.gamma_slider.setTickPosition(QSlider.TicksBelow)
        self.gamma_slider.setTickInterval(5)

        self.editToolBar.addWidget(self.gamma_slider)
        self.gamma_slider.valueChanged.connect(self._gammaSliderChange)

        self.editToolBar.addSeparator()

        # The column selection input field's label
        self.intensity_threshold_label = QLabel()
        self.intensity_threshold_label.setText("Intensity threshold:")
        self.editToolBar.addWidget(self.intensity_threshold_label)

        # Intensity threshold slider
        global intensity_threshold
        self.intensity_threshold_slider = QSlider(Qt.Horizontal)
        self.intensity_threshold_slider.setMinimum(0)
        self.intensity_threshold_slider.setMaximum(255)
        self.intensity_threshold_slider.setValue(intensity_threshold)
        self.intensity_threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.intensity_threshold_slider.setTickInterval(5)

        self.editToolBar.addWidget(self.intensity_threshold_slider)
        self.intensity_threshold_slider.valueChanged.connect(self._intensityThresholdliderChange)

        self.editToolBar.addSeparator()

        # Clear rectangles button
        self.clear_rects_button = QPushButton("Clear drawn zones")
        self.editToolBar.addWidget(self.clear_rects_button)
        self.clear_rects_button.clicked.connect(self._clearRects)


        """
        Disabled selection grid. Currently works when you select the current tile via the grid which updates the selection fields
        accordingly but doesn't work vice versa (meaning it doesn't update the selection grid if you select a tile using the fields).
        """
        # self.grid_layout_widget = QWidget()
        # self.split_layout.addWidget(self.grid_layout_widget)
        # self.grid_layout = QGridLayout()
        # self.grid_layout.setHorizontalSpacing(1)
        # self.grid_layout.setVerticalSpacing(0)
        # self.grid_layout_widget.setLayout(self.grid_layout)

        # for i in range(NUM_ROWS):
        #     for j in range(NUM_COLS):
        #         tile = Tile((i,j))
        #         tile.stateChanged.connect(self._tileClicked)
        #         self.grid_layout.addWidget(tile,i,j)


    def _createMenuBar(self):
        """
        Creates the menu bar. Which is the top bar that usually has File drop down menu.
        """
        menuBar = self.menuBar()

        fileMenu = QMenu("&File", self)
        menuBar.addMenu(fileMenu)

    def _createToolBars(self):
        """
        Creates the move-able toolbar that houses buttons and selection fields.
        """
        self.editToolBar = QToolBar("Edit", self)
        self.addToolBar(self.editToolBar)

    def _createStatusBar(self):
        """
        Creates the status bar that displays a message using self.statusbar.showMessage()
        """
        self.statusbar = self.statusBar()
        self.statusbar.showMessage("Ready", 3000)

    def _writeToStatusBar(self, message : str, time=3000):
        """
        Helper function to display a message to status bar with default display time as 3 secs.
        """
        self.statusbar = self.statusBar()
        self.statusbar.showMessage(message, time)

    def _imageUpdateSlot(self, pic):
        """
        Handler function to take the QImage data from the CameraThreadWorker thread to display on the video feed label's pixmap.
        """
        self.feed_label.setPixmap(QPixmap.fromImage(pic))

    def _lastFrameUpdateSlot(self,frame):
        """
        Inter-thread communication signal to transfer the last frame's data to global scope to use with Peg Check thread.
        """
        global last_frame
        last_frame = frame

    def _stopVideoFeed(self):
        """
        Calls to kill the video feed thread.
        """
        self.camera_thread_worker.stop()

    def _clearRects(self):
        global rect_array
        rect_array = [ [None]*NUM_COLS for _ in range(NUM_ROWS) ]

    def _rowSelectionEnterPressed(self):
        """
        Handles what happens when user pressed Enter while entering value in the row selection field.
        If user inputs a valid row value, updates the current selected_row variable accordingly.
        If a value is larger than maximum, wraps the value by taking the remainder of chosen value with max row size.
        If user inputs a string, do not update selected_row.
        """
        global selected_row
        old_row_select = selected_row
        try:
            new_row = int(self.row_select_field.text())
            if new_row < 0:
                self.row_select_field.setText(str(old_row_select))
            else:
                selected_row = (new_row) % NUM_ROWS
                self.row_select_field.setText(str(selected_row))

                # UNUSED
                # The following block tries to update the selection grid accordingly but it's not working.
                # if self.grid_layout is not None:
                #     self.grid_layout.itemAtPosition(old_row_select,selected_col).widget().setChecked(False)
                #     self.grid_layout.itemAtPosition(selected_row,selected_col).widget().setChecked(True)
            # TODO Update corresponding check boxes
        except:
            self.row_select_field.setText(str(old_row_select))
        print(f"Selected row: {selected_row}")

    def _colSelectionEnterPressed(self):
        """
        Handles what happens when user pressed Enter while entering value in the column selection field.
        If user inputs a valid column value, updates the current selected_col variable accordingly.
        If a value is larger than maximum, wraps the value by taking the remainder of chosen value with max column size.
        If user inputs a string, do not update selected_col.
        """
        global selected_col
        old_col_select = selected_col
        try:
            new_col = int(self.col_select_field.text())
            if new_col < 0:
                self.col_select_field.setText(str(old_col_select))
            else:
                selected_col = (new_col) % NUM_ROWS
                self.col_select_field.setText(str(selected_col))

                # UNUSED
                # The following block tries to update the selection grid accordingly but it's not working.
                # if self.grid_layout is not None:
                #     self.grid_layout.itemAtPosition(selected_row,old_col_select).widget().setChecked(False)
                #     self.grid_layout.itemAtPosition(selected_row,selected_col).widget().setChecked(True)
            # TODO Update corresponding check boxes
        except:
            self.col_select_field.setText(str(old_col_select))
        print(f"Selected col: {selected_col}")

    def _incrementRow(self):
        """
        Increments the currently selected row by 1.
        If no row is selected (i.e. selected is None), updates selected to 0.
        """
        global selected_row
        if selected_row is None:
            selected_row = 0
        else:
            selected_row = (selected_row + 1) % NUM_ROWS
        self.row_select_field.setText(str(selected_row))
        # TODO Update corresponding check boxes for selection grid.

    def _incrementCol(self):
        """
        Increments the currently selected column by 1.
        If no column is selected (i.e. selected is None), updates selected to 0.
        """
        global selected_col
        if selected_col is None:
            selected_col = 0
        else:
            selected_col = (selected_col + 1) % NUM_ROWS
        self.col_select_field.setText(str(selected_col))
        # TODO Update corresponding check boxes for selection grid.

    def _tileClicked(self):
        """
        UNUSED.
        Tile selection handler for the selection grid.
        It is called by a signal handler when user selects a box on the grid.
        This box is stored in self.sender() as the signal's sender.
        It then updates the selection fields to the selected tile and unchecks previously selected tile (if there is one).
        """
        tile = self.sender()

        row,col = tile.pos

        if tile.isChecked():
            self.row_select_field.setText(str(row))
            self.col_select_field.setText(str(col))

            global selected_row
            global selected_col
            old_row_select = selected_row
            old_col_select = selected_col
            selected_row = row
            selected_col = col

            # TODO: Deselect all other check boxes
            print(f"Checked {row},{col}")
            if (old_row_select is not None) and (old_col_select is not None):
                self.grid_layout.itemAtPosition(old_row_select,old_col_select).widget().setChecked(False)
        elif (row == selected_row) and (col == selected_col):
            pass
        else:
            # TODO: Checks if no other boxes are checked i.e. there shouldn't be a state when no box is checked.
            # If user unchecks a box, do something like not unchecking or checks box (0,0).
            print(f"Unchecked {row},{col}")

    def _toggleGreyscale(self):
        global using_greyscale
        using_greyscale = not using_greyscale
        self._setColorFormat()

    def _toggleMasking(self):
        global using_mask
        using_mask = not using_mask
        self._setColorFormat()

    def _maskSliderChange(self):
        global mask_threshold
        new_thresh = self.mask_slider.value()
        mask_threshold = new_thresh
        #print(f"New mask threshold: {mask_threshold}")

    def _gammaSliderChange(self):
        global gamma
        new_gamma = self.gamma_slider.value()
        gamma = new_gamma
        #print(f"New gamma: {gamma}")

    def _intensityThresholdliderChange(self):
        global intensity_threshold
        new_intensity_threshold = self.intensity_threshold_slider.value()
        intensity_threshold = new_intensity_threshold

    def _setColorFormat(self):
        if using_greyscale:
            self.camera_thread_worker.cv_color_format = CV_GRAY_FORMAT
            self.camera_thread_worker.qimage_format = QImage.Format_Grayscale8
        else:
            self.camera_thread_worker.cv_color_format = CV_RGB_FORMAT
            self.camera_thread_worker.qimage_format = QImage.Format_RGB888


class CameraThreadWorker(QThread):
    """
    A thread to fetch video frame from OpenCV and update the video feed.
    """
    # A signal to send a QImage which is the new video frame. QImage is because to display in a QPixmap we need a QImage object.
    thread_image_update = pyqtSignal(QImage)

    # A signal to send the previous OpenCV video frame to global. It is a Numpy array.
    thread_last_frame_update = pyqtSignal(np.ndarray)

    if using_greyscale:
        cv_color_format = CV_GRAY_FORMAT
        qimage_format = QImage.Format_Grayscale8
    else:
        cv_color_format = CV_RGB_FORMAT
        qimage_format = QImage.Format_RGB888

    def run(self):
        """
        Main working function of the thread.
        Uses OpenCV2 to fetch the video frame from VideoCapture.
        After fetching the frame it will use signal.emit(frame) to store it as global last_frame for PegChecker thread.
        It will then converts the frame into a displayable format (QImage) and emits the signal to be handled by MainWindow._imageUpdateSlot().

        IMPORTANT: The displayed video frame should be scaled exactly the same as the PegCheck's video frame.
                    This is because the rectangle's coordinates are relative to the displayed video coordinates.
                    If this does not match, PegCheck will be detecting a different pixel chunk which results in incorrect data.
                    This is why the video frame is consistently scaled to the globals (VIDEO_W x VIDEO_H).
        """
        self.active_thread = True
        cv2_video_capture = cv2.VideoCapture(CAMERA_ID)

        while self.active_thread:
            ret, frame = cv2_video_capture.read()
            if ret:
                display_image = cv2.cvtColor(frame, self.cv_color_format)
                if using_mask:
                    _, mask2 = cv2.threshold(display_image, thresh=mask_threshold, maxval=255, type=cv2.THRESH_BINARY)
                    display_image = cv2.bitwise_and(display_image, mask2)

                display_image = apply_gamma(display_image)

                flipped_display_image = cv2.flip(display_image, 1)
                self.thread_last_frame_update.emit(flipped_display_image)
                image_in_Qt_format = QImage(flipped_display_image.data, flipped_display_image.shape[1], flipped_display_image.shape[0], self.qimage_format)
                pic = image_in_Qt_format.scaled(VIDEO_W, VIDEO_H)   # THIS IS IMPORTANT! READ DOCSTRING.
                self.thread_image_update.emit(pic)

    def stop(self):
        """
        Kills the thread.
        """
        self.active_thread = False
        self.quit()


class PegCheckThreadWorker(QThread):
    """
    A thread to run the peg detection mechanism periodically.
    It uses the image data given by the CameraThread via the global last_frame variable which is a Numpy 2-D array,
    representing an image in BGR color format.
    """
    global last_frame   # Declaring we want to use this variable from the global namespace.

    def run(self):
        """
        This is ran every PEG_CHECK_REFRESH_RATE seconds.
        It converts the image into greyscale with BGR2GRAY format.
        Afterward it will loop through the global rect_array to see if a rectangle selection has been made for each
        grid tile/hole. If one has been drawn for a hole, it checks to see if a peg exists in that defined selection
        area for the hole.
        It will also update the output bit array of the current pegboard state.
        """
        self.active_thread = True

        while self.active_thread:
            self.sleep(PEG_CHECK_REFRESH_RATE)
            #print("1 secs passed")

            if last_frame is not None:
                for i in range(len(rect_array)):
                    row = rect_array[i]
                    for j in range(len(row)):
                        rect = row[j]
                        tile : PegTile = tile_array[i][j]

                        # If a zone/selection rectangle has been defined for this tile/hole of the grid.
                        if rect is not None and tile.coords is not None:
                            tile.has_peg = check_intensity(last_frame,tile.coords,mask_threshold,intensity_threshold)
                            output_bit_array[i][j] = 1 if tile.has_peg else 0

                # TO-DO: Call socket function to send the updated output_bit_array to Unity.

    def stop(self):
        """
        Kills the thread.
        """
        self.active_thread = False
        self.quit()


class SelectionCanvasApp(QWidget):
    """
    The rectangle drawing canvas for zone selection for each tile/hole of the grid.
    This is basically an invisible canvas overlayed on top of the video feed with matching size so as to make the rectangle's
    coordinates accurately correspond to a pixel chunk on the video feed.
    """
    def __init__(self, parent=None):
        """
        PyQt-ish steps to initialize a widget.
        """
        super(SelectionCanvasApp,self).__init__(parent)
        self.main_window = None

        layout = QVBoxLayout()  # Uses a VBoxLayout to be consistent with the video feed so the position/movement of the widget behaves consistently with the Video Feed's label.
        self.setLayout(layout)

        self.canvas_width, self.canvas_height = VIDEO_W,VIDEO_H # Canvas size should be consistent with the video feed.
        self.setMinimumSize(self.canvas_width,self.canvas_height)

        self.pix = QPixmap(self.rect().size())  # The Pixmap to draw on
        self.pix.fill(Qt.transparent)   # The background fill is transparent to overlay on top of the video feed.
        self.red_pen = QPen()   # Red pen to draw the undetected zone.
        self.green_pen = QPen() # Green pen to draw the detected zone.
        self.configPens()   # Initializes the pens configs.

        self.selection_rect_start, self.selection_rect_end = QPoint(), QPoint() # Stores the current selection's rectangle's corners.

    def setMainWindow(self, main_window : MainWindow):
        """
        Sets a reference to the main window object.
        """
        self.main_window = main_window

    def configPens(self, color1=Qt.red, color2=Qt.green, width=2, join_style=Qt.MiterJoin):
        """
        Configure the rectangles drawing pens.
        """
        self.red_pen.setColor(color1)
        self.red_pen.setWidth(width)
        self.red_pen.setJoinStyle(join_style)

        self.green_pen.setColor(color2)
        self.green_pen.setWidth(width)
        self.green_pen.setJoinStyle(join_style)

    def paintEvent(self, event):
        """
        Fire every time we make a change to the window.
        Responsible for rendering the rectangles every frame.

        HOW IT WORKS:
        When the left mouse button is first clicked down (mousePressEvent), we are in DRAWING mode. In drawing mode, we render
        a black thin rectangle to represent the current selected area. This area is defined by self.selection_rect_start
        and self.selection_rect_end, they are being updated every mouseMoveEvent.

        When the left mouse button is released (mouseReleaseEven) we draw a permanent RED rectangle and saves it onto our global rect_array.
        We then nullify self.selection_rect_start and self.selection_rect_end to escape DRAWING mode.
        """
        painter = QPainter(self)
        painter.drawPixmap(QPoint(),self.pix)

        # Draw a selection rectangle (while the mouse has not been released)
        if not self.selection_rect_start.isNull() and not self.selection_rect_end.isNull():
            rect = QRect(self.selection_rect_start, self.selection_rect_end)
            painter.drawRect(rect.normalized())

        # For each saved tile/hole on grid
        for i in range(len(rect_array)):
            row = rect_array[i]
            for j in range(len(row)):
                tile_rect = row[j]

                if tile_rect is not None:   # If a rectangle has been saved for the tile, draw it
                    if output_bit_array[i][j] == 1: # If a peg is detected inside the rectangle, draw green.
                        painter.setPen(self.green_pen)
                    else:   # Else, draw red
                        painter.setPen(self.red_pen)

                    painter.drawText(tile_rect.left(), tile_rect.top()-3, f"({i},{j})")
                    painter.drawRect(tile_rect.normalized())

        painter.setPen(QPen())  # Resets to a black pen for drawing selection rectangle.

    def mousePressEvent(self, event):
        """
        Starts DRAWING mode by setting the initial self.selection_rect_start, self.selection_rect_end.
        """
        if event.buttons() & Qt.LeftButton:
            self.selection_rect_start, self.selection_rect_end = QPoint(), QPoint()
            self.selection_rect_start = event.pos()
            self.selection_rect_end = self.selection_rect_start
            self.update()

    def mouseReleaseEvent(self, event):
        """
        Exits DRAWING mode by saving the current rectangle to the global rect_array to be drawn by paintEvent.
        """
        # Only draws when we have selected a tile.
        if (selected_row is not None) and (selected_col is not None) and (event.button() & Qt.LeftButton):
            if rect_array[selected_row][selected_col] is not None:  # If there has been a previously saved zone for this tile, replaces it.
                new_rect = rect_array[selected_row][selected_col]
                rect_array[selected_row][selected_col].setCoords(self.selection_rect_start.x(),self.selection_rect_start.y(),self.selection_rect_end.x(),self.selection_rect_end.y())
            else:   # There hasn't been a previously defined rectangular zone for this tile, creates a new rectangle.
                new_rect = QRect(self.selection_rect_start, self.selection_rect_end)
                rect_array[selected_row][selected_col] = new_rect

            # The following block saves the coordinates for OpenCV corresponding detection zone.
            # If the coordinates are out of bound from left or top edges, limits them to the nearest edge.
            # TO-DO: Handle right and bottom edge.
            x0 = rect_array[selected_row][selected_col].topLeft().x() if rect_array[selected_row][selected_col].topLeft().x() >= 0 else 0
            y0 = rect_array[selected_row][selected_col].topLeft().y() if rect_array[selected_row][selected_col].topLeft().y() >= 0 else 0
            x1 = rect_array[selected_row][selected_col].bottomRight().x() if rect_array[selected_row][selected_col].bottomRight().x() >= 0 else 0
            y1 = rect_array[selected_row][selected_col].bottomRight().y() if rect_array[selected_row][selected_col].bottomRight().y() >= 0 else 0

            tile_array[selected_row][selected_col].coords = (x0,y0,x1,y1)

            self.selection_rect_start, self.selection_rect_end = QPoint(), QPoint()
            self.update()

        else:
            self.selection_rect_start, self.selection_rect_end = QPoint(), QPoint()
            self.update()

    def mouseMoveEvent(self, event):
        """
        Updates the selection box.
        """
        if event.buttons() & Qt.LeftButton:
            self.selection_rect_end = event.pos()
            if self.main_window: self.main_window._writeToStatusBar(f"Cursor position: ({self.selection_rect_end.x()},{self.selection_rect_end.y()})")
            self.update()


def apply_gamma(frame):
    # Apply gamma
    invGamma = 1.0 / (gamma/10)
    table = np.array([((i / 255.0) ** invGamma) * 255
        for i in np.arange(0, 256)]).astype("uint8")
    # Apply gamma correction using the lookup table
    return cv2.LUT(frame, table)


def get_pegs_bit_array():
    """
    NOTE: This is a helper function for debugging. Outputing the inserted pegs are already handled by PegCheckThreadWorker.run()

    Returns a 2-D bit array of pegs on the grid.
    Format: For a hole at row i and column j:
        output_array[i][j] = 0 if peg is not detected.
        output_array[i][j] = 1 if is is detected.
    """
    output_array = []
    for row in tile_array:
        output_array.append([1 if tile.has_peg else 0 for tile in row])
    return output_array


if __name__ == "__main__":
    """
    Main function. This runs when the program starts.
    """
    qt_app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    qt_app.setStyleSheet('''
        QCheckBox {
            spacing: 0px;
        }

        QCheckBox::indicator {
            width: 20px;
            height: 20px;
        }
    ''')

    try:
        sys.exit(qt_app.exec_())
    except SystemExit:
        with open('rectangles_data', 'wb') as rectangle_data_file:
            # This saves the drawn rectangles data to a local file.
            # This will be loaded on app launch in globals.py
            pickle.dump(rect_array, rectangle_data_file)
            print("Saved rectangles")
        window.camera_thread_worker.stop()
        window.peg_check_thread_worker.stop()
        print("Closing window.")
