
import serial
import time 
import cv2
port = "COM4"
ser = serial.Serial(port = port, baudrate = 115200, bytesize = serial.EIGHTBITS, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, timeout=0)
#print (ser)
Car = 0
prevPLCvalue = 0
PLCvalue = 0
NewCarFlag = False

while(1):

    nowtime = time.time()

    try:
        prevPLCvalue = PLCvalue
        PLCvalue = int.from_bytes(ser.read(100), "big")
        #print(PLC_last_read, time.time())
        #print("PLC: ",PLCvalue)

        if(PLCvalue!=0):
            print("{}: PLCValue != 0".format(nowtime))
        if(PLCvalue!=0 and prevPLCvalue==0):
            NewCarFlag = True
    except:
        NewCarFlag = False
        print("Exception")

    if(NewCarFlag):
        Car+=1
        NewCarFlag = False
        print("Car Number: ", Car)


    if cv2.waitKey(55):
        pass
    #     #print("-")