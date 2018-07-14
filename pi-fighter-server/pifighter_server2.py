import threading
import configparser
import socket
import select
import datetime
import time
import sys
import xml.etree.ElementTree as ElementTree

import fighter_manager

class ClientDisconnnect(Exception):
    def __init__(self, message):
        self.message = message

        def SetUpLogging():
            global logging
            global AttackLogs

            # Setting up logging - add in time to it. Create a filename using time functions
            Now = datetime.datetime.now()
            LogFileName = 'log/pi-fighter-server-' + Now.strftime("%y%m%d%H%M") + ".log"

            # Sets up the logging - no special settings.
            logging.basicConfig(filename=LogFileName, level=logging.DEBUG)

            # Set up file for capturing Attacks only.
            AttackLogFile = 'log/pi-fighter-server-attacks' + Now.strftime("%y%m%d%H%M") + ".log"
            AttackLogs = open(AttackLogFile, "w")


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

    def run(self):

        print("PlayerSessionManager threading run")

        # Set player here - todo Need to update later to allow a choice.
        self.player = self.player_mgr.get_player("Richard Kirby")

        print(self.player)

        try:

            while True:

                [read_sock, write_sock, except_sock] = select.select([self.player_udp_socket, self.opponent_udp_socket, self.tcp_client_socket],[],
                                                       [self.player_udp_socket, self.opponent_udp_socket, self.tcp_client_socket], 0.5)

                if self.tcp_client_socket in read_sock:

                    # self.request is the TCP socket connected to the client
                    data = self.tcp_client_socket.recv(1024).strip()

                    if len(data) == 0:
                        client_exception = ClientDisconnnect("Client Disconnect - killing handler")
                        raise (client_exception)

                    # Decode to ASCII so it can be processed.
                    client_str = data.decode('ascii')

                    # Process the string if length is not equal to 0.
                    if (len(client_str) != 0):

                        # Put the data into an XML Element Tree
                        try:
                            client_element = ElementTree.fromstring(client_str)

                            # If Client is asking for the list of Opponents, go through the Virtual Fighters and
                            # build a list to transmit.
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

                            # If Client has selected an Opponent, then set the opponent to the one selected.
                            elif client_element.tag == 'SelectedPlayer':
                                player_name = client_element.text

                                for player in self.player_mgr.all_players:
                                    if player.name == player_name:
                                        self.player = player

                                        # Reset health of the player - may have been in previous fights.
                                        self.player.reset_health()

                                        print("Found Player {} with {} Health Points" .format(self.player.name, self.player.health))

                            # If Client has selected an Opponent, then set the opponent to the one selected.
                            elif client_element.tag == 'SelectedOpponent':
                                opponent_name = client_element.text

                                for virtual_fighter in self.virtual_opp_mgr.virtual_fighters:
                                    if virtual_fighter.name == opponent_name:
                                        self.opponent = virtual_fighter
                                        self.opponent.reset_health()

                                        print("Found Opponent {} with {} Health Points" .format(self.opponent.name, self.opponent.health))

                                        # Set up opponent attack thread - could be a live opponent at some point todo - sort out live opponents
                                        # todo - probably shouldn't create thread here.
                                        self.opponent_attack_thread = OpponentAttackThread(46, "Opp Attack Thread", self.opponent, self.opponent_port)

                                        self.opponent_attack_thread.start()
                                        self.fight = Fight(self.player, self.opponent)

                            else:
                                print("Don't know how to process this one {}" .format(client_str))
                        except:
                            print ("problem processing something")
                            raise

                # Deal with any UDP messages - typically attack messages.
                if self.player_udp_socket in read_sock:

                    pifighter_data, self.client_udp_address = self.player_udp_socket.recvfrom(4096)
                    #print("udp message {} from {}", self.client_udp_address, pifighter_data)


                    # Make sure a fight is set up
                    if self.opponent_attack_thread is not None and self.fight is not None:

                        # Starts the fight if not already started.
                        if not self.opponent_attack_thread.fight_ongoing_event.is_set() and not self.fight.fight_over:
                            self.opponent_attack_thread.fight_ongoing_event.set()

                        pifighter_msg = ElementTree.fromstring(pifighter_data)

                        if pifighter_msg.tag == 'Attack':
                            damage = float(pifighter_msg.text)
                            self.fight.process_attack(self.opponent, damage)

                            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:

                                if self.fight is not None:
                                    udp_socket.sendto(self.fight.create_fight_state_string(),self.client_udp_address)


                            if self.fight.fight_over and self.opponent_attack_thread is not None:
                                self.opponent_attack_thread.fight_ongoing_event.clear()
                                self.opponent_attack_thread.join()

                                #print("Opponent Attack Thread ", self.opponent_attack_thread)


                    else:
                        print("Not in a Fight - start a new one.")

                # handle UDP messages from the opponent.
                if self.opponent_udp_socket in read_sock:
                    # get the data
                    opponent_data, address = self.opponent_udp_socket.recvfrom(4096)

                    # Process the UDP string
                    msg = ElementTree.fromstring(opponent_data)

                    # Deal with Opponent Attack.
                    if msg.tag == 'OpponentAttack':
                        damage = float(msg.text)

                        if self.fight is not None:

                            # Send the message via UDP to the pi fighter client
                            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                                udp_socket.sendto(opponent_data, self.client_udp_address)
                                udp_socket.sendto(self.fight.create_fight_state_string(),self.client_udp_address)
                                self.fight.process_attack(self.player, damage)

                            # Clearing up at the end of a fight
                            if self.fight.fight_over and self.opponent_attack_thread is not None:
                                self.opponent_attack_thread.fight_ongoing_event.clear()
                                self.opponent_attack_thread.join()
                                self.opponent_attack_thread = None
                                self.fight = None

        except ClientDisconnnect:
            print("Client Disconnect")

        except:

            raise

        finally:
            self.tcp_client_socket.close()
            self.player_udp_socket.close()

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


    def run(self):

        try:
            print("Starting listening socket on {}".format(self.tcp_address))

            # create an INET, STREAMing socket
            serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # bind the socket to a public host, and a well-known port
            serversocket.bind(self.tcp_address)

            # become a server socket
            serversocket.listen(5)

            while True:
                # accept connections from outside
                (clientsocket, address) = serversocket.accept()

                # Set up a session manager
                Session_Manager = PlayerSessionManager(clientsocket, self.player_manager, self.virtual_fighter_manager,
                                                       self.udp_address)

                # Start the session manager thread.
                Session_Manager.start()

        except:

            raise

        finally:
            serversocket.shutdown(socket.SHUT_RDWR)
            serversocket.close()



if __name__ == "__main__":

    fight_mgr = FighterManager()
    fight_mgr.player_manager.print_players()
    fight_mgr.start()







