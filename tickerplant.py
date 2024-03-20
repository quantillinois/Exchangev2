import zmq
import time
import multiprocessing as mp
from dataclasses import dataclass
from orderclass import *
from matching_engine import PriceLevel, PriceLevelList, Order, Timer
import queue
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
    self.best_bid: int = self.min_price
    self.best_ask: int = self.max_price
    self.orderbook = PriceLevelList(self.min_price, self.max_price)
    self.orderid_map = {}

    self.total_bid_orders = 0
    self.total_ask_orders = 0
    self.total_bid_volume = 0
    self.total_ask_volume = 0

  def process_msg(self, msg: bytearray):
    msg_type = msg[0]
    match msg_type:
      case 65: # A
        # print(f"Received A")
        add_order = ITCH_AddOrder()
        add_order.deserialize(msg)
        self.add_order(add_order)
      case 67: # C
        # print(f"Received C")
        cancel_order = ITCH_OrderCancel()
        cancel_order.deserialize(msg)
        self.cancel_order(cancel_order)
      case 84: # T
        # print(f"Received T")
        trade_order = ITCH_Trade()
        trade_order.deserialize(msg)
        self.trade_order(trade_order)
      case _:
        print(f"Unknown message type: {msg[0]}")


  def add_order(self, itch_order: ITCH_AddOrder):
    order = Order(itch_order.exchange_order_id, itch_order.ticker, itch_order.price, itch_order.shares, "", "", itch_order.timestamp, itch_order.side)
    if itch_order.side == "B":
      self.total_bid_orders += 1
      self.total_bid_volume += order.volume
      self.orderbook[order.price].add_order(order)
      if order.price > self.best_bid and order.price < self.best_ask: # TODO: Check if this is correct
        self.best_bid = order.price
    elif itch_order.side == "S":
      self.total_ask_orders += 1
      self.total_ask_volume += order.volume
      self.orderbook[order.price].add_order(order)
      if order.price < self.best_ask and order.price > self.best_bid: # TODO: Check if this is correct
        self.best_ask = order.price

    self.orderid_map[order.order_id] = order


  def cancel_order(self, itch_order: ITCH_OrderCancel):
    order = self.orderid_map.get(itch_order.exchange_order_id, None)
    if order is None:
      print(f"Order ID {itch_order.exchange_order_id} not found") #TODO: Log
      return
    if order.side == "B":
      self.total_bid_orders -= 1
      self.total_bid_volume -= order.volume
      self.orderbook[order.price].bid_total_orders -= 1
      self.orderbook[order.price].bid_total_volume -= order.volume
      self.orderbook[order.price].bids.remove(order)
    elif order.side == "S":
      self.total_ask_orders -= 1
      self.total_ask_volume -= order.volume
      self.orderbook[order.price].ask_total_orders -= 1
      self.orderbook[order.price].ask_total_volume -= order.volume
      self.orderbook[order.price].asks.remove(order)

    self.orderid_map[itch_order.exchange_order_id] = None
    if order.price == self.best_bid:
      while self.orderbook[self.best_bid].bid_total_orders == 0 and self.best_bid > self.min_price:
        self.best_bid -= 1

    if order.price == self.best_ask:
      while self.orderbook[self.best_ask].ask_total_orders == 0 and self.best_ask < self.max_price:
        self.best_ask += 1


  def trade_order(self, itch_order: ITCH_Trade):
    buy_order = self.orderid_map.get(itch_order.buyer_exchange_order_id, None)
    sell_order = self.orderid_map.get(itch_order.seller_exchange_order_id, None)
    if buy_order is None and sell_order is None:
      if buy_order is None:
        print(f"Order ID {itch_order.buyer_exchange_order_id} not found")
      if sell_order is None:
        print(f"Order ID {itch_order.seller_exchange_order_id} not found")
      return

    # TODO only parse for whichever one is on the books
    if buy_order is not None:
      if buy_order.volume - itch_order.shares == 0:
        self.cancel_order(ITCH_OrderCancel("C", "", 0, buy_order.order_id, 0))
      else:
        buy_order.volume -= itch_order.shares
        self.orderbook[buy_order.price].bid_total_volume -= itch_order.shares
        self.total_bid_volume -= itch_order.shares
    elif sell_order is not None:
      if sell_order.volume - itch_order.shares == 0:
        self.cancel_order(ITCH_OrderCancel("C", "", 0, sell_order.order_id, 0))
      else:
        sell_order.volume -= itch_order.shares
        self.orderbook[sell_order.price].ask_total_volume -= itch_order.shares
        self.total_ask_volume -= itch_order.shares


  def __str__(self) -> str:
    lines = [f"---{self.ticker_configuration.symbol}---", "Price: Orders, Volume", "---------------------"]
    i = 4
    while i >= 0:
      if self.best_ask + i > self.max_price:
        i-=1
        continue
      best_ask_char = "A" if i == 0 else " "
      lines.append(f"{best_ask_char}{self.best_ask + i}: {self.orderbook[self.best_ask + i].ask_total_orders}, {self.orderbook[self.best_ask + i].ask_total_volume}")
      i -= 1

    i = 0
    while i < 5:
      if self.best_bid - i < self.min_price:
        break
      best_bid_char = "B" if i == 0 else " "
      lines.append(f"{best_bid_char}{self.best_bid - i}: {self.orderbook[self.best_bid - i].bid_total_orders}, {self.orderbook[self.best_bid - i].bid_total_volume}")
      i += 1

    return "\n".join(lines)


class Tickerplant():
  def __init__(self, port: int, exchange_infos: list[ExchangeInfo], generator_infos: list[GeneratorInfo], ticker_infos: list[TickerConfiguration], timer: Timer):
    self.port = port
    self.timer = timer
    self.exchange_infos = exchange_infos
    self.generator_infos = generator_infos
    self.orderbooks = {}
    self.ticker_infos = ticker_infos
    self.ticker_info_map = {}
    for ticker_info in ticker_infos:
      self.ticker_info_map[ticker_info.symbol] = ticker_info
      self.orderbooks[ticker_info.symbol] = ITCH_Orderbook(ticker_info)

    self.outbound_messages : mp.Queue[tuple[str, bytearray]] = mp.Queue() # Topic, msg
    self.run()

  def run(self):
    processes = []
    print("Starting exchange connection")
    for exchange_info in self.exchange_infos:
      # for topic in exchange_info.topics:
      process = mp.Process(target=self.exchange_daemon, args=(exchange_info.ip_addr, exchange_info.port, exchange_info.topics))
      process.start()
      processes.append(process)

    print("Starting generator connection")
    for generator_info in self.generator_infos:
      # for topic in generator_info.topics:
      process = mp.Process(target=self.generator_daemon, args=(generator_info.ip_addr, generator_info.port, generator_info.topics))
      process.start()
      processes.append(process)

    print("Starting tickerplant")
    process = mp.Process(target=self.tickerplant_daemon, args=(self.port,))
    process.start()
    processes.append(process)

    for process in processes:
      process.join()


  def tickerplant_daemon(self, port: int):
    def concatenate_topic(topic: str, outbound_msg: bytearray) -> bytearray:
      data = bytearray()
      data.extend(topic.encode("ascii"))
      data.extend(b"@")
      data.extend(outbound_msg)
      return data

    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(f"tcp://*:{port}")

    while True:
      try:
        tup = self.outbound_messages.get_nowait()
        if tup is None:
          continue
        topic, msg = tup
        msg = concatenate_topic(topic, msg)
        print(f"Sending message: {topic}")
        socket.send(msg)
      except queue.Empty:
        pass
      time.sleep(0.005)



  def exchange_daemon(self, ip_addr: str, port: int, topics: list[str]):
    def parse_itch_msg(msg: str) -> list[tuple[str, bytearray]]:
      def parse_market_data(msg: str):
        byte_arr = bytearray(msg, "ascii")
        msg_type = byte_arr[0]
        match msg_type:
          case 65 | 67 | 84: # A, C, T
            ticker = byte_arr[1:9].decode("ascii").strip() # TODO: Make sure this is the case ALWAYS, don't hardcode
            self.orderbooks[ticker].process_msg(byte_arr)
            return self.orderbooks[ticker]
          case _:
            print(f"Unknown message type: {msg_type}")
            return None

      def create_bbo5(orderbook: ITCH_Orderbook) -> list[tuple[str, bytearray]]:
        # print(f"Sending BBO5")
        bbo5 = MDF_BBO5(
          ticker=orderbook.ticker_configuration.symbol,
          timestamp=self.timer.get_time(), # TODO: WARNING NOT THREAD SAFE
          best_bid_price=orderbook.best_bid,
          best_ask_price=orderbook.best_ask,
          best_bid_volume=orderbook.orderbook[orderbook.best_bid].bid_total_volume,
          best_ask_volume=orderbook.orderbook[orderbook.best_ask].ask_total_volume,
          total_bid_volume=orderbook.total_bid_volume,
          total_ask_volume=orderbook.total_ask_volume,
          top5_bids = {},
          top5_asks = {}
        )

        bid_start = orderbook.best_bid
        if orderbook.best_bid - 5 < orderbook.min_price:
          bid_start = orderbook.min_price + 4
        for price in range(bid_start, bid_start - 5, -1):
          if price < orderbook.min_price:
            bbo5.top5_bids[price] = 0
            continue
          bbo5.top5_bids[price] = orderbook.orderbook[price].bid_total_volume

        ask_start = orderbook.best_ask
        if orderbook.best_ask + 5 > orderbook.max_price:
          ask_start = orderbook.max_price - 4
        for price in range(ask_start, ask_start + 5):
          if price > orderbook.max_price:
            bbo5.top5_asks[price] = 0
            continue
          bbo5.top5_asks[price] = orderbook.orderbook[price].ask_total_volume

        return [(f"{bbo5.ticker}-BBO5", bbo5.serialize())]

      topic, data = msg.split("@", 1)
      # print(f"Topic: {topic}, Data: {data}")
      subject, ome = topic.split("-", 1)
      outbound_msgs = []
      match subject:
        case "MDF":
          print(f"Received MDF from {ome}, Order type: {data[0]}")
          updated_orderbook = parse_market_data(data)
          outbound_msgs.append((f"{updated_orderbook.ticker_configuration.symbol}-ITCH", data.encode()))
          if updated_orderbook is not None:
            outbound_msgs.extend(create_bbo5(updated_orderbook))
        case _:
          print("Unknown message type")

      return outbound_msgs

    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://{ip_addr}:{port}")
    for topic in topics:
      socket.setsockopt_string(zmq.SUBSCRIBE, topic)
    outbound_messages = []

    try:
      while True:
        try:
          msg = socket.recv_string(flags=zmq.NOBLOCK) # TODO: Determine if this should be recv string or just recv
          # print(f"{msg}")
          outbound_messages = parse_itch_msg(msg)
          for outbound_msg in outbound_messages:
            self.outbound_messages.put(outbound_msg)
        except zmq.error.Again:
          # print("No message received")
          pass
        time.sleep(0.005)
    except KeyboardInterrupt:
      print("Exiting")


  def generator_daemon(self, ip_addr: str, port: int, topics: str):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://{ip_addr}:{port}")
    for topic in topics:
      socket.setsockopt_string(zmq.SUBSCRIBE, topic)

    try:
      while True:
        try:
          msg = socket.recv(flags=zmq.NOBLOCK)
          topic, msg = msg.split(b"@", 1)
          self.outbound_messages.put((topic.decode(), msg))
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

  exchange_info = ExchangeInfo("localhost", 10001, ["MDF-OME1", "BBO5-OME1"])
  gen_info = GeneratorInfo("localhost", 7000, ["GEN-TPC"])
  tpcf1010_info = TickerConfiguration("TPCF1010", 1, 200, 1, 2, "cash", 1)
  tp = Tickerplant(11000, [exchange_info], [gen_info], [tpcf1010_info], Timer())