#!/usr/bin/env python3

import colorsys
import time
from sys import exit

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    exit("This script requires the pillow module\nInstall with: sudo pip install pillow")

import unicornhathd

class TextDisplay:

    def __init__(self,  x_size=16, y_size=16, x_loc=0, y_loc=0, delay=0.01,
                 font_file = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", font_size = 12, colour=(0,0,100)):
        self.x_size = x_size
        self.y_size = y_size
        self.x_loc = 0
        self.y_loc = 0
        self.delay = delay
        self.font_file = font_file
        self.font_size = font_size
        self.colour = colour

    # Display text as requested - set up as rainbow text - taken from Pimoroni examples.
    def display_text(self, text, font_size=0):

        # set to default font_size if not passed in.
        if font_size ==0:
            font_size = self.font_size

        curr_rotation = unicornhathd.get_rotation()

        # Adjusting rotation - will turn it back after the displaying the text.
        unicornhathd.rotation (curr_rotation - 180)

        # Use `fc-list` to show a list of installed fonts on your system,
        # or `ls /usr/share/fonts/` and explore.

        # sudo apt install fonts-droid
        # FONT = ("/usr/share/fonts/truetype/droid/DroidSans.ttf", 12)

        # sudo apt install fonts-roboto
        # FONT = ("/usr/share/fonts/truetype/roboto/Roboto-Bold.ttf", 10)

        # Get the width/height of Unicorn HAT HD.
        # These will normally be 16x16 but it's good practise not to hard-code such numbers,
        # just in case you want to try and hack together a bigger display later.
        width, height = unicornhathd.get_shape()

        # We want to draw our text 1 pixel in, and 2 pixels down from the top left corner
        text_x = 1
        text_y = 2

        # Load the font using PIL's ImageFont
        font = ImageFont.truetype(self.font_file, self.font_size)

        # Ask the loaded font how big our text will be
        text_width, text_height = font.getsize(text)

        # Make sure we accommodate enough width to account for our text_x left offset
        text_width += width + text_x

        # Now let's create a blank canvas wide enough to accomodate our text
        image = Image.new("RGB", (text_width, max(height, text_height)), (0, 0, 0))

        # To draw on our image, we must use PIL's ImageDraw
        draw = ImageDraw.Draw(image)

        # And now we can draw text at our desired (text_x, text_y) offset, using our loaded font
        draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)

        # To give an appearance of scrolling text, we move a 16x16 "window" across the image we generated above
        # The value "scroll" denotes how far this window is from the left of the image.
        # Since the window is "width" pixels wide (16 for UHHD) and we don't want it to run off the end of the,
        # image, we subtract "width".
        for scroll in range(text_width - width):
            for x in range(width):

                # Figure out what hue value we want at this point.
                # "x" is the position of the pixel on Unicorn HAT HD from 0 to 15
                # "scroll" is how far offset from the left of our text image we are
                # We want the text to be a complete cycle around the hue in the HSV colour space
                # so we divide the pixel's position (x + scroll) by the total width of the text
                # If this pixel were half way through the text, it would result in the number 0.5 (180 degrees)
                hue = (x + scroll) / float(text_width)

                # Now we need to convert our "hue" value into r,g,b since that's what colour space our
                # image is in, and also what Unicorn HAT HD understands.
                # This list comprehension is just a tidy way of converting the range 0.0 to 1.0
                # that hsv_to_rgb returns into integers in the range 0-255.
                # hsv_to_rgb returns a tuple of (r, g, b)
                br, bg, bb = [int(n * 255) for n in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]

                # Since our rainbow runs from left to right along the x axis, we can calculate it once
                # for every vertical line on the display, and then re-use that value 16 times below:

                for y in range(height):
                    # Get the r, g, b colour triplet from pixel x,y of our text image
                    # Our text is white on a black background, so these will all be shades of black/grey/white
                    # ie 255,255,255 or 0,0,0 or 128,128,128
                    pixel = image.getpixel((x + scroll, y))

                    # Now we want to turn the colour of our text - shades of grey remember - into a mask for our rainbow.
                    # We do this by dividing it by 255, which converts it to the range 0.0 to 1.0
                    r, g, b = [float(n / 255.0) for n in pixel]

                    # We can now use our 0.0 to 1.0 range to scale our three colour values, controlling the amount
                    # of rainbow that gets blended in.
                    # 0.0 would blend no rainbow
                    # 1.0 would blend 100% rainbow
                    # and anything in between would copy the anti-aliased edges from our text
                    r = int(br * r)
                    g = int(bg * g)
                    b = int(bb * b)

                    # Finally we colour in our finished pixel on Unicorn HAT HD
                    unicornhathd.set_pixel(width - 1 - x, y, r,g,b)

            # Finally, for each step in our scroll, we show the result on Unicorn HAT HD
            unicornhathd.show()

            # And sleep for a little bit, so it doesn't scroll too quickly!
            time.sleep(self.delay)

        # Set rotation back to original.

        unicornhathd.rotation(curr_rotation)

if __name__ == "__main__":
    disp = TextDisplay()
    disp.display_text(" Welcome to Pi-Fighter.....0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789 ")
    disp.display_text("Workout.....")
# unicornhathd.off()
