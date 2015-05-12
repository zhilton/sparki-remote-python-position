class Sparki:
    def move_forward(self, dist):
        print("I moved forward {}".format(dist))


def read_msg(sparki, data):
    funcname, args = data
    func = getattr(sparki, funcname)
    func(*args)

def loopFunct(q):
    while True:
        try:
            message = q.get()
            read_msg(message[0], (message[1], message[2]))
        except:
            pass

'''
>>> import poop
>>> from poop import Sparki
>>> s = Sparki()
>>> from queue import Queue
>>> q = Queue()
>>> message = (s, 'move_forward', (1,))
>>> q.put(message)
>>> loopFunct(q)
'''
