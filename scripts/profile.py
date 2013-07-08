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
ser.setDTR(0)
time.sleep(1)
ser.setDTR(1)
while not ser.inWaiting():
        time.sleep(0.1)

print "Press Enter to begin profiling"
ser.flushInput()
ser.flushOutput()
raw_input()

print "Gathering data"
print "Test started at" +  time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
startTime = time.time()
output = ser.read(ser.inWaiting())

lastTime = startTime
while not endLoop:
    char = ser.read(ser.inWaiting())
    sys.stdout.write(char)
    output += char
endTime = time.time()
runTime = endTime - startTime
samples = map(int,re.findall(r'\b\d+\b', output))
timeScale = np.arange(0,runTime,runTime/len(samples))

path = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())+".waveprofile"
f = open(path,"w")
f.write(output)
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
ser.close()

