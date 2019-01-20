import matplotlib.pyplot as plt
import os
import numpy as np


def todb(v):
    return 10*np.log10(v)


def ldspectra(file_name):
    with open(file_name) as f:
        data = [l for l in f.read().split('\n') if l and not l.startswith('#')]
    return zip(*[tuple(float(v) for v in l.split(' ')) for l in data])


def todb(vec):
    return 10*np.log10(vec)


def clip_edges(vec_, clip_frac=0.03):
    c = int(clip_frac*len(vec_))
    return vec_[c:-c]


if __name__ == '__main__':
    fig = plt.figure()
    ax = fig.add_subplot(111)
    sname = os.sys.argv[1]
    #ax.set_title(sname[sname.find("/")+1:sname.find("_")])
    ax.yaxis.grid()
    ax.set_title("GPS PRN 30")
    ax.set_ylabel("Uncalibraded antenna temperature (dBK)")
    ax.set_xlabel("Offset from center frequency (MHz)")
    vvx, vvy = list(), list()
    for file_name in os.sys.argv[1:]:
        vx, vy = ldspectra(file_name)
        vx, vy = clip_edges(vx), todb(clip_edges(vy))
        vvx.append(vx)
        vvy.append(vy)
        ax.plot(vx, vy, linestyle='-')
    vvx = np.average(np.array(vvx), axis=0)
    vvy = np.average(np.array(vvy), axis=0)
    #ax.plot(vvx, vvy, linestyle='-', marker='.', color='r')
    plt.show()
