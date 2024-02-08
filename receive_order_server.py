from dataclasses import dataclass

@dataclass
class OrderEntry:
  order_type: str
  mpid: str
  ticker: str
  side: str
  price: int
  size: int
  order_id: str

  def deserialize(self, arr):
    self.order_type = arr[0].decode()
    self.mpid = arr[1:11].decode().strip()
    self.ticker = arr[11:19].decode().strip()
    self.side = arr[19].decode()
    self.price = int.from_bytes(arr[20:24], 'big')
    self.size = int.from_bytes(arr[24:28], 'big')
    self.order_id = arr[28:38].decode().strip()

@dataclass
class CancelOrder:
  order_type: str
  mpid: str
  order_id: str

  def deserialize(self, arr):
    self.order_type = arr[0].decode()
    self.mpid = arr[1:11].decode().strip()
    self.order_id = arr[11:21].decode().strip()


def deserialize_order(arr):
  print(arr[0])
  print(arr[0].decode())
  print(arr[1])
  order_type = arr[0].decode()
  if order_type == 'O':
    order = OrderEntry()
    order.deserialize(arr)
    return order
  elif order_type == 'C':
    cancel = CancelOrder()
    cancel.deserialize(arr)
    return cancel
  else:
    raise ValueError("Unknown Order Type")


if __name__ == "__main__":
  import socket
  HOST = "localhost"
  PORT = 62000




  # Socket connection
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    conn, addr = s.accept()

    with conn:
      print("Connected by", addr)
      while True:
        data = conn.recv(1024)
        if not data:
          break
        conn.sendall(data)
        print(data)
        order = deserialize_order(data)
        print(order)
        conn.sendall(data)
        print("Sent", repr(data))
        break