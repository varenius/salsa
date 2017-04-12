import numpy as np
import matplotlib.pyplot as plt
import pyfits
import os
data = pyfits.getdata('spectrum_9721.fits')
print(data)
data.shape
data = data[0,0]
plt.plot(data)
plt.xlabel("VLSR")
plt.ylabel("Antenna Temperature(K)")
plt.title("Solar Drift Scan Plot")
plt.grid(True)
plt.savefig('Solar_drift.png')
plt.show()
print(data)
data = data[5:]
x = max(data)
y = [0,27]
t = y.append(x)
print(t)





