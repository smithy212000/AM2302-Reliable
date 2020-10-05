import Adafruit_DHT
import sys, sched, time
from datetime import datetime
import mysql.connector

mainDb = mysql.connector.connect(
    host="mySql_hostname",
    user="mySql_username",
    password="mySql_password",
    database="mySql_database"
)

sensor = Adafruit_DHT.DHT22
pin = 4
interval = 30

# Don't modify below here (unless you want to)

cursor = mainDb.cursor()
sql = "INSERT INTO logger (date, time, temp, humidity, avgTemp, avgHumidity, iteration, badVal) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
s = sched.scheduler(time.time, time.sleep)

avgTemp = 0.0
avgHumi = 0.0
badValCounter = 0
autoFilterIter = 0
autoFilterTmp = [0, 0, 0, 0, 0, 0]

def getClimate():
    humi, temp = Adafruit_DHT.read_retry(sensor, pin)
    humi = round(humi, 2)
    temp = round(temp, 2)
    return humi, temp

def genAvgSave(dat0, dat1, dat2, option):
    global avgTemp
    global avgHumi
    if option == "deg":
        avgTemp = round((dat0 + dat1 + dat2) / 3, 2)
        return
    if option == "hum":
        avgHumi = round((dat0 + dat1 + dat2) / 3, 2)
        return
    else:
        print("Invalid option for genAvgSave()")
        return

def filterTrain():
    print("Getting 3 humidity and temperature values.\nType YES if the values do not contain anomalies when they are shown.")
    stor0 = getClimate()[1]
    stor1 = getClimate()[1]
    stor2 = getClimate()[1]
    storH0 = getClimate()[0]
    storH1 = getClimate()[0]
    storH2 = getClimate()[0]
    print(str(stor0)+" / "+str(stor1)+" / "+str(stor2)+"\n"+str(storH0)+" / "+str(storH1)+" / "+str(storH2))
    print("Do these values look correct and not differ too much? Enter YES if OK.")
    choice = str(input("Enter: "))
    if "YES" in choice:
        genAvgSave(stor0, stor1, stor2, "deg")
        genAvgSave(storH0, storH1, storH2, "hum")
        print("Saved averages for filtering.")
        print("Average Temperature: "+str(avgTemp)+"C\nAverage Humidity: "+str(avgHumi)+"%\n\n\n")
        return
    else:
        sys.exit("Cancelling.")

def autoFilter(temp0, hum0, temp1, hum1, temp2, hum2):
    print("autoFilter >")
    oldAvgH = avgHumi
    oldAvgT = avgTemp
    genAvgSave(temp0, temp1, temp2, "deg")
    genAvgSave(hum0, hum1, hum2, "hum")
    print("oldAvg="+str(oldAvgT)+"degC/"+str(oldAvgH)+"%")
    print("newAvg="+str(avgTemp)+"degC/"+str(avgHumi)+"%\n")
    return

def filtering(dataIn):
    global badValCounter
    upperLimitH = avgHumi + 7
    lowerLimitH = avgHumi - 7
    upperLimitT = avgTemp + 3
    lowerLimitT = avgTemp - 3
    print("filtering >\nULH="+str(upperLimitH)+"%/LLH="+str(lowerLimitH)+"%/ULT="+str(upperLimitT)+"degC/LLT="+str(lowerLimitT))
    if dataIn[0] < lowerLimitH or dataIn[0] > upperLimitH:
        print("Reject="+str(dataIn[0])+"%")
        badValCounter = badValCounter + 1
        print("BadVal="+str(badValCounter)+"\n")
        return False
    elif dataIn[1] < lowerLimitT or dataIn[1] > upperLimitT:
        print("Reject="+str(dataIn[1])+"degC")
        badValCounter = badValCounter + 1
        print("BadVal="+str(badValCounter)+"\n")
        return False
    else:
        print("Accept="+str(dataIn[1])+"degC/"+str(dataIn[0])+"%\n")
        return True

def getTempAndCheck():
    global autoFilterIter
    global autoFilterTmp
    stor = getClimate()
    print("getTempAndCheck >")
    if filtering(stor):
        print("GoodVal-iter="+str(autoFilterIter))
        if autoFilterIter == 0:
            autoFilterTmp[0] = stor[1]
            autoFilterTmp[1] = stor[0]
            autoFilterIter = autoFilterIter + 1
        elif autoFilterIter == 1:
            autoFilterTmp[2] = stor[1]
            autoFilterTmp[3] = stor[0]
            autoFilterIter = autoFilterIter + 1
        elif autoFilterIter == 2:
            autoFilterTmp[4] = stor[1]
            autoFilterTmp[5] = stor[0]
            autoFilter(autoFilterTmp[0],autoFilterTmp[1],autoFilterTmp[2],autoFilterTmp[3],autoFilterTmp[4],autoFilterTmp[5])
            print("ResetIter")
            autoFilterIter = 0
        return stor
    else:
        return 0

def logTempLoop(sc):
    global autoFilterIter
    global badValCounter
    global interval
    stor = getTempAndCheck()
    print("logTempLoop >")
    now = datetime.now()
    if stor is not 0:
        print("LOG="+now.strftime("DATE:%d/%m/%Y TIME:%H:%M:%S")+" TEMP:"+str(stor[1])+" HUMIDITY:"+str(stor[0])+" AVGTEMP:"+str(avgTemp)+" AVGHUMIDITY:"+str(avgHumi) + " ITERATION:"+str(autoFilterIter)+" BADVAL:"+str(badValCounter))
        cursor.execute(sql, (now.strftime("%d/%m/%Y"), now.strftime("%H:%M:%S"), str(stor[1]) + "C", str(stor[0]) + "%", str(avgTemp) + "C", str(avgHumi) + "%", str(autoFilterIter), str(badValCounter)))
        mainDb.commit()
    else:
        print("Not logging rejected value")
    s.enter(interval, 1, logTempLoop, (sc,))

filterTrain()
s.enter(interval, 1, logTempLoop, (s,))
s.run()
