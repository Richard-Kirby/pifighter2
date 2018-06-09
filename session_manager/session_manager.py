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
        print("finish", end_time)

# Workout class - handles workouts where the attack is specified by pifighter.
class Workout(Event):

    def __init__(self):
        super().__init__("Workout")
        pass

    def init_workout(self):
        print("Init workout")

# Fight class - manages a fight between the player and an opponent.
class Fight(Event):

    player = ""
    opponent = ""

    def __init__(self, fight_player, fight_opponent):
        super().__init__("Fight")
        self.player = fight_player
        self.opponent = fight_opponent

        print("{} v {}" .format(self.player, self.opponent))


# Session class manages a session where the player does workouts and fights as desired.
class Session(Event):

    player = ""
    fight = ""
    workout = ""

    def __init__(self, session_player):
        super().__init__("Session")
        self.player = session_player
        print(self.player)

    # Set up workout for the player.
    def setup_workout(self):
        self.workout = Workout()
        self.workout.init_workout()
        print("workout happening")
        self.workout.finish_event()

    # Set you a fight for he player.
    def setup_fight(self, opponent):
        self.fight = Fight(self.player, opponent)

    def close_session(self):
        print("Session Closing")

if __name__ == "__main__":

    session = Session("R Kirby")
    session.setup_workout()
    session.setup_fight("Trump")
