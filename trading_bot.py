import zmq
from orderclass import *
import multiprocessing
import time
import sys

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
          order = OrderEntry(parts[0], self.name, parts[1], parts[2], parts[3], int(parts[4]), int(parts[5]))
          self.outbound_msgs.append(order)
        elif line.startswith("C"):
          parts = line.split(',')
          cancel = CancelOrder(parts[0], self.name, parts[1], "")
          self.outbound_msgs.append(cancel)


  def establish_network_connections(self):
    context = zmq.Context()
    self.gateway_socket = context.socket(zmq.PAIR)
    self.gateway_socket.connect(self.gateway_network_hostname)
    time.sleep(1)

    # self.market_data_socket = context.socket(zmq.SUB)
    # self.market_data_socket.connect(self.exchange_network_info.hostname_port)
    # self.market_data_socket.setsockopt_string(zmq.SUBSCRIBE, self.exchange_network_info.topic)


  def send_orders(self):
    def parse_message(msg: bytearray):
      msg_type = msg[0]
      if msg_type == 87:
        print(f"Received W")
      elif msg_type == 65:
        # print(f"Received A")
        accept_order = OrderAcceptedOutbound("", "", "", "", 0, "", 0, 0)
        accept_order.deserialize(msg)
        print(accept_order)
      elif msg_type == 69:
        executed_order = OrderExecutedOutbound("", "", "", "", 0, "", "", "", 0, 0)
        executed_order.deserialize(msg)
        print(executed_order)
      else:
        print(f"Received unknown message. Msg code: {msg_type}")

    heartbeat_msg = bytearray([87]) + self.name.encode('ascii')
    self.gateway_socket.send(heartbeat_msg)
    print(f"Sent heartbeat: {heartbeat_msg}")
    while True:
      if len(self.outbound_msgs) > 0:
        msg = self.outbound_msgs[0]
        self.gateway_socket.send(msg.serialize())
        print(f"Sent message: {msg}")
        self.outbound_msgs.pop(0)
      try:
        ouch_msg = self.gateway_socket.recv(flags=zmq.NOBLOCK)
        # print(f"Received message: {ouch_msg}") # TODO: make this a separate process
        parse_message(ouch_msg)
      except zmq.error.Again:
        pass
      # time.sleep(0.5)


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


  def read_ouch_messages(self):
    try:
      while True:
        msg = self.gateway_socket.recv(zmq.NOBLOCK)
        # print(f"Received message: {msg}")
        # parse_message(msg)
    except KeyboardInterrupt:
      print("Exiting")


  def run(self):
    # send_orders_process = multiprocessing.Process(target=self.send_orders)
    # recv_ouch_process = multiprocessing.Process(target=self.read_ouch_messages)
    # scan_market_data_process = multiprocessing.Process(target=self.scan_market_data)
    # trade_process = multiprocessing.Process(target=self.trade)

    # send_orders_process.start()
    # recv_ouch_process.start()
    # scan_market_data_process.start()
    # trade_process.start()

    # send_orders_process.join()
    # recv_ouch_process.join()
    # scan_market_data_process.join()
    # trade_process.join()

    print("Exiting")



if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser(description="Trading Bot")
  parser.add_argument("--name", type=str, help="Name of the bot", default="Bot1")
  parser.add_argument("--ip", type=str, help="IP address of the gateway", default="localhost")
  parser.add_argument("--port", type=int, help="Port to bind to", default=2000)
  parser.add_argument("--file", type=str, help="File containing orders", default="orders.txt")

  args = parser.parse_args()
  bot = TradingBot(args.name, args.file, f"tcp://{args.ip}:{args.port}") # 192.168.56.10

  try:
    bot.send_orders()
    time.sleep(0.05)
  except KeyboardInterrupt:
    print("Exiting")
    sys.exit(0)