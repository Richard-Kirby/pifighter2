
import threading
import configparser
import fighter_manager


class fight_manager(threading.Thread):

    def __init__(self):

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

    
if __name__ == "__main__":

    fight_mgr = fight_manager()
    fight_mgr.player_manager.print_players()



