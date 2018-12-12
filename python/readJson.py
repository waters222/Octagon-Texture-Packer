#!/usr/bin/python
# -*- coding: utf-8 -*-
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
