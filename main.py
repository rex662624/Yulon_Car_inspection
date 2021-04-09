from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import cv2
import os
import os
from stat import S_IREAD, S_IRGRP, S_IROTH, S_IWRITE

import testui as ui

class Main(QMainWindow, ui.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
         
        self.pushButton_3.clicked.connect(self.StartDetectButton)
        self.pushButton_6.clicked.connect(self.LogInRecord)

        self.LogInFileName = 'LogInRecord.txt'
        if not os.path.isfile(self.LogInFileName): 
            #create the file
            self.LogFile = open(self.LogInFileName, 'w+')
            self.LogFile.close()
            # set the file to readonly
            os.chmod(self.LogInFileName, S_IREAD|S_IRGRP|S_IROTH)
            
        else:
            # set the file to readonly
            os.chmod(self.LogInFileName, S_IREAD|S_IRGRP|S_IROTH)   

        #Set             
        #os.chmod(self.LogInFileName, S_IWRITE)
        
        


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

    def LogInRecord(self):
        print("LogInRecord")
        osCommandString = "notepad.exe {}".format(self.LogInFileName)
        os.system(osCommandString)

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())