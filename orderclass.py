from dataclasses import dataclass
# import bytearray

# Header
  # order_type: str
  # mpid: str
  # order_id: str
  # timestamp: int

@dataclass
class OrderEntry:
  order_type: str
  mpid: str
  order_id: str
  ticker: str
  side: str
  price: int
  size: int

  def serialize(self):
    arr = bytearray()
    arr.extend(self.order_type.encode(encoding='ascii'))

    if len(self.mpid) > 10:
      self.mpid = self.mpid[:10]
    else:
      self.mpid = self.mpid.ljust(10, ' ')
    arr.extend(self.mpid.encode(encoding='ascii'))

    if len(self.order_id) > 10:
      raise ValueError("Order ID must be 10 characters long")
    else:
      self.order_id = self.order_id.ljust(10, ' ')
    arr.extend(self.order_id.encode(encoding='ascii'))

    arr.extend(self.ticker.encode(encoding='ascii'))
    arr.extend(self.side.encode(encoding='ascii'))
    arr.extend(self.price.to_bytes(4, 'big'))
    arr.extend(self.size.to_bytes(4, 'big'))

    return arr

  def deserialize(self, arr: bytearray):
    decoded_arr = arr.decode()
    self.order_type = decoded_arr[0]
    self.mpid = decoded_arr[1:11].strip()
    self.order_id = decoded_arr[11:21].strip()
    self.ticker = decoded_arr[21:29].strip()
    self.side = decoded_arr[29]
    self.price = int.from_bytes(arr[30:34], 'big')
    self.size = int.from_bytes(arr[34:38], 'big') #38


@dataclass
class CancelOrder:
  order_type: str
  mpid: str
  order_id: str
  ticker: str

  def serialize(self):
    arr = bytearray()
    arr.extend(self.order_type.encode(encoding='ascii'))

    if len(self.mpid) > 10:
      self.mpid = self.mpid[:10]
    else:
      self.mpid = self.mpid.ljust(10, ' ')
    arr.extend(self.mpid.encode(encoding='ascii'))

    if len(self.order_id) > 10:
      raise ValueError("Order ID must be at most 10 characters long")
    else:
      self.order_id = self.order_id.ljust(10, ' ')
    arr.extend(self.order_id.encode(encoding='ascii'))

    arr.extend(self.ticker.encode(encoding='ascii'))
    return arr


  def deserialize(self, arr: bytearray):
    decoded_arr = arr.decode()
    self.order_type = decoded_arr[0]
    self.mpid = decoded_arr[1:11].strip()
    self.order_id = decoded_arr[11:21].strip()
    self.ticker = decoded_arr[21:29].strip()

@dataclass
class TickerConfiguration:
  symbol: str
  min_price: int
  max_price: int
  lot_size: int
  decimals: int
  settlement: str
  multiplier: int

### OUCH Outbound messages ###
@dataclass
class OrderAcceptedOutbound:
  order_type: str # A
  mpid: str
  order_id: str
  ticker: str
  timestamp: int
  side: str
  price: int
  size: int

  def serialize(self):
    arr = bytearray()
    arr.extend(self.order_type.encode(encoding='ascii'))

    if len(self.mpid) > 10:
      self.mpid = self.mpid[:10]
    else:
      self.mpid = self.mpid.ljust(10, ' ')
    arr.extend(self.mpid.encode(encoding='ascii'))

    if len(self.order_id) > 10:
      raise ValueError("Order ID must be 10 characters long")
    else:
      self.order_id = self.order_id.ljust(10, ' ')
    arr.extend(self.order_id.encode(encoding='ascii'))

    arr.extend(self.ticker.encode(encoding='ascii'))
    arr.extend(self.timestamp.to_bytes(8, 'big'))
    arr.extend(self.side.encode(encoding='ascii'))
    arr.extend(self.price.to_bytes(4, 'big'))
    arr.extend(self.size.to_bytes(4, 'big'))

    return arr

  def deserialize(self, msg: bytearray):
    decoded_arr = msg.decode()
    self.order_type = decoded_arr[0]
    self.mpid = decoded_arr[1:11].strip()
    self.order_id = decoded_arr[11:21].strip()
    self.ticker = decoded_arr[21:29].strip()
    self.timestamp = int.from_bytes(msg[29:37], 'big')
    self.side = decoded_arr[37]
    self.price = int.from_bytes(msg[38:42], 'big')
    self.size = int.from_bytes(msg[42:46], 'big')


@dataclass
class OrderCanceledOutbound:
  order_type: str # C
  mpid: str
  order_id: str
  ticker: str
  timestamp: int
  decremented_shares: int
  reason: str
  # U - User requested cancel

  def serialize(self) -> bytearray:
    arr = bytearray()
    arr.extend(self.order_type.encode(encoding='ascii'))

    if len(self.mpid) > 10:
      self.mpid = self.mpid[:10]
    else:
      self.mpid = self.mpid.ljust(10, ' ')
    arr.extend(self.mpid.encode(encoding='ascii'))

    if len(self.order_id) > 10:
      raise ValueError("Order ID must be 10 characters long")
    else:
      self.order_id = self.order_id.ljust(10, ' ')
    arr.extend(self.order_id.encode(encoding='ascii'))

    arr.extend(self.ticker.encode(encoding='ascii'))
    arr.extend(self.timestamp.to_bytes(8, 'big'))
    arr.extend(self.decremented_shares.to_bytes(4, 'big'))
    arr.extend(self.reason.encode(encoding='ascii'))

    return arr

  def deserialize(self, msg: bytearray):
    decoded_arr = msg.decode()
    self.order_type = decoded_arr[0]
    self.mpid = decoded_arr[1:11].strip()
    self.order_id = decoded_arr[11:21].strip()
    self.ticker = decoded_arr[21:29].strip()
    self.timestamp = int.from_bytes(msg[29:37], 'big')
    self.decremented_shares = int.from_bytes(msg[37:41], 'big')
    self.reason = decoded_arr[41:42]

@dataclass
class OrderRejectedOutbound:
  order_type: str #J
  mpid: str
  order_id: str
  ticker: str
  timestamp: int
  reason: str
  # I - Invalid order (first char not found)
  # N - Orderid does not exist
  # C - Orderid has already been canceled

  def serialize(self):
    arr = bytearray()
    arr.extend(self.order_type.encode(encoding='ascii'))

    if len(self.mpid) > 10:
      self.mpid = self.mpid[:10]
    else:
      self.mpid = self.mpid.ljust(10, ' ')
    arr.extend(self.mpid.encode(encoding='ascii'))

    if len(self.order_id) > 10:
      raise ValueError("Order ID must be 10 characters long")
    else:
      self.order_id = self.order_id.ljust(10, ' ')
    arr.extend(self.order_id.encode(encoding='ascii'))

    arr.extend(self.ticker.encode(encoding='ascii'))
    arr.extend(self.timestamp.to_bytes(8, 'big'))
    arr.extend(self.reason.encode(encoding='ascii'))

    return arr

  def deserialize(self, msg: bytearray):
    decoded_arr = msg.decode()
    self.order_type = decoded_arr[0]
    self.mpid = decoded_arr[1:11].strip()
    self.order_id = decoded_arr[11:21].strip()
    self.ticker = decoded_arr[21:29].strip()
    self.timestamp = int.from_bytes(msg[29:37], 'big')
    self.reason = decoded_arr[37:38]

@dataclass
class OrderExecutedOutbound:
  order_type: str
  mpid: str
  order_id: str
  ticker: str
  timestamp: int
  buyer_mpid: str
  seller_mpid: str
  trade_id: str
  price: int
  size: int

  def serialize(self) -> bytearray:
    arr = bytearray()
    arr.extend(self.order_type.encode(encoding='ascii'))

    if len(self.mpid) > 10:
      self.mpid = self.mpid[:10]
    else:
      self.mpid = self.mpid.ljust(10, ' ')
    arr.extend(self.mpid.encode(encoding='ascii'))

    if len(self.order_id) > 10:
      raise ValueError("Order ID must be 10 characters long")
    else:
      self.order_id = self.order_id.ljust(10, ' ')
    arr.extend(self.order_id.encode(encoding='ascii'))

    arr.extend(self.ticker.encode(encoding='ascii'))
    arr.extend(self.timestamp.to_bytes(8, 'big'))

    if len(self.buyer_mpid) > 10:
      self.buyer_mpid = self.buyer_mpid[:10]
    else:
      self.buyer_mpid = self.buyer_mpid.ljust(10, ' ')
    arr.extend(self.buyer_mpid.encode(encoding='ascii'))

    if len(self.seller_mpid) > 10:
      self.seller_mpid = self.seller_mpid[:10]
    else:
      self.seller_mpid = self.seller_mpid.ljust(10, ' ')
    arr.extend(self.seller_mpid.encode(encoding='ascii'))

    if len(self.trade_id) > 10:
      self.trade_id = self.trade_id[:10]
    else:
      self.trade_id = self.trade_id.ljust(10, ' ')
    arr.extend(self.trade_id.encode(encoding='ascii'))

    arr.extend(self.price.to_bytes(4, 'big'))
    arr.extend(self.size.to_bytes(4, 'big'))

    return arr

  def deserialize(self, msg: bytearray):
    decoded_arr = msg.decode()
    self.order_type = decoded_arr[0]
    self.mpid = decoded_arr[1:11].strip()
    self.order_id = decoded_arr[11:21].strip()
    self.ticker = decoded_arr[21:29].strip()
    self.timestamp = int.from_bytes(msg[29:37], 'big')
    self.buyer_mpid = decoded_arr[37:47].strip()
    self.seller_mpid = decoded_arr[47:57].strip()
    self.trade_id = decoded_arr[57:67].strip()
    self.price = int.from_bytes(msg[67:71], 'big')
    self.size = int.from_bytes(msg[71:75], 'big')


### Market Data messages ###

@dataclass
class ITCH_Trade:
  order_type: str # T
  ticker: str
  timestamp: int
  price: int
  size: int
  buyer_exchange_order_id: str
  seller_exchange_order_id: str
  exchange_trade_id: str

  def serialize(self) -> bytearray:
    arr = bytearray()
    arr.extend(self.order_type.encode(encoding='ascii'))
    arr.extend(self.ticker.encode(encoding='ascii')) # 8
    arr.extend(self.timestamp.to_bytes(8, 'big')) # 8
    arr.extend(self.price.to_bytes(4, 'big')) # 4
    arr.extend(self.size.to_bytes(4, 'big')) # 4
    
    if len(self.buyer_exchange_order_id) > 10:
      self.buyer_exchange_order_id = self.buyer_exchange_order_id[:10]
    else:
      self.buyer_exchange_order_id = self.buyer_exchange_order_id.ljust(10, ' ')
    arr.extend(self.buyer_exchange_order_id.encode(encoding='ascii'))

    if len(self.seller_exchange_order_id) > 10:
      self.seller_exchange_order_id = self.seller_exchange_order_id[:10]
    else:
      self.seller_exchange_order_id = self.seller_exchange_order_id.ljust(10, ' ')
    arr.extend(self.seller_exchange_order_id.encode(encoding='ascii'))

    arr.extend(self.exchange_trade_id.encode(encoding='ascii')) # 10
    return arr

  def deserialize(self, msg: bytearray):
    decoded_arr = msg.decode()
    self.order_type = decoded_arr[0]
    self.ticker = decoded_arr[1:9].strip()
    self.timestamp = int.from_bytes(msg[9:17], 'big')
    self.price = int.from_bytes(msg[17:21], 'big')
    self.size = int.from_bytes(msg[21:25], 'big')
    self.buyer_exchange_order_id = decoded_arr[25:35].strip()
    self.seller_exchange_order_id = decoded_arr[35:45].strip()
    self.exchange_trade_id = decoded_arr[45:55].strip()

@dataclass
class ITCH_OrderbookBBO:
  ticker: str
  timestamp: int
  best_bid_price: int
  best_ask_price: int
  best_bid_volume: int
  best_ask_volume: int
  total_bid_volume: int
  total_ask_volume: int
  top10_bids: dict[int, int] # price to volume, in descending order
  top10_asks: dict[int, int] # price to volume, in ascending order


@dataclass
class ITCH_AddOrder:
  order_type: str # A
  ticker: str
  timestamp: int
  exchange_order_id: str
  side: str
  price: int
  shares: int

  def serialize(self) -> bytearray:
    arr = bytearray()
    arr.extend(self.order_type.encode(encoding='ascii'))
    arr.extend(self.ticker.encode(encoding='ascii'))
    arr.extend(self.timestamp.to_bytes(8, 'big'))

    if len(self.exchange_order_id) > 10:
      self.exchange_order_id = self.exchange_order_id[:10]
    else:
      self.exchange_order_id = self.exchange_order_id.ljust(10, ' ')
    arr.extend(self.exchange_order_id.encode(encoding='ascii'))

    arr.extend(self.side.encode(encoding='ascii'))
    arr.extend(self.price.to_bytes(4, 'big'))
    arr.extend(self.shares.to_bytes(4, 'big'))
    return arr

  def deserialize(self, msg: bytearray):
    decoded_arr = msg.decode()
    self.order_type = decoded_arr[0]
    self.ticker = decoded_arr[1:9].strip()
    self.timestamp = int.from_bytes(msg[9:17], 'big')
    self.exchange_order_id = decoded_arr[17:27].strip()
    self.side = decoded_arr[27:28]
    self.price = int.from_bytes(msg[28:32], 'big')
    self.shares = int.from_bytes(msg[32:36], 'big')

@dataclass
class ITCH_OrderCancel:
  order_type: str # C
  ticker: str
  timestamp: int
  exchange_order_id: str
  canceled_shares: int

  def serialize(self) -> bytearray:
    arr = bytearray()
    arr.extend(self.order_type.encode(encoding='ascii'))
    arr.extend(self.ticker.encode(encoding='ascii'))
    arr.extend(self.timestamp.to_bytes(8, 'big'))
    arr.extend(self.exchange_order_id.encode(encoding='ascii'))
    arr.extend(self.canceled_shares.to_bytes(4, 'big'))
    return arr

