from Sparki import Sparki
import sys
import time
from multiprocessing import Pool, Queue, Manager
from Queue import Empty
import random
import evidencegrid

# The scale of the movement, aka how many CMs per 1 grid unit
# Only used in the current MAX_GRID_SIZE
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
Run the passed function on the passed Sparki process
"""
def read_msg(sparki, data):
    funcname, args = data
    func = getattr(sparki, funcname)
    func(*args)

"""
Start a loop for a Sparki process
"""
def loopFunct(q, sparki):
    if( not sparki.connect()):
		print "Sparki " + sparki.portName + " failed to connect"
		exit()
    while True:
        try:
            message = q.get()
            read_msg(sparki, (message[0], message[1]))
        except Empty:
            pass
    sparki.disconnect

"""
Replace with the code to go to a goal with Sparki
"""
def assignGoal(goal, sparkiQ):
	sparkiQ.put( ('goTo', (goal[0],goal[1],)), True )

	randX = (random.random() * MAX_GRID_SIZE)
	randY = (random.random() * MAX_GRID_SIZE)

	new = (randX, randY)
	#### Add Goals as found ####
	goals.put(new, True)
	sparkis.put(sparkiQ, True)

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

	processes =  Pool(processes=len(comPorts))

	for i in xrange(len(comPorts)):
		sparki = Sparki(comPorts[i],q)
		# Set sparkis x and Y here
		sparki.tellSparkiPos(float(xValues[i]),float(yValues[i]),0)
		sparkiQ = Manager().Queue()
		processes.apply_async(loopFunct, (sparkiQ, sparki))
		sparkis.put(sparkiQ, True)

	if (sparkis.qsize() == 0):
		print "No Sparki given"
		exit()

	generateInitGoals(sparkis.qsize())

	while ( notMapped ):
		try:
			sparkiQ = sparkis.get(False)
		except Empty:
			pass
		else:
			goal = goals.get(True)
			assignGoal(goal, sparkiQ)
			time.sleep(1)

	# Waits for all Sparkis to finish
	processes.close()
	processes.join()
