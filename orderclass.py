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