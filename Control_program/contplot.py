#!/usr/bin/python3
import matplotlib.pyplot as plt
import numpy as np
import sys
import datetime
import time
from scipy.signal import savgol_filter

def on_press(event):
    sys.stdout.flush()
    if event.key == 'r':
        plot(inf)
    elif event.key == 'q':
        sys.exit(0)

def plot(infile):
    plt.close("all")
    data = []
    for l in open(infile):
        ls = l.split()
        draw = ls[2].split("/")
        ts = ls[3]
        year = draw[0]+ "-"
        month =draw[1].zfill(2) + "-"
        day =draw[2].zfill(2)+ "T"
        d = datetime.datetime.strptime(year+month+day+ts, '%Y-%m-%dT%H:%M:%S')
        p = float(ls[6])
        alt = float(ls[8])
        az = float(ls[10])
        ref = float(ls[12])
        data.append([d, p, alt, az, ref])
    data = np.array(data)
    f,ax = plt.subplots(5, sharex=True)
    f.canvas.mpl_connect('key_press_event', on_press)
    ax[0].set_ylabel("Sun")
    ax[1].set_ylabel("Total")
    ax[2].set_ylabel("Ref")
    ax[3].set_ylabel("Alt")
    ax[4].set_ylabel("Az")
    ax[4].set_xlabel("UTC Time")
    ms = 1 # Markersize
    refamp = min(data[:,4])
    corr = refamp/data[:,4]
    diff = data[:,1]*corr-refamp
    diff_smooth = savgol_filter(diff, 101, 3) # window size 51, polynomial order 3
    ax[0].plot(data[:,0],diff, linestyle="none", markersize=ms, marker='o', label="The Sun - Ref")
    ax[0].plot(data[:,0],diff_smooth, linestyle="--", markersize=ms, marker='o', label="The Sun - Ref")
    ax[1].plot(data[:,0],data[:,1], linestyle="none", markersize=ms, marker='o', label="The Sun (inc. ref)")
    ax[2].plot(data[:,0],data[:,4], linestyle="none", markersize=ms, marker='o', label="Reference")
    ax[3].plot(data[:,0],data[:,2], linestyle="none", markersize=ms, marker='o')
    ax[4].plot(data[:,0],data[:,3], linestyle="none", markersize=ms, marker='o')
    f.suptitle("Press 'r' key to re-load latest data, 'q' to quit")
    plt.draw()
    plt.pause(0.001)

# Get infile supplied as argument
inf = sys.argv[1]
# Plot the data, awaiting key-press events
plot(inf)
plt.show()
