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
import sys
import math
import json
import sys
import time
import argparse
from os import listdir
from os.path import isfile, join
from cutImage import drawLineColor
import os
import re
metas = []
Debug = False


FORCE_EIGHT_POINT = 0
AUTO_FOUR_POINT = 1
FORCE_FOUR_POINT = 2

FOUR_POINT_MIN_AREA = 2500
FOUR_POINT_DIFF_AREA = 2500

PATH_DELIMETER = "/"
ALPHA_TEST_THREDHOLD = 5

EXTEND_PIXEL = False

def getRect(im, size):
    pix = im.load()
    left = right = lower = upper = -1
    for y in range(size):
        for x in range(size):
            if pix[x, y][3] > ALPHA_TEST_THREDHOLD:
                upper = y
                break
        if upper >= 0:
            break
    for y in range(size - 1, -1, -1):
        for x in range(size):
            if pix[x, y][3] > ALPHA_TEST_THREDHOLD:
                lower = y
                break
        if lower >= 0:
            break
    for x in range(size):
        for y in range(size):
            if pix[x, y][3] > ALPHA_TEST_THREDHOLD:
                left = x
                break
        if left >= 0:
            break
    for x in range(size - 1, -1, -1):
        for y in range(size):
            if pix[x, y][3] > ALPHA_TEST_THREDHOLD:
                right = x
                break
        if right >= 0:
            break
    return (left, right, upper, lower)

def pastImage(src, dest,tx, ty, sx, sy, dx, dy, width, height):
    sp = src.load()
    dp = dest.load()
    try:
        for y in range(sy, dy + 1):
            y1 = y - sy + ty
            for x in range(sx, dx + 1):
                x1 = x - sx + tx
                if sp[x, y][3] > ALPHA_TEST_THREDHOLD:
                    dp[x1, y1] = sp[x, y]
    except IndexError as e:
        print("[ERROR] Past image from top left: {}, {}, bottom right: {}, {} to {}, {}, width: {}, height: {}".format(sx, sy, dx,
                                                                                                             dy, tx, ty,
                                                                                                             width,
                                                                                                             height))
        print("[ERROR] Index error when pasting image, x1:{}, y1:{}, x:{}, y:{} ".format(x1, y1, x, y))
        raise e
    if EXTEND_PIXEL == True:
       ## do edges
        for y in range(sy, dy + 1):
            tempY = y - sy + ty
            diff = dx - sx
            if sp[sx, y][3] > ALPHA_TEST_THREDHOLD:
                if tx - 1 >= 0:
                    dp[tx - 1, tempY] = sp[sx, y]  
            if sp[dx, y][3] > ALPHA_TEST_THREDHOLD:
                if tx + diff + 1 < width:
                    dp[tx + diff + 1, tempY] = sp[dx, y]
        for x in range(sx, dx + 1):
            tempX = x - sx + tx
            diff = dy - sy
            if sp[x, sy][3] > ALPHA_TEST_THREDHOLD:
                if ty - 1 >= 0:
                    dp[tempX, ty - 1] = sp[x, sy]
            if sp[x, dy][3] > ALPHA_TEST_THREDHOLD:
                if ty + diff + 1 < height:
                    dp[tempX, ty + diff + 1] = sp[x, dy]  
def merge(path, data, polyMetaHash, debug):
    
    # width = data['width']
    # height = data['height']
    # print("start merge with width: "+repr(width)+" height: "+repr(height))
    num = 0
    for sheet in data['sheets']:
        doSheet(path, sheet, polyMetaHash,  num, debug)
        num += 1
def shrinkGap(points, gapDifference):
    left = upper = 900000
    lower = right = -1
    for pt in points:
        if left > pt[0]:
            left = pt[0]
        if right < pt[0]:
            right = pt[0]
        if upper > pt[1]:
            upper = pt[1]
        if lower < pt[1]:
            lower = pt[1]
    ret = []
    for pt in points:
        x = pt[0]
        y = pt[1]
        if x == left:
            x = x + gapDifference
        elif x == right:
            x = x - gapDifference

        if y == upper:
            y = y + gapDifference
        elif y == lower:
            y = y - gapDifference
        ret.append( (x, y) )
    return ret
def expandGap(points, gapDifference):
    left = upper = 900000
    lower = right = -1
    for pt in points:
        if left > pt[0]:
            left = pt[0]
        if right < pt[0]:
            right = pt[0]
        if upper > pt[1]:
            upper = pt[1]
        if lower < pt[1]:
            lower = pt[1]
    ret = []
    for pt in points:
        x = pt[0]
        y = pt[1]
        if x == left:
            x = x - gapDifference
        elif x == right:
            x = x + gapDifference

        if y == upper:
            y = y - gapDifference
        elif y == lower:
            y = y + gapDifference
        ret.append( (x, y) )
    return ret

# def normalize(points, size):

#     ## because its even number size image
#     pivot_y = pivot_x = size * 0.5
#     pts  = []
#     for pt in points:
#         if pt[0] >= pivot_x:
#             x = pt[0] + 0.5 - pivot_x
#         else:
#             x = pt[0] - 0.5 - pivot_x
#         if pt[1] >= pivot_y:
#             y = -(pt[1] + 0.5 - pivot_y)    
#         else:
#             y = -(pt[1] - 0.5 - pivot_y)
#         pts.append( (x, y))
#         # print("## "+str(pt[0])+", "+str(pt[1])+", "+str(x)+", "+str(y))

#     left = upper = 900000
#     lower = right = -1
#     for pt in pts:
#         if left > pt[0]:
#             left = pt[0]
#         if right < pt[0]:
#             right = pt[0]
#         if upper > pt[1]:
#             upper = pt[1]
#         if lower < pt[1]:
#             lower = pt[1]
#     width = right - left
#     height = lower - upper
#     return (pts, width, height, left, right, upper, lower)
def normalize(points, size):

    ## because its even number size image
    pivot_y = pivot_x = (size  - 1)* 0.5
    pts  = []
    for pt in points:
        if pt[0] >= pivot_x:
            x = pt[0] + 0.5 - pivot_x
        else:
            x = pt[0] - 0.5 - pivot_x
        if pt[1] >= pivot_y:
            y = -(pt[1] + 0.5 - pivot_y)    
        else:
            y = -(pt[1] - 0.5 - pivot_y)
        pts.append( (x, y))
        # print("## "+str(pt[0])+", "+str(pt[1])+", "+str(x)+", "+str(y))

    left = upper = 900000
    lower = right = -1
    for pt in pts:
        if left > pt[0]:
            left = pt[0]
        if right < pt[0]:
            right = pt[0]
        if upper > pt[1]:
            upper = pt[1]
        if lower < pt[1]:
            lower = pt[1]
    width = right - left
    height = lower - upper
    return (pts, width, height, left, right, upper, lower)
def rotatePoints(points, size, rotation):
    ps = []
    computeSize = size - 1
    # print("size "+str(size)+" computeSize "+str(computeSize))
    if rotation == 90:
        for pt in points:
            x = pt[0]
            y = pt[1]
            ps.append((y , x ))
                
    elif rotation == 180:
        for pt in points:
            x = pt[0]
            y = pt[1]
            # print("== "+str(x)+" "+str(computeSize - x))
            ps.append((computeSize - x , y))
    elif rotation == 270:
        for pt in points:
            x = pt[0]
            y = pt[1]
            ps.append((computeSize - y, x))
    else:
        return points.copy()
    return ps
    
def rotateImage(im, size, rotation):
    pix = im.load()
    ret = Image.new("RGBA", (size, size),(0,0,0,0))
    dst = ret.load()
    computeSize = size - 1
    if rotation == 90:
        for y in range(size):
            for x in range(size):
                dst[y, x] = pix[x, y]
    elif rotation == 180:
        for y in range(size):
            for x in range(size):
                dst[computeSize - x, y] = pix[x, y]
    elif rotation == 270:
        for y in range(size):
            for x in range(size):
                dst[-y + computeSize, x] = pix[x, y]
    else:
        return im
    return ret

def point_inside_polygon(x, y,poly):
    n = len(poly)
    inside =False
    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y

    return inside

def extendFarSide(points, gap = 1):
    ## first we extend Y direction
    ret = []
    innerPoints = shrinkGap(points, 1)
    for i in range(len(innerPoints)):
        u = points[i][0]
        v = points[i][1]
        count = 0
        if not point_inside_polygon(innerPoints[i][0] + 3, innerPoints[i][1], points):
            count = count +1
            u = u + gap
        if not point_inside_polygon(innerPoints[i][0] - 3, innerPoints[i][1], points):
            count = count + 1

        if not point_inside_polygon(innerPoints[i][0], innerPoints[i][1] + 3, points):
            count = count +1
            v = v + gap
        if not point_inside_polygon(innerPoints[i][0], innerPoints[i][1] - 3, points):
            count = count + 1

        if count >= 3:
            ## its an single point, 
            # print("its an single point "+str(pt[0])+" "+str(pt[1]))
            ret.append((points[i][0] + 0.5, points[i][1] + 0.5))
        else:
            ret.append((u, v)) 
        
    return ret

def printPoints(points):
    print("Start Print Points =====")
    for pt in points:
        print(str(pt[0]) +" "+str(pt[1]))
def fixPlatformPath(path):
    if os.name == "nt":
        return path.replace("/", PATH_DELIMETER)
    else:
        return path.replace("\\", PATH_DELIMETER)

def shiftPoints(points, x, y):
    ret = []
    for pt in points:
        ret.append((pt[0] + x, pt[1] + y))
    return ret
def doSheet(path, data, polyMetaHashm, num, debug):
    print('do sheet #'+repr(num))
    width = data['width']
    height = data['height']
    metas = []
    fileName = path + PATH_DELIMETER +'atlas-'+repr(num)+'.png'
    img = Image.new("RGBA", (width, height),(0,0,0,0))
    count = 0
    for item in data['sprites']:
        # if count > 3:
        #     break;
        # count += 1
        filePath = fixPlatformPath(item['file'])
        nameSplit = filePath.split(PATH_DELIMETER)
        # if nameSplit[len(nameSplit)-1] != "titan_range_aoe_01.png":
        #     continue
        # if nameSplit[len(nameSplit)-1] != "Buildings_Base1.png" and nameSplit[len(nameSplit)-1] != "Enemy_Buildings_Base1.png":
        #     continue    
        # if nameSplit[len(nameSplit)-1] == "Buildings_Base1.png" or nameSplit[len(nameSplit)-1] == "Enemy_Buildings_Base1.png":
        print("process file #"+str(count)+" : "+item['file'])   
        count = count + 1
        oldData = polyMetaHashm[item['file']]
        gapDifference = oldData["gap"]
        rotation = int(item['rotation'])
        # if nameSplit[len(nameSplit)-1] == "Buildings_Base1.png" :
        #     rotation = 0
        #     item['x'] = 0
        #     item['y'] = 0
        # if nameSplit[len(nameSplit)-1] == "Enemy_Buildings_Base1.png" :
        #     rotation = 0
        #     item['x'] = 0
        #     item['y'] = 3000
        size = oldData["newSize"]
        temp = Image.open(filePath)
        if temp.mode != "RGBA":
            temp = temp.convert('RGBA')
        if size != temp.size[0] or size != temp.size[1]:
            print("[INFO] Resize from "+str(temp.size[0])+" to "+str(size))
            temp = temp.resize((size, size), Image.ANTIALIAS) 

        # if nameSplit[len(nameSplit)-1] == "Buildings_Base1.png" or nameSplit[len(nameSplit)-1] == "Enemy_Buildings_Base1.png":
        temp = rotateImage(temp, size, rotation)
        points = []
        for pt in oldData['points']:
            points.append((pt[0], pt[1]))
        if len(points) < 3:
            print("[ERROR] Image point is less then 3: "+item['file'])
            continue

        # a = width - 1
        # b = height - 1
        # print("left "+str(left )+" right "+str(right)+" upper "+str(upper )+ " lower "+str(lower))
        # print("left "+str(left * 65535  / a)+" right "+str(right * 65535 / a)+" upper "+str(upper * 65535  / b)+ " lower "+str(lower * 65535 / b))
        uvPoints = rotatePoints(points, size, rotation)
        uvPoints = shrinkGap(uvPoints, gapDifference)

        left = upper = 900000
        lower = right =-1
        for i in range(len(uvPoints)):
            if left > uvPoints[i][0]:
                left = uvPoints[i][0]
            if right < uvPoints[i][0]:
                right = uvPoints[i][0]
            if upper > uvPoints[i][1]:
                upper = uvPoints[i][1]
            if lower < uvPoints[i][1]:
                lower = uvPoints[i][1]

        # if nameSplit[len(nameSplit)-1] == "Buildings_Base1.png" or nameSplit[len(nameSplit)-1] == "Enemy_Buildings_Base1.png":
        pastImage(temp, img, item['x'], item['y'], left, upper, right, lower, width, height)


        # uvs = []
        # for pt in uvPoints:
        #     uvs.append( ( (float(pt[0] + item['x'] - left)/texWidth), (float(pt[1] + item['y'] - upper )/texHeight) ) )
        # if nameSplit[len(nameSplit)-1] == "Buildings_Base1.png" or nameSplit[len(nameSplit)-1] == "Enemy_Buildings_Base1.png":
        #     drawRoundingBox(img, uvs, width, height)

        uvs = []
        # uvPoints = extendFarSide(uvPoints, 0.5)
        for pt in uvPoints:
            tempX = float(pt[0] - left + item['x']) + 0.5
            tempY = float(pt[1] - upper + item['y']) + 0.5
            uv_x = tempX / width
            uv_y = tempY / height
            uvs.append( (uv_x, uv_y ))

        # points = extendFarSide(points)
        points = shrinkGap(points, gapDifference)

        (points, newW, newH,boxMinX, boxMaxX, boxMinY, boxMaxY) = normalize(points, size)
        uvMinX = 0
        uvMinY = 0
        uvMaxX = 0
        uvMaxY = 0
        for i in range(len(points)):
            if points[i][0] == boxMinX and points[i][1] == boxMinY:
                uvMinX = uvs[i][0]
                uvMaxY = uvs[i][1]
            elif points[i][0] == boxMaxX and points[i][1] == boxMaxY:
                uvMaxX = uvs[i][0]
                uvMinY = uvs[i][1]

        if(Debug):
            tempPoints = []
            for pt in uvs:
                tempPoints.append((pt[0] * width , pt[1] * height))
            drawLineColor(img, tempPoints, 'red')

        metas.append({'file':nameSplit[len(nameSplit)-1], "reverse":(rotation == 90 or rotation == 270) ,'points': points, 'uv':uvs, 
         "boxMinX": boxMinX, "boxMaxX": boxMaxX, "boxMinY": boxMinY, "boxMaxY": boxMaxY, "uvMinX":uvMinX,"uvMinY":uvMinY,"uvMaxX":uvMaxX,"uvMaxY":uvMaxY, "pixelToWorld": oldData['pixelToWorld']})
        

    img.save(fileName, 'PNG')

    f = open(path + PATH_DELIMETER +'atlas-'+repr(num)+'.json',"w")
    f.write(json.dumps(metas, sort_keys = True))
    f.close()
    # if(Debug):
    #     print("save atlas png to: "+fileName)
    #     print("save atlas json to: "+path + PATH_DELIMETER +'atlas-'+repr(num)+'.json')
    # # os.system('pngquant --force ' + fileName)
    # if os.name == "nt":
    #     os.system('PVRTexToolCLI.exe -f PVRTC1_4,UBN,lRGB -q pvrtcbest -i '+fileName)
    # else:
    #     os.system('./PVRTexToolCLI -f PVRTC1_4,UBN,lRGB -q pvrtcbest -i '+fileName)

def drawRoundingBox(im, uvs, width, height):
    ret = []
    for pt in uvs:
        # print("draw: "+str(pt[0] * width)+" "+str(pt[1] * height))
        ret.append( (pt[0] * width, pt[1] * height) )
    drawLineColor(im, ret, "black")
    ret = expandGap(ret, 1)
    drawLineColor(im, ret, "orange")


def walkDirectory(root, folder, pointSetting, scaleSetting,pixelRatio):
    #print("root: "+root+" directory: "+folder+" with shrink: "+repr(shrink))
    for item in listdir(root + folder):
        # path = join(root, item)
        if(isfile(root + folder+item)):
            if(item.endswith('json')):
                try:
                    f = open(root + folder+item,"r")
                    meta = json.load(f)
                    f.close()
                    appendMeta(meta, pointSetting, scaleSetting, pixelRatio, root + folder+item)
                except Exception as exp:
                    print("Error: "+root+folder+item+" is not valid meta file!!! skip > "+str(exp))
        else:
            (newPointSetting, newScaleSetting, newPixelRatio) = getSettings(item, pointSetting, scaleSetting, pixelRatio)
            walkDirectory(root, folder+item+PATH_DELIMETER, newPointSetting, newScaleSetting, newPixelRatio)

def appendMeta(meta, pointSetting, scaleSetting, pixelRatio, fileName):
    
    ratio = 1.0

    if (scaleSetting < 100):
        ratio = scaleSetting / 100

    meta["ratio"] = ratio
    meta["newSize"] = int(meta["size"] * ratio + 0.5)
    meta["pixelToWorld"] = pixelRatio
    rectPoints = []
    for i in range(len(meta["rectPoints"])):
        rectPoints.append((int(meta["rectPoints"][i][0]* ratio + 0.5), int(meta["rectPoints"][i][1]* ratio + 0.5)))
    rectArea = int(meta["rectArea"] * ratio + 0.5)
    

    polyPoints = []
    for i in range(len(meta["polyPoints"])):
        polyPoints.append((int(meta["polyPoints"][i][0]* ratio + 0.5), int(meta["polyPoints"][i][1]* ratio + 0.5)))
    polyArea = int(meta["polyArea"] * ratio + 0.5)
    

    if pointSetting == FORCE_FOUR_POINT:
        # print("Point setting FORCE four point")
        meta["area"] = rectArea
        meta["points"] = rectPoints
    elif pointSetting == AUTO_FOUR_POINT:
        # print("Point setting AUTO four point")
        diff = polyArea - rectArea
        if rectArea > polyArea:
            diff = rectArea - polyArea
        if rectArea < FOUR_POINT_MIN_AREA or diff < FOUR_POINT_DIFF_AREA:
            meta["area"] = rectArea
            meta["points"] = rectPoints
        else:
            meta["area"] = polyArea
            meta["points"] = polyPoints
    else:
        # print("Point setting FORCE eight point")
        meta["area"] = polyArea
        meta["points"] = polyPoints
    meta["file"] = fileName[:-5]
    metas.append(meta)



def getSettings(name, pointSetting, scaleSetting, pixelRatio):
    temp1 = reScale.search(name)
    temp2 = rePoints.search(name)
    temp3 = rePixelToWorld.search(name)
    if temp1:
        ss = temp1.group(0)[1:]
        scaleSetting = int(ss)
        if( scaleSetting > 100):
            scaleSetting = 100
        elif(scaleSetting < 10):
            scaleSetting = 10

    if temp2:
        ss = temp2.group(0)[1:]
        if ss == "A" or ss == "a":
            pointSetting = AUTO_FOUR_POINT
        elif ss == "F" or ss == "f":
            pointSetting = FORCE_FOUR_POINT

    if temp3:
        ss = temp3.group(0)[1:]
        pixelRatio = float(ss)

    return (pointSetting, scaleSetting, pixelRatio)

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
    # if not os.path.exists(Output+folder):
    #     os.makedirs(Output+folder)
    return (base, folder)

def buildMetaHash(meta):
    metaHash = {}
    for m in meta:
        metaHash[m["file"]] = m
    return metaHash

def drawCanvas(path, info):
    width = info['width']
    height = info['height']
    print("start merge with width: "+repr(width)+" height: "+repr(height))
    num = 0
    for sheet in info['sheets']:
        fileName = path + PATH_DELIMETER +'atlas-debug-'+repr(num)+'.png'
        img = Image.new("RGBA", (width, height))
        for info in sheet:
            points = []
            for pt in info["points"]:
                points.append((pt[0] + info["x"], pt[1] + info["y"]))
            drawLine(img, points)    
        num += 1
        img.save(fileName, 'PNG')

def drawLine(im, points):
    drawLineColor(im, points, (255, 0, 0))

def drawLineColor(im, points, color):
    draw = ImageDraw.Draw(im)
    length = len(points) - 1
    for i in range(length):
        draw.line( (points[i][0], points[i][1],points[i + 1][0], points[i + 1][1],), fill = color)
    draw.line( (points[length][0], points[length][1],points[0][0], points[0][1],), fill = color)


parser = argparse.ArgumentParser("Octagon Texture Packer Merger\n")
parser.add_argument('-d','--directory',help='image folder path',required=True)
parser.add_argument('-size','--size',help='atlas max size',required=True)
parser.add_argument('-m', '--merge', help='merge only', required=False)
parser.add_argument('-ep', '--extendPixel', help='extend pixel', required=False)
parser.add_argument('-debug','--debug',help='Debug Option',required=False)


rePoints = re.compile("\\$([AaFf])")
reScale = re.compile("-[0-9]+$")
rePixelToWorld = re.compile("\\%[0-9]+")


if os.name == 'nt':
    PATH_DELIMETER = "\\"

args = parser.parse_args()

if(args.debug != None):
    Debug = True
    print("Debug mode is on")

MaxSize = int(args.size)
if args.extendPixel != None:
    EXTEND_PIXEL = True
print("Start generate atlas with max size: "+repr(MaxSize))
(root, folder) = retrieveBaseFolder(args.directory)
if(args.merge == None):
    if os.path.exists(root+folder+"polygon.json"):
        os.remove(root+folder+"polygon.json")
    if os.path.exists(root+folder+'packing.json'):
        os.remove(root+folder+'packing.json')

    (newPointSetting, newScaleSetting, pixelRatio) = getSettings(folder, FORCE_EIGHT_POINT, 100, 1)
    walkDirectory(root, folder, newPointSetting, newScaleSetting, pixelRatio)
    f = open(root+folder+"polygon.json", 'w')
    f.write(json.dumps(metas,sort_keys = True))
    f.close()
    if os.name == "nt":
        os.system('Packing.exe -f '+root+folder+' --size '+repr(MaxSize))
    else:
        os.system('./Packing -f '+root+folder+' --size '+repr(MaxSize))
polyMetaFile = open(root+folder+"polygon.json", 'r')
polyMetaJson = json.load(polyMetaFile)
polyMetaFile.close()
polyMetaHash = buildMetaHash(polyMetaJson)

f = open(root+folder+'packing.json')
data = json.load(f)
f.close()
# if(Debug):
#     drawCanvas(root+folder, data)
merge(root+folder,data, polyMetaHash, Debug)