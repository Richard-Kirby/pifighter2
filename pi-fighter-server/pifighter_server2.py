import threading
import configparser
import socket
import select
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
    def __init__(self, threadID, name, counter, opponent):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.opponent = opponent

        print("Init Attacker Thread")

    def run(self):

        print("Starting " + self.name)
        # print("**{}" .format(self.Opponent.AttackFile))


        try:
            # print ("Open File")
            # Open the correct file for reading

            FileName = 'AttackFiles/' + self.opponent.AttackFile

            # print("&& ", FileName)
            AttackFile = open(FileName)

            # Read all the lines, which define the attacks, including timing.
            Attacks = AttackFile.readlines()

            # print (Attacks)
            LastTime = 0
            AttackArray = []

            # Process all the attack strings in the file.
            for Attack in Attacks:
                ElemTree = ElementTree.fromstring(Attack)
                # print(Attack)

                if (ElemTree.tag == 'Attack'):

                    # Read through all the information
                    for Child in ElemTree:
                        # print (Child.tag)

                        # ZAccel does the damage - read that data in and put in array, taking the timing from the file.
                        if (Child.tag == 'Time'):

                            Time = datetime.datetime.strptime(Child.text, "%H:%M:%S.%f")

                            # This logic just handles the first attack.  After first attack, we can calculate the amount of time between the
                            # attack and the previous.
                            if (LastTime != 0):

                                TimeDiff = Time - LastTime

                                # Sleep the amount of time between this attack and the previous one.
                                AttackSleep = TimeDiff.total_seconds()

                                # If it has been too long between attacks, use 1.5s - likely caused by end of fight or other problem.
                                if (AttackSleep > 3):
                                    AttackSleep = 1.5

                                    # print ("****{}".format(AttackSleep))

                            # Handling for first attack in the file.  Nothing to compare against.
                            else:
                                TimeDiff = 0
                                AttackSleep = 0

                            LastTime = Time

                        # print (TimeDiff)
                        # Attacks.Append(Damage)

                        # ZAccel does the damage -
                        if (Child.tag == 'ZAccel'):
                            # print(Child.text)
                            Damage = float(Child.text)
                            # print (Damage)
                            # Attacks.Append(Damage)

                AttackArray.append([AttackSleep, Damage])
            # print (AttackArray)

            TotalDelays = 0
            # print(len(AttackArray))

            # Loop through all the attacks if fight is not over.  Otherwise might run out of attacks while the fight
            # is still ongoing.
            while (FightOver.isSet() != True):
                # Work through the list of attacks, which has attack strength and timing.  Stop if the fight finishes.
                for i in range(len(AttackArray)):

                    # Check to see if the fight is over and if it is, then exit
                    if (FightOver.isSet()):
                        print("Fight Over")
                        break

                    # Total Delays is used to calculate average at the end.
                    TotalDelays += AttackArray[i][0]
                    time.sleep(AttackArray[i][0])
                    # print(AttackArray[i][1])
                    # OpponentAttackQueue.put_nowait(AttackArray[i][1])
                    # Health = Player.DecrementHealth(AttackArray[i][1])

                    # Create the string to send to the main UDP process that manages the fighting.
                    OpponentAttackStr = "<OpponentAttack>{}</OpponentAttack>".format(AttackArray[i][1])

                    # Send the message via UDP to Pi Fighter
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as UDPSocket:
                        UDPSocket.setblocking(False)

                        UDPSocket.sendto(bytes(OpponentAttackStr, "utf-8"),
                                         (config['SERVER']['SERVER_HOST'], int(config['SERVER']['UDP_PORT'])))

                    # Send the message via UDP to Pi Fighter
                    #with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as UDPSocket:
                    #    UDPSocket.setblocking(False)

                    #   UDPSocket.sendto(bytes(OpponentAttackStr, "utf-8"), (
                    #       config['PI_TRAINER']['PI_TRAINER'], int(config['PI_TRAINER']['PI_TRAINER_PORT'])))




                        # print("Player's health is {}" .format(Health))

                # Calculate the average
                AvgDelay = TotalDelays / len(AttackArray)

                # print (AvgDelay)
                time.sleep(AvgDelay)


        except:
            print("Opponent Attack Exception" , sys.exc_info()[0])
            raise

        finally:
            FightOver.clear()
            exit()



class PlayerSessionManager(threading.Thread):
    def __init__(self, tcp_client_socket, player_mgr, virtual_opp_mgr, udp_address):

        threading.Thread.__init__(self)

        self.tcp_client_socket = tcp_client_socket
        self.player_mgr = player_mgr
        self.virtual_opp_mgr = virtual_opp_mgr

        player_mgr.print_players()

        # Set up the socket for UDP messages - handles fights
        print(udp_address)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(udp_address)

        print(self.udp_socket)

    def run(self):

        print("PlayerSessionManager threading run")

        try:

            while True:

                [read_sock, write_sock, except_sock] = select.select([self.udp_socket, self.tcp_client_socket],[],
                                                       [self.udp_socket, self.tcp_client_socket], 0.5)

                if self.tcp_client_socket in read_sock:

                    # self.request is the TCP socket connected to the client
                    self.data = self.tcp_client_socket.recv(1024).strip()

                    if len(self.data) == 0:
                        client_exception = ClientDisconnnect("Client Disconnect - killing handler")
                        raise (client_exception)

                    # Decode to ASCII so it can be processed.
                    client_str = self.data.decode('ascii')

                    # Process the string if length is not equal to 0.
                    if (len(client_str) != 0):

                        # Put the data into an XML Element Tree
                        try:
                            print(client_str)

                            client_element = ElementTree.fromstring(client_str)
                            # If Attack received, then calcualte the effect on the opponent.


                            # If Client is asking for the list of Opponents, go through the Virtual Fighters and
                            # build a list to transmit.
                            if (client_element.tag == 'OpponentList'):
                                opponent_str = "<OpponentList>"
                                for virtual_fighter in self.virtual_opp_mgr.virtual_fighters:
                                    Name = virtual_fighter.name
                                    opponent_str += "<Opponent>{}</Opponent>".format(Name)

                                opponent_str += "</OpponentList>"
                                # print (OpponentStr)
                                self.tcp_client_socket.sendall(bytes(opponent_str, "utf-8"))

                            # If Client has selected an Opponent, then set the opponent to the one selected.
                            elif (client_element.tag == 'SelectedOpponent'):
                                opponent_name = client_element.text


                                print (opponent_name)

                                for virtual_fighter in self.virtual_opp_mgr.virtual_fighters:
                                    if virtual_fighter.name == opponent_name:
                                        self.opponent = virtual_fighter

                                        print("Found Opponent {} with {} Health Points" .format(self.opponent.name, self.opponent.health))

                            else:
                                print("Don't know how to process this one {}" .format(client_str))
                        except:
                            print ("problem processing something")

                # Deal with any UDP messages - typically attack messages.
                if self.udp_socket in read_sock:

                    data, address = self.udp_socket.recvfrom(4096)
                    print("udp message {} from {}", address, data)


        except ClientDisconnnect:
            print("Client Disconnect")

        except:

            self.tcp_client_socket.close()
            self.udp_socket.close()
            raise

class FighterManager(threading.Thread):

    def __init__(self):

        threading.Thread.__init__(self)

        # Set up the config parser
        config = configparser.ConfigParser()

        # Read the config file in.
        config.read('pi-fighter-server.cfg')

        self.udp_address = (config['SERVER']['SERVER_HOST'], int(config['SERVER']['UDP_PORT']))
        self.tcp_address = (config['SERVER']['SERVER_HOST'], int(config['SERVER']['TCP_PORT']))

        print("TCP Address {}". format(self.tcp_address))
        print("UDP Address {}" .format(self.udp_address))

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
                # now do something with the clientsocket
                # in this case, we'll pretend this is a threaded server
                #ct = client_thread(clientsocket)
                #ct.run()
                print("**{}**".format((clientsocket, address)))

                Session_Manager = PlayerSessionManager(clientsocket, self.player_manager, self.virtual_fighter_manager,
                                                       self.udp_address)

                Session_Manager.start()

        except:

            serversocket.shutdown(socket.SHUT_RDWR)
            serversocket.close()
            raise


if __name__ == "__main__":

    fight_mgr = FighterManager()
    fight_mgr.player_manager.print_players()
    fight_mgr.start()







