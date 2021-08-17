# Imports used
import socket
import time
import sys
import datetime
# Create connection object
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Note: IP address may change (depends on your config). Port is normally 23 (not 26).
tel = sys.argv[1].lower() # vale or brage
print("TEL:", tel)
sock.connect(("192.168.5.72", 23)) 

def conid():
    msg = "*idn?\n"
    # Send message
    sock.sendall(msg.encode("ascii"))
    # Wait to generate answer
    time.sleep(0.5)
    # Read response
    ans = sock.recv(8192).decode("ascii")
    #print(ans.strip())

def poll():
    if tel == "brage":
        msg = "read:ttl:1?\n" # brage
    elif tel == "vale":
        msg = "read:ttl:2?\n" # vale
    # Send message
    sock.sendall(msg.encode("ascii"))
    # Wait to generate answer
    time.sleep(0.1)
    # Read response
    ans = sock.recv(8192).decode("ascii").strip()
    print(datetime.datetime.now(), ans[-1])

conid()
while True:
    poll()
