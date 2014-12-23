import matplotlib.pyplot as plt
import matplotlib
font = {'size'   : 14}
matplotlib.rc('font', **font)

# Nicer plots in Python, e.g. for rotation curve. 
infilename = 'ROTVALUES.txt'
infile = open(infilename)

for line in infile:
    if not line.startswith('#'):
        rv = line.split()
        r = float(rv[0])
        v = (rv[1])
        plt.plot(r, v, '*k')
plt.axis([0, 10, 0, 250])
plt.title('Rotation curve of the Milky Way')
plt.xlabel('Distance from galactic center [kpc]')
plt.ylabel('Rotational velocity [km/s]')
plt.tight_layout()
plt.show()
