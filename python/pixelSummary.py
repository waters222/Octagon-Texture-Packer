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
import struct
import lzmaffi as lzma

PATH_DELIMETER = '/'
def summary(pixel, width, height):
    transCount0 = 0
    transCount1 = 0
    transCount2 = 0
    trash0 = 0
    trash1 = 0
    for y in range(height):
        for x in range(width):
            if pixel[x, y][3]  == 0:
                if pixel[x, y][0] != 0 or pixel[x, y][1] != 0 or pixel[x, y][2] != 0:
                    trash0 = trash0 + 1
                transCount0 = transCount0 + 1
            elif pixel[x, y][3]  < 10:
                if pixel[x, y][0] != 0 or pixel[x, y][1] != 0 or pixel[x, y][2] != 0:
                    trash1 = trash1 + 1
                transCount1 = transCount1 + 1
            elif pixel[x, y][3]  < 20:
                transCount2 = transCount2 + 1
    total = width * height
    print("[INFO] Total "+ str(total)+ ", total transparent: "+str(transCount0/total)+", less 10: "+str(transCount1/total)+", less 20: "+str(transCount2/total), " trash0: "+str(trash0/total), " trash1: "+str(trash1/total))

parser = argparse.ArgumentParser("Pixel Summary\n")
parser.add_argument('-f','--file',help='Input Image File',required=False)

if os.name == 'nt':
    PATH_DELIMETER = "\\"
args = parser.parse_args()


img = Image.open(args.file)
summary(img.load(), img.size[0], img.size[1])
img.close()
