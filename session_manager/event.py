#!/usr/bin/env python3
import time

# Event Base Class
class Event:

    def __init__(self, type):
        print("Setting up an event")
        start_time= time.time()
        print(type, start_time)

    def finish_event(self):
        end_time = time.time()
        print(end_time)


class Workout(Event):

    def __init__(self):
        super().__init__("Workout")
        pass

class Fight(Event):

    def __init__(self):
        super().__init__("Fight")
        pass

if __name__ == "__main__":

    workout1 = Workout()
    workout1.finish_event()
    fight = Fight()
    fight.finish_event()
