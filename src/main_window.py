import sys
from PyQt5.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QWidget, QToolBar, QVBoxLayout, QMenu, QMenuBar, QCheckBox
from PyQt5.QtCore import QThread, Qt, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QIntValidator
import numpy as np

from peg_check import checkIntensity
from globals import *

import cv2

class PegTile():
    def __init__(self):
        self.coords = None
        self.has_peg = False

tile_array = [ [PegTile()]*NUM_COLS for _ in range(NUM_ROWS) ]

class Tile(QCheckBox):
    def __init__(self, pos):
        QCheckBox.__init__(self)
        self.pos = pos
        self.has_peg = False


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setWindowTitle("DD Interactive Pegboard")
        self.window = QWidget()

        self.layout_main = QVBoxLayout()
        self.layout_widget = QWidget()
        self.layout_main.addWidget(self.layout_widget)
        self.split_layout = QHBoxLayout()
        self.layout_widget.setLayout(self.split_layout)
        
        self.setCentralWidget(self.window)
        self.window.setLayout(self.layout_main)

        menuBar = QMenuBar(self)
        self.setMenuBar(menuBar)
        self._createMenuBar()
        self._createToolBars()
        self._createStatusBar()

        self.feed_label = QLabel()  # Video feed component stored in a label
        self.feed_label.setScaledContents = True
        self.split_layout.addWidget(self.feed_label,0)
        self.layout_main.addStretch(1)

        self.camera_thread_worker = CameraThreadWorker()
        self.camera_thread_worker.start()
        self.camera_thread_worker.thread_image_update.connect(self._imageUpdateSlot)

        self.peg_check_thread_worker = PegCheckThreadWorker()
        self.peg_check_thread_worker.start()
        self.camera_thread_worker.thread_last_frame_update.connect(self._lastFrameUpdateSlot)

        self.imageViewApp = ImageViewApp(self.feed_label)
        self.imageViewApp.setMainWindow(self)
        #self.layout.addWidget(self.imageViewApp)

        self.selected_row_label = QLabel()
        self.selected_row_label.setText("Selected row:")
        self.editToolBar.addWidget(self.selected_row_label)

        self.row_select_field = QLineEdit(str(selected_row))
        #self.row_select_field.setValidator(QIntValidator(0,NUM_ROWS,self))
        self.row_select_field.setFixedWidth(80)
        self.row_select_field.editingFinished.connect(self._rowSelectionEnterPressed)
        self.editToolBar.addWidget(self.row_select_field)

        self.next_row_button = QPushButton("Next Row")
        self.editToolBar.addWidget(self.next_row_button)
        self.next_row_button.clicked.connect(self._incrementRow)

        self.editToolBar.addSeparator()

        self.selected_col_label = QLabel()
        self.selected_col_label.setText("Selected column:")
        self.editToolBar.addWidget(self.selected_col_label)

        self.col_select_field = QLineEdit(str(selected_col))
        #self.col_select_field.setValidator(QIntValidator(0,NUM_COLS,self))
        self.col_select_field.setFixedWidth(80)
        self.col_select_field.editingFinished.connect(self._colSelectionEnterPressed)
        self.editToolBar.addWidget(self.col_select_field)

        self.next_col_button = QPushButton("Next Column")
        self.editToolBar.addWidget(self.next_col_button)
        self.next_col_button.clicked.connect(self._incrementCol)

        self.editToolBar.addSeparator()

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
        menuBar = self.menuBar()

        fileMenu = QMenu("&File", self)
        menuBar.addMenu(fileMenu)

    def _createToolBars(self):
        self.editToolBar = QToolBar("Edit", self)
        self.addToolBar(self.editToolBar)
    
    def _createStatusBar(self):
        self.statusbar = self.statusBar()
        self.statusbar.showMessage("Ready", 3000)

    def _writeToStatusBar(self, message : str, time=3000):
        self.statusbar = self.statusBar()        
        self.statusbar.showMessage(message, time)

    def _imageUpdateSlot(self, pic):
        self.feed_label.setPixmap(QPixmap.fromImage(pic))

    def _lastFrameUpdateSlot(self,frame):
        global last_frame
        last_frame = frame

    def _stopVideoFeed(self):
        self.camera_thread_worker.stop()

    def _rowSelectionEnterPressed(self):
        global selected_row
        old_row_select = selected_row
        try:
            new_row = int(self.row_select_field.text())
            if new_row < 0:
                self.row_select_field.setText(str(old_row_select))
            else:
                selected_row = (new_row) % NUM_ROWS
                self.row_select_field.setText(str(selected_row))
                if self.grid_layout is not None:
                    self.grid_layout.itemAtPosition(old_row_select,selected_col).widget().setChecked(False)
                    self.grid_layout.itemAtPosition(selected_row,selected_col).widget().setChecked(True)
            # TODO Update corresponding check boxes
        except:
            self.row_select_field.setText(str(old_row_select))
        print(f"Selected row: {selected_row}")

    def _colSelectionEnterPressed(self):
        global selected_col
        old_col_select = selected_col
        try:
            new_col = int(self.col_select_field.text())
            if new_col < 0:
                self.col_select_field.setText(str(old_col_select))
            else:
                selected_col = (new_col) % NUM_ROWS
                self.col_select_field.setText(str(selected_col))
                if self.grid_layout is not None:
                    self.grid_layout.itemAtPosition(selected_row,old_col_select).widget().setChecked(False)
                    self.grid_layout.itemAtPosition(selected_row,selected_col).widget().setChecked(True)
            
            # TODO Update corresponding check boxes
        except:
            self.col_select_field.setText(str(old_col_select))
        print(f"Selected col: {selected_col}")

    def _incrementRow(self):
        global selected_row
        if selected_row is None:
            selected_row = 0
        else:
            selected_row = (selected_row + 1) % NUM_ROWS
        self.row_select_field.setText(str(selected_row))
        # TODO Update corresponding check boxes
    
    def _incrementCol(self):
        global selected_col
        if selected_col is None:
            selected_col = 0
        else:
            selected_col = (selected_col + 1) % NUM_ROWS
        self.col_select_field.setText(str(selected_col))
        # TODO Update corresponding check boxes

    def _tileClicked(self):
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
            # TODO: Checks if no other boxes are checked
            print(f"Unchecked {row},{col}")

class CameraThreadWorker(QThread):
    thread_image_update = pyqtSignal(QImage)
    thread_last_frame_update = pyqtSignal(np.ndarray)

    def run(self):
        self.active_thread = True
        cv2_video_capture = cv2.VideoCapture(CAMERA_ID) # Camera ID, in-built webcam is 1

        while self.active_thread:
            ret, frame = cv2_video_capture.read()
            if ret:
                self.thread_last_frame_update.emit(frame)
                cv2_rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                cv2_flipped_rgb_image = cv2.flip(cv2_rgb_image, 1)
                image_in_Qt_format = QImage(cv2_flipped_rgb_image.data, cv2_flipped_rgb_image.shape[1], cv2_flipped_rgb_image.shape[0], QImage.Format_RGB888)
                pic = image_in_Qt_format.scaled(VIDEO_W, VIDEO_H)
                self.thread_image_update.emit(pic)            
    
    def stop(self):
        self.active_thread = False
        self.quit()


class PegCheckThreadWorker(QThread):
    global last_frame
    def run(self):
        self.active_thread = True

        while self.active_thread:
            self.sleep(1)
            #print("1 secs passed")
            if last_frame is not None:
                gray = cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY)
                #print(gray)
                for i in range(len(rect_array)):
                    row = rect_array[i]
                    for j in range(len(row)):
                        rect = row[j]
                        tile = tile_array[i][j]
                        if rect is not None and tile.coords is not None:
                            tile.has_peg = checkIntensity(gray,tile.coords,INTENSITY_THRESHOLD)   
                            print(tile.has_peg)   

    def stop(self):
        self.active_thread = False
        self.quit()


class ImageViewApp(QWidget):
    def __init__(self, parent=None):
        super(ImageViewApp,self).__init__(parent)
        self.main_window = None
        
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.window_width, self.window_height = VIDEO_W,VIDEO_H
        self.setMinimumSize(self.window_width,self.window_height)

        self.pix = QPixmap(self.rect().size())
        self.pix.fill(Qt.transparent)
        self.red_pen = QPen()
        self.green_pen = QPen()
        self.configPens()

        self.rect_start, self.rect_end = QPoint(), QPoint()

    def setMainWindow(self, main_window : MainWindow):
        self.main_window = main_window
    
    def setSelectedTile(self,x=0,y=0):
        self.selected_tile = (x,y)
    
    def configPens(self, color1=Qt.red, color2=Qt.green, width=2, join_style=Qt.MiterJoin):
        self.red_pen.setColor(color1)
        self.red_pen.setWidth(width)
        self.red_pen.setJoinStyle(join_style)

        self.green_pen.setColor(color2)
        self.green_pen.setWidth(width)
        self.green_pen.setJoinStyle(join_style)

    def paintEvent(self, event):
        """
        Fire every time we make a change to the window.
        """
        painter = QPainter(self)
        painter.drawPixmap(QPoint(),self.pix)

        if not self.rect_start.isNull() and not self.rect_end.isNull():
            rect = QRect(self.rect_start, self.rect_end)
            painter.drawRect(rect.normalized())
        
        painter.setPen(self.red_pen)
        for i in range(len(rect_array)):
            row = rect_array[i]
            for j in range(len(row)):
                tile_rect = row[j]
                if tile_rect is not None:
                    painter.drawText(tile_rect.left(), tile_rect.top()-3, f"({i},{j})")
                    painter.drawRect(tile_rect.normalized())
        painter.setPen(QPen())
        #print(rect_array)

    def mousePressEvent(self, event):
        #print("Mouse press")
        if event.buttons() & Qt.LeftButton:
            self.rect_start, self.rect_end = QPoint(), QPoint()
            self.rect_start = event.pos()
            self.rect_end = self.rect_start
            self.update()
    
    def mouseReleaseEvent(self, event):
        #print("Mouse release")
        if (selected_row is not None) and (selected_col is not None) and (event.button() & Qt.LeftButton):
            if rect_array[selected_row][selected_col] is not None:
                new_rect = rect_array[selected_row][selected_col]
                rect_array[selected_row][selected_col].setCoords(self.rect_start.x(),self.rect_start.y(),self.rect_end.x(),self.rect_end.y())
            else:
                new_rect = QRect(self.rect_start, self.rect_end)
                rect_array[selected_row][selected_col] = new_rect

            x0 = rect_array[selected_row][selected_col].topLeft().x() if rect_array[selected_row][selected_col].topLeft().x() >= 0 else 0
            y0 = rect_array[selected_row][selected_col].topLeft().y() if rect_array[selected_row][selected_col].topLeft().y() >= 0 else 0
            x1 = rect_array[selected_row][selected_col].bottomRight().x() if rect_array[selected_row][selected_col].bottomRight().x() >= 0 else 0
            y1 = rect_array[selected_row][selected_col].bottomRight().y() if rect_array[selected_row][selected_col].bottomRight().y() >= 0 else 0

            tile_array[selected_row][selected_col].coords = (x0,y0,x1,y1)

            self.rect_start, self.rect_end = QPoint(), QPoint()
            self.update()
        
        else:
            self.rect_start, self.rect_end = QPoint(), QPoint()
            self.update()

    def mouseMoveEvent(self, event):
        #print("Mouse move")
        if event.buttons() & Qt.LeftButton:
            self.rect_end = event.pos()
            if self.main_window: self.main_window._writeToStatusBar(f"Cursor position: ({self.rect_end.x()},{self.rect_end.y()})")
            self.update()


def get_rectangle_coordinates():
    pass


if __name__ == "__main__":
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
        print("Closing window.")