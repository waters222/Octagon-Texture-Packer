#!/usr/bin/python
# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw
import concurrent.futures
import sys
import time
import argparse
import math
import json
import re
import os
import hashlib
from os import listdir
from os.path import isfile, join




PATH_DELIMETER = '/'


parser = argparse.ArgumentParser("Trim Trash Pixel\n")
parser.add_argument('-f','--file',help='Input Image File',required=False)


if os.name == 'nt':
    PATH_DELIMETER = "\\"
args = parser.parse_args()



img = Image.open(args.file)

width = img.size[0]
height = img.size[1]
pixel = img.load()
for y in range(height):
	for x in range(width):
		if pixel[x, y][3] <= 5:
			pixel[x, y] = (0, 0, 0, 0)

img.save(args.file, 'PNG')
img.close()
