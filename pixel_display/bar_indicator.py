#!/usr/bin/env python

# This class built to work with unicorn hat hd.  Should work with other displays
# assumes 16x16 matrix.
import unicornhathd

# Class to display a bar of a certain width and height, which
# can then display a percentage of the bar.  Optional to change
# the colour depending on the percentage.
class BarIndicator:

    x_loc =0 # start x location of the bar
    y_loc =0 # start y location of the bar.
    x_size =0 # width of the bar.
    y_size =0 # maximum height of the bar.

    # background colour to use for bars that are not fully filled in.
    back_colour = (0,0,0)
    colour_list = []

    # Setting up the object, set size, location, and colours to use.
    def __init__(self, x_size, y_size, x_loc, y_loc,  colour_list, back_colour=(10,0,10)):

        self.x_size = x_size
        self.y_size = y_size
        self.x_loc = x_loc
        self.y_loc = y_loc
        self.back_colour = back_colour
        self.colour_list = colour_list

    # Display a percentage of the bar graph
    def display_percent(self, bar_percent):

        # Calculate number of pixels to illuminate.
        bar_pixels = bar_percent/100 * (self.y_size -1)

        # Figure out the colour to display based on the percentage
        state_colour = self.colour_list[int(bar_percent / 100 * 15)] # 15 is the maximum colours in the colour list

        # Set the pixels as required, using the colour for the state. Pixels not actively lit use the background
        # colour (could be black).
        for i in range (0, self.x_size):
            for j in range (self.y_size):
                if j <= int(bar_pixels):
                    unicornhathd.set_pixel_hsv(self.x_loc + i, self.y_loc + j, state_colour)

                else:
                    unicornhathd.set_pixel(self.x_loc + i, self.y_loc + j, self.back_colour[0],self.back_colour[1], self.back_colour[2])
