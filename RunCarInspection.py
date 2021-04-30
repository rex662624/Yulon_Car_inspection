# Build-in Lib
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import cv2
import os
import os
from stat import S_IREAD, S_IRGRP, S_IROTH, S_IWRITE
import threading
import time
import serial
import datetime
from pathlib import Path
from functools import partial
# Self-defined Lib
import UI_Main as mainui
import subwindow.UI_config as configui
import subwindow.UI_InspectionHistory as InspectionHistoryui
import subwindow.UI_Account as Accountui

class Main(QMainWindow, mainui.Ui_MainWindow):
    def __init__(self):
        # initilize config
        self.__init_config()
        #=initilize ui
        self.__init_UI()
        #=initilize subwindow
        self.__init_subWindow()
        #=initilize save folder
        self.__init_savefolder()

        self.__init_Common_Thread()

    def __init_config(self):
        self.global_time = datetime.datetime.now()
        self.already_detection_time = 0
        self.saved_status = 0
        self.Detection = False
        self.NumberofCar = 0
        self.AlreadyInspection = 0
        
        # 3 level score
        self.Level1Lower = 0
        self.Level1Upper = 59
        self.Level2Lower = 60
        self.Level2Upper = 99
        self.Level3Lower = 100
        self.Level3Upper = 100
        # 3 level count 
        self.AlreadyInspection_Level1 = 0
        self.AlreadyInspection_Level2 = 0
        self.AlreadyInspection_Level3 = 0

    def __init_UI(self):
        super().__init__()
        self.setupUi(self)
         
        self.pushButton_3.clicked.connect(self.StartDetectButton)
        self.pushButton_4.clicked.connect(self.StopDetectionButton)
        self.pushButton_5.clicked.connect(self.CloseButton)
        self.pushButton_6.clicked.connect(self.LogInRecord)
        
        #pop out window UI
        self.SubWindow_Config = QtWidgets.QMainWindow()
        self.SubWindow_Config_ui = configui.Ui_MainWindow()
        self.SubWindow_Config_ui.setupUi(self.SubWindow_Config)
        self.pushButton_7.clicked.connect(self.SubWindow_Config.show)

        self.SubWindow_InspectionHistory = QtWidgets.QMainWindow()
        self.SubWindow_InspectionHistory_ui = InspectionHistoryui.Ui_MainWindow()
        self.SubWindow_InspectionHistory_ui.setupUi(self.SubWindow_InspectionHistory)

        self.__init_log_button()

        self.SubWindow_Account = QtWidgets.QMainWindow()
        self.Account_ui = Accountui.Ui_Form()
        self.Account_ui.setupUi(self.SubWindow_Account)
        self.pushButton_2.clicked.connect(self.__show_account)

        

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

    def __init_log_button(self):
        button_list = [self.toolButton, self.toolButton_2, self.toolButton_3, self.toolButton_4, self.toolButton_5, self.toolButton_6, self.toolButton_7, self.toolButton_8, 
                        self.toolButton_9, self.toolButton_10, self.toolButton_11, self.toolButton_12, self.toolButton_13, self.toolButton_14, self.toolButton_15, self.toolButton_16]
        
        for i in range(len(button_list)):
            #print(i)
            button_list[i].clicked.connect(partial(self.__show_log, i))

    def __init_subWindow(self):
        self.SubWindow_Config_ui.pushButton.clicked.connect(self.__save_config)
    
    def __show_log(self, index):
        #print(index)
        self.SubWindow_InspectionHistory.show()
        self.SubWindow_InspectionHistory_ui.show_result(self.foldername, index)

    def __show_account(self):
        self.SubWindow_Account.show()

    def __init_savefolder(self):
        now_time = datetime.datetime.now()
        self.foldername = ".\\result\\{}".format(now_time.strftime("%Y_%m_%d"))
        Path(self.foldername).mkdir(parents=True, exist_ok=True)

        for i in range(200):
            CarFolderName = self.foldername+'\\Car_{}'.format(i)
            Path(CarFolderName).mkdir(parents=True, exist_ok=True)

        self.saved_status = 0



    def __save_config(self):
        self.Level1Lower = self.SubWindow_Config_ui.textEdit_2.toPlainText()
        self.Level1Upper = self.SubWindow_Config_ui.textEdit_3.toPlainText()
        self.Level2Lower = self.SubWindow_Config_ui.textEdit_6.toPlainText()
        self.Level2Upper = self.SubWindow_Config_ui.textEdit_5.toPlainText()
        self.Level3Lower = self.SubWindow_Config_ui.textEdit_4.toPlainText()
        self.Level3Upper = self.SubWindow_Config_ui.textEdit.toPlainText()
        self.label_7.setText(QCoreApplication.translate("MainWindow", "{}分~{}分: {}輛".format(self.Level1Lower, self.Level1Upper, self.AlreadyInspection_Level1)))
        self.label_8.setText(QCoreApplication.translate("MainWindow", "{}分~{}分: {}輛".format(self.Level2Lower, self.Level2Upper, self.AlreadyInspection_Level2)))
        self.label_6.setText(QCoreApplication.translate("MainWindow", "{}分~{}分: {}輛".format(self.Level3Lower, self.Level3Upper, self.AlreadyInspection_Level3)))

    
        
    def __update_detection_time(self, now, star_time):
        self.already_detection_time = int((now-star_time).total_seconds())
        self.label_14.setText(QCoreApplication.translate("MainWindow", "已檢測時間: "+str(self.already_detection_time)+"秒"))


    def __init_Common_Thread(self):
        self.CommonThreadRunning = True
        self.CommonThread = threading.Thread(target=self.__CommonFeature)  
        self.CommonThread.start()    

    def __CommonFeature(self):
        start_time = datetime.datetime.now()
        while(self.CommonThreadRunning):
            now = datetime.datetime.now()
            if (now - start_time).seconds == 1:
                start_time = now
                self.global_time = now
                self.label_12.setText(QCoreApplication.translate("MainWindow", str(self.global_time.strftime("%Y-%m-%d %H:%M:%S"))))



    def StartDetectButton(self):
        
        self.port = "COM4"
        self.ser = serial.Serial(port = self.port, baudrate = 115200, bytesize = serial.EIGHTBITS, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, timeout=0)
        value = 0
        initilize = 0
        starttime = self.global_time    
 
        self.fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        self.Save_video = cv2.VideoWriter(self.foldername+'\\Car_{}\\{}.mp4'.format(self.AlreadyInspection, self.AlreadyInspection), self.fourcc, 10.0, (821,  682))
                
        self.Detection = True
        cap = cv2.VideoCapture(0)

        #saved_status: 
        #   0: not save any image
        #   1: front door image saved
        #   2: back door image saved
        
        while(self.Detection):

            if(initilize == 0):
                starttime = self.global_time
                initilize = 1
            
            self.__update_detection_time(self.global_time, starttime)
            
            value = int.from_bytes(self.ser.read(), "big")

            ret, frame = cap.read()
            frame = cv2.resize(frame, (821, 682))
            self.showImage(frame)




            self.Save_video.write(frame)
            
            #print(self.already_detection_time)
            if(self.already_detection_time == 25 and self.saved_status == 0):
                self.saved_status = 1
                print("Save Front Inspection Result")
                self.__Save_Inspection_Result(frame,1)
            elif(self.already_detection_time == 40 and self.saved_status == 1):
                self.saved_status = 0
                print("Save Back Inspection Result")
                self.__Save_Inspection_Result(frame,0)
            #elif(self.already_detection_time == 12):
            if(value==1):
                self.already_detection_time = 0
                self.saved_status = 0

                print("******Car Detected: {}******".format(self.AlreadyInspection))
                starttime = self.global_time

                self.AlreadyInspection += 1
                #self.Save_video = cv2.VideoWriter(self.foldername+'\\Car_{}\\{}.mp4'.format(self.AlreadyInspection, self.AlreadyInspection), self.fourcc, 10.0, (821,  682))
                
                #self.label_3.setText(_translate("MainWindow", "通過車輛: {}"format(self.AlreadyInspection)))
                self.label_13.setText(QCoreApplication.translate("MainWindow", str(self.AlreadyInspection)))   

                self.Save_video.release()  
                self.Save_video = cv2.VideoWriter(self.foldername+'\\Car_{}\\{}.mp4'.format(self.AlreadyInspection, self.AlreadyInspection), self.fourcc, 10.0, (821,  682))           

            self.Detect_Algorithm()

            if cv2.waitKey(1) & 0xFF == ord('q') or ret==False :
                cap.release()
                cv2.destroyAllWindows()
                break

    def StopDetectionButton(self):
        self.Detection = False
        self.ser.close()
        
    def CloseButton(self):
        print("Close all service...")
        
        self.PLCThreadRunning = False       
        #self.PLC_ReceiverThread.join()
        print("\tClose PLC Succeed...")

        self.CommonThreadRunning = False
        self.CommonThread.join()
        print("\tClose Common Thread Succeed...")

        exit()   

    def __Save_Inspection_Result(self, frame, front):
        CarFolderName = self.foldername+'\\Car_{}'.format(self.AlreadyInspection)
        
        if(front==1):
            cv2.imwrite(CarFolderName+'\\front_{}.jpg'.format(self.AlreadyInspection,self.AlreadyInspection), frame)
        else:
            cv2.imwrite(CarFolderName+'\\back_{}.jpg'.format(self.AlreadyInspection,self.AlreadyInspection), frame)
            
            log= open(CarFolderName+"\\log.txt", "w")
            log.write("50\n")
            log.write("45")
            log.close()
            # comment
            #self.AlreadyInspection+=1

        

    def PopoutCarInspectionHistoryWindow(self):

        print("click")


    def showImage(self, img):
        height, width, channel = img.shape
        bytesPerline = 3 * width
        qImg = QImage(img.data, width, height, bytesPerline, QImage.Format_RGB888).rgbSwapped()
        self.label_11.setPixmap(QPixmap.fromImage(qImg))  

    def LogInRecord(self):
        print("LogInRecord")
        osCommandString = "notepad.exe {}".format(self.LogInFileName)
        os.system(osCommandString)


    def Detect_Algorithm(self):
        
        self.label_7.setText(QCoreApplication.translate("MainWindow", "{}分~{}分: {}輛".format(self.Level1Lower, self.Level1Upper, self.AlreadyInspection_Level1)))
        self.label_8.setText(QCoreApplication.translate("MainWindow", "{}分~{}分: {}輛".format(self.Level2Lower, self.Level2Upper, self.AlreadyInspection_Level2)))
        self.label_6.setText(QCoreApplication.translate("MainWindow", "{}分~{}分: {}輛".format(self.Level3Lower, self.Level3Upper, self.AlreadyInspection_Level3)))


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())