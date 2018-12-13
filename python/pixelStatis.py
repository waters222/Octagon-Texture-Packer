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



