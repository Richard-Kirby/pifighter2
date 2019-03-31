import threading
import configparser
import socket
import select
import datetime
import time
import sys
import xml.etree.ElementTree as ElementTree
import logging
import json
from multiprocessing import Process

import plot_fight
import fighter_manager

# Exception for a Client Disconnection.
class ClientDisconnnect(Exception):
    def __init__(self, message):
        self.message = message


# Set up logging.
def SetUpLogging():

    # Setting up logging - add in time to it. Create a filename using time functions
    Now = datetime.datetime.now()
    LogFileName = 'log/pifighter_server_' + Now.strftime("%y%m%d%H%M") + ".log"

    # Sets up the logging - no special settings.
    logging.basicConfig(filename=LogFileName, level=logging.DEBUG)


# Class to handle the Opponent Attacks.  Reads the designated file to attack the user.
class OpponentAttackThread(threading.Thread):
    def __init__(self, threadID, name, opponent, virt_fighter_port):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.opponent = opponent
        self.virt_fighter_udp_addres = ('localhost', virt_fighter_port)
        self.fight_ongoing_event = threading.Event()

        #print("Init Attacker Thread")

    def run(self):

        print("Starting ", self.name)

        try:
            file_name = 'AttackFiles/' + self.opponent.attack_file

            # print("&& ", FileName)
            attack_file = open(file_name)

            # Read all the lines, which define the attacks, including timing.
            attacks = attack_file.readlines()

            last_time = 0
            attack_array = []

            # Process all the attack strings in the file.
            for attack in attacks:
                elem_tree = ElementTree.fromstring(attack)

                if elem_tree.tag == 'Attack':

                    # Read through all the information
                    for child in elem_tree:

                        # ZAccel does the damage - read that data in and put in array, taking the timing from the file.
                        if child.tag == 'Time':

                            attack_time = datetime.datetime.strptime(child.text, "%H:%M:%S.%f")

                            # This logic just handles the first attack.  After first attack, we can calculate the amount of time between the
                            # attack and the previous.
                            if last_time != 0:

                                time_diff = attack_time - last_time

                                # Sleep the amount of time between this attack and the previous one.
                                attack_sleep = time_diff.total_seconds()

                                # If it has been too long between attacks, use 1.5s - likely caused by end of fight or other problem.
                                if attack_sleep > 3:
                                    attack_sleep = 1.5

                            # Handling for first attack in the file.  Nothing to compare against.
                            else:
                                time_diff = 0
                                attack_sleep = 0

                            last_time = attack_time

                        # ZAccel does the damage -
                        if child.tag == 'ZAccel':
                            damage = float(child.text)

                attack_array.append([attack_sleep, damage])

            total_delays = 0

            # Wait for the fight to begin
            self.fight_ongoing_event.wait()

            # Loop through all the attacks if fight is not over.  Otherwise might run out of attacks while the fight
            # is still ongoing.

            while self.fight_ongoing_event.is_set():

                # Work through the list of attacks, which has attack strength and timing.  Stop if the fight finishes.
                for i in range(len(attack_array)):

                    # Check to see if the fight is over and if it is, then exit
                    if not self.fight_ongoing_event.is_set():
                        print("Fight Over")
                        break

                    # Total Delays is used to calculate average at the end.
                    total_delays += attack_array[i][0]
                    time.sleep(attack_array[i][0])

                    # Create the string to send to the main UDP process that manages the fighting.
                    opponent_attack_str = "<OpponentAttack>{}</OpponentAttack>".format(attack_array[i][1])

                    # Send the message via UDP to the fight handler
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:

                        udp_socket.sendto(bytes(opponent_attack_str, "utf-8"), self.virt_fighter_udp_addres)

                # Calculate the average
                avg_delay = total_delays / len(attack_array)

                time.sleep(avg_delay)


        except:
            print("Opponent Attack Exception " , sys.exc_info())

            raise

        finally:
            exit()

# Class handles the fights.
class Fight:

    def __init__(self, player, opponent):
        self.player = player
        self.opponent = opponent
        self.fight_over = False
        self.winner = None

    # Create a XML string with the data to determine the state of the fight.
    def create_fight_state_string(self):
        fight_state = ElementTree.Element("FightState")
        p_h = ElementTree.SubElement(fight_state, "PlayerHealth")
        p_h.text = str(self.player.current_health)

        o_h = ElementTree.SubElement(fight_state, "OpponentHealth")
        o_h.text = str(self.opponent.current_health)

        f_o= ElementTree.SubElement(fight_state, "FightOver")
        f_o.text = str(self.fight_over)

        win = ElementTree.SubElement(fight_state, "FightWinner")

        if self.winner is None:
            win.text = "None"
        else:
            win.text = self.winner

        fs_str = ElementTree.tostring(fight_state)

        return fs_str

    # Process any attack on the player or the opponent
    def process_attack(self, fighter, damage):

        # Ignore damage if fight is already over.
        if self.fight_over:
            print("Fight is over {} damage ignored." .format(damage))

        else:

            # Update the appropriate fighter with the damage
            if fighter == self.player:
                self.player.decrement_health(damage)

                if self.player.current_health <= 0:
                    self.winner = self.opponent.name
                    self.fight_over = True

            elif fighter == self.opponent:
                self.opponent.decrement_health(damage)

                if self.opponent.current_health <= 0:
                    self.winner = self.player.name
                    self.fight_over = True

            print("Fighter = {}, Damage = {}, Health = {}" .format(fighter.name, damage, fighter.current_health))


class PlayerSessionManager(threading.Thread):
    def __init__(self, tcp_client_socket, player_mgr, virtual_opp_mgr, udp_address):

        threading.Thread.__init__(self)

        self.tcp_client_socket = tcp_client_socket
        self.player_mgr = player_mgr
        self.virtual_opp_mgr = virtual_opp_mgr

        # Set up port to receive opponent information on - attacks.
        self.opponent_port = 9997

        #player_mgr.print_players()

        # Set up the socket for player UDP messages - handles fights
        self.player_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.player_udp_socket.bind(udp_address)

        # Set up the socket for opponent UDP messages - handles
        self.opponent_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.opponent_udp_socket.bind(('localhost', self.opponent_port))

        self.fight = None
        self.opponent_attack_thread = None
        self.client_udp_address = None
        self.opponent = None

        self.fight_log_file = None
        self.fight_log_dict = {}


    # Function to mark start of fight
    def write_fight_start(self):
        self.fight_log_file.write("<Fight>\n")

    # Function to mark start of fight
    def write_fight_end(self):
        self.fight_log_file.write("</Fight>\n")

    # Function to write a log file string - includes some time information.
    def write_fight_log_item(self, str_to_log):

        if self.fight_log_file is not None:

            fight_log_line = ElementTree.Element("FightLog")
            log_time = ElementTree.SubElement(fight_log_line, "Time")
            log_time.text = str(time.time())

            log_str = ElementTree.SubElement(fight_log_line, "LogStr")
            log_str.text = str(str_to_log)

            fight_log_line_str = ElementTree.tostring(fight_log_line).decode()

            self.fight_log_file.write(fight_log_line_str + '\n')
            self.fight_log_file.flush()


        else:
            print("Log File is None")

    def process_fight_end(self):

        self.opponent_attack_thread.fight_ongoing_event.clear()
        self.opponent_attack_thread.join()
        self.opponent_attack_thread = None

        print("opening JSON file")

        # Write the fight details to a file
        fight_dict_file_str = 'log/pifighter_server_' + time.strftime("%y_%m_%d__%H%M_",
                                                                      time.localtime()) + self.player.name + '_v_' + self.opponent.name + '.json'

        json_file = open(fight_dict_file_str, 'w')

        json.dump(self.fight_log_dict, json_file)

        json_file.close()


        # if player won, regenerate some of player's health
        # print("$$ ", self.fight.winner, self.player.name)
        if self.fight.winner == self.player.name:
            # Regen some of players health.
            self.player.regen(50)

            # Reward player with 2% of the opponents health points
            self.player.reward_health_point(0.02 * self.opponent.initial_health)

            self.player_mgr.update_player_xml(self.player)

            self.player_mgr.update_player_file()

        self.fight = None

        self.plotter = plot_fight.FightPlotter(fight_dict_file_str)

        self.plotter.plot_fight_data()

    # Process TCP comms from the client - typically to set up the session by choosing opponents, etc.
    def process_tcp_comms(self):

        # self.request is the TCP socket connected to the client
        client_str = self.tcp_client_socket.recv(1024).strip().decode()

        # Deal with client disconnection.  Str is zero length in this case.
        if len(client_str) == 0:
            client_exception = ClientDisconnnect("Client Disconnect - killing handler")
            raise (client_exception)

        # Process the string if length is not equal to 0.
        else:

            # Put the data into an XML Element Tree
            try:
                client_element = ElementTree.fromstring(client_str)

                # If Client is asking for the list of players, build a list to transmit.
                if client_element.tag == 'PlayerList':
                    player_str = "<PlayerList>"
                    for player in self.player_mgr.all_players:
                        Name = player.name
                        player_str += "<Player>{}</Player>".format(Name)

                    player_str += "</PlayerList>"

                    self.tcp_client_socket.sendall(bytes(player_str, "utf-8"))

                # If Client is asking for the list of Opponents, go through the Virtual Fighters and
                # build a list to transmit.
                elif client_element.tag == 'OpponentList':
                    opponent_str = "<OpponentList>"
                    for virtual_fighter in self.virtual_opp_mgr.virtual_fighters:
                        Name = virtual_fighter.name
                        opponent_str += "<Opponent>{}</Opponent>".format(Name)

                    opponent_str += "</OpponentList>"
                    self.tcp_client_socket.sendall(bytes(opponent_str, "utf-8"))

                # If Client is logging on, then set the player to the one selected.
                elif client_element.tag == 'SelectedPlayer':
                    player_name = client_element.text

                    for player in self.player_mgr.all_players:
                        if player.name == player_name:
                            self.player = player

                            # Reset health of the player - may have been in previous fights.
                            self.player.reset_health()

                            print("Found Player {} with {} Health Points".format(self.player.name, self.player.health))

                            # if fight log is already open - close it to allow a new file.
                            if self.fight_log_file is not None:
                                self.fight_log_file.close()

                            # Setting up logging - add in time to it. Create a filename using time functions
                            self.fight_log_file = open('log/pifighter_server_fight_log_'
                                                       + time.strftime("%y%m%d%H%M",
                                                                       time.localtime()) + self.player.name + ".xml",
                                                       'wt')
                            self.write_fight_log_item(client_str)

                # If Client has selected an Opponent, then set the opponent to the one selected.
                elif client_element.tag == 'SelectedOpponent':
                    opponent_name = client_element.text

                    # Find the opponent in the list and set everything else up for the fight.
                    for virtual_fighter in self.virtual_opp_mgr.virtual_fighters:
                        if virtual_fighter.name == opponent_name:
                            self.opponent = virtual_fighter
                            self.opponent.reset_health()

                            print("Found Opponent {} with {} Health Points".format(self.opponent.name,
                                                                                   self.opponent.health))

                            # Set up opponent attack thread - could be a live opponent at some point todo - sort out live opponents
                            self.opponent_attack_thread = OpponentAttackThread(46, "Opp Attack Thread", self.opponent,
                                                                               self.opponent_port)

                            self.opponent_attack_thread.start()
                            self.fight = Fight(self.player, self.opponent)

                            # Set initial health to current health - used for regen when fighting.
                            self.player.initial_health = self.player.current_health

                            # Reset the opponents health - this is needed if opponent has already been used.
                            self.opponent.reset_health()

                            print("Health is {}".format(self.opponent.current_health))

                            self.write_fight_start()

                            # Write Opponent to the fight log file.
                            self.write_fight_log_item(client_str)

                            # Zero out the fight dictionary - might have done a fight already.
                            self.fight_log_dict = {}

                            self.fight_log_dict[time.time()] = {'player': self.player.name,
                                                                'player health': self.player.current_health,
                                                                'opponent name': self.opponent.name,
                                                                'opponent current health': self.opponent.current_health,
                                                                'opponent attack damage': None,
                                                                'player attack damage': None,
                                                                'fight winner': self.fight.winner,
                                                                'fight over': self.fight.fight_over}

                            opponent_ready_str = "<OpponentReady>{}</OpponentReady>".format(self.opponent.name)
                            self.tcp_client_socket.sendall(bytes(opponent_ready_str, "utf-8"))
                else:
                    print("Don't know how to process this one {}".format(client_str))
            except:
                print("problem processing something")
                raise

    # Process UDP messages from the player - typically attacks.
    def process_player_udp_comms(self):

        pifighter_data, self.client_udp_address = self.player_udp_socket.recvfrom(4096)

        # Make sure a fight is set up
        if self.opponent_attack_thread is not None and self.fight is not None:

            # Starts the fight if not already started.
            if not self.opponent_attack_thread.fight_ongoing_event.is_set() and not self.fight.fight_over:
                self.opponent_attack_thread.fight_ongoing_event.set()

            pifighter_msg = ElementTree.fromstring(pifighter_data)

            if pifighter_msg.tag == 'Attack':
                damage = float(pifighter_msg.text)
                self.fight.process_attack(self.opponent, damage)

                # Write Attack to the fight log file.
                self.write_fight_log_item(pifighter_data.decode())

                # Log the fight info to the fight dictionary, which results in log file.
                self.fight_log_dict[time.time()] = {'player': self.player.name,
                                                    'player health': self.player.current_health,
                                                    'opponent name': self.opponent.name,
                                                    'opponent current health': self.opponent.current_health,
                                                    'opponent attack damage': damage,
                                                    'player attack damage': None,
                                                    'fight winner': self.fight.winner,
                                                    'fight over': self.fight.fight_over}

                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:

                    fight_state_str = self.fight.create_fight_state_string()

                    if self.fight is not None:
                        # Write Attack to the fight log file.
                        self.write_fight_log_item(fight_state_str.decode())

                        udp_socket.sendto(fight_state_str, self.client_udp_address)


                # Dealing with the end of the fight.
                if self.fight.fight_over and self.opponent_attack_thread is not None:
                    self.process_fight_end()
        else:
            print("Not in a Fight - start a new one.")

    # Process messages as a result of the opponent attacks.
    def process_opponent_udp_comms(self):
        # get the data
        opponent_data, address = self.opponent_udp_socket.recvfrom(4096)

        # Process the UDP string
        msg = ElementTree.fromstring(opponent_data)

        # Deal with Opponent Attack.
        if msg.tag == 'OpponentAttack':

            self.write_fight_log_item(opponent_data.decode())

            damage = float(msg.text)

            if self.fight is not None:

                # Send the message via UDP to the pi fighter client
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                    udp_socket.sendto(opponent_data, self.client_udp_address)
                    self.fight.process_attack(self.player, damage)

                    fight_state_str = self.fight.create_fight_state_string()
                    udp_socket.sendto(fight_state_str, self.client_udp_address)

                    self.write_fight_log_item(fight_state_str.decode())

                    self.fight_log_dict[time.time()] = {'player': self.player.name,
                                                        'player health': self.player.current_health,
                                                        'opponent name': self.opponent.name,
                                                        'opponent current health': self.opponent.current_health,
                                                        'opponent attack damage': damage,
                                                        'player attack damage': None,
                                                        'fight winner': self.fight.winner,
                                                        'fight over': self.fight.fight_over}

                # Clearing up at the end of a fight
                if self.fight.fight_over and self.opponent_attack_thread is not None:
                    self.process_fight_end()

    # Main function to run the thread.
    def run(self):

        print("PlayerSessionManager threading run")

        try:

            while True:

                # Check for items to deal with in the various sockets.
                [read_sock, write_sock, except_sock] = select.select([self.player_udp_socket, self.opponent_udp_socket, self.tcp_client_socket],[],
                                                       [self.player_udp_socket, self.opponent_udp_socket, self.tcp_client_socket], 0.5)

                # Deal with TCP messages - used for setting up fights, logging on, etc.  Fight itself is UDP.
                if self.tcp_client_socket in read_sock:
                    self.process_tcp_comms()

                # Deal with any UDP messages - typically attack messages.
                if self.player_udp_socket in read_sock:
                    self.process_player_udp_comms()

                # handle UDP messages from the opponent.
                if self.opponent_udp_socket in read_sock:
                    self.process_opponent_udp_comms()

        except ClientDisconnnect:
            print("Client Disconnect")

        except:
            raise

        finally:
            print("Clearing up ")
            self.tcp_client_socket.close()
            self.player_udp_socket.close()

            print("Flushing and closing log file {}".format(self.fight_log_file.name))
            self.fight_log_file.flush() # final write.
            self.fight_log_file.close() # close file

# Class to manage Fighers
class FighterManager(threading.Thread):

    def __init__(self):

        threading.Thread.__init__(self)

        # Set up the config parser
        config = configparser.ConfigParser()

        # Read the config file in.
        config.read('pi-fighter-server.cfg')

        self.udp_address = (config['SERVER']['SERVER_HOST'], int(config['SERVER']['UDP_PORT']))
        self.tcp_address = (config['SERVER']['SERVER_HOST'], int(config['SERVER']['TCP_PORT']))

        #print("TCP Address {}". format(self.tcp_address))
        #print("UDP Address {}" .format(self.udp_address))

        self.player_manager = fighter_manager.PlayerManager()

        self.virtual_fighter_manager = fighter_manager.VirtualFighterManager()

        # Set up TCP Server - creates a new thread for each new connection.

    # Processing function
    def run(self):

        try:
            print("Starting listening socket on {}".format(self.tcp_address))

            # create an INET, STREAMing socket
            serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # bind the socket to a public host
            serversocket.bind(self.tcp_address)

            # become a server socket
            serversocket.listen(5)

            while True:
                # accept connections from outside
                (clientsocket, address) = serversocket.accept()

                # Set up a session manager
                session_manager = PlayerSessionManager(clientsocket, self.player_manager, self.virtual_fighter_manager,
                                                       self.udp_address)

                # Start the session manager thread.
                session_manager.start()

        except:

            raise

        finally:
            serversocket.shutdown(socket.SHUT_RDWR)
            serversocket.close()
            clientsocket.shutdown(socket.SHUT_RDWR)
            clientsocket.close()



if __name__ == "__main__":

    fight_mgr = FighterManager()
    fight_mgr.player_manager.print_players()
    fight_mgr.start()
