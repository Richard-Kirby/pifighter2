import json
import matplotlib
import time
#from multiprocessing import Process

matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
from matplotlib import style

#matplotlib.use('Qt5Agg')

style.use('fivethirtyeight')


class FightPlotter():

    def __init__(self, filename):
        #self.fig = plt.figure()
        [self.fig, self.ax] = plt.subplots(2, 1, sharex='col')

        self.fight_log_file = open(filename, 'r')
        self.fight_dict = json.load(self.fight_log_file)

        self.player_health=[]
        self.opponent_health=[]
        self.player_attacks = []
        self.opponent_attacks = []
        self.time_series=[]
        self.player = None
        self.opponent = None


    def prep_data(self):

        for time_x, fight_info in sorted(self.fight_dict.items()):
            #print("{}, {}, {}, {}, {}".format(time_x, fight_info["player"], fight_info["player health"], fight_info["player attack damage"], fight_info["opponent name"], fight_info["opponent current health"], fight_info["opponent attack damage"],))

            self.player = fight_info["player"]
            self.opponent = fight_info["opponent name"]

            self.time_series.append(float(time_x))

            self.player_health.append(float(fight_info["player health"]))
            self.opponent_health.append(float(fight_info["opponent current health"]))

            # Sort of the attack data.
            if fight_info["player attack damage"] is not None:
                player_attack = float(fight_info["player attack damage"])
            else:
                player_attack = 0.0

            self.player_attacks.append(player_attack)

            if fight_info["opponent attack damage"] is not None:
                opponent_attack = float(fight_info["opponent attack damage"])
            else:
                opponent_attack = 0.0

            self.opponent_attacks.append(opponent_attack)


        # baseline the time to the start of the file
        start_time = self.time_series[0]

        for i in range(len(self.time_series)):
            self.time_series[i] = float(self.time_series[i]) - float(start_time)

    def plot_fight_data(self):

        # Prepare the data.
        self.prep_data()

        #plt.ion()

        self.ax[0].clear()
        self.ax[0].plot(self.time_series, self.player_health, label=self.player)
        self.ax[0].plot(self.time_series, self.opponent_health, label=self.opponent)
        self.ax[0].set_ylabel('Health')
        self.ax[0].set_title('Player and Opponent Fight Health')
        self.ax[0].legend()

        self.ax[1].clear()
        self.ax[1].set_ylim(-1,18)
        self.ax[1].set_ylabel('Attacks(g)')
        self.ax[1].plot(self.time_series, self.player_attacks, 'X')
        self.ax[1].plot(self.time_series, self.opponent_attacks, 'o')
        self.ax[1].set_xlabel('time')
        #plt.pause(0.0001)
        plt.show()
        #time.sleep(10)
        #   plt.close(self.fig)

if __name__ == "__main__":

    fight_plotter = FightPlotter("log/pifighter_server_19_04_12__1650_Richard Kirby_v_One Ewok.json")

    fight_plotter.prep_data()

    fight_plotter.plot_fight_data()


