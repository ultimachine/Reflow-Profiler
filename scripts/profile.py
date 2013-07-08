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
parser.add_argument("-o", "--output", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help = "Output file, defaults to stdout")
parser.add_argument("input", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help = "Input file, defaults to stdin")
parser.add_argument("-g", "--graph", action='store_true', default=True, help="graph data")
parser.add_argument("-p", "--port", action='store', default='', help="set serial port")
parser.add_argument("-b", "--baudrate", action='store', type=int, default=115200, help="set serial port (default: 115200)")
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
print "Enter serial port : "
port = "/dev/ttyACM0"
print "Enter baudrate :"
baud = 115200
ser = serial.Serial(port = port,baudrate = int(baud))
print port
print baud
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
print "Test started at" +  str(time.gmtime())
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
path = time.strftime("%Y-%m-%d~%H:%M:%S", time.gmtime())+".waveprofile"
f = open(path,"w")
f.write(output)
f.close()
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

