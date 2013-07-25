#!/usr/bin/env python
import matplotlib.pyplot as plt
import serial
import time
import sys
import numpy as np
import re
import signal
import argparse

#Setup Command line arguments
parser = argparse.ArgumentParser(
    prog = "reflow-profiler", 
    usage = "%(prog)s [options] input...",  
    description = "Log thermocouple data from serial to profile a reflow oven."
    )
parser.add_argument("-p", "--port", action='store', default='', help="set serial port")
parser.add_argument("-b", "--baudrate", action='store', type=int, default=115200, help="set serial port (default: 115200)")
parser.add_argument("-n", "--nograph", action='store_true', default=False, help="supress graph data")
parser.add_argument('--version', action='version', version="%(prog)s 0.0.1-dev")

#Always output help by default
if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(0)
args = parser.parse_args()

endLoop = False
char = ''
#Setup shutdown handlers
def signal_handler(signal, frame):
    print "Stop record."
    global endLoop
    endLoop = True
signal.signal(signal.SIGINT, signal_handler)
 
print "Reflow Profiler"
if args.port == "":
    print "No serial port specified, exiting"
    sys.exit(0)
   
print "Opening " + args.port
print "Connecting at " + str(args.baudrate) + " baud"
ser = serial.Serial(port=args.port, baudrate=args.baudrate)
print "Initializing thermocouple board"
ser.setDTR(False)
time.sleep(1)
ser.setDTR(True)
while not ser.inWaiting():
        time.sleep(0.1)

print "Press Enter to begin profiling"
ser.flushInput()
ser.flushOutput()
raw_input()


print "Gathering data"
profile = "Test started at: " +  time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
startTime = time.time()
output = ser.read(ser.inWaiting())
tempString = ""
lastLen = 0
lastTime = startTime
chars = 0
print "Current temp (C): ",
while not endLoop:
    char = ser.read(ser.inWaiting())
    output += char
    sys.stdout.write(char)
ser.close()
endTime = time.time()
humanEndTime = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
profile += "Test ended at: " + humanEndTime
runTime = endTime - startTime
samples = map(int,re.findall(r'\b\d+\b', output))
timeIncrement = runTime/len(samples)
timeScale = np.arange(0,runTime,timeIncrement)
residency = [0,0,0,0,0,0]
finding = 0
maxTemp = max(samples)

firstReading = False
startAbove227 = 0
endAbove227 = 0
#find time above points
lastVal = samples[0]
for idx, val in enumerate(samples):
    #clone prevoius val ifdeviate more than +-2 degrees
    if val in range(lastVal-3,lastVal+3,1):
        lastVal = val
    else:
        val = lastVal
        samples[idx] = lastVal
    if val == 40 and finding == 0:
        startTime = idx
        profileStart = idx
    elif val == 150 and finding == 0:
        lastTime = idx
        residency[finding] = (lastTime - startTime) * timeIncrement
        startTime = idx
        finding = 1
    elif val == 175 and finding == 1:
        lastTime = idx
        residency[finding] = (lastTime - startTime) * timeIncrement
        startTime = idx
        finding = 2
    elif val == maxTemp and finding == 2:
        lastTime = idx
        residency[finding] = (lastTime - startTime) * timeIncrement
        startTime = idx
        finding = 4
    elif val == 227 and not firstReading:
        startAbove227 = idx
        firstReading = True
    elif val == 227:
        endAbove227 = idx
    elif val == 95 and finding == 4:
        lastTime = idx
        residency[5] = (lastTime - profileStart) * timeIncrement/60
        
residency[3] = (endAbove227 - startAbove227) * timeIncrement
residency[4] = (227-40)/((endAbove227 - lastTime) * timeIncrement)                        
profile += "\nMax temp: " + str(maxTemp)
profile += "\nSeconds from 40C to 150C: " + str(residency[0])
profile += "\nSeconds from 150C to 175C: " + str(residency[1])
profile += "\nSeconds to max temp: " + str(residency[2])
profile += "\nSeconds above 227C: " + str(residency[3])
profile += "\nCooldown rate (C/sec): " + str(residency[4])
profile += "\nProfile length (min): " + str(residency[5]) + "\n"
print profile
profile = profile + "Data entries taken every " + str(timeIncrement) + " seconds:\n" + output
path = humanEndTime+".waveprofile"
f = open(path,"w")
f.write(profile)
f.close()
if not args.nograph:
    plt.plot(timeScale, samples)
    plt.plot([0,runTime],[150,150])
    plt.plot([0,runTime],[175,175])
    plt.plot([0,runTime],[227,227])
    plt.plot([0,runTime],[235,235])
    plt.plot([0,runTime],[255,255])
    plt.ylabel('Temp (C)')
    plt.xlabel('Time (S)')
    plt.title('Thermocouple Output')
    plt.show()


