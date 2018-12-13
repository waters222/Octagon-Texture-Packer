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
import json
import argparse
import os
metas = []
Debug = False


parser = argparse.ArgumentParser("Atalas Reader\n")
parser.add_argument('-f','--file',help='meta file',required=True)
parser.add_argument('-n','--name',help='atlas element name',required=True)

args = parser.parse_args()
if os.name == 'nt':
    PATH_DELIMETER = "\\"

f = open(args.file+".json","r")
metas = json.load(f)
f.close()

found = False
item = {}
for elem in metas:
    if elem["file"] == args.name :
        found = True
        item = elem
if not found :
    print("Can not find atlas: "+args.name+" in meta file: ", args.file)
else:
    img = Image.open(args.file+".png")
    w = img.size[0]
    h = img.size[1]
    minX = w
    minY = h
    maxX = 0
    maxY = 0
    for pt in item["uv"]:
        x = pt[0] * w
        y = pt[1] * h
        if minX > x:
            minX = x
        if maxX < x:
            maxX = x
        if minY > y:
            minY = y
        if maxY < y:
            maxY = y
    minX = minX + 0.5
    minY = minY + 0.5
    maxX = maxX + 0.5
    maxY = maxY + 0.5
    im = img.crop((int(minX), int(minY), int(maxX), int(maxY)))
    im.show()
