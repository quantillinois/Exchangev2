from orderclass import OrderEntry, CancelOrder, TickerConfiguration
from sortedcontainers import SortedDict
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
  price: int
  volume: int
  buyer_mpid: str
  buyer_order_id: str
  seller_mpid: str
  seller_order_id: str
  trade_id: str

  def serialize(self):
    arr = bytearray()
    arr.extend(self.timestamp.to_bytes(8, 'big'))
    arr.extend(self.price.to_bytes(4, 'big'))
    arr.extend(self.volume.to_bytes(4, 'big'))
    arr.extend(self.buyer_mpid.encode(encoding='ascii'))
    arr.extend(self.buyer_order_id.encode(encoding='ascii'))
    arr.extend(self.seller_mpid.encode(encoding='ascii'))
    arr.extend(self.seller_order_id.encode(encoding='ascii'))
    arr.extend(self.trade_id.encode(encoding='ascii'))
    return arr


  def deserialize(self, arr: bytearray):
    self.timestamp = int.from_bytes(arr[0:8], 'big')
    self.price = int.from_bytes(arr[8:12], 'big')
    self.volume = int.from_bytes(arr[12:16], 'big')
    self.buyer_mpid = arr[16:26].decode().strip()
    self.buyer_order_id = arr[26:36].decode().strip()
    self.seller_mpid = arr[36:46].decode().strip()
    self.seller_order_id = arr[46:56].decode().strip()
    self.trade_id = arr[56:66].decode().strip()


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


class PriceLevelList():
  def __init__(self, min_price: int, max_price: int, *args, **kwargs):
    self.price_level_list = [PriceLevel(price=price, bids=[], bid_total_volume=0, bid_total_orders=0, asks=[], ask_total_volume=0, ask_total_orders=0) for price in range(min_price, max_price+1)]

  def __getitem__(self, key):
    if key < 1:
      raise ValueError("Price levels start at 1")
    return self.price_level_list[key-1]

  def __setitem__(self, key, value):
    if key < 1:
      raise ValueError("Price levels start at 1")
    self.price_level_list[key-1] = value

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
    self.outbound_msgs = []
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

  def add_order(self, order: Order) -> Order:
    output_order = None
    if order.side == Side.BUY:
      while order.price >= self.best_ask and order.volume > 0: # Iterate through price levels
        while self.orderbook[self.best_ask].ask_total_orders > 0: # Iterate through orders at price level
          if order.volume <= 0:
            break

          resting_ask_order = self.orderbook[self.best_ask].asks[0]
          if order.volume >= resting_ask_order.volume: # Found trade, incoming volume greater
            trade_msg = TradeMessage(
              timestamp=self.timer.get_time(),
              price=self.best_ask,
              volume=resting_ask_order.volume,
              buyer_mpid=order.mpid,
              buyer_order_id=order.mpid_orderid,
              seller_mpid=resting_ask_order.mpid,
              seller_order_id=resting_ask_order.mpid_orderid,
              trade_id=self.trade_id_generator.generate_trade_id()
            )
            self.outbound_msgs.append(trade_msg)
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
              price=self.best_ask,
              volume=order.volume,
              buyer_mpid=order.mpid,
              buyer_order_id=order.mpid_orderid,
              seller_mpid=resting_ask_order.mpid,
              seller_order_id=resting_ask_order.mpid_orderid,
              trade_id=self.trade_id_generator.generate_trade_id()
            )
            self.outbound_msgs.append(trade_msg)
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
        output_order = order

    elif order.side == Side.SELL:
      while order.price <= self.best_bid and order.volume > 0:
        while self.orderbook[self.best_bid].bid_total_orders > 0:
          if order.volume <= 0:
            break

          resting_bid_order = self.orderbook[self.best_bid].bids[0]
          if order.volume >= resting_bid_order.volume:
            trade_msg = TradeMessage(
              timestamp=self.timer.get_time(),
              price=self.best_bid,
              volume=resting_bid_order.volume,
              buyer_mpid=resting_bid_order.mpid,
              buyer_order_id=resting_bid_order.mpid_orderid,
              seller_mpid=order.mpid,
              seller_order_id=order.mpid_orderid,
              trade_id=self.trade_id_generator.generate_trade_id()
            )
            self.outbound_msgs.append(trade_msg)
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
              price=self.best_bid,
              volume=order.volume,
              buyer_mpid=resting_bid_order.mpid,
              buyer_order_id=resting_bid_order.mpid_orderid,
              seller_mpid=order.mpid,
              seller_order_id=order.mpid_orderid,
              trade_id=self.trade_id_generator.generate_trade_id()
            )
            self.outbound_msgs.append(trade_msg)
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
        output_order = order

    if self.total_ask_orders == 0:
      self.best_ask = self.max_price

    if self.total_bid_orders == 0:
      self.best_bid = self.min_price

    return output_order

  def cancel_order(self, order_id: str):
    # TODO: Optimize O(n) to O(1)
    order = self.orderid_map.get(order_id, None)
    if order is None:
      return
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


  def modify_order(self, order_id, new_order):
    # TODO: Implement
    pass


  def __repr__(self) -> str:
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
  def __init__(self, symbols: [TickerConfiguration], timer: Timer):
    self.timer = timer

    self.orderbooks = {}
    for symbol_config in symbols:
      self.orderbooks[symbol_config.symbol] = OrderBook(symbol_config, self.timer, TradeIDGenerator())

    self.orderid_to_ticker_map = {}


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
    output_order = ob.add_order(order)
    if output_order is not None:
      self.orderid_to_ticker_map[output_order.order_id] = order_entry.ticker
      # print(f"Order {output_order.order_id} added to orderbook with volume {output_order.volume} at price {output_order.price}") # TODO: Log
    else:
      # print(f"Order {order.order_id} fully traded") # TODO: Log
      self.orderid_to_ticker_map[order.order_id] = None

  def process_cancel_order(self, order: bytearray):
    cancel_order = CancelOrder("", "", "")
    cancel_order.deserialize(order)
    if cancel_order.order_id not in self.orderid_to_ticker_map:
      print(f"Order ID {cancel_order.order_id} not found")
      return
    ticker = self.orderid_to_ticker_map.get(cancel_order.order_id, None)
    if ticker is None:
      print(f"Order ID {cancel_order.order_id} has been completed previously")
      return
    ob = self.orderbooks[ticker]
    ob.cancel_order(cancel_order.order_id)
    self.orderid_to_ticker_map[cancel_order.order_id] = None
    # print(f"Order {cancel_order.order_id} cancelled") # TODO: Log


  def get_outbound_msgs(self, ticker: str) -> [TradeMessage]:
    msg = self.orderbooks[ticker].outbound_msgs
    self.orderbooks[ticker].outbound_msgs = []
    return msg