from Sparki import Sparki
import sys
import time
from multiprocessing import Pool, Queue
from Queue import Empty

#################################################################v
# Not needed in real code
import random
#################################################################^

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
		randX = random.choice([1,-1]) * random.random() * MAX_GRID_SIZE
		randY = random.choice([1,-1]) * random.random() * MAX_GRID_SIZE
		goals.put((randX, randY),True)

"""
Replace with the code to go to a goal with Sparki
"""
def assignTask(goal, sparki):
	#################################################################v
	# Replace with what you want SParki to do
	# Don't forget to generate new goals throughout this function in some way
	# likely by just adding goals at all spots seen in the sweep
	while( not sparki.go_to( (goal[0] * CM_SCALE), (goal[1]) * CM_SCALE)):
		pass
	randX = (random.random() * MAX_GRID_SIZE)
	randY = (random.random() * MAX_GRID_SIZE)

	new = (randX, randY)


	#### Add Goals as found ####
	goals.put(new, True)

	#################################################################^

	# Free Sparki again
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

	for com in comPorts:
		sparki = Sparki(com)
		if( not sparki.connect()):
			print "Sparki " + com + " failed to connect"
			break
		#################################################################v
		# Set sparkis x and Y here
		#################################################################^
		sparkis.put(sparki, True)

	if (sparkis.qsize() == 0):
		print "No Sparki connected"
		exit()

	generateInitGoals(sparkis.qsize())

	processes =  Pool(processes=len(comPorts))

	while ( notMapped ):
		#################################################################v
		# Not needed in real code though we DO neeed a way to stop mapping
		# Butler is probably fine with us NOT stopping and jsut doing while true
		# Randomly forces an end for testing
		if (random.random() > .95):
			notMapped = False
		#################################################################^

		try:
			sparki = sparkis.get(False)
		except Empty:
			pass
		else:
			goal = goals.get(True)
			processes.apply_async(assignTask, (goal, sparki) )
			time.sleep(1)

	# Waits for all Sparkis to finish
	processes.close()
	processes.join()

	# Disconnect all Sparkis
	for i in xrange(0, sparkis.qsize()):
		sparki = sparkis.get()
		sparki.disconnect()