from orderclass import OrderEntry, CancelOrder
from collections import OrderedDict
from dataclasses import dataclass


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

  def __new__(cls):
    if not hasattr(cls, 'instance'):
      cls.instance = super(TradeIDGenerator, cls).__new__(cls)
      cls.trade_id = 0
    return cls.instance

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
  price: int
  volume: int
  buyer_mpid: str
  buyer_order_id: str
  seller_mpid: str
  seller_order_id: str
  trade_id: str


@dataclass
class PriceLevel:
  price: int
  bids: [Order]
  bid_total_volume: int
  bid_total_orders: int
  asks: [Order]
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


class OrderBook:

  def __init__(self, symbol: str, timer: Timer, trade_id_generator: TradeIDGenerator):
    self.symbol = symbol
    self.orderbook = OrderedDict()
    self.timer = timer
    self.trade_id_generator = trade_id_generator
    self.outbound_msgs = []

  def add_order(self, order):
    if order.price not in self.orderbook:
      self.orderbook[order.price] = PriceLevel(price=order.price, bids=[], bid_total_volume=0, bid_total_orders=0, asks=[], ask_total_volume=0, ask_total_orders=0)

    if order.side == Side.BUY:
      if self.orderbook[order.price].ask_total_orders > 0:
        while self.orderbook[order.price].ask_total_orders > 0:
          if order.volume <= 0:
            break

          if order.volume >= self.orderbook[order.price].asks[0].volume:
            trade_msg = TradeMessage(
              timestamp=self.timer.get_time(),
              price=order.price,
              volume=self.orderbook[order.price].asks[0].volume,
              buyer_mpid=order.mpid,
              buyer_order_id=order.mpid_orderid,
              seller_mpid=self.orderbook[order.price].asks[0].mpid,
              seller_order_id=self.orderbook[order.price].asks[0].mpid_orderid,
              trade_id=self.trade_id_generator.generate_trade_id()
            )
            self.outbound_msgs.append(trade_msg)
            order.volume -= self.orderbook[order.price].asks[0].volume
            self.orderbook[order.price].ask_total_volume -= self.orderbook[order.price].asks[0].volume
            self.orderbook[order.price].ask_total_orders -= 1
            self.orderbook[order.price].asks.pop(0)
          else:
            trade_msg = TradeMessage(
              timestamp=self.timer.get_time(),
              price=order.price,
              volume=order.volume,
              buyer_mpid=order.mpid,
              buyer_order_id=order.mpid_orderid,
              seller_mpid=self.orderbook[order.price].asks[0].mpid,
              seller_order_id=self.orderbook[order.price].asks[0].mpid_orderid,
              trade_id=self.trade_id_generator.generate_trade_id()
            )
            self.outbound_msgs.append(trade_msg)
            self.orderbook[order.price].asks[0].volume -= order.volume
            self.orderbook[order.price].ask_total_volume -= order.volume
            order.volume = 0

        if order.volume > 0:
          self.orderbook[order.price].add_order(order)
      else:
        self.orderbook[order.price].add_order(order)
    elif order.side == Side.SELL:
      if self.orderbook[order.price].bid_total_orders > 0:
        while self.orderbook[order.price].bid_total_orders > 0:
          if order.volume <= 0:
            break

          if order.volume >= self.orderbook[order.price].bids[0].volume:
            trade_msg = TradeMessage(
              timestamp=self.timer.get_time(),
              price=order.price,
              volume=self.orderbook[order.price].bids[0].volume,
              buyer_mpid=self.orderbook[order.price].bids[0].mpid,
              buyer_order_id=self.orderbook[order.price].bids[0].mpid_orderid,
              seller_mpid=order.mpid,
              seller_order_id=order.mpid_orderid,
              trade_id=self.trade_id_generator.generate_trade_id()
            )
            self.outbound_msgs.append(trade_msg)
            order.volume -= self.orderbook[order.price].bids[0].volume
            self.orderbook[order.price].bid_total_volume -= self.orderbook[order.price].bids[0].volume
            self.orderbook[order.price].bid_total_orders -= 1
            self.orderbook[order.price].bids.pop(0)
          else:
            trade_msg = TradeMessage(
              timestamp=self.timer.get_time(),
              price=order.price,
              volume=order.volume,
              buyer_mpid=self.orderbook[order.price].bids[0].mpid,
              buyer_order_id=self.orderbook[order.price].bids[0].mpid_orderid,
              seller_mpid=order.mpid,
              seller_order_id=order.mpid_orderid,
              trade_id=self.trade_id_generator.generate_trade_id()
            )
            self.outbound_msgs.append(trade_msg)
            self.orderbook[order.price].bids[0].volume -= order.volume
            self.orderbook[order.price].bid_total_volume -= order.volume
            order.volume = 0

        if order.volume > 0:
          self.orderbook[order.price].add_order(order)
      else:
        self.orderbook[order.price].add_order(order)


  def cancel_order(self, order_id):
    pass

  def modify_order(self, order_id, new_order):
    pass




class OrderMatchingEngine:
  def __init__(self, symbols: [str], timer: Timer):
    self.timer = timer

    self.orderbooks = {}
    for symbol in symbols:
      self.orderbooks[symbol] = OrderBook(symbol, self.timer, TradeIDGenerator())


  def process_order(self, order: bytearray):
    switch = {
      b'O': self.process_order_entry,
      b'C': self.process_cancel_order
    }

    order_type = bytes(order[0:1])
    switch[order_type](order)

  def process_order_entry(self, order: bytearray):
    order_entry = OrderEntry("", "", "", "", 0, 0, "")
    order_entry.deserialize(order)
    order = Order(order_entry.order_id, order_entry.ticker, order_entry.price, order_entry.size, order_entry.mpid, order_entry.order_id, self.timer.get_time(), order_entry.side)
    ob = self.orderbooks[order_entry.ticker]
    ob.add_order(order)

  def process_cancel_order(self, order: bytearray):
    pass