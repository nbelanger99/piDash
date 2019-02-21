import time
import datetime
import csv
import tkinter
import can
import random
from tkinter import *
from can import *
import RPi.GPIO as GPIO

#GPIO Init
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off

#initializing the window
bgrndColor = "black"
nrmlTextColor = "green2"
errTextColor = "red"

root = Tk()
root.overrideredirect(True)
root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))
root.configure(background=bgrndColor, cursor="none")

tagMessages = ["piDash is developing emotions", "( ͡° ͜ʖ ͡°)", "piDash is getting loaded", "~10 screws and plate sold seperately~", "piDash contemplating life choices", "Do a flip!", "Nick loves youuuu <3", "It's fun to stay at the ... Y M C A !", "SELF DESTRUCT SEQUENCE ACTIVATED", "Full send bro", "It be like that sometimes", "The cake is a lie", "Half Life 3 Confirmed", "Weclome to SVT", "Bet you won't hit 60 MPH", "Hooty Hoo", "Law and Order EVT DUN DUN", "Come here often?", "A E S T H E T I C", "I reject your reality and substitute my own", "This isn't even piDash's final form", "*Jesus takes wheel*", "My motor controller is telling me no; my throttle is telling me yes", "You drive like my ex", "Zero thiccness error", "piDash rated PE, parental guidence", "The past participle of yeet is have yaunt", "But can your Prius do this?", "You wanna Sprite Cranberry", "At least take piDash out to dinner first"]

#Dynamic lables - just a few examples of readings that can be displayed
speedo = Label(root, font = "Helvetica 112", background=bgrndColor, foreground=nrmlTextColor)
voltMeter = Label(root, font = "Helvetica 36", background=bgrndColor, foreground=nrmlTextColor)
stateCharge = Label(root, font = "Helvetica 48", background=bgrndColor, foreground=nrmlTextColor)
errLabel = Label(root, font = "Helvetica 16", background=bgrndColor, foreground=errTextColor)
lowAvgHigh = Label(root, font = "Helvetica 12", background=bgrndColor, foreground=nrmlTextColor)
tagLabel = Label(root, text = tagMessages[random.randint(0,len(tagMessages)-1)], font = "Helvetica 12", background=bgrndColor, foreground=nrmlTextColor)
speedo.grid(row=2, column=0, columnspan=3, sticky=N)
voltMeter.grid(row=1, column=0)
stateCharge.grid(row=0, column=0)
errLabel.grid(row=0, column=2, rowspan=2)
lowAvgHigh.grid(row=3, column=0, columnspan=3)
tagLabel.grid(row=4, column=0, columnspan=3)

root.columnconfigure(2, weight=1)
root.rowconfigure(2, weight=1)

#initializing log
stamp = datetime.datetime.now().isoformat()
log = open("/home/pi/piDash2/"+stamp+".csv", "w")
logger = csv.writer(log, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
header = ["Time", "RPM", "Speed", "Motor Current", "Pack Voltage", "Controller Temperature", "Motor Temperature", "Lowest Cell Voltage", "Low Cell Voltage ID", "Average Cell Voltage", "Highest Cell Voltage", "High Cell Voltage ID", "State of Charge", "Errors"]

for i in range(1,25):
	header.append("V" + str(i))

for i in range(1,25):
	header.append("R" + str(i))

logger.writerow(header)

start = time.time()

#Defining a bus and message object
bus = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=250000)
msg = Message

# Cell Voltage and Resistance list and log row list
cellV = [0] * 24
cellR = [0] * 24

#An object for anything that is to be measured through the can bus
class reading():
	def __init__(self, id, data):
		self.id = id
		self.data = data

	#Checking the msg object for the ID we're looking for
	def checkFor(self):
		if self.id == msg.arbitration_id:
			self.data = msg.data

#Defining readings ... id is the can-bus ID, data is initialized as a bytearray
kelly1 = reading(id=217128453, data=(b'\x00\x00\x00\x00\x00\x00\x00\x00'))
kelly2 = reading(id=217128709, data=(b'\x00\x00\x00\x00\x00\x00\x00\x00'))
orion1 = reading(id=2047, data =(b'\x00\x00\x00\x00\x00\x00\x00\x00'))
orion2 = reading(id=191, data =(b'\x00\x00\x00\x00\x00\x00\x00\x00'))
orion3 = reading(id=54, data =(b'\x00\x00\x00\x00\x00\x00\x00\x00'))

def update():

	#exit button
	if GPIO.input(10) == GPIO.HIGH:
		quit()

	#global variabeles
	global msg
	global logRow
	global cellV

	logRow = []

	#Reading canbus data into global message object
	msg = bus.recv(timeout=5)

	#Kelly errors in english
	errList1 = ["Throttle Error", "Over Temp", "Internal Voltage", "Motor Stall", " ", "Low Voltage", "Over Voltage", "Identification Error"]
	errList2 = ["H.G. Sensor", "Motor over-temp", " ", " ", "Angle Sensor error", "Throttle Short", "Internal Rst"]

	# Checking for readings
	kelly1.checkFor()
	kelly2.checkFor()
	orion1.checkFor()
	orion2.checkFor()
	orion3.checkFor()

	# Parsing Kelly1
	rpm = kelly1.data[1] * 256 + kelly1.data[0]
	speed = rpm * .0138
	motorCurrent = (kelly1.data[3] * 256 + kelly1.data[2]) / 10
	battVoltage = (kelly1.data[5] * 256 + kelly1.data[4]) / 10

	speedo['text']= round(speed), "MPH"
	#ampMeter['text']=round(motorCurrent), "A"
	voltMeter['text']=(battVoltage), "V"

	#Handling kelly1 errors
	kellyErr1 = str(bin(int(hex(kelly1.data[6]), 16))[2:].zfill(8))
	kellyErr2 = str(bin(int(hex(kelly1.data[7]), 16))[2:].zfill(8))

	errs = " "

	for x in range (0, 8):
		if kellyErr1[x] == "1":
			errs += errList1[x]
	for x in range (0, 8):
		if kellyErr2[x] == "1":
			errs += errList2[x]

	if (kelly1.data[6] == 0 & kelly1.data[7] == 0):
		errs = " "

	errLabel['text'] = errs

	#Parsing kelly2
	contrTemp = kelly2.data[1] - 40
	motrTemp = kelly2.data[2] - 30

	#Parsing orion1
	lowCell = (orion1.data[0] * 256 + orion1.data[1]) / 10000
	highCell = (orion1.data[2] * 256 + orion1.data[3]) / 10000
	avgCell = (orion1.data[4] * 256 + orion1.data[5]) / 10000

	lowAvgHigh['text'] = "Low:", lowCell, "Avg:", avgCell, "High:", highCell

	#Parsing orion2
	soc = orion2.data[0] / 2
	stateCharge['text'] = soc, "%"
	highID = orion2.data[5]
	lowID = orion2.data[6]

	#Parsing orion3
	cellV[orion3.data[0]] = (orion3.data[1] * 256 + orion3.data[2]) / 10000
	cellR[orion3.data[0]] = (orion3.data[3] * 256 + orion3.data[4]) / 10000

	#Appending data to global row list
	logRow.append(time.time()- start)
	logRow.append(rpm)
	logRow.append(speed)
	logRow.append(motorCurrent)
	logRow.append(battVoltage)
	logRow.append(contrTemp)
	logRow.append(motrTemp)
	logRow.append(lowCell)
	logRow.append(lowID)
	logRow.append(avgCell)
	logRow.append(highCell)
	logRow.append(highID)
	logRow.append(soc)
	logRow.append(errs)

	for x in range (0, 24):
		logRow.append(cellV[x])

	for x in range (0, 24):
		logRow.append(cellR[x])

	logger.writerow(logRow)

	#Setting the function to be called in tkinter event loop
	root.after(1, update)

update()
root.mainloop()
