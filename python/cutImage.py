#!/usr/bin/python
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
# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw
import sys
import math
import json
import shutil
import decimal
# FORCE_EIGHT_POINT = 0
# AUTO_FOUR_POINT = 1
# FORCE_FOUR_POINT = 2

# ROTATE_DEFAULT = 5
# ROTATE_MAX_DEFAULT = 90


# ROTATION_MIN_AREA = 4096
# FOUR_POINT_MIN_AREA = 2000
# FOUR_POINT_DIFF_AREA = 1000

ALPHA_TEST_THREDHOLD = 5

def pastImage(src, dp,tx, ty, sx, sy, dx, dy):
    # print("[DEBUG] Past image from "+str(tx)+" "+str(ty) +" "+str(sx)+" "+str(sy)+" -> "+str(dx)+" "+str(dy))
    sp = src.load()
    for y in range(sy, dy + 1):
        y1 = y - sy + ty
        for x in range(sx, dx + 1):
            x1 = x - sx + tx
            if sp[x, y][3] > 0:
                dp[x1, y1] = sp[x, y]   

def cutImage(img, path, gap, debug):
    print("################################################")
    print("Cutting image: "+path)
    fileNameAltDebug = path[:-4]+"-debug.png"

    w = img.size[0]
    h = img.size[1]

    if w != h:
        if w > h:
            size = w + 128
            offsetX = 64
            offsetY = 64 + int((w - h) * 0.5)
        else:
            size = h + 128
            offsetY = 64
            offsetX = 64 + int((h - w) * 0.5)
            
    else:
        size = w + 128
        offsetX = 64
        offsetY = 64
    width = size
    height = size
    ## we extend the original image a little bit for cutting beyond border problem
    im = Image.new("RGBA", (size, size),(0,0,0,0))
    pix = im.load()
    pastImage(img, pix, offsetX, offsetY, 0, 0, w-1, h-1)
    im.save(path)
    # first we need to get the are of image
    
    (left, right, upper, lower) = getRect(pix, width, height)
    # if debug:
    #     print("left is " + str(left[0]) +", "+str(left[1])+ ", "+str(left[2]))
    #     print("right is " + str(right[0]) +", "+str(right[1])+ ", "+str(right[2]))
    #     print("upper is " + str(upper[0]) +", "+str(upper[1])+ ", "+str(upper[2]))
    #     print("lower is " + str(lower[0]) +", "+str(lower[1])+ ", "+str(lower[2]))
    # generate rectPoints
    rectPoints = []
    rectPoints.append( (left[0] - gap, upper[0] - gap) )
    rectPoints.append( (left[0] - gap, lower[0] + gap) )
    rectPoints.append( (right[0] + gap, lower[0] + gap) )
    rectPoints.append( (right[0] + gap, upper[0] - gap) )
    rectArea = (right[0] - left[0] + 2 *gap) * (lower[0] - upper[0] + 2 * gap)

    polyPoints = getOctagon(pix, left, right, upper, lower, gap)
    polyPoints = degeneratePolygon(polyPoints, debug)
    polyArea = polygonArea(polyPoints)
    ## now we get the octagon here
    if debug: 
        draw = ImageDraw.Draw(im)
        drawLineColor(draw, polyPoints, "red")
        drawPoints(draw, polyPoints, "red")
        # drawLineColor(draw, rectPoints, "blue")
        # fillPolygon(draw, polyPoints, "black")
        # fillPolygon(draw, rotatePolygon(polyPoints, 2), "blue")
        # fillPolygon(draw, rotatePolygon(polyPoints, 3), "red")
        im.save(fileNameAltDebug)
        del draw

    
    print("Processing Image Finished: "+path)
    print("================================================")
    im.close()
    return {"file": path,"file-debug":fileNameAltDebug, "polyPoints":polyPoints, "polyArea":int(polyArea), "rectPoints":rectPoints, "rectArea":rectArea, "gap":gap, "size": size}



def rotatePolygon(points, n):
    ret = []
    if n == 1:
        for pt in points:
            ret.append((-pt[1],pt[0]))
    elif n == 2:
        for pt in points:
            ret.append((-pt[0],pt[1]))
    elif n == 3:
        for pt in points:
            ret.append((pt[1],-pt[0]))
    minx = 999999
    miny = 999999
    for pt in ret:
        if minx > pt[0]:
            minx = pt[0]
        if miny > pt[1]:
            miny = pt[1]
    end = []
    for pt in ret:
        end.append((pt[0] - minx, pt[1] - miny) )
    return end

def fillPolygon(draw, points, color):
    ## we first construct an empty array
    left = 99999999
    upper = 99999999
    right = 0
    lower = 0
    drawPoints = []
    for pt in points:
        if left > pt[0]:
            left = pt[0]
        if right < pt[0]:
            right = pt[0]
        if upper > pt[1]:
            upper = pt[1]
        if lower < pt[1]:
            lower = pt[1]
        drawPoints.append((pt[0], pt[1]))
    drawPoints.append((points[0][0], points[0][1]))
    # print("[INFO] left is "+str(left)+" right is "+str(right)+" lower is "+str(lower)+" upper is "+str(upper))
    ## now lets draw it new canvas using bit
    width = right - left + 1
    height = lower - upper + 1
    canvas = [0] *(width * height)

    # print("canvas length is "+str(len(canvas)))
    ## now lets draw line
    last_pt = None
    for pt in drawPoints:
        x = pt[0] - left
        y = pt[1] - upper
        if last_pt != None:
            if last_pt[0] == x:
                if last_pt[1] <= y:
                    for i in range(last_pt[1], y + 1):
                        canvas[ i * width + x] = 1
                else:
                    for i in range(y, last_pt[1] + 1):
                        canvas[ i * width + x] = 1
            elif last_pt[1] == y:
                if last_pt[0] <= x:
                    for i in range(last_pt[0], x + 1):
                        canvas[y * width + i] = 1
                else:
                    for i in range(x, last_pt[0] + 1):
                        canvas[y * width + i] = 1
            else:
                # start from last point to new points
                ## we test which direction difference is bigger
                if abs(last_pt[0] - x) <= abs(last_pt[1] - y):
                    if last_pt[1] <= y:
                        ratio = (x - last_pt[0]) / (y - last_pt[1])
                        for i in range(last_pt[1], y + 1):
                            temp = ratio * (i - last_pt[1]) +last_pt[0]
                            canvas[int(temp) + i * width] = 1
                            canvas[int(temp + 0.5) + i * width] = 1
                    else:
                        ratio = (x - last_pt[0]) / (y - last_pt[1])
                        for i in range(last_pt[1], y - 1, - 1):
                            temp = ratio * (i - last_pt[1]) +last_pt[0]
                            canvas[int(temp) + i * width] = 1
                            canvas[int(temp + 0.5) + i * width] = 1

                else:
                    if last_pt[0] <= x:
                        ratio = (y - last_pt[1]) / (x - last_pt[0])
                        for i in range(last_pt[0], x + 1):
                            temp = ratio * (i - last_pt[0]) +last_pt[1]
                            canvas[int(temp) * width + i] = 1
                            canvas[int(temp + 0.5) * width + i] = 1
                    else:
                        ratio = (y - last_pt[1]) / (x - last_pt[0])
                        for i in range(last_pt[0], x - 1, -1):
                            temp = ratio * (i - last_pt[0]) +last_pt[1]
                            canvas[int(temp) * width + i] = 1
                            canvas[int(temp + 0.5) * width + i] = 1
        last_pt = (x, y)
    ## now we scan from left to right to fill canvas
    # print("now scan backward")
    for y in range(height):
        start = None
        drawed = False
        for x in range(width):
            if canvas[y * width + x] == 1:
                if start != None:
                    drawed = True
                    # scan backward
                    for i in range(x, start, -1):
                        canvas[y * width + i] = 1
                start = x
        if not drawed:
            print("[ERROR] one line has faled")
        # if start != None and drawed == False:
        #     if start > 0:
        #         for i in range(start, width, 1):
        #             canvas[y * width + i] = 1
        #     else:
        #         for i in range(width - 1, start - 1, -1):
        #             canvas[y * width + i] = 1

    for i in range(width * height):
        if canvas[i] == 1:
            y =  int(i / width)
            x =  i - y * width
            draw.point((x + left, y + upper), fill = color)
    return             
    

def degeneratePolygon(points, debug):
    ret = []
    size = len(points)
    ## lets find middle point
    x = points[0][0]
    y = points[0][1]
    for i in range(1, size):
        x = x + points[i][0]
        y = y + points[i][1]
    x = x / size
    y = y / size

    for i in range(size):
        toBeAdded = True
        for p in range(i + 1, size):
            
            if points[i][0] == points[p][0] and points[i][1] == points[p][1]:
                toBeAdded = False
        if toBeAdded == True:
            ret.append(points[i])
    size = len(ret)
    newRet = []
    
    lastX = ret[0][0]
    lastY = ret[0][1]
    i = 1
    while i < size:
        distance = math.sqrt(math.pow(ret[i][0] - lastX, 2) + math.pow(ret[i][1] - lastY, 2))
        if distance > 5:
            newRet.append((lastX, lastY))
            lastX = ret[i][0]
            lastY = ret[i][1]
            
            i = i + 1
            if i == size:
                newRet.append(( lastX, lastY ))
                break
        else:
            newX = 0
            newY = 0
            if lastX < x:
                if lastX < ret[i][0]:
                    newX = lastX
                else:
                    newX = ret[i][0]
            else:
                if lastX > ret[i][0]:
                    newX = lastX
                else:
                    newX = ret[i][0]

            if lastY < y:
                if lastY < ret[i][1]:
                    newY = lastY
                else:
                    newY = ret[i][1]
            else:
                if lastY > ret[i][1]:
                    newY = lastY
                else:
                    newY = ret[i][1]
            lastX = newX
            lastY = newY
            i = i + 1
            if i == size:
                newRet.append(( lastX, lastY ))
                break
    if debug:
        if len(newRet) != len(points):
            print("[INFO] polygon has been degenerated into "+str(len(newRet))+" points")
    return newRet

def getOctagon(pix, left, right, upper, lower, gap):
    ## firs do left -> top slash
    left_top = None
    for y in range(left[1], upper[0], -1):
        diff = y - upper[0]
        found = False
        if diff != 0:
            for x in range(left[0] + 1, upper[1] + 1, 1):
                diffX = x - left[0]
                ratio = diffX / diff
                area = diffX * diff * 0.5
                if left_top == None or area > left_top[2]:
                    for pos_y in range( 1, diff + 1, 1):
                        pos_x = left[0] + pos_y * ratio
                        pos_y = y - pos_y
                        # we should check two pixel if nessccery
                        if pix[int(pos_x), int(pos_y)][3] > ALPHA_TEST_THREDHOLD:
                            # we stop here
                            # print("failed for "+str(x)+" "+str(y)+" area "+str(area))
                            found = True
                            break
                        elif pix[int(pos_x + 0.5), int(pos_y + 0.5)][3] > ALPHA_TEST_THREDHOLD:
                            # we stop here
                            # print("failed for "+str(x)+" "+str(y)+" area "+str(area))
                            found = True
                            break
                    if not found:
                        # print("found for "+str(x)+" "+str(y)+" area "+str(area))
                        left_top = (x, y, area)
                    else:
                        break

    if left_top == None:
        left_top = (left[0], upper[0], 0)
    ## second do right -> top slash
    # print("======= do left_top "+str(left_top[0]) +" "+str(left_top[1])+" "+str(left_top[2]))
    right_top = None
    for y in range( right[1], upper[0], -1):
        diff = y - upper[0]
        found = False
        if diff == 0:
            continue
        # print("#### "+str(diff) +" -> "+str(right[0])+" "+str(upper[2]))
        for x in range(right[0] - 1, upper[2] - 1, -1):
            diffX = right[0] - x
            ratio = diffX / diff
            area = (diffX) * (diff) * 0.5
            if right_top == None or area > right_top[2]:
                for pos_y in range( 1, diff + 1, 1):
                    pos_x = right[0] - pos_y * ratio
                    pos_y = y - pos_y
                    # we should check two pixel if nessccery
                    if pix[int(pos_x), int(pos_y)][3] > ALPHA_TEST_THREDHOLD:
                        # we stop here
                        found = True
                        break
                    elif pix[int(pos_x + 0.5), int(pos_y + 0.5)][3] > ALPHA_TEST_THREDHOLD:
                        # we stop here
                        found = True
                        break
            else:
                continue
            if not found:
                if right_top == None or area > right_top[2]:
                    right_top = (x, y, area)
            else:
                break
    if right_top == None:
        right_top = (right[0], upper[0], 0)
    # print("======= do right_top "+str(right_top[0]) +" "+str(right_top[1])+" "+str(right_top[2]))
    
    ## third we do left -> bottom slash
    left_bottom = None
    for y in range( left[2], lower[0], 1):
        diff = lower[0] - y
        found = False
        if diff == 0:
            continue
        for x in range(left[0] + 1, lower[1] + 1, 1):
            diffX = x - left[0]
            ratio = diffX / diff
            area = diffX * diff * 0.5
            if left_bottom == None or area > left_bottom[2]:
                for pos_y in range( 1, diff + 1, 1):
                    pos_x = left[0] + pos_y * ratio
                    pos_y = y + pos_y
                    # we should check two pixel if nessccery
                    if pix[int(pos_x), int(pos_y)][3] > ALPHA_TEST_THREDHOLD:
                        # we stop here
                        found = True
                        break
                    elif pix[int(pos_x + 0.5), int(pos_y + 0.5)][3] > ALPHA_TEST_THREDHOLD:
                        # we stop here
                        found = True
                        break
            else:
                continue
            if not found:
                if left_bottom == None or area > left_bottom[2]:
                    left_bottom = (x, y, area)
            else:
                break

    if left_bottom == None:
        left_bottom = (left[0], lower[0], 0)

    ## forth we do right -> bottom slash
    # print("======= do left_bottom "+str(left_bottom[0]) +" "+str(left_bottom[1])+" "+str(left_bottom[2]))
    right_bottom = None
    for y in range( right[2], lower[0], 1):
        diff = lower[0] - y
        found = False
        if diff == 0:
            continue
        for x in range(right[0] - 1, lower[2] - 1, -1):
            diffX = right[0] - x
            ratio =diffX / diff
            area = diffX * diff * 0.5
            if right_bottom == None or area > right_bottom[2]:
                for pos_y in range( 1, diff + 1, 1):
                    pos_x = right[0] - pos_y * ratio
                    pos_y = y + pos_y
                    # we should check two pixel if nessccery
                    if pix[int(pos_x), int(pos_y)][3] > ALPHA_TEST_THREDHOLD:
                        # we stop here
                        found = True
                        break
                    elif pix[int(pos_x + 0.5), int(pos_y + 0.5)][3] > ALPHA_TEST_THREDHOLD:
                        # we stop here
                        found = True
                        break
            else:
                continue
            if not found:
                if right_bottom == None or area > right_bottom[2]:
                    right_bottom = (x, y, area)
            else:
                break
    if right_bottom == None:
        right_bottom = (right[0], lower[0], 0)
    # print("======= do right_bottom "+str(right_bottom[0]) +" "+str(right_bottom[1])+" "+str(right_bottom[2]))
    ## lets compose the polygon now
    ## start from top left corner and do as counter-clock wise direction 
    points = []
    points.append((left_top[0], upper[0] - gap))
    points.append((left[0] - gap, left_top[1]))

    points.append((left[0] - gap, left_bottom[1]))
    points.append((left_bottom[0], lower[0] + gap))

    points.append((right_bottom[0], lower[0] + gap))
    points.append((right[0] + gap, right_bottom[1]))

    points.append((right[0] + gap, right_top[1]))
    points.append((right_top[0], upper[0] - gap))
    return points

def getPointsFromRect(left, right, upper, lower, gap):
    points = []
    points.append((left - gap, upper - gap))
    points.append((left - gap, lower + gap))
    points.append((right + gap, lower + gap))
    points.append((right + gap, upper - gap))
    return points
def getRect(pix, w, h):
    #upper
    found = False
    upper = 0
    upper_left = 0
    upper_right = 0
    
    for y in range( h ):
        for x in range(w):
            if pix[x, y][3] > ALPHA_TEST_THREDHOLD:
                if not found:
                    upper = y
                    upper_left = x
                    upper_right = x
                    found = True
                else:
                    upper_right = x
        if found:
            break

    #lower
    found = False
    lower = 0
    lower_left = 0
    lower_right = 0
    
    for y in range( (h - 1), -1, -1):
        for x in range(w):
            if pix[x, y][3] > ALPHA_TEST_THREDHOLD:
                if not found:
                    lower = y
                    lower_left = x
                    lower_right = x
                    found = True
                else:
                    lower_right = x
        if found:
            break

    #left
    found = False
    left = 0
    left_top = 0
    left_bottom = 0
    for x in range(w):
        for y in range(h):
            if pix[x, y][3] > ALPHA_TEST_THREDHOLD:
                if not found:
                    left = x
                    left_top = y
                    left_bottom = y
                    found = True
                else:
                    left_bottom = y
        if found:
            break

    #right 
    found = False
    right = 0
    right_top = 0
    right_bottom = 0
    for x in range( (w - 1), -1, -1):
        for y in range(h):
            if pix[x, y][3] > ALPHA_TEST_THREDHOLD:
                if not found:
                    right = x
                    right_top = y
                    right_bottom = y
                    found = True
                else:
                    right_bottom = y
        if found:
            break
    
    left_block = (left, left_top, left_bottom)
    right_block = (right, right_top, right_bottom)
    upper_block = (upper, upper_left, upper_right)
    lower_block = (lower, lower_left, lower_right)
    return (left_block, right_block, upper_block, lower_block)

def drawLine(draw, points):
    drawLineColor(draw, points, (255, 0, 0))

def drawLineColor(draw, points, color):
    length = len(points) - 1
    for i in range(length):
        draw.line( (points[i][0], points[i][1],points[i + 1][0], points[i + 1][1],), fill = color)
    draw.line( (points[length][0], points[length][1],points[0][0], points[0][1],), fill = color)

def drawPoints(draw, points, color):
    
    count = 0
    for pt in points:
        # print("draw points "+str(pt[0])+" "+str(pt[1]))
        draw.ellipse((pt[0] - 5, pt[1] - 5, pt[0] + 5, pt[1] + 5), fill = color)
        draw.text(pt, str(count), fill = "blue")
        count = count + 1

def polygonArea(points):
    area = 0
    length = len(points)
    j = length - 1
    for i in range(length):
        area = area + (points[j][0] + points[i][0]) * (points[j][1] - points[i][1])
        j = i
    return area/2

