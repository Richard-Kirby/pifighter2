#!/usr/bin/env python3

import numpy
from pixel_display.bar_indicator import BarIndicator
from pixel_display.text_handler import TextDisplay
import unicornhathd
import time


# Class to manage the pixel display - covers player health, opponent health, player attacks, opponent attacks.
# Also Text displays.
class PixelDisplay:

    # Set up Attack indication bars.
    player_attack_bar = BarIndicator(6, 16, 8, 15, numpy.arange(.93, .60, -.33 / 16))
    opponent_attack_bar = BarIndicator(6, 16, 2, 15, numpy.arange(0, .33, .33 / 16))

    # Set up text display
    text_display = TextDisplay()

    # Initialisation - some default colour for each pixel.
    # Set up the required objects for the display.
    def __init__(self):
        unicornhathd.clear()
        unicornhathd.set_all(10, 0, 10)
        unicornhathd.show()
        unicornhathd.rotation(270) # Rotation
        unicornhathd.brightness(.75)
        unicornhathd.show()

    # Display a welcome message
    def welcome_message(self, name):
        self.text_display.display_text("Next Pi Fighter {} ".format(name))

    # Display any string
    def text_message(self, display_str):
        display_str += " "
        self.text_display.display_text(display_str)

    # Set up player health
    def set_up_player_health(self, pixel_height):
        #global BarIndicator

        #self.player_health_bar = BarIndicator(2, pixel_height, 0, 0, numpy.arange(0, .33, .33 / 16))
        self.player_health_bar = BarIndicator(2, pixel_height, 14, 0, numpy.arange(0, .33, .33 / 16))

    # Set up opponent health
    def set_up_opponent_health(self, pixel_height):
        #global BarIndicator
        #self.opponent_health_bar = BarIndicator(2, 16, 14, 0, numpy.arange(.93, .60, -.33 / 16))
        self.opponent_health_bar = BarIndicator(2, pixel_height, 0, 0, numpy.arange(.93, .60, -.33 / 16))

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

    # Display a quadrant for the attack
    # quadrant 1 = Left Kick, 2 = Left Punch, 3 = Right Kick, 4 = Right Punch
    # colour = -1 means to use default
    def workout_attack(self, attack_type, delay = 0.2, colour = -1):

        # x and y lengths of the pixels to display
        x_len = 2
        y_len = 5

        #print(attack_type)

        # Translate the quadrant to pixel start locations and
        # colours.  Use Red for Right (Hue =1), Green (Hue =0.33) for Left.
        if attack_type == 'KickLeft':
            x_start = 0
            y_start = 0

            if colour == -1:
                attack_colour=0.33
            else:
                attack_colour = colour

        elif attack_type == 'PunchLeft':
            x_start = 0
            y_start = 11
            if colour == -1:
                attack_colour=0.33
            else:
                attack_colour= colour

        elif attack_type == 'PunchRight':
            x_start = 14
            y_start = 11
            if colour == -1:
                attack_colour=1
            else:
                attack_colour=1
        elif attack_type == 'KickRight':
            x_start = 14
            y_start = 0

            if colour == -1:
                attack_colour= 1
            else:
                attack_colour=1

        # Don't do anything special for Wait - it is just a pause.
        elif attack_type == 'Wait':
            x_start = 0
            y_start = 0
            attack_colour =0

        # Raise exception of quadrant doesn't make sense.
        else:
            print("attack {} not handled " .format(attack_type))
            x_start =7
            y_start =0
            attack_colour = 0.78

        # Set the pixels and then display.
        for i in range (x_len):
            for j in range (y_len):
                unicornhathd.set_pixel_hsv(x_start+i, y_start+ j, attack_colour)

        unicornhathd.show()

        time.sleep(delay)
        for i in range (x_len):
            for j in range (y_len):
                unicornhathd.set_pixel_hsv(x_start+i, y_start+ j, 0, v=0)

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

    Display.text_message("Bye{} ".format("Ricardo"))

    print("Left kick")
    Display.workout_attack(1)

    time.sleep(2)

    print("Left punch")
    Display.workout_attack(2)

    time.sleep(2)

    print("right kick")
    Display.workout_attack(3)

    time.sleep(2)

    print("right punch")
    Display.workout_attack(4)

    Display.set_player_attack(101)
