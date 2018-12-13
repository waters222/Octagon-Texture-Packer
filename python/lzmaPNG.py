#!/usr/bin/python
# -*- coding: utf-8 -*-

# The MIT License (MIT)

# Copyright (c) 2018 Wei Shi

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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

MODE_RGB565 = 0
MODE_RGBA4444 = 1
MODE_RGB888 = 2
MODE_RGBA8888 = 3

def ExtractPixelData(fileName, output):
    img = Image.open(fileName)
    mode = -1
    if img.mode == 'RGBA':
        mode = MODE_RGBA8888
    elif img.mode == 'RGB':
        mode = MODE_RGB888
    else:
        print("[ERROR] not support image format ", img.mode)
        return False

    w = img.size[0]
    h = img.size[1]
    out = open(output, 'wb')
    out.write(struct.pack('>H', w))
    out.write(struct.pack('>H', h))
    out.write(struct.pack('B', mode))
    pixel = img.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixel[x, y]
            out.write(struct.pack('4B',r, g, b, a))
    img.close()
    out.close()
    return True


parser = argparse.ArgumentParser("LZMA PNG Image\n")
parser.add_argument('-f','--file',help='Input Image File',required=False)
parser.add_argument('-o','--output',help='Output Image File',required=True)
parser.add_argument('-debug','--debug',help='Debug Option',required=False)

if os.name == 'nt':
    PATH_DELIMETER = "\\"
args = parser.parse_args()
if ExtractPixelData(args.file, args.output):
    lz=lzma.LZMACompressor(preset= 7 | lzma.PRESET_EXTREME)
    fp = open(args.output, 'rb')
    data = fp.read()
    fp.close()
    fp = open(args.output+".lzma", 'wb')
    fp.write(lz.compress(data))
    fp.write(lz.flush())
    fp.close()
