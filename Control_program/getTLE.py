#!/usr/bin/env python
# Downloads TLEs in an automatic fashion

import numpy as np
import datetime
from urllib.request import urlopen
import sys
import os
import configparser

sys.path.append('./')

# Load the config file
abspath = os.path.abspath(__file__)
configfile = os.path.dirname(abspath) + '/SALSA.config'
config=configparser.ConfigParser()
config.read(configfile)
# set the directory with TLE files and names of the new files
TLEdir=config.get('TLE','tledir_name')
inFile=config.get('TLE','tlelinks')
outFile=config.get('TLE','tleoutfile_name')
print(TLEdir, inFile, outFile)

date=datetime.datetime.utcnow()
year=date.strftime("%Y")
doy=date.strftime("%j")
print ('Current Doy: %s Year: %s' % (doy,year))

constellations= np.genfromtxt(inFile, skip_header=1, delimiter=' ',dtype=str,usecols=0)
links= np.genfromtxt(inFile, skip_header=1, delimiter=' ',dtype=str,usecols=1)
ctr=0
print ('#############################################')
for i in constellations:

    url=links[ctr]
    print(url)

    # Downloading almanac with the progress bar
    u=urlopen(url)
    f=open(TLEdir+outFile+i+".tle",'wb')
    meta=u.info()
    fileSize=int(meta.get("Content-Length")[0])
    print ("Downloading TLEs for %-8s  (%s Bytes) ... " % (i, fileSize))

    fileSizeDl=0
    blockSize=2048
    while True:
        buffer = u.read(blockSize)
        if not buffer:
            break

        fileSizeDl+=len(buffer)
        f.write(buffer)
        status = r"%10d [%3.2f%%]" % (fileSizeDl, fileSizeDl * 100. / fileSize )
        status = status + chr(8)*(len(status)+1)
        print(status)
    f.close()
    ctr+=1
print ('##################DONE#######################')

sys.exit(0)
