from orderclass import *
from sortedcontainers import SortedDict
from dataclasses import dataclass
import zmq
import multiprocessing


class Timer(object):
  time: int = 0

  def __new__(cls):
    if not hasattr(cls, 'instance'):
      cls.instance = super(Timer, cls).__new__(cls)
      cls.time = 0
    return cls.instance

  def get_time(cls):
    cls.time += 1
    return cls.time


class TradeIDGenerator:
  trade_id: int = 0

  # def __new__(cls):
  #   if not hasattr(cls, 'instance'):
  #     cls.instance = super(TradeIDGenerator, cls).__new__(cls)
  #     cls.trade_id = 0
  #   return cls.instance

  def generate_trade_id(cls):
    cls.trade_id += 1
    return str(cls.trade_id)


class ExchangeOrderIDGenerator:
  trade_id: int = 0

  def __new__(cls):
    if not hasattr(cls, 'instance'):
      cls.instance = super(ExchangeOrderIDGenerator, cls).__new__(cls)
      cls.trade_id = 0
    return cls.instance

  def generate_trade_id(cls):
    cls.trade_id += 1
    return str(cls.trade_id)


class Side:
  BUY = "B"
  SELL = "S"


@dataclass
class Order:
  order_id: str
  symbol: str
  price: int
  volume: int
  mpid: str
  mpid_orderid: str
  timestamp: int
  side: Side


@dataclass
class TradeMessage:
  timestamp: int
  ticker:str
  price: int
  volume: int
  buyer_mpid: str
  buyer_order_id: str
  buyer_exchange_order_id: str
  seller_mpid: str
  seller_order_id: str
  seller_exchange_order_id: str
  trade_id: str

  def serialize(self):
    arr = bytearray()
    arr.extend(self.timestamp.to_bytes(8, 'big'))
    arr.extend(self.ticker.encode())
    arr.extend(self.price.to_bytes(4, 'big'))
    arr.extend(self.volume.to_bytes(4, 'big'))
    arr.extend(self.buyer_mpid.encode())
    arr.extend(self.buyer_order_id.encode())
    arr.extend(self.seller_mpid.encode())
    arr.extend(self.seller_order_id.encode())
    arr.extend(self.trade_id.encode())
    return arr


  def deserialize(self, arr: bytearray):
    self.timestamp = int.from_bytes(arr[0:8], 'big')
    self.ticker = arr[8:16].decode()
    self.price = int.from_bytes(arr[16:20], 'big')
    self.volume = int.from_bytes(arr[20:24], 'big')
    self.buyer_mpid = arr[24:32].decode()
    self.buyer_order_id = arr[32:42].decode()
    self.seller_mpid = arr[42:50].decode()


@dataclass
class PriceLevel:
  price: int
  bids: list[Order]
  bid_total_volume: int
  bid_total_orders: int
  asks: list[Order]
  ask_total_volume: int
  ask_total_orders: int

  def add_order(self, order: Order):
    if order.side == Side.BUY:
      assert len(self.asks) == 0, "Cannot add buy order to ask side"
      self.bids.append(order)
      self.bid_total_volume += order.volume
      self.bid_total_orders += 1
    elif order.side == Side.SELL:
      assert len(self.bids) == 0, "Cannot add sell order to bid side"
      self.asks.append(order)
      self.ask_total_volume += order.volume
      self.ask_total_orders += 1


class PriceLevelList():
  def __init__(self, min_price: int, max_price: int, *args, **kwargs):
    assert min_price <= max_price, "Min price must be less than or equal to max price"
    self.price_level_list = [PriceLevel(price=price, bids=[], bid_total_volume=0, bid_total_orders=0, asks=[], ask_total_volume=0, ask_total_orders=0) for price in range(min_price, max_price+1)]
    self.min_price = min_price
    self.max_price = max_price

  def __getitem__(self, key):
    if key < self.min_price:
      raise ValueError(f"Accessed price: {key}, but price levels start at {self.min_price}")
    if key > self.max_price:
      raise IndexError("Price level does not exist: " + str(key))
    return self.price_level_list[key-self.min_price]

  def __setitem__(self, key, value):
    if key < self.min_price:
      raise ValueError(f"Accessed price: {key}, but price levels start at {self.min_price}")
    if key > self.max_price:
      raise IndexError("Price level does not exist: " + str(key))
    self.price_level_list[key-self.min_price] = value

  def __delitem__(self, key):
    del self.price_level_list[key-1]

  def __iter__(self):
    return iter(self.price_level_list)

  def __len__(self):
    return len(self.price_level_list)

  def __repr__(self):
    return repr(self.price_level_list)

  def __str__(self):
    return str(self.price_level_list)


class OrderBook:

  def __init__(self, ticker_configuration: TickerConfiguration, timer: Timer, trade_id_generator: TradeIDGenerator):
    self.symbol = ticker_configuration.symbol
    self.timer = timer
    self.trade_id_generator = trade_id_generator
    self.outbound_trade_msgs = []
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

  def ouch_outbound_msg_from_trade(self, trade: TradeMessage) -> list[OrderExecutedOutbound]:
    order_executed_outbound_msgs = []
    order_executed_outbound_msgs.append(OrderExecutedOutbound(
      order_type="E",
      mpid=trade.buyer_mpid,
      order_id=trade.buyer_order_id,
      timestamp=trade.timestamp,
      ticker=trade.ticker,
      buyer_mpid=trade.buyer_mpid,
      seller_mpid=trade.seller_mpid,
      trade_id=trade.trade_id,
      price=trade.price,
      size=trade.volume
    ))
    order_executed_outbound_msgs.append(OrderExecutedOutbound(
      order_type="E",
      mpid=trade.seller_mpid,
      order_id=trade.seller_order_id,
      timestamp=trade.timestamp,
      ticker=trade.ticker,
      buyer_mpid=trade.buyer_mpid,
      seller_mpid=trade.seller_mpid,
      trade_id=trade.trade_id,
      price=trade.price,
      size=trade.volume
    ))
    return order_executed_outbound_msgs


  def itch_outbound_msg_from_trade(self, trade: TradeMessage) -> ITCH_Trade:
    itch_trade = ITCH_Trade(
      order_type="T",
      ticker=trade.ticker,
      timestamp=trade.timestamp,
      price=trade.price,
      shares=trade.volume,
      buyer_exchange_order_id=trade.buyer_exchange_order_id,
      seller_exchange_order_id=trade.seller_exchange_order_id,
      exchange_trade_id=trade.trade_id
    )
    return itch_trade


  def add_order(self, order: Order) -> tuple[Order, list[OrderExecutedOutbound], list]:
    """Add order to orderbook and execute trades if possible. Return leftover order and outbound messages.

    Args:
      order (Order): Order to add to orderbook

    Returns:
      A tuple containing the leftover order and a list of outbound messages to be sent to the clients.
    """
    order_executed_outbound_msgs = []
    itch_executed_outbound_msgs = []
    leftover_order = None
    if order.side == Side.BUY:
      while order.price >= self.best_ask and order.volume > 0: # Iterate through price levels
        while self.orderbook[self.best_ask].ask_total_orders > 0: # Iterate through orders at price level
          if order.volume <= 0:
            break

          resting_ask_order = self.orderbook[self.best_ask].asks[0]
          if order.volume >= resting_ask_order.volume: # Found trade, incoming volume greater
            trade_msg = TradeMessage(
              timestamp=self.timer.get_time(),
              ticker=self.symbol,
              price=self.best_ask,
              volume=resting_ask_order.volume,
              buyer_mpid=order.mpid,
              buyer_order_id=order.mpid_orderid,
              buyer_exchange_order_id=order.order_id,
              seller_mpid=resting_ask_order.mpid,
              seller_order_id=resting_ask_order.mpid_orderid,
              seller_exchange_order_id=resting_ask_order.order_id,
              trade_id=self.trade_id_generator.generate_trade_id()
            )
            self.outbound_trade_msgs.append(trade_msg)
            order_executed_outbound_msgs.extend(self.ouch_outbound_msg_from_trade(trade_msg))
            itch_executed_outbound_msgs.append(self.itch_outbound_msg_from_trade(trade_msg))

            order.volume -= resting_ask_order.volume
            self.orderbook[self.best_ask].ask_total_volume -= resting_ask_order.volume
            self.orderbook[self.best_ask].ask_total_orders -= 1
            self.orderbook[self.best_ask].asks.pop(0)
            self.orderid_map[resting_ask_order.order_id] = None

            self.total_ask_orders -= 1
            self.total_ask_volume -= trade_msg.volume
          else:
            trade_msg = TradeMessage(
              timestamp=self.timer.get_time(),
              ticker=self.symbol,
              price=self.best_ask,
              volume=order.volume,
              buyer_mpid=order.mpid,
              buyer_order_id=order.mpid_orderid,
              buyer_exchange_order_id=order.order_id,
              seller_mpid=resting_ask_order.mpid,
              seller_order_id=resting_ask_order.mpid_orderid,
              seller_exchange_order_id=resting_ask_order.order_id,
              trade_id=self.trade_id_generator.generate_trade_id()
            )
            self.outbound_trade_msgs.append(trade_msg)
            order_executed_outbound_msgs.extend(self.ouch_outbound_msg_from_trade(trade_msg))
            itch_executed_outbound_msgs.append(self.itch_outbound_msg_from_trade(trade_msg))

            resting_ask_order.volume -= order.volume
            self.orderbook[self.best_ask].ask_total_volume -= order.volume
            order.volume = 0

        # Loop through price levels to find next best ask
        while self.orderbook[self.best_ask].ask_total_orders == 0 and self.best_ask < self.max_price:
          self.best_ask += 1

      if order.volume > 0: # If there is still volume left, add to orderbook
        self.orderbook[order.price].add_order(order)
        self.total_bid_orders += 1
        self.total_bid_volume += order.volume
        self.orderid_map[order.order_id] = order
        if order.price > self.best_bid:
          self.best_bid = order.price
        leftover_order = order
        itch_add_order = ITCH_AddOrder("A", order.symbol, order.timestamp, order.order_id, "B" if order.side == Side.BUY else "S", order.price, order.volume)
        itch_executed_outbound_msgs.append(itch_add_order)

    elif order.side == Side.SELL:
      while order.price <= self.best_bid and order.volume > 0:
        while self.orderbook[self.best_bid].bid_total_orders > 0:
          if order.volume <= 0:
            break

          resting_bid_order = self.orderbook[self.best_bid].bids[0]
          if order.volume >= resting_bid_order.volume:
            trade_msg = TradeMessage(
              timestamp=self.timer.get_time(),
              ticker=self.symbol,
              price=self.best_bid,
              volume=resting_bid_order.volume,
              buyer_mpid=resting_bid_order.mpid,
              buyer_order_id=resting_bid_order.mpid_orderid,
              buyer_exchange_order_id=resting_bid_order.order_id,
              seller_mpid=order.mpid,
              seller_order_id=order.mpid_orderid,
              seller_exchange_order_id=order.order_id,
              trade_id=self.trade_id_generator.generate_trade_id()
            )
            self.outbound_trade_msgs.append(trade_msg)
            order_executed_outbound_msgs.extend(self.ouch_outbound_msg_from_trade(trade_msg))
            itch_executed_outbound_msgs.append(self.itch_outbound_msg_from_trade(trade_msg))

            order.volume -= resting_bid_order.volume
            self.orderbook[self.best_bid].bid_total_volume -= resting_bid_order.volume
            self.orderbook[self.best_bid].bid_total_orders -= 1
            self.orderbook[self.best_bid].bids.pop(0)
            self.orderid_map[resting_bid_order.order_id] = None

            self.total_bid_orders -= 1
            self.total_bid_volume -= trade_msg.volume
          else:
            trade_msg = TradeMessage(
              timestamp=self.timer.get_time(),
              ticker=self.symbol,
              price=self.best_bid,
              volume=order.volume,
              buyer_mpid=resting_bid_order.mpid,
              buyer_order_id=resting_bid_order.mpid_orderid,
              buyer_exchange_order_id=resting_bid_order.order_id,
              seller_mpid=order.mpid,
              seller_order_id=order.mpid_orderid,
              seller_exchange_order_id=order.order_id,
              trade_id=self.trade_id_generator.generate_trade_id()
            )
            self.outbound_trade_msgs.append(trade_msg)
            order_executed_outbound_msgs.extend(self.ouch_outbound_msg_from_trade(trade_msg))
            itch_executed_outbound_msgs.append(self.itch_outbound_msg_from_trade(trade_msg))

            resting_bid_order.volume -= order.volume
            self.orderbook[self.best_bid].bid_total_volume -= order.volume
            order.volume = 0

        while self.orderbook[self.best_bid].bid_total_orders == 0 and self.best_bid > self.min_price:
          self.best_bid -= 1

      if order.volume > 0:
        self.orderbook[order.price].add_order(order)
        self.total_ask_orders += 1
        self.total_ask_volume += order.volume
        self.orderid_map[order.order_id] = order
        if order.price < self.best_ask:
          self.best_ask = order.price
        leftover_order = order
        itch_add_order = ITCH_AddOrder("A", order.symbol, order.timestamp, order.order_id, "B" if order.side == Side.BUY else "S", order.price, order.volume)
        itch_executed_outbound_msgs.append(itch_add_order)

    if self.total_ask_orders == 0:
      self.best_ask = self.max_price

    if self.total_bid_orders == 0:
      self.best_bid = self.min_price

    return (leftover_order, order_executed_outbound_msgs, itch_executed_outbound_msgs)


  def cancel_order(self, order_id: str) -> tuple[Order, list[OrderCanceledOutbound], list[ITCH_OrderCancel]]:
    # TODO: Optimize O(n) to O(1)
    order = self.orderid_map.get(order_id, None)
    if order is None:
      return (None, [], [])
    if order.side == Side.BUY:
      self.total_bid_orders -= 1
      self.total_bid_volume -= order.volume
      self.orderbook[order.price].bid_total_orders -= 1
      self.orderbook[order.price].bid_total_volume -= order.volume
      self.orderbook[order.price].bids.remove(order)
    elif order.side == Side.SELL:
      self.total_ask_orders -= 1
      self.total_ask_volume -= order.volume
      self.orderbook[order.price].ask_total_orders -= 1
      self.orderbook[order.price].ask_total_volume -= order.volume
      self.orderbook[order.price].asks.remove(order)

    self.orderid_map[order_id] = None
    if order.price == self.best_bid:
      while self.orderbook[self.best_bid].bid_total_orders == 0 and self.best_bid > self.min_price:
        self.best_bid -= 1

    if order.price == self.best_ask:
      while self.orderbook[self.best_ask].ask_total_orders == 0 and self.best_ask < self.max_price:
        self.best_ask += 1

    ouch_cancel = \
    OrderCanceledOutbound(
      order_type="C",
      mpid=order.mpid,
      order_id=order.mpid_orderid,
      ticker=order.symbol,
      timestamp=self.timer.get_time(),
      decremented_shares=order.volume,
      reason="U"
    )
    itch_order_cancel = ITCH_OrderCancel("C", ouch_cancel.ticker, ouch_cancel.timestamp, order.order_id, ouch_cancel.decremented_shares)
    return (order, [ouch_cancel], [itch_order_cancel])

  def modify_order(self, order_id, new_order):
    # TODO: Implement
    pass


  def __str__(self) -> str:
    lines = [f"---{self.symbol}---", "Price: Orders, Volume", "---------------------"]
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


  def info(self) -> str:
    return f"Symbol: {self.symbol}, Best Bid: {self.best_bid}, Best Ask: {self.best_ask}, Total Bid Orders: {self.total_bid_orders}, Total Bid Volume: {self.total_bid_volume}, Total Ask Orders: {self.total_ask_orders}, Total Ask Volume: {self.total_ask_volume}"






class OrderMatchingEngine:
  def __init__(self, symbols: list[TickerConfiguration], timer: Timer, exchange_order_id_generator: ExchangeOrderIDGenerator):
    self.timer = timer
    self.exchange_order_id_generator = exchange_order_id_generator

    self.orderbooks = {}
    for symbol_config in symbols:
      self.orderbooks[symbol_config.symbol] = OrderBook(symbol_config, self.timer, TradeIDGenerator())

    self.exchange_orderid_to_ticker_map = {}
    self.orderid_to_exchange_orderid_map = {}
    self.ouch_inbound_queue = []
    self.ouch_outbound_queue = []
    self.mdf_outbound_queue = []

    context = zmq.Context()
    # Publisher for sending out
    self.outbound_socket = context.socket(zmq.PUB)
    self.outbound_socket.bind("tcp://*:8001") # TODO: Refactor
    self.outbound_topic = "ENTRY-OME1"

    # Server for receiving incoming orders
    self.inbound_socket = context.socket(zmq.PULL)
    self.inbound_socket.bind("tcp://*:9001") # TODO: Refactor

    # Publisher for sending market data
    context = zmq.Context()
    self.market_data_socket = context.socket(zmq.PUB)
    self.market_data_socket.bind("tcp://*:10001") # TODO: Refactor
    self.market_data_topic = "MDF-OME1"
    self.bbo_topic = "BBO5-OME1"


  def run(self):
    # Scan for incoming, write to orderbook
    # orderbook process processes order
    # send outbound messages
    while True:
      self.get_inbound_msgs_daemon()
      # for ticker in self.orderbooks:
      #   self.get_outbound_msgs(ticker)
      self.send_market_data()
      self.send_outbound_msgs()

  def process_order(self, order: bytearray) -> tuple[list[bytearray], list[bytearray]]:
    switch = {
      b'O': self.process_order_entry,
      b'C': self.process_cancel_order
    }

    order_type = bytes(order[0:1])
    print(f"Processing order: {order_type}") # TODO: Log
    if order_type not in switch:
      return self.process_invalid_entry(order, 'I')
    return switch[order_type](order)


  def process_order_entry(self, order: bytearray) -> tuple[list[bytearray], list[bytearray]]:
    def itch_order_from_order_accept(order: Order) -> tuple[bytearray]:
      itch_order_accepted = ITCH_AddOrder(
        order_type="A",
        ticker=order.symbol,
        timestamp=order.timestamp,
        exchange_order_id=order.order_id,
        side="B" if order.side == Side.BUY else "S",
        price=order.price,
        shares=order.volume
      )
      return [itch_order_accepted]

    itch_messages = []
    order_entry = OrderEntry("", "", "", "", "", 0, 0)
    order_entry.deserialize(order)
    # TODO: Check if order_entry is valid?
    accepted_order_outbound = OrderAcceptedOutbound("A", order_entry.mpid, order_entry.order_id, order_entry.ticker, self.timer.get_time(), order_entry.side, order_entry.price, order_entry.size)
    order = Order(self.exchange_order_id_generator.generate_trade_id(), order_entry.ticker, order_entry.price, order_entry.size, order_entry.mpid, order_entry.order_id, self.timer.get_time(), order_entry.side)
    # itch_messages.extend(itch_order_from_order_accept(order))
    ob = self.orderbooks[order_entry.ticker]
    leftover_order, trade_messages, itch_msgs = ob.add_order(order)
    itch_messages.extend(itch_msgs)
    if leftover_order is not None:
      self.orderid_to_exchange_orderid_map[order_entry.order_id] = leftover_order.order_id
      self.exchange_orderid_to_ticker_map[leftover_order.order_id] = order_entry.ticker
      print(f"Order {leftover_order.order_id} added to orderbook with volume {leftover_order.volume} at price {leftover_order.price}") # TODO: Log
    else:
      print(f"Order {order.order_id} fully traded") # TODO: Log
      self.exchange_orderid_to_ticker_map[order.order_id] = None

    outbound_messages = []
    outbound_messages.append(accepted_order_outbound)
    outbound_messages.extend(trade_messages)
    return [msg.serialize() for msg in outbound_messages], [msg.serialize() for msg in itch_messages]



  def process_cancel_order(self, order: bytearray) -> tuple[list[bytearray], list[bytearray]]:
    outbound_messages = []
    cancel_order = CancelOrder("", "", "", "")
    cancel_order.deserialize(order)
    if cancel_order.order_id not in self.orderid_to_exchange_orderid_map:
      print(f"Order ID {cancel_order.order_id} not found")
      return self.process_invalid_entry(order, 'N')
    exchange_oid = self.orderid_to_exchange_orderid_map[cancel_order.order_id]
    ticker = self.exchange_orderid_to_ticker_map.get(exchange_oid, None)
    if ticker is None:
      print(f"Order ID {cancel_order.order_id} has been completed previously")
      return self.process_invalid_entry(order, 'C')
    ob = self.orderbooks[ticker]
    canceled_order, ouch_messages, itch_messages = ob.cancel_order(exchange_oid)
    self.exchange_orderid_to_ticker_map[cancel_order.order_id] = None
    print(f"Order {cancel_order.order_id} cancelled") # TODO: Log

    return [msg.serialize() for msg in ouch_messages], [msg.serialize() for msg in itch_messages]


  def process_invalid_entry(self, order: bytearray, reason: str) -> tuple[list[bytearray], list[bytearray]]:
    print(f"Invalid: {order}") # TODO: Log
    reject_order = OrderRejectedOutbound(
      order_type="J",
      mpid=order[1:11].decode().strip(),
      order_id=order[11:21].decode().strip(),
      ticker=order[21:29].decode().strip(),
      timestamp=self.timer.get_time(),
      reason=reason
    )
    return [reject_order.serialize()], []



  def send_market_data(self) -> None:
    for itch_msg in self.mdf_outbound_queue:
      print(f"Sending market data: {itch_msg}")
      actual_msg = bytearray(self.market_data_topic.encode())
      actual_msg.extend(b"@")
      actual_msg.extend(itch_msg)
      self.market_data_socket.send(actual_msg)
    self.mdf_outbound_queue = []
      # match ouch_msg[0]:
      #   case 65: # A - Order Accepted
      #     pass
      #   case 67: # C - Order Canceled
      #     pass
      #   case 69: # E - Order Executed
      #     pass
      #   case 74: # J - Order Rejected
      #     pass


  def get_inbound_msgs_daemon(self):
    # print("Scanning inbound messages") # TODO: Log
    try:
      message = self.inbound_socket.recv(flags=zmq.NOBLOCK)
      print(f"Received message: {message}") # TODO: Log
      outbound_messages, itch_messages = self.process_order(message)
      self.mdf_outbound_queue.extend(itch_messages)
      self.ouch_outbound_queue.extend(outbound_messages)
    except zmq.error.Again:
      pass


  def send_outbound_msgs(self):
    for msg in self.ouch_outbound_queue:
      print(f"Sending message: {msg}") # TODO: Log
      actual_msg = bytearray(self.outbound_topic.encode())
      actual_msg.extend(b"@")
      actual_msg.extend(msg)

      self.outbound_socket.send(actual_msg)
      # self.outbound_socket.send(msg)
    self.ouch_outbound_queue = []



if __name__ == "__main__":
  timer = Timer()
  ticker_config = TickerConfiguration("TPCF1010", 1, 200, 1, 2, "cash", 1)
  matching_engine = OrderMatchingEngine([ticker_config], timer, ExchangeOrderIDGenerator())
  matching_engine.run()
  # try:
  #   while True:
  #     matching_engine.get_inbound_msgs_daemon()
  #     for ticker in matching_engine.orderbooks:
  #       matching_engine.get_outbound_msgs(ticker)
  #     matching_engine.send_outbound_msgs()
  # except KeyboardInterrupt:
  #   print("Exiting")