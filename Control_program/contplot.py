#!/usr/bin/python3
import matplotlib.pyplot as plt
import numpy as np
import sys
import datetime
import time

def on_press(event):
    plot(inf)
def plot(infile):
    data = []
    for l in open(infile):
        ls = l.split()
        draw = ls[2].split("/")
        ts = ls[3]
        year = draw[0]+ "-"
        month =draw[1].zfill(2) + "-"
        day =draw[2].zfill(2)+ "T"
        d = datetime.datetime.strptime(year+month+day+ts, '%Y-%m-%dT%H:%M:%S')
        p = float(ls[6][:-1]) # skip comma
        alt = float(ls[8][:-1])
        az = float(ls[10][:-1])
        data.append([d, p, alt, az])
    data = np.array(data)
    f,ax = plt.subplots(3, sharex=True)
    f.canvas.mpl_connect('key_press_event', on_press)
    ax[0].set_ylabel("Power")
    ax[1].set_ylabel("Alt")
    ax[2].set_xlabel("UTC Time")
    ax[2].set_ylabel("Az")
    ax[0].plot(data[:,0],data[:,1])
    ax[1].plot(data[:,0],data[:,2])
    ax[2].plot(data[:,0],data[:,3])

inf = sys.argv[1]
plt.ion()
plt.show()

while True:
    plt.close("all")
    plot(inf)
    plt.draw()
    plt.pause(0.001)
    ans = input("Press [enter] to redraw the plot with new data, or type 'quit' and press enter to exit plotting: ")
    if ans.lower()=="quit":
        sys.exit(1)
