import zmq
from orderclass import *
import multiprocessing as mp
import time
import sys
import queue
from dataclasses import dataclass
from generator import TenPokerCardSample
@dataclass
class TickerplantInfo:
  ip_addr: str
  port: int
  topics: list[str]

@dataclass # TODO: Refactor
class ExchangeInfo:
  ip_addr: str
  port: int



class TradingBot: # TODO: There is still a bug for some reason where it doesn't receive the messages from the exchange after you run a second bot and after the second bot is done sending orders
  def __init__(self, name: str, order_file: str, exchange_network_info: ExchangeInfo, tickerplant_info: TickerplantInfo):
    self.name = name
    if len(self.name) > 10:
      self.name = self.name[:10]
    else:
      self.name = self.name.ljust(10, ' ')
    self.order_file = order_file
    # self.gateway_network_hostname : str = gateway_network_hostname
    self.exchange_network_info = exchange_network_info
    self.tickerplant_info = tickerplant_info
    self.outbound_msgs = mp.Queue()
    self.inbound_msgs = []
    self.trades = []

    if order_file is not None:
      self.load_orders(order_file)

    self.topic_queues : dict[str, mp.Queue] = {topic.encode(): mp.Queue() for topic in tickerplant_info.topics}

    # self.gateway_socket = None
    # self.market_data_socket = None


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
    send_orders_process = mp.Process(target=self.send_orders, args=(self.exchange_network_info.ip_addr, self.exchange_network_info.port))
    send_orders_process.start()
    processes.append(send_orders_process)

    recv_mdf_process = mp.Process(target=self.scan_market_data, args=(self.tickerplant_info.ip_addr, self.tickerplant_info.port, self.tickerplant_info.topics))
    recv_mdf_process.start()
    processes.append(recv_mdf_process)

    trade_logic_process = mp.Process(target=self.trade, args=())
    trade_logic_process.start()
    processes.append(trade_logic_process)

    for process in processes:
      process.join()


  def send_orders(self, exchange_ip_addr : str, exchange_port : int):
    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.connect(f"tcp://{exchange_ip_addr}:{exchange_port}")
    time.sleep(1)

    def parse_message(msg: bytearray):
      msg_type = msg[0]
      if msg_type == 87:
        print(f"Received W")
      elif msg_type == 65: # A
        # print(f"Received A")
        accept_order = OrderAcceptedOutbound()
        accept_order.deserialize(msg)
        print(f"Received OUCH Add: {accept_order}")
      elif msg_type == 67: # C
        cancel_order = OrderCanceledOutbound()
        cancel_order.deserialize(msg)
        print(f"Received OUCH Cancel: {cancel_order}")
      elif msg_type == 69: # E
        executed_order = OrderExecutedOutbound()
        executed_order.deserialize(msg)
        print(f"Received OUCH Trade: {executed_order}")
      elif msg_type == 74: # J
        rejected_order = OrderRejectedOutbound()
        rejected_order.deserialize(msg)
        print(f"Received OUCH Reject: {rejected_order}")
      else:
        print(f"Received unknown message. Msg code: {msg_type}")

    heartbeat_msg = bytearray([87]) + self.name.encode('ascii')
    socket.send(heartbeat_msg)
    # print(f"Sent heartbeat: {heartbeat_msg}")
    while True:
      try:
        msg = self.outbound_msgs.get_nowait()
        msg = msg.serialize()
        socket.send(msg)
        # print(f"Sent message: {msg}")
      except queue.Empty:
        pass
      try:
        ouch_msg = socket.recv(flags=zmq.NOBLOCK)
        # print(f"Received message: {ouch_msg}") # TODO: make this a separate process
        parse_message(ouch_msg)
      except zmq.error.Again:
        pass
      # time.sleep(0.5)


  def scan_market_data(self, tickerplant_ip_addr : str, tickerplant_port : int, topics : list[str]): # TODO: Finish writing this
    def parse_itch(msg: bytearray):
      msg_type = msg[0]
      match msg_type:
        case 65: # A
          add_order = ITCH_AddOrder()
          add_order.deserialize(msg)
          return add_order
        case 67: # C
          cancel_order = ITCH_OrderCancel()
          cancel_order.deserialize(msg)
          return cancel_order
        case 69: # E
          trade = ITCH_Trade()
          trade.deserialize(msg)
          return trade
        case _:
          print(f"Received unknown message. Msg code: {msg_type}")
          return None

    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://{tickerplant_ip_addr}:{tickerplant_port}")
    # socket.setsockopt_string(zmq.SUBSCRIBE, "TPCF1010-ITCH")
    for topic in topics:
      socket.setsockopt_string(zmq.SUBSCRIBE, topic)
    time.sleep(1)

    try:
      while True:
        try:
          raw_msg = socket.recv(flags=zmq.NOBLOCK)
          print(raw_msg)
          print(raw_msg.split(b'@', 1))
          topic, msg = raw_msg.split(b'@', 1)
          print("Received message: ", topic, msg)
          print(msg.split(b'@', 1))
          ticker, topic_type = topic.decode().split('-')
          match topic_type:
            case "BBO5":
              bbo = MDF_BBO5("", 0, 0, 0, 0, 0, 0, 0, {}, {})
              bbo.deserialize(msg)
              print(f"{topic}: {bbo}")
              self.topic_queues[topic].put(bbo)
            case "ITCH":
              itch_order = parse_itch(msg)
              print(f"{topic}: {itch_order}")
              self.topic_queues[topic].put(itch_order)
            case "TPC":
              print(msg)
              tpc_sample = TenPokerCardSample()
              tpc_sample.deserialize(msg)
              print(f"{topic}: {tpc_sample}")
              self.topic_queues[topic].put(tpc_sample)
        except zmq.error.Again:
          pass
        time.sleep(0.050)
    except KeyboardInterrupt:
      print("Exiting")


  def trade(self):
    try:
      while True:
        time.sleep(1)
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
  exchange_info = ExchangeInfo("localhost", 2001)
  tickerplant_info = TickerplantInfo("localhost", 11000, ["TPCF1010-BBO5", "TPCF1010-ITCH", "GEN-TPC"])

  bot = TradingBot(args.name, args.file, exchange_info, tickerplant_info) # 192.168.56.10

  try:
    bot.run()
    time.sleep(0.05)
  except KeyboardInterrupt:
    print("Exiting")
    sys.exit(0)