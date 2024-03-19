import zmq
from orderclass import *
import multiprocessing as mp
import time
import sys
import queue

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
    self.outbound_msgs = mp.Queue()
    self.inbound_msgs = []
    self.trades = []

    if order_file is not None:
      self.load_orders(order_file)

    self.gateway_socket = None
    self.market_data_socket = None


  def load_orders(self, order_file: str):
    with open(order_file, 'r') as f:
      for line in f:
        line = line.strip()
        if line.startswith("O"):
          parts = line.split(',')
          order = OrderEntry(parts[0], self.name, parts[1], parts[2], parts[3], int(parts[4]), int(parts[5]))
          self.outbound_msgs.put(order)
        elif line.startswith("C"):
          parts = line.split(',')
          cancel = CancelOrder(parts[0], self.name, parts[1], "")
          self.outbound_msgs.put(cancel)


  def run(self):
    processes = []
    send_orders_process = mp.Process(target=self.send_orders, args=())
    send_orders_process.start()
    processes.append(send_orders_process)

    recv_mdf_process = mp.Process(target=self.scan_market_data, args=())
    recv_mdf_process.start()
    processes.append(recv_mdf_process)

    for process in processes:
      process.join()


  def send_orders(self):
    context = zmq.Context()
    self.gateway_socket = context.socket(zmq.PAIR)
    self.gateway_socket.connect(self.gateway_network_hostname)
    time.sleep(1)

    def parse_message(msg: bytearray):
      msg_type = msg[0]
      if msg_type == 87:
        print(f"Received W")
      elif msg_type == 65: # A
        # print(f"Received A")
        accept_order = OrderAcceptedOutbound("", "", "", "", 0, "", 0, 0)
        accept_order.deserialize(msg)
        print(f"Received OUCH Add: {accept_order}")
      elif msg_type == 67: # C
        cancel_order = OrderCanceledOutbound("", "", "", "", 0, 0, "")
        cancel_order.deserialize(msg)
        print(f"Received OUCH Cancel: {cancel_order}")
      elif msg_type == 69: # E
        executed_order = OrderExecutedOutbound("", "", "", "", 0, "", "", "", 0, 0)
        executed_order.deserialize(msg)
        print(f"Received OUCH Trade: {executed_order}")
      elif msg_type == 74: # J
        rejected_order = OrderRejectedOutbound("", "", "", "", 0, "")
        rejected_order.deserialize(msg)
        print(f"Received OUCH Reject: {rejected_order}")
      else:
        print(f"Received unknown message. Msg code: {msg_type}")

    heartbeat_msg = bytearray([87]) + self.name.encode('ascii')
    self.gateway_socket.send(heartbeat_msg)
    # print(f"Sent heartbeat: {heartbeat_msg}")
    while True:
      try:
        msg = self.outbound_msgs.get_nowait()
        msg = msg.serialize()
        self.gateway_socket.send(msg)
        # print(f"Sent message: {msg}")
      except queue.Empty:
        pass
      try:
        ouch_msg = self.gateway_socket.recv(flags=zmq.NOBLOCK)
        # print(f"Received message: {ouch_msg}") # TODO: make this a separate process
        parse_message(ouch_msg)
      except zmq.error.Again:
        pass
      # time.sleep(0.5)


  def scan_market_data(self): # TODO: Finish writing this
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:11000")
    socket.setsockopt_string(zmq.SUBSCRIBE, "TPCF1010-BBO5")
    time.sleep(1)

    try:
      while True:
        try:
          msg = socket.recv(flags=zmq.NOBLOCK)
          topic, msg = msg.split(b'@', 1)
          # print(topic, msg)
          bbo = MDF_BBO5("", 0, 0, 0, 0, 0, 0, 0, {}, {})
          bbo.deserialize(msg)
          print(f"BBO5: {bbo}")
          # print(f"Received BBO5")
        except zmq.error.Again:
          # print("No message received")
          pass
        time.sleep(0.5)
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
    bot.run()
    time.sleep(0.05)
  except KeyboardInterrupt:
    print("Exiting")
    sys.exit(0)