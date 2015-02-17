import sys
import numpy as np
import matplotlib.pyplot as plt

vmin = -250
vmax = 200

spec = sys.argv[1]
outfile = sys.argv[2]
lines = [line.strip() for line in open(spec)]
# Read header
header = lines[0].split()
glon = header[1]
glat = header[2]
beam = header[4]
data = []
for line in lines:
    if not (line.startswith('%') or (line == '')):
        ldata = line.split()
        print ldata
        v = float(ldata[0])
        if v>vmin and v<vmax:
            T = float(ldata[1])
            data.append([v, T])

data = np.array(data)
plt.plot(data[:,0], data[:,1])
plt.title('Glon = ' + glon + ', glat=' + glat + ', beam = ' + beam + ' [deg]')
plt.savefig(outfile)
#plt.show()
