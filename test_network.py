import zmq
import random
import sys
import time

port = "2000"
context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.connect("tcp://localhost:%s" % port)

try:
  while True:
      print("Sending message")
      socket.send(b'W')
      time.sleep(1)
except KeyboardInterrupt:
  sys.exit(0)