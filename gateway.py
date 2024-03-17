# Handles specific PAIR interaction,
# subscribed to exchange outbound msgs
import zmq
import time
from multiprocessing import Process

class Gateway:

  def __init__(self,  start_port: int = 2000, max_connections: int = 10): # TODO: Add exchange_settings which takes in info about all OMEs
    # self.exchange_settings = "tcp://localhost:5555"`
    self.exchange_outbound_socket = None
    self.exchange_entry_socket = None
    self.connect_to_exchange()

    self.connections = {}
    self.start_port = start_port
    self.max_connections = max_connections

    self.setup_new_connection() # TODO: Add map from mpid to socket
    self.processes = []


  def connect_to_exchange(self):
    context = zmq.Context()
    self.exchange_outbound_socket = context.socket(zmq.SUB)
    self.exchange_outbound_socket.connect("tcp://localhost:8001") # TODO: Don't hardcode
    self.exchange_outbound_socket.setsockopt_string(zmq.SUBSCRIBE, "ENTRY-OME1") # TODO: Don't hardcode

    self.exchange_entry_socket = context.socket(zmq.PUSH)
    self.exchange_entry_socket.connect("tcp://localhost:9001") # TODO: Don't hardcode


  def run(self):
    try:
      while True:
        # self.scan_exchange_outbound()
        self.scan_connections()
        time.sleep(0.005)
    except KeyboardInterrupt:
      print("Exiting")


  def setup_new_connection(self):
    print(f"Gateway connection: IP: localhost, Port: {self.start_port}-{self.start_port+self.max_connections}") # TODO: Log
    context = zmq.Context()
    port = self.start_port
    while port < self.start_port + self.max_connections:
      self.connections[port] = context.socket(zmq.PULL)
      self.connections[port].bind(f"tcp://*:{port}")
      # self.connections[port].setsockopt(zmq.CONFLATE, 1)
      port += 1


  def scan_connections(self):
    # print("Scanning connections") # TODO: Log
    for port, socket in self.connections.items():
      # print("Checking port: ", port) # TODO: Log
      try:
        msg = socket.recv(flags=zmq.NOBLOCK)
        self.process_inbound_message(msg, port, socket)
      except zmq.error.Again or zmq.error.ZMQError as e:
        pass


  def process_inbound_message(self, msg: bytearray, port: int, socket: zmq.Socket):
    # print(f"Processing message") # TODO: Log
    match msg[0]:
      case 87: # W - Heartbeat
        print(f"Port {port}: Received W")
        socket.send(b'OK')
      case 67: # C - Order Cancel
        print(f"Port {port}: Received C")
        ouch_msg = self.send_order(msg)
      case 79: # O - Order Entry
        print(f"Port {port}: Received O")
        ouch_msg = self.send_order(msg)
      case _:
        print("Received unknown message. Msg code: ", msg[0])
        # self.send_order(msg)



  def send_order(self, arr: bytearray) -> bytearray:
    self.exchange_entry_socket.send(arr)
    # msg = self.exchange_entry_socket.recv()
    # match msg[0]:
    #   case 79:
    #     return b'O'
    #   case 67:
    #     return b'C'
    #   case _:
    #     return b'R'


  def scan_exchange_outbound(self):
    try:
      msg = self.exchange_outbound_socket.recv()
      topic, messagedata = msg.split()
      print(f"Received message: {messagedata}") # TODO: Send to correct trading bot

    except zmq.error.Again:
      pass




if __name__ == "__main__":
  gateway = Gateway()
  gateway.run()