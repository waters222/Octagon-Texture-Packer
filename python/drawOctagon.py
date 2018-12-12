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
