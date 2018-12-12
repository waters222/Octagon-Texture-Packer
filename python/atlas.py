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
from cutImage import cutImage


# debug option
PATH_DELIMETER = '/'
Debug = False;
Output = 'result'+PATH_DELIMETER
Gap = 2
BaseFolder = ''
ROTATE_DEFAULT = 5
ROTATE_MAX_DEFAULT = 90

def hashfile(afile, hasher, blocksize=65536):
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    afile.close()
    return hasher.hexdigest()

def processImage(root, folder, path):
    img = Image.open(root+folder+path)
    if img.mode != 'RGBA':
        print("[WARN] Image "+path+" is not RGBA Image, converting it to RGBA mode")
        img = img.convert("RGBA")
    w = img.size[0]
    h = img.size[1]
    hashKey = hashfile(open(root+folder+path, 'rb'), hashlib.sha256())
    if(os.path.isfile(Output+folder+path+".json")):
        try:
            f = open(Output+folder+path+".json","r")
            oldMeta = json.load(f)
            f.close()
            if(oldMeta["md5"] == hashKey):
                return
        except:
            print("Error: "+Output+folder+path+".json is not valid")
    img.save(Output+folder+path,'PNG')
    print("################################################")
    meta = cutImage(img, Output+folder+path, Gap, Debug)
    meta["md5"] = hashKey
    # print("write json to "+Output+folder+path+".json")
    f = open(Output+folder+path+".json","w")
    f.write(json.dumps(meta))
    f.close()
    img.close()
    # metas.append(cutImage(im, Output+folder+path, Gap, Debug))
# directory walk algorithm
# def getShrink(name, shrink):
#     if(name[-1] == PATH_DELIMETER):
#         name = name[:-1]
#     print('process shrink: '+name)
#     pattern = re.compile('_([1-9][0-9])+$')
#     ret = pattern.search(name)
#     if(ret != None):
#         return int(ret.group(1))
#     else:
#         return shrink


def getSettings(name, rotateSetting):
    temp2 = reDegree.search(name)
    if temp2:
        ss = temp2.group(0)[1:]
        rotateSetting = int(ss)
        if rotateSetting < ROTATE_DEFAULT:
            rotateSetting = ROTATE_DEFAULT
        elif rotateSetting > ROTATE_MAX_DEFAULT:
            rotateSetting = ROTATE_MAX_DEFAULT
    return rotateSetting




def walkDirectory(root, folder):
    #print("root: "+root+" directory: "+folder+" with shrink: "+repr(shrink))
    if not os.path.exists(Output+folder):
        os.makedirs(Output+folder)
    for item in listdir(root + folder):
        # path = join(root, item)
        if(isfile(root + folder+item)):
            if(item.endswith('png')):
                # processImage(root, folder, item, rotateSetting)
                processImage(root, folder, item)
                # threadPool.submit(processImage,root, folder, item)
        else:
            walkDirectory(root, folder+item+PATH_DELIMETER)

def retrieveBaseFolder(root):

    if(root[-1] == PATH_DELIMETER):
        root = root[:-1]
    folders = root.split(PATH_DELIMETER)
    if(len(folders) > 1):
        folder = folders[len(folders) - 1] + PATH_DELIMETER
        del folders[len(folders) - 1]
        base = PATH_DELIMETER.join(folders) +PATH_DELIMETER
    elif(len(folders) == 1):
        folder = folders[0] + PATH_DELIMETER
        base = '.'+PATH_DELIMETER
    else:
        base = '.'+PATH_DELIMETER
        folder = ''
    if not os.path.exists(Output+folder):
        os.makedirs(Output+folder)
    return (base, folder)



# rePoints = re.compile("#([AaFf])")
reDegree = re.compile("#([0-9]+)")


parser = argparse.ArgumentParser("Hexgon Texture Packer Generator\n")
parser.add_argument('-o','--output',help='Output directory',required=False)
parser.add_argument('-d','--directory',help='image folder path',required=True)
parser.add_argument('-gap','--gap',help='cutting gap',required=False)
parser.add_argument('-debug','--debug',help='Debug Option',required=False)



if os.name == 'nt':
    PATH_DELIMETER = "\\"

args = parser.parse_args()

if(args.debug != None):
    Debug = True
    print("Debug mode is on")
if(args.output != None):
    if(args.output[-1] == PATH_DELIMETER):
        Output = args.output
    else:
        Output = args.output+PATH_DELIMETER
if(args.gap):
    Gap = int(args.gap)

start_time = time.time()
# threadPool = concurrent.futures.ThreadPoolExecutor(max_workers=4)
(root, folder) = retrieveBaseFolder(args.directory)
walkDirectory(root, folder)
# threadPool.shutdown(wait=True)

print("Cut Image Done within: " + repr((time.time() - start_time)/60) + " mins")
