import zmq
import time
import multiprocessing as mp
from dataclasses import dataclass
from orderclass import *
from matching_engine import PriceLevel, PriceLevelList
@dataclass
class ExchangeInfo:
  ip_addr: str
  port: int
  topics: list[str]

@dataclass
class GeneratorInfo:
  ip_addr: str
  port: int
  topics: list[str]

class ITCH_Orderbook():
  def __init__(self, ticker_configuration: TickerConfiguration):
    self.ticker_configuration = ticker_configuration
    self.max_price: int = ticker_configuration.max_price
    self.min_price: int = ticker_configuration.min_price
    self.best_bid: int = 0
    self.best_ask: int = 0
    self.orderbook = PriceLevelList()
    self.orderid_map = {}

    self.total_bid_orders = 0
    self.total_ask_orders = 0
    self.total_bid_volume = 0
    self.total_ask_volume = 0

  def process_msg(self, msg):
    pass


class Tickerplant():
  def __init__(self, exchange_infos: list[ExchangeInfo], generator_infos: list[GeneratorInfo]):
    self.exchange_infos = exchange_infos
    self.generator_infos = generator_infos

    self.run()

  def run(self):
    processes = []
    print("Starting exchange connection")
    for exchange_info in self.exchange_infos:
      for topic in exchange_info.topics:
        process = mp.Process(target=self.exchange_daemon, args=(exchange_info.ip_addr, exchange_info.port, topic))
        process.start()
        processes.append(process)

    print("Starting generator connection")
    for generator_info in self.generator_infos:
      for topic in generator_info.topics:
        process = mp.Process(target=self.generator_daemon, args=(generator_info.ip_addr, generator_info.port, topic))
        process.start()
        processes.append(process)

    for process in processes:
      process.join()


  def exchange_daemon(self, ip_addr: str, port: int, topic: str):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://{ip_addr}:{port}")
    if topic is not None:
      socket.setsockopt_string(zmq.SUBSCRIBE, topic)

    def parse_itch_msg(msg: str):
      def parse_market_data(msg: str):
        byte_arr = bytearray(msg, "ascii")
        msg_type = byte_arr[0]
        match msg_type:
          case 65: # A
            print(f"Received A")
            add_order = ITCH_AddOrder("", "", 0, "", "", 0, 0)
            add_order.deserialize(byte_arr)
            print(add_order)
          case 67: # C
            print(f"Received C")
            canceled_order = ITCH_OrderCancel("", "", 0, "", 0)
            canceled_order.deserialize(byte_arr)
            print(canceled_order)
          case 84: # T
            print(f"Received T")
            trade_order = ITCH_Trade("", "", 0, 0, 0, "", "", "")
            trade_order.deserialize(byte_arr)
            print(trade_order)
          case _:
            print(f"Unknown message type: {msg_type}")

      topic, data = msg.split("@", 1)
      # print(f"Topic: {topic}, Data: {data}")
      subject, ome = topic.split("-", 1)
      match subject:
        case "MDF":
          order = parse_market_data(data)
        case "BBO10":
          print("BBO10")
        case _:
          print("Unknown message type")

    try:
      while True:
        try:
          msg = socket.recv_string(flags=zmq.NOBLOCK)
          # print(f"{msg}")
          parse_itch_msg(msg)
        except zmq.error.Again:
          # print("No message received")
          pass
        time.sleep(0.005)
    except KeyboardInterrupt:
      print("Exiting")


  def generator_daemon(self, ip_addr: str, port: int, topic: str):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://{ip_addr}:{port}")
    if topic is not None:
      socket.setsockopt_string(zmq.SUBSCRIBE, topic)

    try:
      while True:
        try:
          msg = socket.recv_string(flags=zmq.NOBLOCK)
          print(f"{msg}")
        except zmq.error.Again:
          # print("No message received")
          pass
        time.sleep(0.005)
    except KeyboardInterrupt:
      print("Exiting")


if __name__ == "__main__":
  # context = zmq.Context()
  # socket = context.socket(zmq.SUB)
  # socket.connect("tcp://localhost:7000")
  # socket.setsockopt_string(zmq.SUBSCRIBE, "TPC")

  # try:
  #   while True:
  #     try:
  #       msg = socket.recv_string(flags=zmq.NOBLOCK)
  #       print(f"{msg}")
  #     except zmq.error.Again:
  #       print("No message received")
  #     time.sleep(0.5)
  # except KeyboardInterrupt:
  #   print("Exiting")

  exchange_info = ExchangeInfo("localhost", 10001, ["MDF-OME1", "BBO10-OME1"])
  gen_info = GeneratorInfo("localhost", 7000, ["TPC"])
  tp = Tickerplant([exchange_info], [gen_info])