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

  def __init__(self, order_type, mpid, ticker, side, price, size, order_id):
    self.order_type = order_type
    self.mpid = mpid
    if len(self.mpid) > 10:
      self.mpid = self.mpid[:10]
    else:
      self.mpid = self.mpid.ljust(10, ' ')

    self.ticker = ticker
    if len(self.ticker) < 4:
      raise ValueError("Ticker must be 4 characters long")
    if self.ticker[:4] == "TPCF":
      if len(self.ticker) < 8:
        raise ValueError("Ticker TPCF must be 8 characters long")
      self.ticker = self.ticker[:8]
    else:
      raise ValueError("Unknown Ticker")

    self.side = side
    self.price = int(price)
    self.size = int(size)
    self.order_id = order_id
    if len(self.order_id) > 10:
      raise ValueError("Order ID must be 10 characters long")

  def serialize(self):
    arr = bytearray()
    arr.extend('O'.encode())
    # arr.extend(self.mpid.encode())
    # arr.extend(self.ticker.encode())
    # arr.extend(self.side.encode())
    # arr.extend(self.price.to_bytes(4, 'big'))
    # arr.extend(self.size.to_bytes(4, 'big'))
    # arr.extend(self.order_id.encode())
    return arr

@dataclass
class CancelOrder:
  order_type: str
  mpid: str
  order_id: str

  def serialize(self):
    arr = bytearray()
    arr.extend('C'.encode())
    return arr


def serialize_order(order):
  return order.serialize()

if __name__ == "__main__":
  import socket
  HOST = "localhost"
  PORT = 62000

  order_list = []
  with open("order.in", "r") as f:
    for line in f:
      if line.startswith("O"):
        order = line.strip().split(",")
        order_list.append(OrderEntry(*order))
      if line.startswith("C"):
        cancel = line.strip().split(",")
        order_list.append(CancelOrder(*cancel))

  print(order_list)

  with open("order.out", "wb") as f:
    for order in order_list:
      f.write(serialize_order(order))

  # Socket connection
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    with open("order.out", "rb") as f:
      s.sendall(f.read())
    data = s.recv(1024)

  print("Received", repr(data))