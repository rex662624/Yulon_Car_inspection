from .Training.src.keras_yolo3.yolo import YOLO
from PIL import Image
import numpy as np
import cv2
from pathlib import Path
import tensorflow as tf
class Detection(object):

    def __init__(self):
        

        base_path = Path(__file__).parent
        model_weights = (base_path / "Inference\\Model_Weights\\trained_weights_final.h5").resolve()
        classes_path = (base_path / 'Inference\\Model_Weights\data_classes.txt').resolve()
        #anchors_path = (base_path / 'Training\src\keras_yolo3\model_data\yolo-tiny_anchors.txt').resolve()        
        anchors_path = (base_path / 'Training\src\keras_yolo3\model_data\yolo_anchors.txt').resolve()        
        gpu_num = 1
        score = 0.25

        # output as xmin, ymin, xmax, ymax, class_index, confidence
        self.yolo = YOLO(
            **{
                "model_path": model_weights,
                "anchors_path": anchors_path,
                "classes_path": classes_path,
                "score": score,
                "gpu_num": gpu_num,
                "model_image_size": (416, 416),
            }
        )

        
        #====readin class====
        class_list = []
        with open(classes_path) as f:
            class_list = f.readlines()
        self.class_list = [x.replace('\n','') for x in class_list]
        print(self.class_list)
        #====================        
        
        
    def init_config(self):

        base_path = Path(__file__).parent
        golden_path = (base_path / 'Inference\\New_Golden.npy').resolve()
        #=======================YOLO==================================
        self.frame_count = 0
        self.prev_centerX, self.prev_centerY = 0, 0
        self.Wheel_Record = []
        self.Acc_Wheel = 0
        self.Golden = np.load(golden_path)
        self.Golden_Pt = np.array(self.Golden[:,:-1])
        #[True, center_x, center_y, frame_count, index_min, Nowx, Nowy]
        self.Find_Front = [False,2**32-1,2**32-1,-1,-1,-1,-1]
        self.Find_Back = [False,2**32-1,2**32-1,-1,-1,-1,-1]
        print(self.Golden_Pt)
        self.missing = 0
        self.Find_Wheelx, self.Find_Wheely = -1, -1
        self.Upper = 270
        #=====================inspection============================
        self.x_min, self.y_min = 0, 0
        self.x_max, self.y_max = 0, 0
        self.inspection_v = 0
        self.M_operator = (0,0)
        self.Inspection_pt = [
                #[ColumnValid, [Detected,Location,AccFrame]]
                [False,[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0]],
                [False,[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0]],
                [False,[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0]],
                [False,[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0]],
                [False,[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0]],
                [False,[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0],[False, (0,0), 0]],
                ]  
        #存線段的起點和終點
        self.Number_of_Inspectionpt_Line = len(self.Inspection_pt)
        self.line_list = [[[0, 0],[0, 0]] for i in range(self.Number_of_Inspectionpt_Line)]     
        self.Interval = 70
        self.IntervalAcc = 0    
        self.ColCount = 0             
        self.Inspection_pt_offset_x, self.Inspection_pt_offset_y = 0, 0
        # 窗戶那條橫線
        self.Window_Line_OffsetLeft = 0
        self.Window_Line_OffsetRight = 0
        self.Window_Line_NowLeft = 0
        self.Window_Line_NowRight = 0
        # 窗戶直線
        #self.Window_Stright_Line = [[860, 0], [600, 682]] 
        self.Window_Stright_Line = [740, 350]
        #各個part的檢測點儲存:
        self.Window_H_InspectionPt = [[False, (0,0), 0] for i in range(12)]
        self.Window_V_InspectionPt = [[False, (0,0), 0] for i in range(10)]
        self.Outer_Contour_InspectionPt = [[False, (0,0), 0] for i in range(25)]
        self.NowScore = 0

    def __bottom_line(self, x):
        return int(-((650-x)*400/650-680))

    def __find_operator(self, image, lastM):
        # threshold
        imagecopy = image.copy()
        imagecopy = cv2.blur(imagecopy,(5,5))
        imagecopy = cv2.cvtColor(imagecopy, cv2.COLOR_BGR2HSV)
        imagecopy = cv2.inRange(imagecopy, (101, 139, 57), (126, 255, 255))
        kernel = np.ones((13,13),np.uint8) 
        imagecopy = cv2.morphologyEx(imagecopy, cv2.MORPH_CLOSE, kernel) 
        
        #contour
        contours, hierarchy = cv2.findContours(imagecopy, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        area_low_threshold = 3000
        area_high_threshold = 100000
        areamax = [0,-1]#[max area, index of max area]
        cXmax,cYmax = 0,0
        for i in range(len(contours)):  
            area = cv2.contourArea(contours[i])
            M_temp = cv2.moments(contours[i])
            if M_temp["m00"] != 0:
                cX_temp, cY_temp = int(M_temp["m10"] / M_temp["m00"]), int(M_temp["m01"] / M_temp["m00"]) 
            else:
                cX_temp, cY_temp = (0,0)
            if area>area_low_threshold and area<area_high_threshold:
                #先找距離超近的，一定就是
                if(lastM!=(0,0)):
                    dist_temp = np.linalg.norm(np.array(lastM)-np.array((cX_temp,cY_temp)))
                    if(dist_temp<50):
                        return [contours[i]], (cX_temp, cY_temp)
                #找面積最大的
                elif area>areamax[0]:
                    areamax = [area, i]
                    cXmax, cYmax = cX_temp, cY_temp
        
        #cv2.drawContours(image, contours, areamax[-1], (255,0,255), -1)
        return [contours[areamax[-1]]], (cXmax, cYmax)

    def __ComputeInspection(self, operator_now, Inspection_pt, operator_offsety, threshold, inspected_threshold):
        x_min,y_min,w,h = cv2.boundingRect(operator_now[0])
        y_min += operator_offsety
        x_min -= threshold
        y_min -= threshold
        x_max = x_min + w + 2*threshold
        y_max = y_min + h + 2*threshold

        for i in range(len(Inspection_pt)):
            pt = Inspection_pt[i][1]
            if(Inspection_pt[i][0] == False):
                if(pt[0] < x_max and pt[0] > x_min and pt[1] < y_max and pt[1] > y_min):
                    Inspection_pt[i][2]+=1
                    if(Inspection_pt[i][2]>=inspected_threshold):
                        Inspection_pt[i][0] = True
                else:
                    Inspection_pt[i][2] = 0
            

    def __ComputeScore(self, Inspection_pt):
        inspection_point_number = 0
        total_point_number = len(Inspection_pt)
        for i in range(len(Inspection_pt)):
            if(Inspection_pt[i][0]==True):
                inspection_point_number+=1

        if(total_point_number==0):
            return 0
        else:
            return int(inspection_point_number*100/total_point_number)


    def find_line(self, image, x1, y1, slope):

        m=slope
        h,w=image.shape[:2]
        if m!='NA':
            ### here we are essentially extending the line to x=0 and x=width
            ### and calculating the y associated with it
            ##starting point
            px=0
            py=-(x1-0)*m+y1
            ##ending point
            qx=w
            qy=-(x1-w)*m+y1
        else:
        ### if slope is zero, draw a line with x=x1 and y=0 and y=height
            px,py=x1,0
            qx,qy=x1,h
        #cv2.line(image, (int(px), int(py)), (int(qx), int(qy)), (0, 255, 0), 5)
        return (int(px), int(py)), (int(qx), int(qy))

    def __line_intersection(self, line1, line2):
        xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
        ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

        def det(a, b):
            return a[0] * b[1] - a[1] * b[0]

        div = det(xdiff, ydiff)
        if div == 0:
            raise Exception('lines do not intersect')

        d = (det(*line1), det(*line2))
        x = det(d, xdiff) / div
        y = det(d, ydiff) / div
        return int(x), int(y)

    def detection_algorithm(self, frame, passtime):

        self.frame_count += 1
        #cv2.imwrite('temp\\{}.jpg'.format(self.frame_count), frame)
        #if(self.Find_Front[0]==False):
        offsetx = 2*(frame.shape[0])//3
        offsety = 2*(frame.shape[1])//3   

        right_bottom = frame.copy()[offsety:, offsetx:]       
        prediction, _ = self.yolo.detect_image(Image.fromarray(cv2.cvtColor(right_bottom, cv2.COLOR_BGR2RGB)))
        new_image = frame.copy()
        Wheel_List = []

        self.Upper-=0.025
        Upper_int = int(self.Upper)
        
        
        now_centerX, now_centerY = 0, 0
        # print(passtime)
        
        # if(passtime>=2 and self.Find_Front[0]==False):
        #     center_x = 698
        #     center_y = 643
        #     index_min = 0
        #     self.Find_Front = [True, center_x, center_y, self.frame_count, index_min, center_x, center_y]#offsetx offsety
        #     self.line_list[0] = [[center_x, Upper_int],[center_x, center_y]]
        #     self.Inspection_pt[0][0] = True
        #     self.ColCount+=1
        #     #print("Find Front")
            
        # elif(passtime>=5 and self.Find_Back[0]==False):
        #     center_x = 663
        #     center_y = 628
        #     index_min = 84           
        #     self.Find_Back = [True, center_x, center_y, self.frame_count, index_min, center_x, center_y]
        #     #print("Find Back")

        if(len(prediction)==0):
            self.missing+=1

        for object_detected in prediction:
            object_name = self.class_list[object_detected[4]]
            
            
            if(object_name == 'Wheel'):

                center_x = (object_detected[0] + object_detected[2])//2 + offsetx  
                center_y = (object_detected[1] + object_detected[3])//2 + offsety
                area = (object_detected[3]- object_detected[1])*(object_detected[2]-object_detected[0])
                #print("Area: ", area)
                Wheel_List.append([object_detected, center_x, center_y])
                #cv2.circle(new_image, (center_x, center_y), 10 ,(0, 0, 255), -1)
                
                #cv2.rectangle(new_image, (object_detected[0]+ offsetx, object_detected[1]+ offsety), (object_detected[2]+ offsetx, object_detected[3]+ offsety), (0, 255, 255), -1)
                
                if(((abs(center_x-self.prev_centerX)<30 and abs(center_y-self.prev_centerY)<30) or self.prev_centerX==0) and self.Acc_Wheel<10 and area > 3000):
                    #print("Y:", center_y)
                    #print("Diff", center_x-self.Find_Wheelx)
                    if(self.Find_Front[0] == False):#應該畫面內只會有前輪，因此找到的一定是前輪
                        self.Acc_Wheel+=1
                        self.prev_centerX, self.prev_centerY = center_x, center_y
                        #cv2.circle(new_image, (center_x, center_y), 10 ,(255, 0, 0), -1)

                    elif(abs(center_x-self.Find_Wheelx)>300):#要找後輪，但可能前後輪都被偵測到，要排除前輪
                        self.Acc_Wheel+=1
                        self.prev_centerX, self.prev_centerY = center_x, center_y
                        #cv2.circle(new_image, (center_x, center_y), 10 ,(0, 255, 0), -1)

                    else:
                        self.missing+=1

                elif(self.Acc_Wheel>=10):
                    dist = np.linalg.norm([self.prev_centerX, self.prev_centerY]-self.Golden_Pt, axis=1)
                    index_min = np.argmin(dist)
                    
                    if(self.Find_Front[0] == False):
                        self.Find_Front = [True, center_x, center_y, self.frame_count, index_min, center_x, center_y]#offsetx offsety
                        self.prev_centerX, self.prev_centerY, self.missing, self.Acc_Wheel = 0, 0, 0, 0
                        #print(self.frame_count)
                        
                        #======檢測點
                        wheel_door_offset = 40
                        self.line_list[0] = [[center_x + wheel_door_offset, Upper_int],[center_x + wheel_door_offset, center_y]]
                        self.Inspection_pt[0][0] = True
                        self.ColCount+=1
                        #算車窗的那條分隔線參數
                        #cv2.line(new_image, (0, 250), (820, 420), (0, 0, 255), 5)
                        #cv2.line(new_image, (0, 260), (820, 470), (0, 0, 255), 5)
                        window_start_line = (260, 490)
                        window_end_line = (260, 400)
                        EndFrame_Dist = self.Golden[-1][2]-self.Golden[self.Find_Front[4]][2]
                        self.Window_Line_OffsetLeft = (window_end_line[0]-window_start_line[0])/EndFrame_Dist
                        self.Window_Line_OffsetRight = (window_end_line[1]-window_start_line[1])/EndFrame_Dist
                        self.Window_Line_NowLeft = window_start_line[0]
                        self.Window_Line_NowRight = window_start_line[1]
                        print("Dist: ", EndFrame_Dist)

                    elif(self.Find_Back[0] == False):
                        if(np.min(dist)>50):
                            self.prev_centerX, self.prev_centerY, self.missing, self.Acc_Wheel = 0, 0, 0, 0
                        else:#找到後輪
                            self.Find_Back = [True, center_x, center_y, self.frame_count, index_min, center_x, center_y]#offsetx offsety
                            #print(frame_count)


                else:
                    self.missing+=1
            else:
                self.missing+=1

        #print(missing)
        if(self.missing>10):
            self.prev_centerX, self.prev_centerY, self.missing, self.Acc_Wheel = 0, 0, 0, 0

        
        Wheel_Pt = []
        Wheel_Find_List = [self.Find_Front, self.Find_Back]
        
        for i in range(len(Wheel_Find_List)):
            Find_Wheel = Wheel_Find_List[i]
            
            if(Find_Wheel[0] == True):
                GoldenX, GoldenY, Golden_Start_Frame = self.Golden[Find_Wheel[4]][0], self.Golden[Find_Wheel[4]][1], self.Golden[Find_Wheel[4]][2]
                # print(GoldenX, GoldenY)
                # exit(0)

                Start_Frame = Find_Wheel[3]
                if((Find_Wheel[4]+self.frame_count-Start_Frame) < len(self.Golden)):
                    Wheeloffsetx = self.Golden[Find_Wheel[4]+(self.frame_count-Start_Frame)][0] - GoldenX
                    Wheeloffsety = self.Golden[Find_Wheel[4]+(self.frame_count-Start_Frame)][1] - GoldenY
                    
                    self.Find_Wheelx, self.Find_Wheely = Find_Wheel[1]+Wheeloffsetx, Find_Wheel[2]+Wheeloffsety
                    
                    Find_Wheel[5], Find_Wheel[6] = self.Find_Wheelx, self.Find_Wheely

                    #存前後輪座標
                    Wheel_Pt.append([self.Find_Wheelx, self.Find_Wheely])
                else:# 任何一輪子已經沒有Golden Sample可以看都要跳出
                    
                    self.Find_Front[0] = False
                    self.Find_Back[0] = False

                    # 把所有的檢測點打開
                    for inspection_pt_index in range(self.Number_of_Inspectionpt_Line):
                        self.Inspection_pt[inspection_pt_index][0] = False                    

                    print("break")
                    break

            



        if(len(Wheel_Pt)==0):# not find the wheel
            #print("Not find the wheel")
            pass
        elif(len(Wheel_Pt)==1):# find the front wheel
            #print("find front wheel")
            #cv2.rectangle(new_image, (Wheel_Pt[0][0], Upper_int), (frame.shape[1], frame.shape[0]), (255, 0, 0), 2)
            #print(Wheel_Pt[0][0])
            # 用現在的 x_min - 前一個 x_min
            if(self.x_min!=0):
                self.inspection_v =Wheel_Pt[0][0]- self.x_min
            #inspection_v-=0.05
            self.y_min, self.y_max = Upper_int, frame.shape[0]
            self.x_min, self.x_max = Wheel_Pt[0][0], frame.shape[1]
            
        elif(len(Wheel_Pt)==2):# find the both wheel
            #print("find both wheel")
            #cv2.rectangle(new_image, (Wheel_Pt[0][0], Upper_int), (Wheel_Pt[1][0], Wheel_Pt[1][1]), (255, 0, 0), 2)
            #print(Wheel_Pt[0][0])
            # 用現在的 x_min - 前一個 x_min
            if(self.x_min!=0):
                self.inspection_v =Wheel_Pt[0][0]- self.x_min
            #inspection_v-= 0.2
            self.y_min, self.y_max = Upper_int, Wheel_Pt[1][1]
            self.x_min, self.x_max = Wheel_Pt[0][0], Wheel_Pt[1][0]

            # 把所有的檢測點打開
            for inspection_pt_index in range(self.Number_of_Inspectionpt_Line):
                self.Inspection_pt[inspection_pt_index][0] = True
        #endregion     

        #=======================================畫檢測點===========================================
        if(Wheel_Find_List[1][0]==False):#還沒找到後輪
            # 77    # 136    # 201    # 252    # 299    # 334    # 362    # 393            
            #先看看觸發新的點col了沒
            #Now position - Start Position
            #(self.Find_Front[1]-self.Find_Front[5])
            while((self.Find_Front[1]-self.Find_Front[5]) >self.IntervalAcc and self.ColCount<self.Number_of_Inspectionpt_Line and (self.Find_Front[1]-self.Find_Front[5])<500 ):
                #self.Interval -=15 # initilize: 110         
                self.IntervalAcc+=self.Interval
                #print("===",IntervalAcc)

                #===先算初始位置
                #x = int(x_max-((x_max-x_min)/(ColCount)))
                self.line_list[self.ColCount] = [[760, self.y_min],[760, self.y_max]]
                #=============
                self.Inspection_pt[self.ColCount][0] = True
                self.ColCount+=1
                
            #print(Inspection_pt[0])
            #print(line_list[0])
            #算出新的col位置
            for i in range(self.Number_of_Inspectionpt_Line):
                
                if(self.Inspection_pt[i][0]==True):
                    self.line_list[i][0][0] = self.line_list[i][1][0] =  int(self.line_list[i][0][0] + self.inspection_v)
                    self.line_list[i][1][1] = self.__bottom_line(self.line_list[i][1][0])
                    
                    # if(i<5):
                    #     line_min_expected = self.line_list[i][1][1]-180-80*i#line_list[i][1][1]-150-100*i
                    #     self.line_list[i][0][1] = max(line_min_expected, self.y_min)
                    # else:
                    #     self.line_list[i][0][1] = 300#280
                    #print(line_list[i])
                    #cv2.line(new_image, tuple(line_list[i][0]),tuple(line_list[i][1]), (0,250,250),3)
                    line_min_expected = self.line_list[i][1][1]-140-80*i#line_list[i][1][1]-150-100*i
                    self.line_list[i][0][1] = max(line_min_expected, self.y_min)
                    



        else:#找到後輪了 用九等分演算法
            inspection_temp_inteval = (self.x_max-self.x_min)/(self.Number_of_Inspectionpt_Line)
            for i in range(self.Number_of_Inspectionpt_Line):
                tempx = int(self.x_min+i*inspection_temp_inteval)
                self.line_list[i][0][0] = self.line_list[i][1][0] = tempx
                self.line_list[i][1][1] = self.__bottom_line(tempx)
                if(i<=1):
                    line_min_expected = self.line_list[i][1][1]-100-i*70
                    self.line_list[i][0][1] = max(line_min_expected, self.y_min)
                elif(i==self.Number_of_Inspectionpt_Line-1):
                    self.line_list[i][0][0] = self.x_max+20
                    self.line_list[i][0][1] = self.y_min+10
                else:
                    self.line_list[i][0][1] = self.y_min-10
                cv2.line(new_image, tuple(self.line_list[i][0]),tuple(self.line_list[i][1]), (0,250,250),3)
                #cv2.circle(new_image, (int(self.x_max), int(self.Upper)), 6 ,(255, 255, 255), -1)
            
        #===============================分割前後窗戶和車門=================================

        Final_Contour = np.zeros((frame.shape[0], frame.shape[1]), np.uint8)
        Door_Window_Contour = np.zeros((frame.shape[0], frame.shape[1]), np.uint8)#frame.copy()
        Window_Vertical = np.zeros((frame.shape[0], frame.shape[1]), np.uint8)
        Window_Horizontal = np.zeros((frame.shape[0], frame.shape[1]), np.uint8)
        
        #用線的兩端找車門車窗輪廓
        Shape_Key_Point = []
        Upper_PT_List = []
        Lower_PT_List = []
        if(self.Inspection_pt[1][0]==True):#第二排要出現，才會有輪廓
            for i in range(self.Number_of_Inspectionpt_Line):
                if(self.Inspection_pt[i][0]==True):
                    Upper_PT_List.append([self.line_list[i][0]])
                    Lower_PT_List.append([self.line_list[i][1]])
                    #cv2.circle(new_image, (Shape_Key_Point[-2][0],Shape_Key_Point[-2][1]), 4 ,(50, 50, 50), -1)
                    #cv2.circle(new_image, (Shape_Key_Point[-1][0],Shape_Key_Point[-1][1]), 4 ,(50, 50, 50), -1)
        #print(np.array(Shape_Key_Point).shape)
        if(self.Find_Back[0]==False):
            Shape_Key_Point = Upper_PT_List + Lower_PT_List[::-1]# reverse
        else:
            NewPt = [[[40+int((self.line_list[-1][0][0]+self.line_list[-1][-1][0])/2),
                    int((self.line_list[-1][0][1]+self.line_list[-1][-1][1])/2)]]]
            Shape_Key_Point = Upper_PT_List + NewPt +Lower_PT_List[::-1]# reverse

        #print(Shape_Key_Point)
        if(len(Shape_Key_Point)>0):
            #cv2.drawContours(contour_image, np.array([Shape_Key_Point]), 0, (0, 0, 255), 3)
            cv2.drawContours(Final_Contour , np.array([Shape_Key_Point]), 0, 1, -1)
            cv2.drawContours(Door_Window_Contour, np.array([Shape_Key_Point]), 0, 1, 5)

        # 窗戶的水平線
        if(self.Find_Front[0] ==True):
            
            #cv2.line(contour_image, (0, int(self.Window_Line_NowLeft)), (820, int(self.Window_Line_NowRight)), (0, 0, 255), 5)
            cv2.line(Window_Horizontal, (0, int(self.Window_Line_NowLeft)), (820, int(self.Window_Line_NowRight)), 1, 5)
            self.Window_Line_NowLeft+=self.Window_Line_OffsetLeft
            self.Window_Line_NowRight+=self.Window_Line_OffsetRight

        #畫後輪的弧度
        if(self.Find_Back[0] == True):
            
            # print(self.frame_count)
            # exit()
            #cv2.circle(new_image, (self.Find_Back[5], self.Find_Back[6]), 30, (0, 0, 255), -1)
            #cv2.ellipse(contour_image,(self.Find_Back[5],self.Find_Back[6]),(110,70),60,0,360,255,-1)
            h = int(110+0.08*(self.Find_Back[5]-self.Find_Back[1]))
            w = int(70+0.08*(self.Find_Back[5]-self.Find_Back[1]))
            cv2.ellipse(Final_Contour,(self.Find_Back[5],self.Find_Back[6]),(h,w),60,0,360,0,-1)
            
            #cv2.imwrite('b.jpg', contour_image)
            #exit()

        
        # 窗戶直線
        line = []
        if(self.Find_Back[0] ==True):
            #找到後輪的話要用第4個column的第2個點作為參考點
            
            #每一個column的距離
            inspection_temp_inteval = (self.x_max-self.x_min)/self.Number_of_Inspectionpt_Line
            tempx = int(self.x_min+3*inspection_temp_inteval)
            tempy_max = self.__bottom_line(tempx)
            tempy_min = self.y_min
            interval_now = (tempy_max-tempy_min)/7
            tempy = int(tempy_min+interval_now)
            #cv2.circle(new_image, (tempx, tempy), 10, (255, 255, 255), -1)
            line = self.find_line(new_image, tempx, tempy, -2)
        elif(self.Find_Front[0] ==True and self.Find_Front[5]<400):
            #cv2.imwrite('a.jpg',frame)
            #exit()
            line = self.find_line(new_image, self.Window_Stright_Line[0], self.Window_Stright_Line[1], -2)
            self.Window_Stright_Line[0] -= (240/280)

        #剛才找到線，現在找轉折點畫線
        inspectionpt = []       
        if(len(line)!=0):
            inspectionpt = self.__line_intersection(line, ((0,self.Window_Line_NowLeft), (820,self.Window_Line_NowRight)))
            cv2.line(Window_Vertical, line[1], inspectionpt, 1, 5)#前後車窗分隔
            cv2.line(Window_Vertical, inspectionpt, (inspectionpt[0], new_image.shape[1]), 1, 5)#前後車門分隔
        
        #算交叉點
        intersection = (np.logical_and(Window_Horizontal, Door_Window_Contour)*1).astype(np.uint8)

        contours, hierarchy = cv2.findContours(intersection, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        #print("interspection1: ", len(contours), end = ' ')

        intersection = (np.logical_and(Window_Vertical, Door_Window_Contour)*1).astype(np.uint8)
        contours2, hierarchy = cv2.findContours(intersection, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        #print("interspection2: ", len(contours2))

        ref_pt_h = []
        ref_pt_v = []
        if(len(contours)==2):
            ref_pt_h = [contours[0][0][-1], contours[1][0][0]]
        if(len(contours2)==2):
            ref_pt_v = [contours2[0][0][0], contours2[1][0][0]]
            

        #========畫出車框=======
        contours, hierarchy = cv2.findContours(Final_Contour, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for i in range(len(contours)):  
            cv2.drawContours(new_image, contours, i, (0, 0, 255), 5)
        
        #=======畫出5個交叉點========
        if(len(ref_pt_h)!=0):
            #print(ref_pt_h)
            #cv2.circle(new_image, (ref_pt_h[0][0], ref_pt_h[0][1]), 10 ,(0, 0, 0), -1)
            #cv2.circle(new_image, (ref_pt_h[1][0], ref_pt_h[1][1]), 10 ,(255, 0, 255), -1)
            cv2.line(new_image, (ref_pt_h[0][0], ref_pt_h[0][1]), (ref_pt_h[1][0]+5, ref_pt_h[1][1]), (255, 0, 255), 3)
        if(len(ref_pt_v)!=0):
            #print(ref_pt_v)
            #cv2.circle(new_image, (ref_pt_v[0][0], ref_pt_v[0][1]), 10 ,(0, 0, 0), -1)
            #cv2.circle(new_image, (ref_pt_v[1][0], ref_pt_v[1][1]), 10 ,(0, 255, 255), -1)
            cv2.line(new_image, (ref_pt_v[0][0], ref_pt_v[0][1]), (inspectionpt[0], inspectionpt[1]), (255, 0, 255), 3)
            cv2.line(new_image, (ref_pt_v[1][0], ref_pt_v[1][1]), (inspectionpt[0], inspectionpt[1]), (255, 0, 255), 3)
        if(len(inspectionpt)!=0):
            #print(inspectionpt)
            #cv2.circle(new_image, (inspectionpt[0], inspectionpt[1]), 10 ,(255, 255, 0), -1)
            pass

        #======================算出檢測點位置========================================
        inspectionptcount = 0
        #上面找到線了 現在找點
        if(self.Inspection_pt[1][0]==True):#從第二個column出現開始灑點
            #灑第一個column的直線
            if(self.Inspection_pt[0][0]==True):
                number_of_pt = 4
                interval_now = (self.line_list[i][1][1]-self.line_list[i][0][1])/(number_of_pt)
                for j in range(number_of_pt):
                    #cv2.circle(new_image, (self.line_list[i][0][0], int(self.line_list[i][0][1]+interval_now*j)), 4 ,(150, 150, 150), -1)
                    self.Outer_Contour_InspectionPt[inspectionptcount][1] = (self.line_list[i][0][0], int(self.line_list[i][0][1]+interval_now*j))
                    inspectionptcount+=1

            #灑其他橫線
            for i in range(1, self.Number_of_Inspectionpt_Line):


                if(self.Inspection_pt[i][0]==True):
                    number_of_pt = 2
                    interval_x_top_now = (self.line_list[i-1][0][0] - self.line_list[i][0][0])/(number_of_pt)
                    interval_y_top_now = (self.line_list[i-1][0][1] - self.line_list[i][0][1])/(number_of_pt)

                    interval_x_bottom_now = (self.line_list[i-1][1][0] - self.line_list[i][1][0])/(number_of_pt)
                    interval_y_bottom_now = (self.line_list[i-1][1][1] - self.line_list[i][1][1])/(number_of_pt)

                    for j in range(number_of_pt):
                        self.Outer_Contour_InspectionPt[inspectionptcount][1] = (int(self.line_list[i][0][0] + interval_x_top_now*j)
                                    , int(self.line_list[i][0][1]+interval_y_top_now*j))
                        inspectionptcount+=1
                        # cv2.circle(new_image, (int(self.line_list[i][0][0] + interval_x_top_now*j)
                        #             , int(self.line_list[i][0][1]+interval_y_top_now*j)), 4 ,(150, 150, 150), -1)
                        if(i<self.Number_of_Inspectionpt_Line-1):
                            self.Outer_Contour_InspectionPt[inspectionptcount][1] = (int(self.line_list[i][1][0] + interval_x_bottom_now*j)
                                        , int(self.line_list[i][1][1]+interval_y_bottom_now*j))
                            inspectionptcount+=1                                    
                            # cv2.circle(new_image, (int(self.line_list[i][1][0] + interval_x_bottom_now*j)
                            #             , int(self.line_list[i][1][1]+interval_y_bottom_now*j)), 4 ,(150, 150, 150), -1)               
                            
            #最後一個Column
            if(self.Find_Back[0] == True):
                number_of_pt = 3
                CenterPt = (40+int((self.line_list[-1][0][0]+self.line_list[-1][-1][0])/2),int((self.line_list[-1][0][1]+self.line_list[-1][-1][1])/2))
                interval_x_top_now = (CenterPt[0] - self.line_list[-1][0][0])/(number_of_pt)
                interval_y_top_now = (CenterPt[1] - self.line_list[-1][0][1])/(number_of_pt)
                
                for j in range(number_of_pt):
                    cv2.circle(new_image, (int(self.line_list[-1][0][0] + interval_x_top_now*j)
                                , int(self.line_list[-1][0][1]+interval_y_top_now*j)), 4 ,(150, 150, 150), -1)
                    self.Outer_Contour_InspectionPt[inspectionptcount][1] = (int(self.line_list[-1][0][0] + interval_x_top_now*j)
                                , int(self.line_list[-1][0][1]+interval_y_top_now*j))
                    inspectionptcount+=1
            #print(inspectionptcount)
            #窗戶的直線
            if(len(ref_pt_v)!=0):               
                for vpt in range(2): 
                    number_of_pt = 6
                    interval_x_top_now = (ref_pt_v[vpt][0] - inspectionpt[0])/(number_of_pt)
                    interval_y_top_now = (ref_pt_v[vpt][1] - inspectionpt[1])/(number_of_pt)
                    for j in range(number_of_pt):
                        # cv2.circle(new_image, (int(inspectionpt[0] + interval_x_top_now*j)
                        #             , int(inspectionpt[1] + interval_y_top_now*j)), 4 ,(150, 150, 150), -1)
                        self.Window_H_InspectionPt[vpt*number_of_pt+j][1] = (int(inspectionpt[0] + interval_x_top_now*j),
                                                            int(inspectionpt[1] + interval_y_top_now*j))


            #窗戶的橫線
            if(self.ColCount>=4 and len(ref_pt_h)!=0):#第4個出來才有交點
                number_of_pt = 4+3*(self.ColCount-4)
                interval_x_top_now = (ref_pt_h[1][0] - ref_pt_h[0][0] )/(number_of_pt)
                interval_y_top_now = (ref_pt_h[1][1] - ref_pt_h[0][1] )/(number_of_pt)                
                for j in range(number_of_pt):
                    # cv2.circle(new_image, (int(ref_pt_h[0][0] + interval_x_top_now*j)
                    #             , int(ref_pt_h[0][1] + interval_y_top_now*j)), 4 ,(150, 150, 150), -1)
                    self.Window_V_InspectionPt[j][1] = (int(ref_pt_h[1][0] - interval_x_top_now*j), int(ref_pt_h[1][1] - interval_y_top_now*j))
                    inspectionptcount+=1         

        #=======================================找操作員==============================================
        operator_offsety = 150
        threshold = 40
        inspected_threshold = 15
        operator_now, M_operator = self.__find_operator(frame.copy()[operator_offsety:,], self.M_operator)
        cv2.drawContours(new_image, operator_now, 0, (0,255,0), 3, offset = (0,operator_offsety))
        x,y,w,h = cv2.boundingRect(operator_now[0])
        y = y + operator_offsety
        #cv2.rectangle(new_image,(x-threshold,y-threshold),(x+w+threshold,y+h+threshold),(0,255,0),2)

        #ComputeInspection
        self.__ComputeInspection(operator_now, self.Window_V_InspectionPt, operator_offsety, threshold, inspected_threshold)
        self.__ComputeInspection(operator_now, self.Window_H_InspectionPt, operator_offsety, threshold, inspected_threshold)
        self.__ComputeInspection(operator_now, self.Outer_Contour_InspectionPt, operator_offsety, threshold, inspected_threshold)
        # #=======================================畫出點===============================================

        if(self.Find_Front[0]==True):
            temp_inspection = self.Window_V_InspectionPt+self.Window_H_InspectionPt+self.Outer_Contour_InspectionPt
            for i in range(len(temp_inspection)):
                if(temp_inspection[i][0] == True):
                    cv2.circle(new_image, temp_inspection[i][1], 4, (0, 255, 0), -1)
                else:
                    cv2.circle(new_image, temp_inspection[i][1], 4, (150, 150, 150), -1)


            self.NowScore = max(self.NowScore, self.__ComputeScore(temp_inspection))
            cv2.putText(new_image, "Score: {}".format(self.NowScore), (50, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1.1, (50, 255, 50), 1, cv2.LINE_AA)
    
        

        return new_image, self.NowScore


