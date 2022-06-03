import RPi.GPIO as GPIO
import time
import servomo  as ser
import mysql.connector
from mysql.connector import Error
from datetime import datetime


trigger_pin = 23
echo_pin = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(trigger_pin, GPIO.OUT)
GPIO.setup(echo_pin, GPIO.IN)

fod_time=[] #設定紀錄時間list
fod_dist=[] #設定紀錄距離list
fod_reco=[] #設定紀錄文字list


def TurnOnLED(GPIOnum):
    GPIO.output(GPIOnum, True)

def TurnOffLED(GPIOnum):
    GPIO.output(GPIOnum, False)
    
def Setup(GPIOnum, OUT_IN):
    GPIO.setmode(GPIO.BCM)
    
    if OUT_IN == "OUT" :
        GPIO.setup(GPIOnum, GPIO.OUT)
    else:
        GPIO.setup(GPIOnum, GPIO.IN)
        
def send_trigger_pulse():
    GPIO.output(trigger_pin, True)
    time.sleep(0.00001)
    GPIO.output(trigger_pin, False)



def distance(speed=34000):#計算超音波感測器距離
    send_trigger_pulse()
    while GPIO.input(echo_pin) == 0 :
        StartTime = time.time()
        
    while GPIO.input(echo_pin) == 1:
        StopTime = time.time()
        
    TimeElapsed = StopTime - StartTime
    distance_cm = (TimeElapsed * speed) / 2
    
    return distance_cm
    
    
if __name__ == "__main__":
    try:  
        while True:
            for d in range(0,60,1): #每60筆匯入資庫庫
                dist = distance() #計算距離
                currentTime = time.strftime("%Y-%m-%d %H:%M:%S") #目前偵測時間
                record=""
                
                if dist<15: #當偵測異物距離<15cm
                    record="注意！！有異物靠近" #紀錄狀態
                    
                    for i in range(5): #並設定伺服馬達轉動五次
                        ser.SetAngle(0) #設定旋轉角度
                        ser.SetAngle(90)
                        ser.SetAngle(180)
                        time.sleep(0.5)
                        ser.SetAngle(90)
                        ser.SetAngle(0)
                        time.sleep(0.5)
                        Setup(2, "OUT") #LED亮燈提醒
                        TurnOnLED(2)
                        time.sleep(0.5)
                        TurnOffLED(2)
                        time.sleep(0.5)

                else: #假設>15cm
                    record="附近無異物" #紀錄狀態
                    ser.SetAngle(0) #並設定伺服馬達動動
                    time.sleep(1)
                    
                fod_time.append(currentTime) #將記錄新增至list
                fod_dist.append(dist)
                fod_reco.append(record)
                record_list = list(zip(fod_time,fod_dist , fod_reco)) #將list用zip串為一筆
                print (currentTime,"Object Distance = %.1f cm" % dist, record)
                time.sleep(1)
                
            try:
                # 連接 MySQL/MariaDB 資料庫
                connection = mysql.connector.connect(
                    host='',          # 主機名稱
                    database='', # 資料庫名稱
                    user='',        # 帳號
                    password='')  # 密碼
                # 新增資料
                sql = """INSERT INTO food (datetime, distance, record) VALUES (%s, %s, %s);"""
                print("將紀錄儲存至DB-food中")
                
                cursor = connection.cursor()
                cursor.executemany(sql, record_list)

                # 確認資料有存入資料庫
                connection.commit()
                
                
                # close connect
                cursor.close()
                print("DB連線已關閉")

            finally:
                if (connection.is_connected()):
                    cursor.close()
                    connection.close()
            
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup ()