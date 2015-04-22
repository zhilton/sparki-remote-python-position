# Sparki.py
# zde

import serial
import struct
import time
from math import atan2,sin,cos

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
	
	def moveForward(self):
		# Should be open port
		self.serialPort.write(self.MOVE_FORWARD)

	def moveForwardDist(self, dist):
		# Should be open port
		self.serialPort.write(self.MOVE_FORWARD_DIST)
		self.serialPort.write(struct.pack('f',dist))
	
	def moveBackward(self):
		# Should be open port
		self.serialPort.write(self.MOVE_BACKWARD)

	def moveBackwardDist(self, dist):
		# Should be open port
		self.serialPort.write(self.MOVE_BACKWARD_DIST)
		self.serialPort.write(struct.pack('f',dist))
	
	def moveLeft(self):
		# Should be open port
		self.serialPort.write(self.MOVE_LEFT)

	def moveLeftDeg(self, deg):
		# Should be open port
		self.serialPort.write(self.MOVE_LEFT_DEG)
		self.serialPort.write(struct.pack('f',deg))
	
	def moveRight(self):
		# Should be open port
		self.serialPort.write(self.MOVE_RIGHT)

	def moveRightDeg(self, deg):
		# Should be open port
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
		pos = self.serialPort.read(size=12)
		retValues = struct.unpack("fff", pos)
		curX = retValues[0]
		curY = retValues[1]
		curTheta = retValues[2]

	
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

	def go_to(x, y):
		if (abs(sparki.curX - x) < EPS_XY  and abs(sparki.curY - y) < EPS_XY ): # Check if at goal
			moveStop()
			return True
		else: # Move toward goal
			phi = atan2(y - sparki.curY, x - sparki.curX); # bearing of goal
			delta_theta = atan2(sin(phi - sparki.curTheta),cos(phi - sparki.curTheta)) # signed difference between bearing and goal
			if (abs(delta_theta) < EPS_T): # if facing goal -> move forward
				moveForward()
			elif (delta_theta > 0): # else turn toward goal
				moveLeft()
			else:
				moveRight()
		return False;

	def readLandmark():
		sense = sparki.lineSense()
		if (sense[0] == 1 and sense[4] != 1): # turn left
			while (sense[4] != 1):
				turnLeft()
				sense = lineSense()
		elif (sense[0] != 1 and sense[4] == 1): # turn right
			while (sense[0] != 1):
				turnRight()
				sense = lineSense()
		# move towards center counting rings
		count = 0
		on_ring = False
		pos = curX, curY
		while (dist(curX, pos[0], curY, pos[1]) < .07): # haven't hit center of barcode
			sense = lineSense()
			if (sense[2] == 1 and on_ring == False):
				count += 1
				on_ring = True
			elif (sense[2] == 0 and on_ring == True):
				on_ring = False
			moveForward()
		# At center of barcode
		while (sense[2] != 1):
			moveLeft()
			sense = lineSense()
		return count