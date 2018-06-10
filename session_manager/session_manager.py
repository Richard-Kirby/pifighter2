#!/usr/bin/env python3
import time
import threading
import xml.etree.ElementTree as ET
import pixel_display.pixel_display as pix_display


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
class Workout(Event, threading.Thread):

    def __init__(self):
        Event.__init__("Workout")
        threading.Thread.__init__(self)

    def run_workout_sequence(self):
        print("workout seq")

        '''
        # Read in the sequences from the XML file.
        sequence_tree = ET.parse('pi-fighter_seq.xml')
        seq_root = sequence_tree.getroot()


        for sequence in seq_root:

            print(sequence.attrib)
            # device.show_message(Sequence.attrib, font=proportional(CP437_FONT), delay = 0.05)
            # time.sleep(.4)

            for command in sequence:
                
                PixelState = [NO_STATE_COLOUR, NO_STATE_COLOUR, NO_STATE_COLOUR, NO_STATE_COLOUR,
                              NO_STATE_COLOUR, NO_STATE_COLOUR, NO_STATE_COLOUR, NO_STATE_COLOUR,
                              NO_STATE_COLOUR, NO_STATE_COLOUR, NO_STATE_COLOUR, NO_STATE_COLOUR,
                              NO_STATE_COLOUR, NO_STATE_COLOUR, NO_STATE_COLOUR, NO_STATE_COLOUR]
                
                
                # print (Command.tag)
                if command.tag == 'Attack':
                    for attack in command:
                        # print (Attack.tag)
                        # print (Attack.text)

                        if attack.tag == 'Punch':
                            # print(Attack.text)
                            # Set the colour according to left or right
                            if attack.text == 'Left':
                                AttackColour = LEFT_PUNCH_COLOUR
                                for i in range(12, 16):
                                    PixelState[i] = AttackColour
                            elif attack.text == 'Right':
                                for i in range(0, 4):
                                    AttackColour = RIGHT_PUNCH_COLOUR
                                    PixelState[i] = AttackColour
                            else:
                                AttackColour = 0
                                print("Unrecognised text", attack.text)

                            if AttackColour != 0:

                                for i in range(0, 16):
                                    # Set the current pixel as required by the punch sequence - use half the time to display,
                                    # half off so it is sequence can have 2 of the same in a row
                                    strip.setPixelColor(i, PixelState[
                                        i])  # Actual strip is Green Red Blue, so swap colours around
                                strip.show()
                                time.sleep(CMD_FLASH_TIME / 1000)

                                for i in range(0, 16):
                                    # Set the current pixel as required by the punch sequence - use half the time to display,
                                    # half off so it is sequence can have 2 of the same in a row
                                    strip.setPixelColor(i, neopixel.Color(0, 0,
                                                                          0))  # Actual strip is Green Red Blue, so swap colours around

                                strip.show()

                        if attack.tag == 'Kick':
                            # print(Attack.text)
                            # Set the colour according to left or right
                            if attack.text == 'Left':
                                AttackColour = LEFT_KICK_COLOUR
                                for i in range(8, 12):
                                    PixelState[i] = AttackColour
                            elif attack.text == 'Right':
                                for i in range(4, 8):
                                    AttackColour = RIGHT_KICK_COLOUR
                                    PixelState[i] = AttackColour
                            else:
                                AttackColour = 0
                                print("Unrecognised text", attack.text)

                            if AttackColour != 0:

                                for i in range(0, 16):
                                    # Set the current pixel as required by the punch sequence - use half the time to display,
                                    # half off so it is sequence can have 2 of the same in a row
                                    strip.setPixelColor(i, PixelState[
                                        i])  # Actual strip is Green Red Blue, so swap colours around
                                strip.show()
                                time.sleep(CMD_FLASH_TIME / 1000)

                                for i in range(0, 16):
                                    # Set the current pixel as required by the punch sequence - use half the time to display,
                                    # half off so it is sequence can have 2 of the same in a row
                                    strip.setPixelColor(i, neopixel.Color(0, 0,
                                                                          0))  # Actual strip is Green Red Blue, so swap colours around

                                strip.show()


                        elif attack.tag == 'Wait':
                            # print(Attack.text)
                            for i in range(0, 16):
                                AttackColour = NO_STATE_COLOUR
                                PixelState[i] = AttackColour
                                strip.setPixelColor(i, PixelState[i])
                            strip.show()
                            AttackWait = (int)(attack.text) * STD_PUNCH_WAIT / 1000

                            time.sleep(AttackWait)
                elif command.tag == 'Rest':
                    # print (Command.text)
                    CommandWait = (int)(command.text) * STD_PUNCH_WAIT / 1000
                    strip.setPixelColor(CurrentPixel, WAIT_COLOUR)  # Turn pixel white when finished
                    strip.show()
                    time.sleep(CommandWait)

            strip.setPixelColor(CurrentPixel, FINISHED_COLOUR)  # Turn pixel white when finished
            CurrentPixel -= 1
            strip.show()
            time.sleep(BETWEEN_SEQ_REST / 1000)

            # flash to tell the person to get ready
            strip.setPixelColor(CurrentPixel, WAIT_COLOUR)  # Turn pixel white when finished
            strip.show()
            time.sleep(3)
            strip.setPixelColor(CurrentPixel, neopixel.Color(0, 0, 0))  # Turn pixel off when finished
            strip.show()
            time.sleep(3)
         '''

    def init_workout(self):
        print("Init workout")

        # Change later to allow specific work out sequences.
        self.run_workout_sequence()


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
        self.pix_display = pix_display.PixelDisplay()
        self.pix_display.welcome_message(self.player)
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
