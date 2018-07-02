import tkinter as tk
import configparser
import queue
import xml.etree.ElementTree as et
import time

# My modules
import session_manager as session_mgr
import server_communicator.server_communicator as server_comm

# Main application
class Application(tk.Frame):
    players = ["Richard Kirby", "Joh Kirby", "GUEST"]
    opponents = ["Darth", "Yoda", "Others"]

    # Set up the basic GUI elements
    def __init__(self, master=None):
        super().__init__(master)
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

        # Holds player string.
        self.player = tk.StringVar()
        pi_fighter_width = 40
        pi_fighter_font = ("Starjhol.ttf", 12, "bold")

        # Title of the application
        self.heading_label = tk.Label(text="PI FIGHTER", bg="green", width=pi_fighter_width,
                                      font=("Starjhol.ttf", 25, "bold"))
        self.heading_label.pack(side="top")

        # Init with guest logon.
        self.player.set("No one logged on - assume GUEST")
        self.player_label = tk.Label(textvariable=self.player, width=pi_fighter_width,
                                     font=("Starjhol.ttf", 20, "bold"))
        self.player_label.pack(side="top")
        self.pack()

        # Create the list of possible players
        self.player_list = tk.Listbox(self, font=pi_fighter_font, width=pi_fighter_width, selectmode=tk.SINGLE,
                                      exportselection=0)
        # Create select box of players
        for player in self.players:
            self.player_list.insert(tk.END, player)
        self.player_list.pack(side="top")

        # Select first player
        self.player_list.select_set(0)  # This only sets focus on the first item.
        self.player_list.event_generate("<<ListboxSelect>>")

        self.player_button = tk.Button(self, font=pi_fighter_font, width=pi_fighter_width, bg="green")
        self.player_button["text"] = "Logon Player"
        self.player_button["command"] = self.player_select
        self.player_button.pack(side="top")

        # Create opponent list.
        self.opponent_list = tk.Listbox(self, font=pi_fighter_font, width=pi_fighter_width, selectmode=tk.SINGLE,
                                        exportselection=0)

        self.opponent_list.pack(side="top")
        self.opponent_list.select_set(0)  # This only sets focus on the first item.
        self.opponent_list.event_generate("<<ListboxSelect>>")

        # get list of opponents from the server. todo need to make robust
        self.opponent_list_setup()

        # Workout button initiates a workout.
        self.workout = tk.Button(self, font=pi_fighter_font, bg="green")
        self.workout["text"] = "Workout"
        self.workout["command"] = self.start_workout
        self.workout.pack(side="top")

        # Fight button starts a fight with the selected opponent.
        self.workout = tk.Button(self, font=pi_fighter_font, bg="green")
        self.workout["text"] = "Fight"
        self.workout["command"] = self.start_fight
        self.workout.pack(side="top")

        # Window to display the current fight information
        # self.fight_window = tk.Text

        # Quit button
        self.quit = tk.Button(self, text="QUIT", fg="red", font=pi_fighter_font,
                              command=self.master.destroy)
        self.quit.pack(side="bottom")


    # Start workout
    def start_workout(self):
        print("Start workout")
        self.session.close_session()
        self.session.setup_workout()

    def opponent_list_setup(self):
        # Get list of Opponents

        self.tcp_send_q.put_nowait("<OpponentList></OpponentList>")
        print("Put Opponent List Request into TCP Queue")

        # Allow a few seconds for a response.
        time.sleep(3)

        # Processing of Opponent Information - create a list of opponents
        self.opponents = []

        if not self.tcp_rec_q.empty():

            # Blocking waiting for a list of oppoonents.
            server_data = self.tcp_rec_q.get()

            # Decode to ASCII so it can be processed.
            server_str = server_data.decode('ascii')

            # print (ServerStr)

            # Put the data into an XML Element Tree
            server_element = et.fromstring(server_str)


            if server_element.tag == 'OpponentList':
                for child in server_element:
                    # print (Child.tag + Child.text)
                    if child.tag == 'Opponent':
                        opponent_info = child.text
                        self.opponents.append(opponent_info)

            for opponent in self.opponents:
                self.opponent_list.insert(tk.END, opponent)

            #self.opponent_list.update()

        # Check for a new list once in a while from the server.
        root.after(15000000000000000000, self.opponent_list_setup())



    # Set Player.
    def player_select(self):
        player_index = int(self.player_list.curselection()[0])
        self.player.set(self.players[player_index])
        print(self.player.get())

        # Set up a session for this player.
        self.session = session_mgr.Session(self.player.get(), self.tcp_send_q, self.tcp_rec_q, self.udp_send_q, self.udp_rec_q)

    # Set opponent
    def opponent_select(self):
        opponent_index = int(self.opponent_list.curselection()[0])
        self.opponent = self.opponents[opponent_index]
        print(self.opponent)

    # Start fight
    def start_fight(self):
        self.opponent_select()

        fight_str = "Fight {} v {}".format(self.player.get(), self.opponent)

        self.session.setup_fight(self.opponent)

        self.player.set(fight_str)



root = tk.Tk()
app = Application(master=root)
app.mainloop()