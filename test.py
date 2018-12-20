import socket
import time
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
addr=('192.168.4.1',80)
s.connect(addr)
s.send(b'asfsadfa')
time.sleep(1)
r = s.recv(1024)
s.close()
print (r)
