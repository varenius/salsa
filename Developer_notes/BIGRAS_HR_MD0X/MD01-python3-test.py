# Basic Python3 script to communicate with MD-01 via Ethernet module
# Only using standard Python3 libraries
#
# Format from http://ryeng.name/blog/3
#The SPID protocol supports 3 commands: stop, status and set. The stop
#command stops the rotator in its current position. The status command
#returns the current position of the rotator, and the set command tells
#the rotator to rotate to a given position.
#All commands are issued as 13 byte packets, and responses are received
#12 byte packets (Rot2Prog).
#
#COMMAND PACKETS
#Byte:    0   1    2    3    4    5    6    7    8    9    10   11  12
#       -----------------------------------------------------------------
#Field: | S | H1 | H2 | H3 | H4 | PH | V1 | V2 | V3 | V4 | PV | K | END |
#       -----------------------------------------------------------------
#Value:   57  3x   3x   3x   3x   0x   3x   3x   3x   3x   0x   xF  20 (hex)
#
#S:     Start byte. This is always 0x57 ('W')
#H1-H4: Azimuth as ASCII characters 0-9
#PH:    Azimuth resolution in pulses per degree (ignored!)
#V1-V4: Elevation as ASCII characters 0-9
#PV:    Elevation resolution in pulses per degree (ignored!)
#K:     Command (0x0F=stop, 0x1F=status, 0x2F=set)
#END:   End byte. This is always 0x20 (space)

# Imports used
import socket
import time
import sys
# Create connection object
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Connect to MD-01 via ethernet interface, using default config (as in manual).
# Note: IP address may change (depends on your config). Port is normally 23 (not 26).
sock.connect(("192.168.5.10", 23)) 


def set_azel(taz,tel):
    PH = 10 # Pulses per degree, 0A in hex
    PV = 10 # Pulses per degree, 0A in hex
    H = str(int(PH * (360+taz)))
    H1 = "3"+H[0]
    H2 = "3"+H[1]
    H3 = "3"+H[2]
    H4 = "3"+H[3]
    V = str(int(PV * (360+tel)))
    V1 = "3"+V[0]
    V2 = "3"+V[1]
    V3 = "3"+V[2]
    V4 = "3"+V[3]
    msg = bytes.fromhex("57"+H1+H2+H3+H4+"0A"+V1+V2+V3+V4+"0A2F20")
    print("SETMSG", msg.hex())
    # Send message
    sock.send(msg)
    # Read response from MD-01
    data = sock.recv(1024)
    # Decode bytes to hex
    ans = data.hex()
    print("SET", ans)

def calibrate(taz,tel):
    PH = 10 # Pulses per degree, 0A in hex
    PV = 10 # Pulses per degree, 0A in hex
    H = str(int(PH * (360+taz)))
    H1 = "3"+H[0]
    H2 = "3"+H[1]
    H3 = "3"+H[2]
    H4 = "3"+H[3]
    V = str(int(PV * (360+tel)))
    V1 = "3"+V[0]
    V2 = "3"+V[1]
    V3 = "3"+V[2]
    V4 = "3"+V[3]
    msg = bytes.fromhex("57"+H1+H2+H3+H4+"0A"+V1+V2+V3+V4+"0AF920")
    print("SETMSG", msg.hex())
    # Send message
    sock.send(msg)
    # Read response from MD-01
    data = sock.recv(1024)
    # Decode bytes to hex
    ans = data.hex()
    print("CALIBRATE", taz, tel, ans)

def reset():
    # Set az/el to 0
    #Format status request message as bytes
    #Content taken from the XLS files supplied by RF HAM DESIGN
    msg = bytes.fromhex("5700000000000000000000F820")
    # Send message
    sock.send(msg)
    # Read response from MD-01
    data = sock.recv(1024)
    # Decode bytes to hex
    ans = data.hex()
    print("RESET", ans)

def stop():
    #Format status request message as bytes
    #Content taken from the XLS files supplied by RF HAM DESIGN
    msg = bytes.fromhex("57000000000000000000000F20")
    # Send message
    sock.send(msg)
    # Read response from MD-01
    data = sock.recv(1024)
    # Decode bytes to hex
    ans = data.hex()
    print("STOP", ans)

def get_azel():
    #Format status request message as bytes
    #Content taken from the XLS files supplied by RF HAM DESIGN
    msg = bytes.fromhex("57000000000000000000001F20")
    # Send message
    sock.send(msg)
    # Read response from MD-01
    data = sock.recv(1024)
    # Decode bytes to hex
    ans = data.hex()
    print("GET",ans)
    # Extract relevant data as floating point numbers
    H1 = float(ans[2:4])
    H2 = float(ans[4:6])
    H3 = float(ans[6:8])
    H4 = float(ans[8:10])
    V1 = float(ans[12:14])
    V2 = float(ans[14:16])
    V3 = float(ans[16:18])
    V4 = float(ans[18:20])
    # Calculate angles for Az/El
    az = H1 * 100 + H2 * 10 + H3 + H4 / 10 -360
    el = V1 * 100 + V2 * 10 + V3 + V4 / 10 -360
    return az, el

def get_config():
    #Format status request message as bytes
    #Content taken from the XLS files supplied by RF HAM DESIGN
    msg = bytes.fromhex("57000000000000000000004F20")
    # Send message
    sock.send(msg)
    # Read response from MD-01
    data = sock.recv(1024)
    # Decode bytes to hex
    ans = data.hex()
    print("GETCONF",ans)

#set_azel(100, -100)
#time.sleep(1)
print(get_azel())
#stop()
get_config()
#reset()
#calibrate(250,90)
#time.sleep(1)
#print(get_azel())

#while True:
#    # Read Az/El once every second
#    az, el = get_azel()
#    # Print result
#    print("AZ {:2.1f} EL {:2.1f}".format(az,el))
#    # Sleep for 1 sec until next call
#    time.sleep(1)
