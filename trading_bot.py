import sys
import time

import zmq

from orderclass import OrderEntry, CancelOrder


class TradingBot:
  def __init__(self, name: str, order_file: str, gateway_network_hostname: str):
    self.name = name
    if len(self.name) > 10:
      self.name = self.name[:10]
    else:
      self.name = self.name.ljust(10, ' ')
    self.order_file = order_file
    self.gateway_network_hostname : str = gateway_network_hostname
    self.exchange_network_info = None # TODO
    self.outbound_msgs = []
    self.inbound_msgs = []
    self.trades = []

    if order_file is not None:
      self.load_orders(order_file)

    self.gateway_socket = None
    self.market_data_socket = None
    self.establish_network_connections()

  def load_orders(self, order_file: str):
    with open(order_file, 'r') as f:
      for line in f:
        line = line.strip()
        if line.startswith("O"):
          parts = line.split(',')
          order = OrderEntry(parts[0], self.name, parts[1], parts[2], int(parts[3]), int(parts[4]), parts[5])
          self.outbound_msgs.append(order)
        elif line.startswith("X"):
          parts = line.split(',')
          cancel = CancelOrder(parts[0], self.name, parts[1])
          self.outbound_msgs.append(cancel)


  def establish_network_connections(self):
    context = zmq.Context()
    self.gateway_socket = context.socket(zmq.PAIR)
    self.gateway_socket.connect(self.gateway_network_hostname)

    # self.market_data_socket = context.socket(zmq.SUB)
    # self.market_data_socket.connect(self.exchange_network_info.hostname_port)
    # self.market_data_socket.setsockopt_string(zmq.SUBSCRIBE, self.exchange_network_info.topic)


  def send_orders(self):
    try:
      while True:
        while len(self.outbound_msgs) > 0:
          msg = self.outbound_msgs[0]
          self.gateway_socket.send(msg.serialize())
          print(f"Sent message: {msg}")
          self.outbound_msgs.pop(0)
          ouch_msg = self.gateway_socket.recv()
          print(f"Received message: {ouch_msg}")
          time.sleep(1) # TODO: Remove
    except KeyboardInterrupt:
      print("Exiting")


  def scan_market_data(self):
    try:
      while True:
        pass
    except KeyboardInterrupt:
      print("Exiting")


  def trade(self):
    try:
      while True:
        pass
    except KeyboardInterrupt:
      print("Exiting")


  def run(self):
    pass



if __name__ == "__main__":
  bot = TradingBot("Bot1", "orders.txt", "tcp://localhost:2000")

  try:
    while True:
      bot.send_orders()
      time.sleep(1)
  except KeyboardInterrupt:
    print("Exiting")
    sys.exit(0)