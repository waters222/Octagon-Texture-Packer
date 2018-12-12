import re

prog = re.compile("_[0-9]+$")
result = prog.search("dsfdsf #fA#a_90")
if result:
	print(result.group(0)[1:])
for i in range(4):
	print(i)