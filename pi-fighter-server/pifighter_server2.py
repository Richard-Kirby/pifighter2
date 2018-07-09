


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

        self.player_manager = PlayerManager()


