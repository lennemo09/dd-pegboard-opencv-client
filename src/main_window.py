import sys
from PyQt5.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QPushButton, QWidget, QToolBar, QVBoxLayout, QMenu, QMenuBar
from PyQt5.QtCore import QThread, Qt, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen

import cv2

# GLOBALS
VIDEO_W, VIDEO_H = (640,480)
NUM_ROWS, NUM_COLS = 3, 3
selected_row : int = 1
selected_col : int = 1
rect_array = [ [None]*NUM_COLS for _ in range(NUM_ROWS)]
class Tile:
    def __init__(self, pos=None, id=None):
        self.pos = pos
        self.id = id
        self.selected = False


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setWindowTitle("DD Interactive Pegboard")
        self.window = QWidget()
        self.layout = QVBoxLayout()
        self.layout.addStretch(1)
        self.setCentralWidget(self.window)
        self.window.setLayout(self.layout)

        self.feed_label = QLabel()  # Video feed component stored in a label
        self.feed_label.setScaledContents = True
        self.layout.addWidget(self.feed_label,0)

        self.thread_worker = ThreadWorker()
        self.thread_worker.start()
        self.thread_worker.thread_image_update.connect(self._imageUpdateSlot)

        self.imageViewApp = ImageViewApp(self.feed_label)
        self.imageViewApp.setMainWindow(self)
        #self.layout.addWidget(self.imageViewApp)

        # self.update_button = QPushButton("Update")
        # self.layout.addWidget(self.update_button,0)

        # self.stop_button = QPushButton("Stop")
        # self.layout.addWidget(self.stop_button,0)
        # self.stop_button.clicked.connect(self._stopVideoFeed)

        menuBar = QMenuBar(self)
        self.setMenuBar(menuBar)
        self._createMenuBar()
        self._createToolBars()
        self._createStatusBar()
        #self.setFixedSize(self.size())

    def _createMenuBar(self):
        menuBar = self.menuBar()

        fileMenu = QMenu("&File", self)
        menuBar.addMenu(fileMenu)

    def _createToolBars(self):
        editToolBar = QToolBar("Edit", self)
        self.addToolBar(editToolBar)
    
    def _createStatusBar(self):
        self.statusbar = self.statusBar()
        self.statusbar.showMessage("Ready", 3000)

    def _writeToStatusBar(self, message : str, time=3000):
        self.statusbar = self.statusBar()        
        self.statusbar.showMessage(message, time)

    def _imageUpdateSlot(self, pic):
        self.feed_label.setPixmap(QPixmap.fromImage(pic))

    def _stopVideoFeed(self):
        self.thread_worker.stop()

class ThreadWorker(QThread):
    thread_image_update = pyqtSignal(QImage)

    def run(self):
        self.active_thread = True
        cv2_video_capture = cv2.VideoCapture(1) # Camera ID, in-built webcam is 1

        while self.active_thread:
            ret, frame = cv2_video_capture.read()
            if ret:
                cv2_rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                cv2_flipped_rgb_image = cv2.flip(cv2_rgb_image, 1)
                image_in_Qt_format = QImage(cv2_flipped_rgb_image.data, cv2_flipped_rgb_image.shape[1], cv2_flipped_rgb_image.shape[0], QImage.Format_RGB888)
                pic = image_in_Qt_format.scaled(VIDEO_W, VIDEO_H, Qt.KeepAspectRatio)
                self.thread_image_update.emit(pic)
    
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
        self.pen = QPen()
        self.configPen()

        self.rect_start, self.rect_end = QPoint(), QPoint()

    def setMainWindow(self, main_window : MainWindow):
        self.main_window = main_window
    
    def setSelectedTile(self,x=0,y=0):
        self.selected_tile = (x,y)
    
    def configPen(self, color=Qt.red, width=2, join_style=Qt.MiterJoin):
        self.pen.setColor(color)
        self.pen.setWidth(width)
        self.pen.setJoinStyle(join_style)

    def paintEvent(self, event):
        """
        Fire every time we make a change to the window.
        """
        painter = QPainter(self)
        painter.drawPixmap(QPoint(),self.pix)

        if not self.rect_start.isNull() and not self.rect_end.isNull():
            rect = QRect(self.rect_start, self.rect_end)
            painter.drawRect(rect.normalized())
        
        painter.setPen(self.pen)
        for row in rect_array:
            for tile_rect in row:
                if tile_rect is not None:
                    painter.drawRect(tile_rect.normalized())
        painter.setPen(QPen())
        print(rect_array)

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
            #print(f"rect start {self.rect_start.x()},{self.rect_start.y()}")
            #print(f"rect end {self.rect_end.x()},{self.rect_end.y()}")

            # painter = QPainter(self.pix)
            # painter.setPen(self.pen)
            # painter.drawRect(new_rect.normalized())

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


if __name__ == "__main__":
    qt_app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    try:
        sys.exit(qt_app.exec_())
    except SystemExit:
        print("Closing window.")