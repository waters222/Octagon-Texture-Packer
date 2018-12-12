#!/usr/bin/python
# -*- coding: utf-8 -*-
from PIL import Image
import sys
import time
import argparse
import os

def computeStats( imgPath, cutoff):
    im = Image.open(imgPath)
    w = im.size[0]
    h = im.size[1]
    pix = im.load()
    count = 0;
    print("Image width: "+repr(w)+" height: "+repr(h)+" cutoff value: "+repr(cutoff))
    for y in range( h ):
        for x in range( w):
            if(pix[x, y][3] > cutoff ):
                count+=1

    percentage = float(count)/float(w * h) * 100;
    print("alpha pixel count "+repr(count)+ " percentage: "+repr(percentage) +'%')

parser = argparse.ArgumentParser()
parser.add_argument('-f','--file',help='image file name',required=True)
parser.add_argument('-a','--alpha',help='alpha cutoff percentage value, default: 10%')
args = parser.parse_args()
cutoff = 0
if( args.alpha == None ):
    cutoff = 25
else:
    cutoff = int(255 * float(args.alpha) * 0.01)
computeStats(args.file, cutoff)



