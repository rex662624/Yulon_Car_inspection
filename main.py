from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import cv2

import testui as ui

class Main(QMainWindow, ui.Ui_MainWindow):
    def __init__(self):
         super().__init__()
         self.setupUi(self)
         
         self.pushButton_3.clicked.connect(self.StartDetectButton)

    def StartDetectButton(self):
        cap = cv2.VideoCapture("yolact\Short_Video.mp4")

        while(1):
            ret, frame = cap.read()
            self.showImage(frame)
            if cv2.waitKey(1) & 0xFF == ord('q') or ret==False :
                cap.release()
                cv2.destroyAllWindows()
                break

    def showImage(self, img):
        height, width, channel = img.shape
        bytesPerline = 3 * width
        qImg = QImage(img.data, width, height, bytesPerline, QImage.Format_RGB888).rgbSwapped()
        self.label_11.setPixmap(QPixmap.fromImage(qImg))   

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())