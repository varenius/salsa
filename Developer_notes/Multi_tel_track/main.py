#!/usr/bin/python3
import sys
import time
from md01 import *
import curses

def curses_loop(tels, target):
    stdscr = curses.initscr()
    loop = True
    cw = 12 # column width
    stdscr.nodelay(True) # Don't wait for user input
    while loop:
        # Sleep 0.5s between reading and sending commands
        time.sleep(0.5)
        # Display info on screen...
        stdscr.clear()
        stdscr.addstr(0, 0, "UTC now   | ", curses.A_BOLD)
        stdscr.addstr(1, 0, "TELESCOPE | ", curses.A_BOLD)
        stdscr.addstr(2, 0, "Cur. Alt. | ", curses.A_BOLD)
        stdscr.addstr(3, 0, "Cur. Az.  | ", curses.A_BOLD)
        stdscr.addstr(4, 0, "Tar. Alt. | ", curses.A_BOLD)
        stdscr.addstr(5, 0, "Tar. Az.  | ", curses.A_BOLD)
        stdscr.addstr(6, 0, "TRACKING: | ", curses.A_BOLD)
        ## Some space
        stdscr.addstr(10, 0, "Available commands: ", curses.A_BOLD)
        stdscr.addstr(11, 0, "s - stop telescopes")
        stdscr.addstr(12, 0, "q - stop telescopes and quit program")
        stdscr.addstr(13, 0, "g - Track new Galactic (GLON/GLAT) position")
        stdscr.addstr(14, 0, "h - Track new Horizontal (ALT/AZ) direction ")
        stdscr.addstr(15, 0, "i - Track the Sun")
        # Set datetime info
        utcnow = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        stdscr.addstr(0, cw, utcnow)
        # Print tel names and current position
        for i, tel in enumerate(tels):
            stdscr.addstr(1, cw * (1+i), tel.site.name, curses.A_UNDERLINE)
            (cal, caz) = tel.get_current_alaz()
            stdscr.addstr(2, cw * (1+i), "{}".format(cal))
            stdscr.addstr(3, cw * (1+i), "{}".format(caz))
        # Sleep 0.5s between reading and sending commands
        time.sleep(0.5)

        # Set target info
        if target[0]=="":
            stdscr.addstr(6, cw, "N/A")
            tal = ""
            taz = ""
            for i, tel in enumerate(tels):
                # Print target alt/az
                stdscr.addstr(4, cw * (1+i), "{}".format(tal))
                stdscr.addstr(5, cw * (1+i), "{}".format(taz))
        elif target[0]=="HOR":
            stdscr.addstr(6, cw, "HORIZONTAL")
            tal = target[1]
            taz = target[2]
            for i, tel in enumerate(tels):
                # Print target alt/az
                stdscr.addstr(4, cw * (1+i), "{}".format(tal))
                stdscr.addstr(5, cw * (1+i), "{}".format(taz))
        elif target[0]=="GAL":
            glon = target[1]
            glat = target[2]
            stdscr.addstr(6, cw, "GALACTIC LON={}, LAT={}".format(glon, glat))
            for i, tel in enumerate(tels):
                # Don't get current pos, instead get desired
                tal,taz = tel.get_desired_alaz(target)
                # Move all telescopes
                tel.move(tal, taz)
                # Print target alt/az from now or last loop
                stdscr.addstr(4, cw * (1+i), "{}".format(tal))
                stdscr.addstr(5, cw * (1+i), "{}".format(taz))
        elif target[0]=="SUN":
            stdscr.addstr(6, cw, "The Sun")
            for i, tel in enumerate(tels):
                # Don't get current pos, instead get desired
                tal,taz = tel.get_desired_alaz(target)
                # Move all telescopes
                tel.move(tal, taz)
                # Print target alt/az from now or last loop
                stdscr.addstr(4, cw * (1+i), "{}".format(tal))
                stdscr.addstr(5, cw * (1+i), "{}".format(taz))
        
        # Handle user input
        try:
            key = stdscr.getkey().lower()
            if key=="s":
                # Stop all tels
                for i, tel in enumerate(tels):
                    tel.stop()
                target = ["", "", ""]
            elif key=="q":
                # Stop all tels
                for i, tel in enumerate(tels):
                    tel.stop()
                stdscr.clear()
                stdscr.refresh()
                loop = False
            elif key=="g" or key=="h" or key=="i":
                # Quit this loop to get new target from user
                stdscr.clear()
                stdscr.refresh()
                loop = False
        except:
            pass
        stdscr.refresh()
    curses.endwin()

    # Return user input to control loop
    return key

def control_loop(tels):
    # Enable curses loop
    cloop = True
    # Initialize target to empty string
    target = ["","",""]
    while cloop:
        # Run curses loop awaiting user input
        ans = curses_loop(tels, target)
        # We got user input, deal with it...
        if ans == "g":
            glon = float(input("Please enter target galactic longitude in decimal degrees e.g. 80.5 :"))
            glat = float(input("Please enter target galactic latitude in decimal degrees e.g. 0.0 :"))
            conf = input("Are you sure you want to track glon={} glat={} deg ? [Yes/No]".format(glon,glat))
            if conf.lower()=="yes":
                target = ["GAL", glon, glat]
                # Stop all tels
                for i, tel in enumerate(tels):
                    tel.stop()
                time.sleep(1.0)
                # Movement done by curses_loop in this case
        if ans == "h":
            az = float(input("Please enter target azimuth in decimal degrees e.g. 148.5 :"))
            al = float(input("Please enter target altitude in decimal degrees e.g. 43.5 :"))
            conf = input("Are you sure you want to track alt={} az={} deg ? [Yes/No]".format(al, az))
            if conf.lower()=="yes":
                target = ["HOR", al,az]
                # Stop all tels
                for i, tel in enumerate(tels):
                    tel.stop()
                time.sleep(1.0)
                # Move all telescopes, started here to simplify code (but yes, ugly place)
                for i, tel in enumerate(tels):
                    tel.move(al, az)
        if ans == "i":
            conf = input("Are you sure you want to track the Sun ? [Yes/No]")
            if conf.lower()=="yes":
                target = ["SUN", "", ""]
                # Stop all tels
                for i, tel in enumerate(tels):
                    tel.stop()
                time.sleep(1.0)
                # Movement done by curses_loop in this case
        elif ans == "q":
            # Quit program
            cloop = False

if __name__ == '__main__':
    # Assume list of config files given as script arguments on command line, 
    # so we run "python3 script.py tel1.conf tel2.conf ..."
    # Each config file reflects a telescope to be controlled
    configs = sys.argv[1:]
    tels = []
    
    # Create one MD01 object for each config file (each telescope)
    for cf in configs:
        tels.append(MD01(cf))
    # Start control loop
    control_loop(tels)
