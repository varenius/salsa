# TLEephem class to cope with data from TLE files

import numpy as np
import os
import glob
import ephem
import datetime
import shutil


class TLEephem:
    """A simple class coping with TLE"""

    itsObjectLines=np.zeros((1, 3),dtype=object)
    itsObserver= ephem.Observer()

    def __init__(self,iTLEdir):
        self.TLEdir=iTLEdir
        self.Extension='*.tle'
        self.GetFiles()

    def SetObserver(self, phi, lam, eh, time = None ):
        """
        Sets the ephem observer using provided parameters.
        :param phi: latitude
        :param lam: longitude
        :param eh: height
        :param time: time
        :return: nothing
        """
        if not time: time = datetime.datetime.utcnow()

        self.itsObserver.lon=lam
        self.itsObserver.lat=phi
        self.itsObserver.elevation=eh
        self.itsObserver.date=time.strftime('%Y/%d/%m %H:%M:%S')


    def GetFiles(self):
        """
        Parses the TLE files and stores TLE lines in the itsObjectLines container.

        :return: nothing
        """
        tmpFile="tmp1.txt"
        with open(tmpFile, 'wb') as wfd:
            for filename in glob.glob(os.path.join(self.TLEdir, self.Extension)):
                with open(filename, 'rb') as fd:
                    shutil.copyfileobj(fd, wfd, 1024 * 1024 * 10)
        tleLines = np.genfromtxt(tmpFile, comments='#', delimiter='\n', dtype=str)
        self.GetLines(tleLines)
        os.remove(tmpFile)

    def GetLines(self,tleLines):
        """
        Helper function storing TLE from files into class container.
        :param tleLines: TLE from multiple files
        :return: nothing
        """
        itsFirstLines=tleLines[::3]
        itsSecondlines=tleLines[1::3]
        itsThirdlines = tleLines[2::3]

        n=len(itsFirstLines)
        m=3

        self.itsObjectLines.resize((n,m))
        self.itsObjectLines[:,0] = itsFirstLines
        self.itsObjectLines[:,1] = itsSecondlines
        self.itsObjectLines[:,2] = itsThirdlines

    def ComputeAzEl(self,constellation,visibility=None,time = None):
        """
        Computes azimuth and elevation angles for a defined group of GNSS satellites
        :param constellation: all' or 'ALL' or 'GPS' or 'GLONASS' or 'GALILEO' or 'BEIDOU'
        :param visibility: 'all' or 'ALL' or 'visible' or 'VISIBLE'
        :param time: if 'none' then computes the coordinates for current UTC time
        :return: SatAzEl - list of SatName, Az, El
        """

        SatAzEl = []

        if not time: time=datetime.datetime.utcnow()
        self.itsObserver.date=time
        if not visibility: visibility = False

        for i in range(0,len(self.itsObjectLines)):
                satName=str(self.itsObjectLines[i,0])
                if satName.find(constellation,0) >= 0 or constellation=="ALL" or constellation=="all":
                    sat=ephem.readtle(satName, str(self.itsObjectLines[i,1]), str(self.itsObjectLines[i,2]))
                    sat.compute(self.itsObserver)
                    if visibility:
                        if np.degrees(sat.alt) > 0.0:
                            SatAzEl.append(satName)
                            SatAzEl.extend([np.degrees(sat.az), np.degrees(sat.alt)])
                    else:
                        SatAzEl.append(satName)
                        SatAzEl.extend([np.degrees(sat.az), np.degrees(sat.alt)])
        return SatAzEl


    def ComputeAzElSingle(self,satName,time = None):
        """
         Returns Azimuth and Elevation angles in decimal degrees for a given satName
        :param satName: name of the satellite
        :param time:  if 'none' then computes the coordinates for current UTC time
        :return: az, el - in decimal degrees
        """
        az=0.0
        el=0.0
        if not time: time=datetime.datetime.utcnow()
        self.itsObserver.date=time

        for i in range(0,len(self.itsObjectLines)):

            if satName==str(self.itsObjectLines[i,0]):
                sat=ephem.readtle(satName, str(self.itsObjectLines[i,1]), str(self.itsObjectLines[i,2]))
                sat.compute(self.itsObserver)
                az=np.degrees(sat.az)
                el=np.degrees(sat.alt)
                break


        return az,el


