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


def drawLineColor(im, points, color):

	draw = ImageDraw.Draw(im)
	length = len(points) - 1
	for i in range(length):
		draw.line( (points[i][0], points[i][1],points[i + 1][0], points[i + 1][1],), fill = color)
		#print("points # "+repr(i)+" x "+repr(points[i][0])+" y "+repr(points[i][1]))
	draw.line( (points[length][0], points[length][1],points[0][0], points[0][1],), fill = color)


im = Image.new("RGBA", (1024, 1024), (0,0,0,0))

points = []
points.append((34, 0))
points.append((0, 34))
points.append((0, 66))
points.append((43, 110))
points.append((65, 110))
points.append((103, 72))
points.append((103, 32))
points.append((71, 0))

drawLineColor(im, points, "red")
im.show()
