import json


class AttackProcessor():
    def __init__(self, opponent_file, fighter_name, fight_name, player =1):
        self.opponent_file = opponent_file
        self.player = player
        self.fighter_name = fighter_name
        self.fight_name = fight_name
        print(self.opponent_file)

        self.fight_file = open(opponent_file, 'r')
        self.fight_dict = json.load(self.fight_file)
        self.normalised_fight ={}


    def process_fight(self):
        last_time = 0.0 # initialise the last time - only for the first attack.

        # Go through the dictionary and extract player or opponent attacks as needed.
        for record_key in sorted(self.fight_dict):

            if self.player == 1:

                player_attack = self.fight_dict[record_key].get("player attack damage")
                if player_attack != None:
                    if last_time == 0.0:
                        attack_time = 0.0

                    else:
                        attack_time = float(record_key) - last_time

                    last_time = float(record_key)
                    #print(attack_time, record_key, player_attack)

                    self.normalised_fight[attack_time] = player_attack
        #print(self.normalised_fight)

    def write_to_file(self):
        #create file name
        self.filename = self.fighter_name + self.fight_name + ".json"
        with open(self.filename, "w") as write_file:
            json.dump(self.normalised_fight, write_file)

        with open(self.filename, "r") as read_file:
            fight = json.load(read_file)
            print(fight)


        # If player is equal to 1, then pull out the player attack information, otherwise pull out the opponent attacks
        #if player is 1:

if __name__== "__main__":
    print("file 1")
    opponent_attacks = AttackProcessor("./log/pifighter_server_19_04_14__1659_Richard Kirby_v_C3-PO.json", "Richard Kirby", "v C3-PO 19 04 14")
    opponent_attacks.process_fight()
    opponent_attacks.write_to_file()

    print("file 2")
    opponent_attacks = AttackProcessor("./log/pifighter_server_19_04_13__1133_Richard Kirby_v_One Ewok.json",  "Richard Kirby", "v One Ewok 19 04 14")
    opponent_attacks.process_fight()
    opponent_attacks.write_to_file()

