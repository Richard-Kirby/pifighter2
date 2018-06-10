import tkinter as tk
import session_manager.session_manager as session_mgr

# Main application
class Application(tk.Frame):
    players = ["Richard Kirby", "Joh Kirby", "GUEST"]
    opponents = ["Darth", "Yoda", "Others"]

    # Set up the basic GUI elements
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master

        # Holds player string.
        self.player = tk.StringVar()
        pi_fighter_width = 30
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

        for opponent in self.opponents:
            self.opponent_list.insert(tk.END, opponent)
        self.opponent_list.pack(side="top")
        self.opponent_list.select_set(0)  # This only sets focus on the first item.
        self.opponent_list.event_generate("<<ListboxSelect>>")

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

        # Quit button
        self.quit = tk.Button(self, text="QUIT", fg="red", font=pi_fighter_font,
                              command=self.master.destroy)
        self.quit.pack(side="bottom")

    # Start workout
    def start_workout(self):
        print("Start workout")
        self.session.close_session()
        self.session.setup_workout()

    # Set Player.
    def player_select(self):
        player_index = int(self.player_list.curselection()[0])
        self.player.set(self.players[player_index])
        print(self.player.get())

        # Set up a session for this player.
        self.session = session_mgr.Session(self.player.get())

    # Set opponent
    def opponent_select(self):
        opponent_index = int(self.opponent_list.curselection()[0])
        self.opponent = self.opponents[opponent_index]
        print(self.opponent)

    # Start fight
    def start_fight(self):
        self.opponent_select()
        print("Start fight {} v {}".format(self.player.get(), self.opponent))


root = tk.Tk()
app = Application(master=root)
app.mainloop()