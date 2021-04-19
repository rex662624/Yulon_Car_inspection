# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI_InspectionHistory.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets
import cv2

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1014, 774)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(170, 60, 161, 41))
        font = QtGui.QFont()
        font.setFamily("微軟正黑體")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(700, 60, 161, 41))
        font = QtGui.QFont()
        font.setFamily("微軟正黑體")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(40, 170, 401, 351))
        self.label_3.setText("")
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(580, 170, 401, 351))
        self.label_4.setText("")
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setGeometry(QtCore.QRect(690, 590, 271, 41))
        font = QtGui.QFont()
        font.setFamily("微軟正黑體")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(self.centralwidget)
        self.label_6.setGeometry(QtCore.QRect(180, 590, 291, 41))
        font = QtGui.QFont()
        font.setFamily("微軟正黑體")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.label_6.setFont(font)
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(self.centralwidget)
        self.label_7.setGeometry(QtCore.QRect(0, 0, 1000, 750))
        self.label_7.setText("")
        # notice
        self.label_7.setPixmap(QtGui.QPixmap("resource/background.jpg"))
        self.label_7.setObjectName("label_7")
        self.label_7.raise_()
        self.label.raise_()
        self.label_2.raise_()
        self.label_3.raise_()
        self.label_4.raise_()
        self.label_5.raise_()
        self.label_6.raise_()
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)


    def showImage(self, img, label):
        height, width, channel = img.shape
        bytesPerline = 3 * width
        qImg = QtGui.QImage(img.data, width, height, bytesPerline, QtGui.QImage.Format_RGB888).rgbSwapped()
        label.setPixmap(QtGui.QPixmap.fromImage(qImg))  

    def show_result(self, foldername,index):
        CarFolderName = foldername+'\\Car_{}'.format(index)
        front_img = cv2.imread(CarFolderName+'\\front_{}.jpg'.format(index),cv2.IMREAD_COLOR)
        back_img = cv2.imread(CarFolderName+'\\back_{}.jpg'.format(index),cv2.IMREAD_COLOR)       
        self.showImage(front_img, self.label_3)
        self.showImage(back_img, self.label_4)

        log = open(CarFolderName+"\\log.txt", "r")
        scorelist = log.read().split("\n")
        self.label_6.setText(QtCore.QCoreApplication.translate("MainWindow", "前門分數: {}/50".format(scorelist[0])))
        self.label_5.setText(QtCore.QCoreApplication.translate("MainWindow", "後門分數: {}/50".format(scorelist[1])))

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label.setText(_translate("MainWindow", "前車門檢測圖"))
        self.label_2.setText(_translate("MainWindow", "後車門檢測圖"))
        self.label_5.setText(_translate("MainWindow", "分數"))
        self.label_6.setText(_translate("MainWindow", "分數"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
