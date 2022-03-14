import redis
import serial
from time import sleep

# Connects to Redis database on port 6379
r = redis.Redis(host='192.168.1.8', port=6379, db=0)
# Connect to Decawave tag over serial
DWM = serial.Serial(port="/dev/ttyACM0", baudrate=115200)
# Writes two carriage returns to initiate communication with Decawave tag
DWM.write("\r\r".encode())
print("Entering UART Shell Mode")
sleep(2)
# Tell Decawave board to start sending data
DWM.write("lec\r".encode())
print("Sending Data")
sleep(2)
try:
    while True:
        data = DWM.readline()  # Puts serial contents into variable data
        if(data):
            # Ensures recieved data has distances from all anchors
            if ("DIST".encode() in data and "AN0".encode() in data and "AN1".encode() in data and "AN2".encode() in data):
                data = data.replace("\r\n".encode(), "".encode())  # Puts all the data on one line by removing enters and new lines
                data = data.decode().split(",")  # Splits the data using commas
                if("POS" in data):
                    x_pos = str(int(float(data[data.index("POS")+1])*100))  # Gets byte value of x
                    y_pos = str(int(float(data[data.index("POS")+2])*100))  # Gets byte value of y
                    pos = ('X,'+x_pos+',Y,'+y_pos)  # Creates formate for the program to split
                    print(pos)
                    r.set('pos', pos)  # Sets the cordinates to the database named pos
except KeyboardInterrupt:
    DWM.write("\r".encode())
    DWM.close()
    print("Stop")