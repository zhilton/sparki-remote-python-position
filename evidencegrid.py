import sys
import math
import numpy as np
import math
from multiprocessing import Process, Manager
try:
    from Queue import Empty
    import Tkinter as tkinter
except:
    from queue import Empty
    import tkinter
from PIL import Image, ImageTk


def launch(scale, width, height, observation_queue):
    """
    Monitors a queue for observations. When an observation comes in the evidence
    grid and gui are both updated. An observation put into the queue can be
    - An observation of nothing: a 3-tuple of (angle, sparki_x, sparki_y)
    - An observation of something: a 4-tuple of (dist, angle, sparki_x, sparki_y)
    Anything else will trigger an Exception.

    Params:
        scale: the scale of the map in meters per pixel.
        width: the width of the evidence grid in tiles.
        height: the height of the evidence grid in tiles.
        observation_queue: for the love of god pass a multiprocessing.Manager().Queue().
    """
    proc = Process(target=_launch_helper, args=(scale, width, height, observation_queue))
    proc.start()


def _launch_helper(scale, width, height, observation_queue):
    man = Manager()
    draw_queue = man.Queue()
    draw_queue.put(np.ones((height, width))*60) # initialize with odds of 1
    exit_event = man.Event()
    window_proc = Process(target=create_window, args=(scale, draw_queue, exit_event))
    window_proc.start()
    grid = EvidenceGrid(scale, width, height)
    draw_queue.put(grid.oddsarray)

    # get observation, update grid, update gui, in a cycle.
    while not exit_event.is_set():
        try:
            # make sure we keep looping to check for exit event
            obs = observation_queue.get(timeout=1)
            if len(obs) == 3:
                grid.observe_nothing(*obs)
            elif len(obs) == 4:
                grid.observe_something(*obs)
            else:
                raise Exception("bad observation")
            draw_queue.put(grid.oddsarray)
        except Empty:
            pass


# field of view of the ultrasonic sensor is about 15 degrees
ultrasonic_fov = 15 * (np.pi / 180)
# the maximum range of the ultrasonic sensor in meters
max_range = 2


def sensor_model_nothing(x, y, angle):
    """
    The sensor model for observing nothing.

    \   * / x: horizontal
     \   /  y: vertical
      \ /   angle: how this figure it rotated
       o

    The returned value is at most 1 (since it reduces the odds)
    """
    dev = ultrasonic_fov/4
    # a gaussian with a peak value of 1 and mean of 0
    gauss = 1 - .5*math.exp(-(x*x)/(2*dev*dev))
    return gauss


class EvidenceGrid:
    """
    Handles the calculations and storage of an evidence grid.
    Each observation updates self.oddsarray which is indexed
    self.oddsarray[y][x]. self.oddsarray holds numbers from 
    0 to inf that are the odds of each tile being occupied.
    """

    def __init__(self, scale, width, height):
        """
        Params:
            scale: the scale of the map in meters per pixel.
            width, height: the dimensions of the grid in tiles.
        """
        self.oddsarray = np.ones((height, width), np.float64)
        self.scale = scale


    def observe_something(self, dist, angle, sparki_x, sparki_y):
        """
        Params:
            dist: the reported distance to the object in m
            angle: the angle the sensor is pointing in a standard
                   coordinate system (0 rad along x axis)
            sparki_x, sparki_y: positions in m
        """
        self._observe(True, dist, angle, sparki_x, sparki_y)

    def observe_nothing(self, angle, sparki_x, sparki_y):
        """
        Params:
            angle: the angle the sensor is pointing in a standard
                   coordinate system (0 rad along x axis)
            sparki_x, sparki_y: positions in m
        """
        self._observe(False, None, angle, sparki_x, sparki_y)


    def _observe(self, observed_something, dist, angle, sparki_x, sparki_y):
        angle = math.atan2(math.sin(angle), math.cos(angle)) # wrap angle from -pi to pi.

        # the left and right limits of sparki's ultrasonic sensor
        left_limit = angle + ultrasonic_fov/2
        right_limit = angle - ultrasonic_fov/2

        # think of the triangle that encloses the sector
        triangle_hyp = max_range / math.cos(ultrasonic_fov/2)
        # one triangle point is sparki's center, here are the other two
        # (left and right are from sparki's perspective)
        left_point_y = sparki_y + triangle_hyp * math.sin(left_limit)
        left_point_x = sparki_x + triangle_hyp * math.cos(left_limit)
        right_point_y = sparki_y + triangle_hyp * math.sin(right_limit)
        right_point_x = sparki_x + triangle_hyp * math.cos(right_limit)
        # calculate bounding box
        bot = min(sparki_y, left_point_y, right_point_y)
        top = max(sparki_y, left_point_y, right_point_y)
        left = min(sparki_x, left_point_x, right_point_x)
        right = max(sparki_x, left_point_x, right_point_x)
        # convert bounding box to tiles and clip it to the dimensions of the array
        ymin, xmin = self._meters_to_tile(bot, left)
        ymax, xmax = self._meters_to_tile(top, right)
        ymin = max(ymin, 0)
        ymax = min(ymax, self.oddsarray.shape[0])
        xmin = max(xmin, 0)
        xmax = min(xmax, self.oddsarray.shape[1])

        for y in range(ymin, ymax):
            for x in range(xmin, xmax):
                # tile coordinates from origin
                y_m, x_m = self._tile_to_meters(y, x)
                # tile coordinates from sparki
                dy, dx = (y_m - sparki_y, x_m - sparki_x)
                # angle and euclidean distance to the tile
                t_angle = math.atan2(dy, dx)
                t_dist = math.sqrt(dy*dy + dx*dx)

                # the default 1 means the odds are unmodified.
                odds = 1
                relative_angle = math.atan2(math.sin(t_angle - angle), math.cos(t_angle - angle))
                # checking if an angle is between two others is ugly
                if right_limit <= t_angle <= left_limit or \
                   right_limit <= t_angle+2*math.pi <= left_limit or \
                   right_limit <= t_angle-2*math.pi <= left_limit:
                    if observed_something:
                        # 4 cm band of high obstacle odds at the end of vision
                        if dist - 0.04 <= t_dist <= dist + 0.04:
                            odds = 1.5
                        # decreased odds for anywhere closer
                        elif t_dist <= dist - 0.04:
                            odds = sensor_model_nothing(relative_angle, t_dist, ultrasonic_fov/4)
                    else:
                        # observed nothing so decrease odds.
                        if t_dist <= max_range:
                            odds = sensor_model_nothing(relative_angle, t_dist, ultrasonic_fov/4)
                 
                self.oddsarray[y, x] *= odds


    def _meters_to_tile(self, y_m, x_m):
        ycount, xcount = self.oddsarray.shape
        to_y_m = y_m
        to_x_m = x_m
        origin_y = ycount/2
        origin_x = xcount/2
        ytile = int(round(origin_y + to_y_m / self.scale))
        xtile = int(round(origin_x + to_x_m / self.scale))
        return (ytile, xtile)


    def _tile_to_meters(self, y, x):
        ycount, xcount = self.oddsarray.shape
        origin_y = (self.scale * ycount/2)
        origin_x = (self.scale * xcount/2)
        relative_y = self.scale*y - origin_y
        relative_x = self.scale*x - origin_x
        return (relative_y, relative_x)


def create_window(scale, draw_queue, exit_event):
    """
    Create a window that draw whatever evidence grid data comes through the
    queue.
    """
    root = tkinter.Tk()
    label = tkinter.Label(root)
    label.pack()
    root.after(0, update_window, root, label, draw_queue)
    def exit_callback():
        exit_event.set()
        sys.exit()
    root.protocol("WM_DELETE_WINDOW", exit_callback)
    root.mainloop()


def update_window(root, label, q):
    """Used internally to update from the draw queue"""
    newodds = None
    while True:
        try:
            newodds = q.get_nowait()
        except Empty:
            break
    if not newodds is None:
        darknesses = (1 - newodds / (newodds + 1)) * 255
        darknesses = darknesses.astype(np.int8, copy=False)
        darknesses = np.flipud(darknesses)
        img = Image.fromarray(darknesses, 'L')
        imgTk = ImageTk.PhotoImage(img)
        label.configure(image=imgTk)
        label.image = imgTk

    root.after(10, update_window, root, label, q)
