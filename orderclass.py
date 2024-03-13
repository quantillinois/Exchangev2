from dataclasses import dataclass
# import bytearray

@dataclass
class OrderEntry:
  order_type: str
  mpid: str
  ticker: str
  side: str
  price: int
  size: int
  order_id: str

  def serialize(self):
    arr = bytearray()
    arr.extend(self.order_type.encode(encoding='ascii'))

    if len(self.mpid) > 10:
      self.mpid = self.mpid[:10]
    else:
      self.mpid = self.mpid.ljust(10, ' ')
    arr.extend(self.mpid.encode(encoding='ascii'))

    arr.extend(self.ticker.encode(encoding='ascii'))
    arr.extend(self.side.encode(encoding='ascii'))
    arr.extend(self.price.to_bytes(4, 'big'))
    arr.extend(self.size.to_bytes(4, 'big'))

    if len(self.order_id) > 10:
      raise ValueError("Order ID must be 10 characters long")
    else:
      self.order_id = self.order_id.ljust(10, ' ')
    arr.extend(self.order_id.encode(encoding='ascii'))
    return arr

  def deserialize(self, arr: bytearray):
    decoded_arr = arr.decode()
    self.order_type = decoded_arr[0]
    self.mpid = decoded_arr[1:11].strip()
    self.ticker = decoded_arr[11:19].strip()
    self.side = decoded_arr[19]
    self.price = int.from_bytes(arr[20:24], 'big')
    self.size = int.from_bytes(arr[24:28], 'big')
    self.order_id = decoded_arr[28:38].strip()


@dataclass
class CancelOrder:
  order_type: str
  mpid: str
  order_id: str

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
    return arr


  def deserialize(self, arr: bytearray):
    decoded_arr = arr.decode()
    self.order_type = decoded_arr[0]
    self.mpid = decoded_arr[1:11].strip()
    self.order_id = decoded_arr[11:21].strip()

@dataclass
class TickerConfiguration:
  symbol: str
  min_price: int
  max_price: int
  lot_size: int
  decimals: int
  settlement: str
  multiplier: int