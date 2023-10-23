#!/home/ruben/piwrite/bin/python3.11

# For _reasons_ I need to use a separate virtual environment for this

import argparse

import inky
from inky import InkyPHAT
from PIL import Image, ImageDraw, ImageFont

from pathlib import Path

static = Path(__file__).parent / "static"

inky_display = InkyPHAT("red")

parser = argparse.ArgumentParser()
parser.add_argument(
    "--font",
    "-f",
    choices=["mono", "latex", "gyre", "serif", "sans"],
    required=True,
    help="Font",
)
parser.add_argument(
    "--state", "-s", choices=["on", "off"], required=True, help="State (on, off)"
)
args, _ = parser.parse_known_args()

padding = 1

inky_display.lut = "red_ht"

img = Image.new("P", inky_display.resolution)
draw = ImageDraw.Draw(img)

# Load the fonts

monoid = ImageFont.truetype(str(static / "monoid-bold.ttf"), 40)
monoid_small = ImageFont.truetype(str(static / "monoid-bold.ttf"), 16)
monoid_med = ImageFont.truetype(str(static / "monoid-bold.ttf"), 24)
piwrite = "PiWrite"

font = monoid
if args.font == "gyre":
    font = ImageFont.truetype(str(static / "texgyreheros-bold.otf"), 50)
if args.font == "latex":
    font = ImageFont.truetype(str(static / "cmunbx.ttf"), 50)
if args.font == "serif":
    font = ImageFont.truetype(str(static / "ImFell.ttf"), 54)

power_color = inky_display.BLACK if args.state == "off" else inky_display.RED

# Draw border
for x in range(0, img.width):
    for y in range(0, img.height):
        if x < 4 or y < 3 or x > img.width - 5 or y > img.height - 5:
            img.putpixel((x, y), power_color)

pw_w, pw_h = font.getsize(piwrite)
pw_x = int((inky_display.width - pw_w) / 2)
pw_y = int((inky_display.height - pw_h) / 2) + padding
draw.text((pw_x, pw_y), piwrite, inky_display.BLACK, font=font)


state = args.state.upper()
s_w, s_h = monoid_small.getsize(state)
s_x = pw_x + 20
s_y = 3
draw.text((s_x, s_y), state, inky_display.BLACK, font=monoid_small)

draw.text((pw_x, 0), "•", power_color, font=monoid_med)

l_height = 4

lower = pw_y + pw_h + 6

for y in range(lower, lower + l_height):
    for x in range(pw_x, inky_display.width - pw_x):
        img.putpixel((x, y), power_color)

upper = pw_y - 1

if args.font == "gyre":
    upper += 13

for y in range(upper - l_height, upper):
    for x in range(pw_x, inky_display.width - pw_x):
        img.putpixel((x, y), power_color)


# I wasn't sure if it was working properly, so did this manually

colors = [inky.WHITE, inky.BLACK, inky.RED]
for x in range(img.width):
    for y in range(img.height):
        inky_display.set_pixel(x, y, colors[img.getpixel((x, y))])

inky_display.show()
