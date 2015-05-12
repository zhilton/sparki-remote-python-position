# Sparki.py
# zde

import serial
import struct
import time
from math import atan2,sin,cos,sqrt,pi
from evidencegrid import EvidenceGrid
import window
from multiprocessing import Process, Manager

def dist(x1, y1, x2, y2):
	return sqrt((x1-x2)**2 + (y1-y2)**2)

class Sparki:

	SERVO_CENTER = 0
	SERVO_LEFT = 90
	SERVO_RIGHT = -90
	
	STATUS_OK = struct.pack('!B',0)
	MOVE_FORWARD = struct.pack('!B',1)
	MOVE_LEFT = struct.pack('!B',2)
	MOVE_RIGHT = struct.pack('!B',3)
	SERVO = struct.pack('!B',4)
	REQ_PING = struct.pack('!B',5)
	REQ_WHEELS = struct.pack('!B',6)
	MOVE_STOP = struct.pack('!B',7)
	REQ_LINESENS = struct.pack('!B',8)
	MOVE_FORWARD_DIST = struct.pack('!B',9)
	REQ_POS = struct.pack('!B',10)
	MOVE_RIGHT_DEG = struct.pack('!B',11)
	MOVE_LEFT_DEG = struct.pack('!B',12)
	SENSE = struct.pack('!B',13)
	UPDATE_POSE = struct.pack('!B',14)
	REQ_3PING = struct.pack('!B',15)

	portName = None
	serialPort = None

	EPS_XY = 3
	EPS_T = .035
	RAD_TO_DEG = 57.2957786
	LM_DIST = 5
	curX = 0
	curY = 0
	curTheta = 0

	lm = [] # array to store landmarks
	grid = EvidenceGrid(0.01, 512, 512) #evidence grid

	def __init__(self, comPort, q):
		# Error check if comPort is a string
		self.portName = comPort
		self.q = q

	"""
	Returns a boolean as to connection status
	"""
	def connect(self):
		print "Trying to Connect"
		self.serialPort = serial.Serial()
		self.serialPort.port = self.portName
		self.serialPort.baudrate = 9600
		self.serialPort.parity = 'N'
		self.serialPort.writeTimeout = 0.5
		# Might want to set other settings as well, to be safe
		self.serialPort.open()
		# Can throw ValueErrors on failure
		if (self.serialPort.isOpen()):
			print "Connected"
			self.servo(self.SERVO_CENTER)
			self.sendSparkiPos(self.curX, self.curY, self.curTheta)
			return True
		else:
			return False
	
	def disconnect(self):
		print "Disconnecting..."
		self.serialPort.close()
		if (self.serialPort.isClosed()):
			print "Disconnected"
	
	def moveForward(self, dist = 0):
		# Should be open port
		if (dist == 0):
			self.serialPort.write(self.MOVE_FORWARD)
		else:
			self.serialPort.write(self.MOVE_FORWARD_DIST)
			self.serialPort.write(struct.pack('f',dist))
	
	def moveBackward(self, dist = 0):
		# Should be open port
		if (dist == 0):
			self.serialPort.write(self.MOVE_BACKWARD)
		else:
			self.serialPort.write(self.MOVE_BACKWORD_DIST)
			self.serialPort.write(struct.pack('f',dist))

	def moveLeft(self, deg = 0):
		# Should be open port
		if (deg == 0):
			self.serialPort.write(self.MOVE_LEFT)
		else:
			self.serialPort.write(self.MOVE_LEFT_DEG)
			self.serialPort.write(struct.pack('f',deg))

	def moveRight(self, deg = 0):
		# Should be open port
		if (deg == 0):
			self.serialPort.write(self.MOVE_RIGHT)
		else:
			self.serialPort.write(self.MOVE_RIGHT_DEG)
			self.serialPort.write(struct.pack('f',deg))
	
	def moveStop(self):
		# Should be open port
		self.serialPort.write(self.MOVE_STOP)
	
	def servo(self, angle):
		# Should be open port
		# Should check angle to be int
		if (angle < -90 or angle > 90):
			print "Invalid servo angle: " + str(angle)
			return
		angle = -1*(angle) + 90
		self.serialPort.write(self.SERVO)
		self.serialPort.write(struct.pack('!B',angle))
	
	"""
	Returns an int of the ping value or -1
	"""
	def ping(self):
		# Should be open port
		distance = -1
		self.serialPort.write(self.REQ_PING)
		distance = int(self.readString())
		return distance
	
	"""
	Returns a list of ints for the travel of the two motors
	"""
	def totalTravel(self):
		# Should be open port
		values = [0,0]
		self.serialPort.write(self.REQ_WHEELS)
		retValues = self.readString().split()
		values[0] = int(retValues[0])
		values[1] = int(retValues[1])
		return values

	def updatePosition(self):
		self.serialPort.write(self.REQ_POS)
		pos = self.readString().split()
		self.curX = float(pos[0])
		self.curY = float(pos[1])
		self.curTheta = float(pos[2])

	
	"""
	Returns a list of the line sensor data
	"""
	def lineSense(self):
		# Should be open port
		values = [0,0,0,0,0]
		self.serialPort.write(self.REQ_LINESENS)
		retValues = self.readString().split()
		values[0] = int(retValues[0])
		values[1] = int(retValues[1])
		values[2] = int(retValues[2])
		values[3] = int(retValues[3])
		values[4] = int(retValues[4])
		return values
	
	"""
	Reads return strings from Sparki that EOL with '*'
	Returns the string
	"""
	def readString(self):
		# Should be open port
		# Validate that conversion to string works
		output = ""
		last = ""
		while (True):
			last = str(self.serialPort.read(size=1))
			if (last == "*"):
				break
			output = output + last
		return output
	
	def delay(self, duration):
		# Should validate time is int in milliseconds
		time.sleep(duration/1000)

	"""
	Stops sparki, collects and sends
	all three ping reads to the evidence grid.
	"""	
	def dataCollandSend(self):
		# Request data from sparki to add to map
		# Req3Ping returns 3 pings (-90,0,90) and the position
		# Also stops sparki
		self.serialPort.write(self.REQ_3PING);
		# 0-2 are ping values, followed by X, Y, theta.
		valpos = self.readString().split();
		for x in xrange(5):
			valpos[x] = float(valpos[x]) / 100
		valpos[5] = float(valpos[5])
		thetachange = pi/2;
		# Send all three values to evidence grid.
		print valpos
		for x in xrange(0,3):
			if valpos[x] != -1:
				self.q.put((valpos[x],(thetachange + valpos[5]), valpos[3], valpos[4]))
				print valpos[x],(thetachange + valpos[5]), valpos[3], valpos[4]
			else: 
				self.q.put(((thetachange + valpos[5]), valpos[3], valpos[4]))
				print (thetachange + valpos[5]), valpos[3], valpos[4]
			thetachange -= pi / 2;	

		
	def goTo(self, x, y):
		while (dist(self.curX, self.curY, x, y) > self.EPS_XY):
			
			self.dataCollandSend();
			
			# Move on to goto
			self.serialPort.write(self.SENSE) # try and detect landmark
			retValue = int(self.readString())
			if (retValue == 1): # landmark sensed
				# do "slam"
				self.updatePosition()
				self.slam(self.curX, self.curY, self.curTheta)
				# turn towards goal and move out of landmark
				phi = atan2(y - self.curY, x - self.curX); 
				delta_theta = atan2(sin(phi - self.curTheta),cos(phi - self.curTheta)) 
				if (abs(delta_theta) > self.EPS_T): 
					self.moveLeft(delta_theta*self.RAD_TO_DEG)
				self.moveForward(7)
				self.updatePosition()
			phi = atan2(y - self.curY, x - self.curX); # bearing of goal
			delta_theta = atan2(sin(phi - self.curTheta),cos(phi - self.curTheta)) # signed difference between bearing and goal
			if (abs(delta_theta) < self.EPS_T): # if facing goal -> move forward
				self.moveForward()
			else:
				self.moveLeft(delta_theta*self.RAD_TO_DEG)
			self.updatePosition()
			print self.lm
		self.moveStop()

	def sendSparkiPos(self, x, y, theta):
		self.serialPort.write(self.UPDATE_POSE)
		self.serialPort.write(struct.pack('f',x))
		self.serialPort.write(struct.pack('f',y))
		self.serialPort.write(struct.pack('f',theta))

	def tellSparkiPos(self, x, y, theta):
		self.curX = x
		self.curY = y
		self.curTheta = theta
		if ((self.serialPort is not None) and self.serialPort.isOpen()):
			sendSparkiPos(self,self.curX, self.curY, self.curTheta)

	def slam(self, x, y, theta):
		# match up landmark
		lm_found = False
		for lm in self.lm:
			if dist(x,y,lm[0],lm[1]) < self.LM_DIST: # found match update sparki/lm position
				# compute weighted avg based on number of time landmark has been observed
				tmp_x = (1.0 / (1 + lm[3]))*self.curX + (float(lm[3]) / (1 + lm[3]))*lm[0]
				tmp_y = (1.0 / (1 + lm[3]))*self.curY + (float(lm[3]) / (1 + lm[3]))*lm[1]
				tmp_theta = (1.0 / (1 + lm[3]))*self.curTheta + (float(lm[3]) / (1 + lm[3]))*lm[2]
				# update x,y,theta on Sparki
				self.sendSparkiPos(tmp_x, tmp_y, tmp_theta)
				# update x,y,theta of landmark
				lm[0] = tmp_x
				lm[1] = tmp_y
				lm[2] = tmp_theta
				# update number of times lm has been seen
				lm[3] += 1
				lm_found = True
				break
		if not lm_found:
			self.lm.append([x,y,theta,1]) # add x,y,theta to landmarks and inital number of times seen (1)
