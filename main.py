import tkinter as tk
import configparser
import queue
import xml.etree.ElementTree as et
import time
import threading
from PIL import Image, ImageTk

# My modules
import session_manager as session_mgr
import server_communicator.server_communicator as server_comm



# Main application
class Application(tk.Frame, threading.Thread):

    # Set up the basic GUI elements
    def __init__(self, master=None):
        super().__init__(master, borderwidth=5, relief="sunken", width=200, height=100)
        threading.Thread.__init__(self)

        self.master = master

        # Read in the config

        config = configparser.ConfigParser()
        config.read('pifighter2.cfg')
        self.server_address = config['SERVER']['SERVER_HOST']
        self.udp_port = int(config['SERVER']['UDP_PORT'])
        self.tcp_port = int(config['SERVER']['TCP_PORT'])
        print(self.server_address, self.udp_port, self.tcp_port)

        self.udp_rec_q = queue.Queue()
        self.udp_send_q = queue.Queue()
        self.tcp_rec_q = queue.Queue()
        self.tcp_send_q = queue.Queue()

        self.server_comm = server_comm.ServerCommunicator(self.server_address,
                                                          self.udp_port, self.udp_send_q, self.udp_rec_q,
                                                          self.tcp_port, self.tcp_send_q, self.tcp_rec_q)

        #
        self.grid(row=0, column=0) #, columnspan=2, rowspan=8, sticky="nsew")
        #root.grid_rowconfigure(0, weight=1)
        #root.grid_columnconfigure(0, weight=1)

        # Holds player string.
        self.player = tk.StringVar()
        pi_fighter_width = 40
        pi_fighter_font = ("Starjhol.ttf", 12, "bold")

        # Title of the application
        self.heading_label = tk.Label(self, text="PI FIGHTER", bg="green", width=15,
                                      font=("Starjhol.ttf", 25, "bold"))
        self.heading_label.grid(row=0, column=0)

        # Init with guest logon.
        #
        self.player.set("Logon to Fight or Workout")
        self.player_label = tk.Label(self, textvariable=self.player, width=pi_fighter_width,
                                     font=("Starjhol.ttf", 20, "bold"))
        self.player_label.grid(row=1, column=0)

        # Create the list of possible players
        self.player_list = tk.Listbox(self, font=pi_fighter_font, width=pi_fighter_width, selectmode=tk.SINGLE,
                                      exportselection=0)

        # Requests list of players from the server
        self.player_list_setup()
        self.player_list.grid(row = 2, column =0)


        # Select first player
        self.player_list.select_set(0)  # This only sets focus on the first item.
        self.player_list.event_generate("<<ListboxSelect>>")

        self.player_button = tk.Button(self, font=pi_fighter_font, width=pi_fighter_width, bg="green")
        self.player_button["text"] = "Logon Player"
        self.player_button["command"] = self.player_select
        self.player_button.grid(row = 3, column =0 )

        # Create opponent list.
        self.opponent_list = tk.Listbox(self, font=pi_fighter_font, width=pi_fighter_width, selectmode=tk.SINGLE,
                                        exportselection=0)

        self.opponent_list.grid(row = 4, column =0 )
        self.opponent_list.select_set(0)  # This only sets focus on the first item.
        self.opponent_list.event_generate("<<ListboxSelect>>")

        # get list of opponents from the server. todo need to make robust
        self.opponent_list_setup()

        # Workout button initiates a workout.
        self.workout = tk.Button(self, font=pi_fighter_font, bg="green")
        self.workout["text"] = "Workout"
        self.workout["command"] = self.start_workout
        self.workout.grid(row = 5, column =0 )

        # Fight button starts a fight with the selected opponent.
        self.workout = tk.Button(self, font=pi_fighter_font, bg="green")
        self.workout["text"] = "Fight"
        self.workout["command"] = self.start_fight
        self.workout.grid(row = 6, column =0 )

        self.image = Image.open("luke.jpg")
        photo = ImageTk.PhotoImage(self.image)
        self.label = tk.Label(image=photo)
        self.label.image = photo  # keep a reference!
        self.label.grid(row=0, column =1)

        # Quit button
        self.quit = tk.Button(self, text="QUIT", fg="red", font=pi_fighter_font,
                              command=self.master.destroy)
        self.quit.grid(row = 7, column =0 )

        self.session = None


        # Start workout
    def start_workout(self):
        print("Start workout")
        self.session.close_session()
        self.session.setup_workout()

    def run(self):

        # init of winner_text
        winner_text = 'none'

        while(1):

            #print("1")
            if not self.tcp_rec_q.empty():

                # Blocking waiting for a list of oppoonents.
                server_data = self.tcp_rec_q.get()

                # Decode to ASCII so it can be processed.
                server_str = server_data.decode('ascii')

                # print (ServerStr)

                # Put the data into an XML Element Tree
                server_element = et.fromstring(server_str)

                # Set up player list received from the Server
                if server_element.tag == 'PlayerList':
                    for child in server_element:
                        # print (Child.tag + Child.text)
                        if child.tag == 'Player':
                            player_info = child.text
                            print(player_info)
                            self.players.append(player_info)

                    for player in self.players:
                        self.player_list.insert(tk.END, player)

                # Set up Opponent list received from Server
                elif server_element.tag == 'OpponentList':
                    for child in server_element:
                        # print (Child.tag + Child.text)
                        if child.tag == 'Opponent':
                            opponent_info = child.text
                            print(opponent_info)
                            self.opponents.append(opponent_info)

                    for opponent in self.opponents:
                        self.opponent_list.insert(tk.END, opponent)

                elif server_element.tag == 'OpponentReady':
                    print("** Opponent Ready", server_element.text)
                    for i in range (5,-1, -1):
                        count = "...{}...".format(i)
                        self.session.pix_display.text_message(count)
                        time.sleep(0.25)

                    self.session.pix_display.text_message("Fight!")

                    self.session.fight.start_fight()

            if not self.udp_rec_q.empty():

                # Get data from server
                server_data = self.udp_rec_q.get()

                # Decode to ASCII so it can be processed.
                server_str = server_data.decode('ascii')

                # print (ServerStr)

                # Put the data into an XML Element Tree
                server_element = et.fromstring(server_str)

                if server_element.tag == 'OpponentAttack':
                    print("OpponentAttack ", server_str)
                    damage = float(server_element.text)
                    #print("Damage {}" .format(damage))
                    self.session.opponent_attack_q.put_nowait(damage)

                elif server_element.tag == 'FightState':

                    for child in server_element:
                        if child.tag == 'PlayerHealth':
                            self.session.pix_display.set_player_health(float(child.text)/300 * 100)
                        elif child.tag == 'OpponentHealth':
                            self.session.pix_display.set_opponent_health(float(child.text)/300 * 100)
                        elif child.tag == 'FightWinner':
                            print(child.text)
                            if child.text != 'None':
                                # print(child.text, self.player_name)
                                if child.text == self.player_name and winner_text != 'announced':
                                    winner_text = "You beat {}. " .format(self.opponent)

                                else:
                                    winner_text = "{} beat you. " .format(self.opponent)

                                self.session.pix_display.text_message(winner_text)
                                winner_text = "announced"
                            else:
                                winner_text = "None"

                        else: # todo Need to process other information as well.
                            print (child.tag)


                else:
                    print("Unable to Decode ",server_str)

                    #self.opponent_list.update()
            time.sleep(0.01)
        # Check for a new list once in a while from the server.
        #root.after(15000000000000000000, self.opponent_list_setup())

    # Requesting Player List.
    def player_list_setup(self):
        # Get list of Opponents
        self.players = []
        self.tcp_send_q.put_nowait("<PlayerList></PlayerList>")
        print("Put player List Request into TCP Queue")

    # Requesting Opponent List.
    def opponent_list_setup(self):
        # Get list of Opponents
        self.opponents = []
        self.tcp_send_q.put_nowait("<OpponentList></OpponentList>")
        print("Put Opponent List Request into TCP Queue")

    # Set Player.
    def player_select(self):
        player_index = int(self.player_list.curselection()[0])
        player = self.players[player_index]
        self.player.set(self.players[player_index])
        player_sel_str = "<SelectedPlayer>{}</SelectedPlayer>" .format(player)
        self.player_name = self.players[player_index]

        # Send selected player to the Server
        self.tcp_send_q.put_nowait(player_sel_str)

        # Set up a session for this player.
        self.session = session_mgr.Session(self.player.get(), self.tcp_send_q, self.tcp_rec_q, self.udp_send_q, self.udp_rec_q)
        self.session.start()

    # Set opponent
    def opponent_select(self):
        opponent_index = int(self.opponent_list.curselection()[0])
        self.opponent = self.opponents[opponent_index]
        print(self.opponent)

    # Start fight
    def start_fight(self):
        self.opponent_select()

        fight_str = "Fight {} v {}".format(self.player_name, self.opponent)

        self.player.set("")

        # Updates the banner at the top of the application.
        self.player.set(fight_str)


        # Set up the fight.
        self.session.setup_fight(self.opponent)


root = tk.Tk()
app = Application(master=root)

app.start()

app.mainloop()