from Sparki import Sparki
import sys
import time
from multiprocessing import Pool, Queue, Manager
from Queue import Empty
import random
import evidencegrid


# The scale of the movement, aka how many CMs per 1 grid unit
# Only used in the current assignTask
CM_SCALE = 1

# The number of CM to map in any given direction from the origin
MAX_GRID_SIZE = 100 / CM_SCALE

# Manually set initial goals
goals = Queue()

# Are we still mapping?
notMapped = True

"""
Make some random goals to begin with, one for each Sparki in practice
"""
def generateInitGoals( number ):
	for i in xrange(0, number):
		randX = random.choice([1,-1]) * random.random() /3 * MAX_GRID_SIZE
		randY = random.choice([1,-1]) * random.random() /3 * MAX_GRID_SIZE
		goals.put((randX, randY),True)

"""
Replace with the code to go to a goal with Sparki
"""
def assignTask(goal, sparki):
	#################################################################v
	# Replace with what you want SParki to do
	# Don't forget to generate new goals throughout this function in some way
	# likely by just adding goals at all spots seen in the sweep
	if( not sparki.connect()):
		print "Sparki " + sparki.portName + " failed to connect"
		goals.put(goal, True)
		return

	sparki.goTo(goal[0],goal[1])

	randX = (random.random() * MAX_GRID_SIZE)
	randY = (random.random() * MAX_GRID_SIZE)

	new = (randX, randY)

	print goal
	#### Add Goals as found ####
	goals.put(new, True)
	
	#################################################################^

	# Free Sparki again
	sparki.disconnect()
	sparkis.put(sparki, True)
	

if __name__ == "__main__":

	if( (len(sys.argv)- 1) % 3 == 0):
		comPorts = sys.argv[1::3]
		xValues = sys.argv[2::3]
		yValues = sys.argv[3::3]
	else:
		print "Invalid args (ComPort X Y ...)"
		exit()

	sparkis = Queue(len(comPorts))
	q = Manager().Queue()
	evidencegrid.launch(0.01, 512, 512, q)

	for i in xrange(len(comPorts)):
		sparki = Sparki(comPorts[i],q)
		#if( not sparki.connect()):
		#	print "Sparki " + comPorts[i] + " failed to connect"
		#	continue
		#################################################################v
		# Set sparkis x and Y here
		sparki.tellSparkiPos(float(xValues[i]),float(yValues[i]),0)
		#################################################################^
		sparkis.put(sparki, True)

	if (sparkis.qsize() == 0):
		print "No Sparki given"
		exit()

	generateInitGoals(sparkis.qsize())

	processes =  Pool(processes=len(comPorts))

	while ( notMapped ):
		#################################################################v
		# Not needed in real code though we DO neeed a way to stop mapping
		# Butler is probably fine with us NOT stopping and jsut doing while true
		# Randomly forces an end for testing
		#if (random.random() > .95):
		#	notMapped = False
		#################################################################^

		try:
			sparki = sparkis.get(False)
		except Empty:
			pass
		else:
			goal = goals.get(True)
			processes.apply_async(assignTask, (goal, sparki))
			time.sleep(1)

	# Waits for all Sparkis to finish
	processes.close()
	processes.join()

	# Disconnect all Sparkis
	#for i in xrange(0, sparkis.qsize()):
	#	sparki = sparkis.get()
	#	sparki.disconnect()
