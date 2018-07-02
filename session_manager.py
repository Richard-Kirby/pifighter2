#!/usr/bin/env python3
import time
import threading
import xml.etree.ElementTree as ET
import queue

# Custom modules/packages
import pixel_display.pixel_display as pix_display
import accel.accel as accel


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

    def __init__(self, pix_display):
        Event.__init__(self, "Workout")
        threading.Thread.__init__(self)
        self.pix_display = pix_display
        self.pix_display.text_message("Workout ")

    # Run the workout sequence.
    def run(self):
        print("workout seq")


        print("done")

        # Read in the sequences from the XML file.
        sequence_tree = ET.parse('/home/pi/pifighter2/data_files/workouts/pi-fighter_seq.xml')
        seq_root = sequence_tree.getroot()

        for sequence in seq_root:

            #print(sequence.attrib)
            # device.show_message(Sequence.attrib, font=proportional(CP437_FONT), delay = 0.05)
            # time.sleep(.4)

            for command in sequence:
                # print (Command.tag)
                if command.tag == 'Attack':
                    for attack in command:
                        # print (Attack.tag)
                        # print (Attack.text)

                        if attack.tag == 'Punch':
                            # print(Attack.text)
                            # Set the colour according to left or right
                            if attack.text == 'Left':
                                self.pix_display.workout_attack('PunchLeft')
                            elif attack.text == 'Right':
                                self.pix_display.workout_attack('PunchRight')
                            else:
                                print("Unrecognised text", attack.text)

                        elif attack.tag == 'Kick':
                            # print(Attack.text)
                            # Set the colour according to left or right
                            if attack.text == 'Left':
                                self.pix_display.workout_attack('KickLeft')

                            elif attack.text == 'Right':
                                self.pix_display.workout_attack('KickRight')

                            else:
                                print("Unrecognised text", attack.text)

                        elif attack.tag == 'Wait':
                            time.sleep(0.5)
                            #print("wait")

                elif command.tag == 'Rest':
                    # print (Command.text)
                    #print("Rest")
                    for i in range(100, -1, -4):
                        #print(i)
                        self.pix_display.set_opponent_attack(i)
                        #time.sleep(0.0005)

            #print("finished a sequence - rest")




# Fight class - manages a fight between the player and an opponent.
class Fight(Event):

    player = ""
    opponent = ""

    def __init__(self, fight_player, fight_opponent):
        super().__init__("Fight")
        self.player = fight_player
        self.opponent = fight_opponent

        print("{} v {}" .format(self.player, self.opponent))

# Class to handle the attack outputs - send them to the server and display
class AttackHandler(threading.Thread):

    def __init__(self, pix_display, player_attack_q, opponent_attack_q, delay=0.3):
        threading.Thread.__init__(self)
        self.pix_display = pix_display
        self.player_attack_q = player_attack_q
        self.opponent_attack_q = opponent_attack_q
        self.delay = delay

    def run(self):

        print("++++++++ AttackHandler+++++++")

        while (1):

            # Deal with Player's attack Queue
            if not self.player_attack_q.empty():
                accel_perc = float(self.player_attack_q.get_nowait())/16.0 * 100
                print("&&&", int(accel_perc))
                if accel_perc >100:
                    accel_perc = 100

                self.pix_display.set_player_attack(int(accel_perc))
                time.sleep(self.delay)
                self.pix_display.set_player_attack(0)

            # Deal with Player's attack Queue
            if not self.opponent_attack_q.empty():
                accel_perc = float(self.opponent_attack_q.get_nowait())/16.0 * 100
                print("&&&", int(accel_perc))
                if accel_perc >100:
                    accel_perc = 100

                self.pix_display.set_opponent_attackint(accel_perc)
                time.sleep(self.delay)
                self.pix_display.set_opponent_attack(0)


            # Short sleep - to reduce the CPU drain.
            time.sleep(0.1)

# Session class manages a session where the player does workouts and fights as desired.
class Session(Event):

    player = ""
    fight = ""
    workout = ""

    def __init__(self, session_player, tcp_send_q, tcp_rec_q, udp_send_q, udp_rec_q):
        super().__init__("Session")
        self.player = session_player
        self.tcp_send_q = tcp_send_q
        self.tcp_rec_q = tcp_rec_q
        self.udp_send_q = udp_send_q
        self.udp_rec_q = udp_rec_q

        self.pix_display = pix_display.PixelDisplay()
        self.pix_display.welcome_message(self.player)


        self.player_q = queue.Queue()
        self.opponent_q = queue.Queue()

        self.accel = accel.Accelerometer(20, self.player_q )
        self.accel.start()

        # Handles the attacks -Either player or opponent.
        self.attack_handler = AttackHandler(self.pix_display, self.player_q, self.opponent_q)
        #print(self.player)
        self.attack_handler.start()


    # Set up workout for the player.
    def setup_workout(self):
        self.workout = Workout(self.pix_display)
        print("workout happening")
        self.workout.start()
        self.workout.finish_event()


    # Set you a fight for the player.
    def setup_fight(self, opponent):
        self.fight = Fight(self.player, opponent)
        selected_opp_str = "<SelectedOpponent>{}</SelectedOpponent>".format(opponent)
        print(selected_opp_str)
        self.tcp_send_q.put_nowait(selected_opp_str)
        time.sleep(1)
        #self.udp_send_q.put_nowait(selected_opp_str)


    def close_session(self):
        print("Session Closing")

if __name__ == "__main__":


    session = Session("R Kirby")

    session.setup_workout()
    #session.setup_fight("Trump")
    #session.pix_display.workout_attack('KickRight')

