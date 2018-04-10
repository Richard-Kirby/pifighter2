#!/usr/bin/env python

from bar_indicator import BarIndicator
from text_handler import TextDisplay
import numpy

import unicornhathd

# Class to manage the pixel display - covers player health, opponent health, player attacks, opponent attacks.
# Also Text displays.

class PixelDisplay:

    # Set up Attack indication bars.
    player_attack_bar = BarIndicator(6, 16, 2, 0, numpy.arange(.93, .60, -.33 / 16))
    opponent_attack_bar = BarIndicator(6, 16, 8, 0, numpy.arange(0, .33, .33 / 16))

    # Set up text display
    text_display = TextDisplay()

    # Initialisation - some default colour for each pixel.
    # Set up the required objects for the display.
    def __init__(self):
        unicornhathd.clear()
        unicornhathd.set_all(10, 0, 10)
        unicornhathd.show()
        unicornhathd.rotation(-90)
        unicornhathd.brightness(.75)
        #unicornhathd.set_pixel(0,0,255,0,0)
        #unicornhathd.set_pixel(1,0,255,0,0)
        #unicornhathd.set_pixel(15,15,0,0,255)
        #unicornhathd.set_pixel(15,14,0,255,0)

        unicornhathd.show()
        #time.sleep(10)



    # Display a welcome message
    def welcome_message(self, name):
        self.text_display.display_text(" WELCOME Adversary {} to PI-FIGHTER ".format(name))

    # Set up player health
    def set_up_player_health(self, pixel_height):
        global BarIndicator

        self.player_health_bar = BarIndicator(2, pixel_height, 0, 0, numpy.arange(0, .33, .33 / 16))

    # Set up opponent health
    def set_up_opponent_health(self, pixel_height):
        global BarIndicator

        self.opponent_health_bar = BarIndicator(2, 16, 14, 0, numpy.arange(.93, .60, -.33 / 16))

    # Set the player's health in percentage.
    def set_player_health(self, percentage):
        self.player_health_bar.display_percent(percentage)
        unicornhathd.show()

    # Set opponents health in percentage.
    def set_opponent_health(self, percentage):
        self.opponent_health_bar.display_percent(percentage)
        unicornhathd.show()

    # Set player attack bar percentage.
    def set_player_attack(self, percentage):
        self.player_attack_bar.display_percent(percentage)
        unicornhathd.show()

    # Set opponent attack bar percentage.
    def set_opponent_attack(self, percentage):
        self.opponent_attack_bar.display_percent(percentage)
        unicornhathd.show()



if __name__ == "__main__":

    import time
    import random

    Display = PixelDisplay()
    Display.set_up_player_health(10)
    Display.set_up_opponent_health(16)

    Display.welcome_message("Ricardo")

    for i in range (101, -1, -1):
        Display.set_player_health(i)
        Display.set_opponent_health(i)

        Display.set_player_attack(random.randrange(0,101))
        Display.set_opponent_attack(random.randrange(0,101))

        time.sleep(0.05)