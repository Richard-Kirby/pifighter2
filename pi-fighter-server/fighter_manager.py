import xml.etree.ElementTree as ET

# Fighter class - base class for opponents and players.
class fighter():
    def __init__(self, name, health):
        self.name = name
        self.health = float(health)
        self.initial_health = float(health)
        self.current_health = float(health)

    # print out information.
    def print_info(self):
        print("Name:{} health:{} Initial Health:{} Current Health{} ". format(self.name, self.health, self.initial_health, self.current_health))

    # Decrements health - usually due to an attack.
    def decrement_health(self, attack):
        self.current_health -= attack
        # print("Fighter Health now {}".format(self.CurrentHealth))
        return (self.current_health)

    # Resets Health - set the health back to the maximum
    def reset_health(self):
        self.current_health = self.initial_health

# Class to handle the Virtual Fighters.
class VirtualFighter(fighter):

    # Virtual fighter init
    def __init__(self, name, health, attack_filename):
        super().__init__(name, health)
        self.attack_file = attack_filename

# Player Class - manages player information.  It is just a type of fighter, but gets re-gen and extra health when wins a fight.
class Player(fighter):
    def __init__(self, name, health):
        super().__init__(name, health)

    def regen(self, percent):
        # Maximum Regeneration Calc - capped at original.  Regenerate the defined percentage
        # of what has been lost
        self.current_health += (self.initial_health - self.current_health) * (percent / 100)

        print("Regened Health ", self.current_health)

    # Increase the User's health points - usually for winning a fight.
    def reward_health_point(self, reward_pts):
        # Add the Reward Points to Health, but not initial health (to keep track of what changed during the session)
        self.health += reward_pts
        print("Bonus Health - Player {}'s profile now has {} health points.\n  {} started session with {} and currently has {}"
                .format(self.name, self.health, self.name, self.initial_health, self.current_health))

# Manager for the Virtual Fighters todo Need to change to file based storage like players.
class VirtualFighterManager():
    def __init__(self):
        # Build a list of Virtual Fighters - todo should be put into a file.
        self.virtual_fighters = [
            VirtualFighter("One Ewok", 75, 'One_Ewok_Attack_LevelOne.xml'),
            VirtualFighter("C3-PO", 110, "C3-PO_Attack_LevelOne.xml"),
            VirtualFighter("Early Luke SkyWalker", 125, "Early_Luke_Attack_LevelOne.xml"),
            VirtualFighter("JarJar Binks", 200, "JarJar_Binks_Attack_LevelOne.xml"),
            VirtualFighter("Many Ewoks", 250, "Many_Ewoks_Attack_LevelOne.xml"),
            VirtualFighter("Jedi Luke", 300, "Jedi_Luke_Attack_LevelOne.xml"),
            VirtualFighter("Yoda", 400, "Yoda_LevelOne.xml"),
            VirtualFighter("Darth Vader", 400, "Darth_Vader_Attack_LevelOne.xml")
        ]

# Class to manager players - users of the site.
class PlayerManager():
    def __init__(self):
        self.player_file = "pi-fighter-users.xml"

        print("Processing all players from file" + self.player_file)

        self.all_players = []

        # parse all the players into a element tree
        self.player_file_info = ET.parse(self.player_file)

        # Grabs the root of the XML tree for processing.
        self.player_et_root = self.player_file_info.getroot()

        # Parse the User information into separate players - this works through the
        # The XML Element Tree
        for player in self.player_et_root:

            # Build a list of players
            self.all_players.append(Player(player.attrib.get('Name'), player.find('Health').text))

        print("Found {} Players" .format(len(self.all_players)))

    # Find and return the player that is being searched.
    def get_player(self, name):

        player = None

        # Search through to get the player name
        for candidate in self.all_players:
            if candidate.name == name:
                player = candidate

        # return the player object - may be None if not successful
        return player


    # Updates the player's information in the XML tree.
    def update_player_xml(self, player_to_update):
        # Go through the players looking for the player in question.
        for player in self.player_et_root:
            # print(User.tag, User.attrib)
            # If ind the right player then update his/her health.
            if player.attrib.get('Name') == player_to_update.name:
                player.find('Health').text = str(player_to_update.health)
                # print ("$${}$$".format(User.find('Health').text))

    # Update the XML file for persistent storage.
    def update_player_file(self):
        self.player_file_info.write(self.player_file)

    def print_players(self):
        for player in self.all_players:
            player.print_info()


if __name__ == "__main__":
    player_manager = PlayerManager()

    player_manager.print_players()

    for vfighter in virtual_fighters:
        vfighter.print_info()

