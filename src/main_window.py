import sys
from PyQt5.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QMenu, QMenuBar
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QPixmap, QPainter

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setWindowTitle("DD Interactive Pegboard")
        self.window_width, self.window_height = 1200,800
        self.setMinimumSize(self.window_width,self.window_height)

        self.window = QWidget()
        self.layout = QGridLayout()
        self.setCentralWidget(self.window)
        self.window.setLayout(self.layout)

        self.imageViewApp = ImageViewApp(self)
        self.layout.addWidget(self.imageViewApp)

        menuBar = QMenuBar(self)
        self.setMenuBar(menuBar)
        self._createMenuBar()
    
    
    def _createMenuBar(self):
        menuBar = self.menuBar()
        
        fileMenu = QMenu("&File", self)
        menuBar.addMenu(fileMenu)


class ImageViewApp(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.window_width, self.window_height = 1200,800
        self.setMinimumSize(self.window_width,self.window_height)

        self.pix = QPixmap(self.rect().size())
        self.pix.fill(Qt.white)

        self.rect_start, self.rect_end = QPoint(), QPoint()

    def paintEvent(self, event):
        """
        Fire every time we make a change to the window.
        """
        painter = QPainter(self)
        painter.drawPixmap(QPoint(),self.pix)

        if not self.rect_start.isNull() and not self.rect_end.isNull():
            rect = QRect(self.rect_start, self.rect_end)
            painter.drawRect(rect.normalized())

    def mousePressEvent(self, event):
        #print("Mouse press")
        if event.buttons() & Qt.LeftButton:
            self.rect_start = event.pos()
            self.rect_end = self.rect_start
            self.update()
    
    def mouseReleaseEvent(self, event):
        #print("Mouse release")
        if event.button() & Qt.LeftButton:
            rect = QRect(self.rect_start, self.rect_end)
            print(f"rect start {self.rect_start.x()},{self.rect_start.y()}")
            print(f"rect end {self.rect_end.x()},{self.rect_end.y()}")

            painter = QPainter(self.pix)
            painter.drawRect(rect.normalized())

            self.rect_start, self.rect_end = QPoint(), QPoint()
            self.update()

    def mouseMoveEvent(self, event):
        #print("Mouse move")
        if event.buttons() & Qt.LeftButton:
            self.rect_end = event.pos()
            self.update()


if __name__ == "__main__":
    qt_app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    try:
        sys.exit(qt_app.exec_())
    except SystemExit:
        print("Closing window.")