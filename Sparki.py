# Sparki.py
# zde

import serial
import struct
import time
from math import atan2,sin,cos,sqrt

def dist(x1, x2, y1,y2):
	return sqrt((x1-x2)**2 + (y1-y2)**2)

class Sparki:

	SERVO_CENTER = 0
	SERVO_LEFT = 90
	SERVO_RIGHT = -90
	
	STATUS_OK = struct.pack('!B',0)
	MOVE_FORWARD = struct.pack('!B',1)
	MOVE_BACKWARD = struct.pack('!B',2)
	MOVE_LEFT = struct.pack('!B',3)
	MOVE_RIGHT = struct.pack('!B',4)
	SERVO = struct.pack('!B',5)
	REQ_PING = struct.pack('!B',6)
	REQ_WHEELS = struct.pack('!B',7)
	MOVE_STOP = struct.pack('!B',8)
	REQ_LINESENS = struct.pack('!B',9)
	MOVE_FORWARD_DIST = struct.pack('!B',10)
	REQ_POS = struct.pack('!B',11)
	MOVE_BACKWORD_DIST = struct.pack('!B',12)
	MOVE_RIGHT_DEG = struct.pack('!B',13)
	MOVE_LEFT_DEG = struct.pack('!B',14)

	portName = None
	serialPort = None

	EPS_XY = .05
	EPS_T = .035
	curX = curY = curTheta = 0

	def __init__(self, comPort):
		# Error check if comPort is a string
		self.portName = comPort
		self.serialPort = serial.Serial()

	"""
	Returns a boolean as to connection status
	"""
	def connect(self):
		print "Trying to Connect"
		self.serialPort.port = self.portName
		self.serialPort.baudrate = 9600
		self.serialPort.parity = 'N'
		self.serialPort.writeTimeout = 0
		# Might want to set other settings as well, to be safe
		self.serialPort.open()
		# Can throw ValueErrors on failure
		if (self.serialPort.isOpen()):
			print "Connected"
			self.servo(self.SERVO_CENTER)
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
		print pos
		self.curX = pos[0]
		self.curY = pos[1]
		self.curTheta = pos[2]

	
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
	
	def delay(self, time):
		# Should validate time is int in milliseconds
		time.sleep(time/1000)

	def go_to(self, x, y):
		if (abs(self.curX - x) < self.EPS_XY  and abs(self.curY - y) < self.EPS_XY ): # Check if at goal
			self.moveStop()
			return True
		else: # Move toward goal
			phi = atan2(y - self.curY, x - self.curX); # bearing of goal
			delta_theta = atan2(sin(phi - self.curTheta),cos(phi - self.curTheta)) # signed difference between bearing and goal
			if (abs(delta_theta) < self.EPS_T): # if facing goal -> move forward
				self.moveForward(dist(x,self.curX,y,self.curY))
			elif (delta_theta > 0): # else turn toward goal
				self.moveLeft()
			else:
				self.moveRight()
		self.updatePosition()
		return False;

	def printPos(self):
		print self.curX,self.curY,self.curTheta
