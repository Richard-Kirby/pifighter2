import socketserver
import socket
import xml.etree.ElementTree as ElementTree
import binascii
import configparser
import threading
import datetime
import logging
import time
import queue
import sys

num_attacks = 0
opponent_defeated = False
FinalAttackNum = 0

# Event to indicate the fight is over.  This synchronises across threads.  
FightOver = threading.Event()
FightOver.clear()

AllPlayers = []


class ClientDisconnnect(Exception):
    def __init__(self, message):
        self.message = message


class PlayerManager:
    UserFile = "pi-fighter-users.xml"
    global AllPlayers
    UserET_Root = ''
    UserFileInfo = ''

    def __init__(self):
        logging.info("Processing all players from file" + self.UserFile)

    # Read all the player information from the player file.
    def ReadPlayerInfo(self):

        self.UserFileInfo = ElementTree.parse(self.UserFile)

        # print(UserFileInfo)

        # Grabs the root of the XML tree for processing.
        self.UserET_Root = self.UserFileInfo.getroot()

        # Parse the User information into separate players - this works through the
        # The XML Element Tree
        for User in self.UserET_Root:
            # print(User.tag, User.attrib)

            Name = User.attrib.get('Name')

            for UserData in User:
                # Find the Health Tag via the find function
                Health = User.find('Health').text

            # Build a list of players
            AllPlayers.append(Player(Name, Health))

        logging.info("Found {} Players".format(len(AllPlayers)))

    # Updates the player's information in the XML tree.
    def UpdatePlayerXML(self, Player):
        # Go through the players looking for the player in question.
        for User in self.UserET_Root:
            # print(User.tag, User.attrib)
            # If ind the right player then update his/her health.
            if (User.attrib.get('Name') == Player.name):
                User.find('Health').text = str(Player.Health)
                # print ("$${}$$".format(User.find('Health').text))

    # Update the XML file for persistent storage.
    def UpdatePlayerFile(self):
        self.UserFileInfo.write(self.UserFile)


class fighter:
    Health = 1.0
    CurrentHealth = 1.0
    name = ""

    def __init__(self, name, health):
        self.name = name
        # print (name)
        self.Health = float(health)
        self.InitialHealth = float(health)
        self.CurrentHealth = float(health)

    # print ("Health is ", self.CurrentHealth)

    # Decrements health - usually due to an attack.
    def DecrementHealth(self, Attack):
        self.CurrentHealth -= Attack
        # print("Fighter Health now {}".format(self.CurrentHealth))
        return (self.CurrentHealth)

    # Resets Health - set the health back to the maximum
    def ResetHealth(self):
        self.CurrentHealth = self.InitialHealth


# Class to handle the Virtual Fighters.
class VirtualFighter(fighter):
    AttackFile = ""

    def __init__(self, name, health, AttackFileName):
        super(VirtualFighter, self).__init__(name, health)
        self.AttackFile = AttackFileName

        # print (self.name, self.Health, self.AttackFile)


# Build a list of Virtual Fighters - should be put into a file.
VirtualFighters = [
    VirtualFighter("One Ewok", 50, 'One_Ewok_Attack_LevelOne.xml'),
    VirtualFighter("C3-PO", 60, "C3-PO_Attack_LevelOne.xml"),
    VirtualFighter("Early Luke SkyWalker", 75, "Early_Luke_Attack_LevelOne.xml"),
    VirtualFighter("JarJar Binks", 100, "JarJar_Binks_Attack_LevelOne.xml"),
    VirtualFighter("Many Ewoks", 150, "Many_Ewoks_Attack_LevelOne.xml"),
    VirtualFighter("Jedi Luke", 200, "Jedi_Luke_Attack_LevelOne.xml"),
    VirtualFighter("Yoda", 200, "Yoda_LevelOne.xml"),
    VirtualFighter("Darth Vader", 300, "Darth_Vader_Attack_LevelOne.xml")
]


# Player Class - manages player information.  It is just a type of fighter, but gets re-gen and extra health when wins a fight. 
class Player(fighter):
    def Regen(self, Percent):
        # Maximum Regeneration Calc - capped at original.  Regenerate the defined percentage
        # of what has been lost
        self.CurrentHealth += (self.InitialHealth - self.CurrentHealth) * (Percent / 100)

        # if (self.Health > self.InitialHealth):
        #	self.Health = self.InitialHealth

        print("Regened Health ", self.CurrentHealth)

    # Increase the User's health points - usually for winning a fight.
    def RewardHealthPoint(self, RewardPts):
        # Add the Reward Points to Health, but not initial health (to keep track of what changed during the session)
        self.Health += RewardPts
        print(
            "Bonus Health - Player {}'s profile now has {} health points.\n  {} started session with {} and currently has {}"
                .format(self.name, self.Health, self.name, self.InitialHealth, self.CurrentHealth))


# Player = Player("Example")



# Set up the config parser
config = configparser.ConfigParser()

# Read the config file in.
config.read('pi-fighter-server.cfg')


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


class PiFighterUDPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantianted once per connection to the server, and must
    override the handle() method to implement communication to the
    client.

    """

    # Send the opponents health to the Client. Client needs to display
    def SendOpponentInfo(self):
        global HealthPoints
        global num_attacks
        global opponent_defeated
        global opponent
        global PiAddress

        OpponentHealthStr = "<OpponentInfo><Name>{}</Name><HealthPoints>{}</HealthPoints><Defeated>{}</Defeated></OpponentInfo>".format(
            opponent.name, opponent.CurrentHealth, opponent_defeated)

        self.socket.sendto(bytes(OpponentHealthStr, "utf-8"), self.client_address)
        #self.socket.sendto(bytes(OpponentHealthStr, "utf-8"), PiAddress)


    # Send the player's current health to the Client.
    def SendPlayerInfo(self):
        global Player
        global PiAddress

        Defeated = (Player.CurrentHealth < 0)
        PlayerHealthStr = "<PlayerInfo><HealthPoints>{}</HealthPoints><Defeated>{}</Defeated></PlayerInfo>".format(
            Player.CurrentHealth, Defeated)

        print(PlayerHealthStr)
        #socket = self.request[1]
        self.socket.sendto(bytes(PlayerHealthStr, "utf-8"), self.client_address)
        #self.request.(bytes(PlayerHealthStr, "utf-8"))

    def SendAttack(self, date_string, time_string, MaxAccel):
        AttackStr = "<Attack><Date>{}</Date><Time>{}</Time><XAccel>{:2.3}</XAccel><YAccel>{:2.3f}</YAccel><ZAccel>{:2.3f}</ZAccel></Attack>".format(
            date_string, time_string, MaxAccel[0], MaxAccel[1], MaxAccel[2])
        self.request[1].sendto(bytes(AttackStr, "utf-8"), self.client_address)

    def handle(self):
        global HealthPoints
        global num_attacks
        global opponent_defeated
        global FinalAttackNum
        global OpponentName
        global Player
        global OpponentStartHealth
        global PlayerMgr
        global PiAddress

        self.timeout = 0

        # self.request is the UDP socket connected to the client
        self.data = self.request[0].strip()
        self.socket = self.request[1]

        # Decode to ASCII so it can be processed.
        ClientStr = self.data.decode('ascii')

        # Put the data into an XML Element Tree
        try:
            # print (ClientStr)
            ClientElement = ElementTree.fromstring(ClientStr)

            # Log the Attack
            logging.info(ClientStr)

            # If Attack received, then calcualte the effect on the opponent.

            print("$$$ ", ClientElement.tag)

            if (ClientElement.tag == 'Attack'):

                damage = float(ClientElement.text)

                if (damage > 2):
                    opponent.DecrementHealth(damage)
                    print(damage, num_attacks)
                    num_attacks += 1

                    # Determine if Opponent is Defeated
                    if opponent.CurrentHealth < 0:

                        if not opponent_defeated:
                            FinalAttackNum = num_attacks
                            opponent_defeated = True
                            FightOver.set()

                            # Player won, allow up to 50% regen
                            Player.Regen(50)

                            # Reward player with 2% of the opponents health points
                            Player.RewardHealthPoint(0.02 * opponent.InitialHealth)

                            # Keep Player Information up to date in XML as well.
                            PlayerMgr.UpdatePlayerXML(Player)
                            PlayerMgr.UpdatePlayerFile()

                        if (opponent_defeated == True):
                            print("That dude is finished after - stop beating on him/her - Oh the Humanity",
                                  FinalAttackNum)

                    # Send Opponent Information to the Client for display or other usage.
                    self.SendOpponentInfo()

                    # If first attack (player gets first punch), then start up the attacks from the opponent.
                    if (num_attacks == 1):
                        print("run attacker thread")
                        # Spin off opponent thread here.
                        AttackerThread = OpponentAttackThread(1, "Attacker Thread - Punch Up", 1, opponent)
                        # AttackerThread.setDaemon(True)
                        AttackerThread.start()
                        FirstAttack = False

            elif (ClientElement.tag == 'SelectedOpponent'):
                # Send Opponent Information to the Client for display or other usage.

                self.SendOpponentInfo()

                self.FirstAttack = True

                PiAddress = self.client_address

                print(PiAddress)


                num_attacks = 0
                # Send Player information to initialise
                self.SendPlayerInfo()

            elif ClientElement.tag == 'OpponentAttack':
                # Adjust the User's health by the amount of the attack

                AttackValue = float(ClientElement.text)

                if not FightOver.isSet():
                    Player.DecrementHealth(AttackValue)
                    self.SendPlayerInfo()
                else:
                    print("Opponent Attack of {} ignored".format(AttackValue))

                # Declare fight over if Player has lost all health.
                if (Player.CurrentHealth < 0):
                    print("Player Lost to ", opponent.name)
                    FightOver.set()


            else:
                print("Can't process string {}".format(ClientStr))

        except:
            print("Trouble Processing String: {}".format(ClientStr))
            raise


# Class to handle the TCP Comms - manages the session, etc. 
class UDPCommsThread(threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter

    # print ("Starting listening socket on {} Port {}".format(config['SERVER']['SERVER_HOST'],config['SERVER']['UDP_PORT']))



    def run(self):
        # print ("Starting " + self.name)

        try:
            # print ("UDP")
            # Create the UDP server.
            UDPserver = socketserver.UDPServer((config['SERVER']['SERVER_HOST'], int(config['SERVER']['UDP_PORT'])),
                                               PiFighterUDPHandler)

            print("UDP")

            # Activate the server; this will keep running until you
            # interrupt the program with Ctrl-C
            UDPserver.serve_forever()
        except:
            print("UDP Exception")
            raise


        finally:
            UDPserver.close()
            exit()


# Class to handle the Opponent Attacks.  Reads the designated file to attack the user.
class OpponentAttackThread(threading.Thread):
    def __init__(self, threadID, name, counter, Opponent):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.Opponent = Opponent

        print("Init Attacker Thread")

    def run(self):

        print("Starting " + self.name)
        # print("**{}" .format(self.Opponent.AttackFile))


        try:
            # print ("Open File")
            # Open the correct file for reading

            FileName = 'AttackFiles/' + self.Opponent.AttackFile

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


# Handler of TCP traffic - used to set up the sessions as opposed to run the session which is UDP.
class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):

        global OpponentName
        global HealthPoints
        global opponent_defeated
        global opponent

        try:

            while (1):

                # self.request is the TCP socket connected to the client
                self.data = self.request.recv(1024).strip()

                if len(self.data) == 0:
                    client_exception = ClientDisconnnect("Client Disconnect - killing handler")
                    raise (client_exception)

                # Decode to ASCII so it can be processed.
                client_str = self.data.decode('ascii')

                # Process the string if length is not equal.
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
                            for i in (range(len(VirtualFighters))):
                                Name = VirtualFighters[i].name
                                opponent_str += "<Opponent>{}</Opponent>".format(Name)

                            opponent_str += "</OpponentList>"
                            # print (OpponentStr)
                            self.request.sendall(bytes(opponent_str, "utf-8"))

                        # If Client has selected an Opponent, then set the opponent to the one selected.
                        elif (client_element.tag == 'SelectedOpponent'):
                            OpponentName = client_element.text
                            # print (OpponentName)

                            # Find the Selected Opponent.

                            for i in range(len(VirtualFighters)):
                                if VirtualFighters[i].name == OpponentName:
                                    opponent = VirtualFighters[i]

                                    print("Found Opponent", OpponentName)

                                    # Clear the fight over flag - this may not be the first fight
                                    FightOver.clear()
                                    break

                            # Setting up for the fight - setting various things back up.
                            opponent_defeated = False  # Set Opponent Defeated to False

                            # Reset the opponents health - this is needed if opponent has already been used.
                            opponent.ResetHealth()

                            print("Health is {}".format(opponent.CurrentHealth))

                            OpponentReadyStr = "<OpponentReady>{}</OpponentReady>".format(opponent.name)

                            self.request.sendall(bytes(OpponentReadyStr, "utf-8"))


                        else:
                            print("Don't know how to process this one")

                    except:
                        print("Trouble Processing String: {}".format(client_str))

                        raise ()
        except ClientDisconnnect:
            print("Client Disconnect")

        except:

            raise


# Class to handle the TCP Comms - manages the session, etc. TCP Comms is used to set up the session only.
# UDP is used for the fighting.  
class TCPCommsThread(threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        print("Starting listening socket on {} Port {}".format(config['SERVER']['SERVER_HOST'],
                                                               config['SERVER']['TCP_PORT']))

    def run(self):

        print("Starting " + self.name)

        try:
            print("TCP")
            # Create a socket (SOCK_STREAM means a TCP socket)
            TCPsock = socketserver.TCPServer((config['SERVER']['SERVER_HOST'], int(config['SERVER']['TCP_PORT'])),
                                             MyTCPHandler)

            # Activate the server; this will keep running until you
            # interrupt the program with Ctrl-C
            TCPsock.serve_forever()  # Connect to server and send data

        except:
            print("TCP Exception")
            TCPsock.shutdown()
            TCPsock.server_close()
            raise

        finally:
            TCPsock.server_close()
            exit()


# Read in all the user information
PlayerMgr = PlayerManager()
PlayerMgr.ReadPlayerInfo()

# Set Player to first player - will set it later.


# Player = AllPlayers[0]
print("Welcome to Pi Fighter Server - this server starts up and waits for players to connect")
print("Select Player")

for i in range(len(AllPlayers)):
    print("{}. {}".format(i, AllPlayers[i].name))

PlayerNum = input("Enter Player Num:")
Player = AllPlayers[int(PlayerNum)]

print("{} is the challenger with {} Health.".format(Player.name, Player.CurrentHealth))

# Setup the logging 
SetUpLogging()

# Start the 2 threads to deal with the Comms - UDP for attacks, skips, etc.  TCP is used for managing session, etc.
# Both threads are set up a Daemon threads, so they will be killed when the main thread exits.
UDPCommsThread = UDPCommsThread(1, "UDP Data Transmission Thread - real time data might drop some packets.", 1)
UDPCommsThread.setDaemon(True)
UDPCommsThread.start()
TCPCommsThread = TCPCommsThread(1, "TCP Data Transmission Thread - non real time data - manage session, etc.", 1)
TCPCommsThread.setDaemon(True)
TCPCommsThread.start()

try:
    while (1):
        pass
except:
    print("Main Function Exception")
finally:
    print("Server is dead - long live Server")
    logging.shutdown()
    AttackLogs.close()

