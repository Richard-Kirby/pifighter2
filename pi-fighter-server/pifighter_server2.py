import threading
import configparser
import socket
import xml.etree.ElementTree as ElementTree

import fighter_manager

class ClientDisconnnect(Exception):
    def __init__(self, message):
        self.message = message


class PlayerSessionManager(threading.Thread):
    def __init__(self, tcp_client_socket, player_mgr, virtual_opp_mgr):

        threading.Thread.__init__(self)

        self.tcp_client_socket = tcp_client_socket
        self.player_mgr = player_mgr
        self.virtual_opp_mgr = virtual_opp_mgr

        player_mgr.print_players()

    def run(self):

        print("PlayerSessionManager threading run")

        try:

            while True:

                # self.request is the TCP socket connected to the client
                self.data = self.tcp_client_socket.recv(1024).strip()

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
                            for virtual_fighter in self.virtual_opp_mgr.virtual_fighters:
                                Name = virtual_fighter.name
                                opponent_str += "<Opponent>{}</Opponent>".format(Name)

                            opponent_str += "</OpponentList>"
                            # print (OpponentStr)
                            self.tcp_client_socket.sendall(bytes(opponent_str, "utf-8"))

                        # If Client has selected an Opponent, then set the opponent to the one selected.
                        elif (client_element.tag == 'SelectedOpponent'):
                            OpponentName = client_element.text


                            print (OpponentName)

                            # Find the Selected Opponent.

                            #for i in range(len(VirtualFighters)):
                            #    if VirtualFighters[i].name == OpponentName:
                            #        opponent = VirtualFighters[i]

                            #        print("Found Opponent", OpponentName)

                                    # Clear the fight over flag - this may not be the first fight
                            #        FightOver.clear()
                            #       break

                            # Setting up for the fight - setting various things back up.
                            #opponent_defeated = False  # Set Opponent Defeated to False

                            # Reset the opponents health - this is needed if opponent has already been used.
                            #opponent.ResetHealth()

                            #print("Health is {}".format(opponent.CurrentHealth))

                            #OpponentReadyStr = "<OpponentReady>{}</OpponentReady>".format(opponent.name)

                            #self.request.sendall(bytes(OpponentReadyStr, "utf-8"))


                        else:
                            print("Don't know how to process this one")

                    except:
                        print("Trouble Processing String: {}".format(client_str))

                        raise ()
        except ClientDisconnnect:
            print("Client Disconnect")

        except:

            raise

class fight_manager(threading.Thread):

    def __init__(self):

        threading.Thread.__init__(self)

        # Set up the config parser
        config = configparser.ConfigParser()

        # Read the config file in.
        config.read('pi-fighter-server.cfg')

        self.udp_address = (config['SERVER']['SERVER_HOST'], int(config['SERVER']['UDP_PORT']))
        self.tcp_address = (config['SERVER']['SERVER_HOST'], int(config['SERVER']['TCP_PORT']))

        print(self.tcp_address)
        print(self.udp_address)

        self.player_manager = fighter_manager.PlayerManager()

        self.virtual_fighter_manager = fighter_manager.VirtualFighterManager()

        # Set up TCP Server - creates a new thread for each new connection.


    def run(self):

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

            Session_Manager = PlayerSessionManager(clientsocket, self.player_manager, self.virtual_fighter_manager)

            Session_Manager.start()




if __name__ == "__main__":

    fight_mgr = fight_manager()
    fight_mgr.player_manager.print_players()
    fight_mgr.start()




