# Handles specific PAIR interaction,
# subscribed to exchange outbound msgs
import zmq
import time
import multiprocessing as mp
import queue
import signal

class Gateway:

  def __init__(self,  start_port: int = 2000, max_connections: int = 10): # TODO: Add exchange_settings which takes in info about all OMEs
    # Exchange settings
    # self.exchange_settings = "tcp://localhost:5555"`
    self.exchange_ip = "localhost"
    self.exchange_inbound_port = 9001
    self.exchange_outbound_port = 8001

    # Client connections
    self.connections = {}
    self.start_port : int = start_port
    self.max_connections : int = max_connections

    # self.client_processes = {}

    self.ouch_inbound_exchange = mp.Queue()
    self.ouch_outbound_client_map : dict[int, mp.Queue] = {port: mp.Queue() for port in range(self.start_port, self.start_port + self.max_connections)}
    self.ouch_outbound_exchange = mp.Queue()

  def run(self):
    processes = []
    print("Starting exchange connection")
    processes.append(mp.Process(target=self.read_from_exchange_daemon, args=()))
    processes[-1].start()
    processes.append(mp.Process(target=self.write_to_exchange_daemon, args=()))
    processes[-1].start()
    processes.append(mp.Process(target=self.outbound_client_mask_daemon, args=()))
    processes[-1].start()

    # Client processes
    print("Starting client connections")
    for port in range(self.start_port, self.start_port + self.max_connections):
      process = mp.Process(target=self.client_connection_daemon, args=(port,))
      process.start()
      processes.append(process)

    for process in processes:
      process.join()


  def run_exchange(self):
    pass

  def pass_client_to_exchange_daemon(self):
    pass

  def write_to_exchange_daemon(self):
    context = zmq.Context()
    connection = context.socket(zmq.PUSH)
    connection.connect(f"tcp://{self.exchange_ip}:{self.exchange_inbound_port}")
    time.sleep(1)

    while True:
      try:
        try:
          msg = self.ouch_inbound_exchange.get_nowait()
        except queue.Empty:
          continue
        if msg is None:
          continue
        print(f"Sending message to exchange: {msg}")
        connection.send(msg)
      except KeyboardInterrupt:
        print("Exiting")
        break
      time.sleep(0.005)

  def read_from_exchange_daemon(self):
    context = zmq.Context()
    connection = context.socket(zmq.SUB)
    connection.connect(f"tcp://{self.exchange_ip}:{self.exchange_outbound_port}")
    connection.setsockopt_string(zmq.SUBSCRIBE, "ENTRY-OME1")
    time.sleep(1)

    while True:
      try:
        try:
          raw = connection.recv(flags=zmq.NOBLOCK)
          topic, msg = raw.split(b'@', 1)
          self.ouch_outbound_exchange.put(msg)
          print(f"Received message from exchange: {msg}")
        except zmq.error.Again:
          pass
      except KeyboardInterrupt:
        print("Exiting")
        break
      time.sleep(0.005)


  def run_client(self):
    pass


  def client_connection_daemon(self, port: int):
    print("Establish client connection port: ", port)
    context = zmq.Context()
    connection = context.socket(zmq.PAIR)
    connection.bind(f"tcp://*:{port}")
    mpid = None
    # time.sleep(2)

    def process_inbound_message(msg: bytearray, port: int, socket: zmq.Socket):

      match msg[0]:
        case 87: # W - Heartbeat
          print(f"Port {port}: Received W")
          # mpid = msg[1:5]
          # print(f"MPID: {mpid}")
          # socket.send(b'OK')
        case 67: # C - Order Cancel
          print(f"Port {port}: Received C")
          self.ouch_inbound_exchange.put(msg)
        case 79: # O - Order Entry
          print(f"Port {port}: Received O")
          self.ouch_inbound_exchange.put(msg)
        case _:
          print(f"Received unknown message. Port: {port}, Msg code: {msg[0]}")
          # self.send_order(msg)

    def process_outbound_message(port: int, socket: zmq.Socket):
      try:
        try:
          msg = self.ouch_outbound_client_map[port].get_nowait()
        except queue.Empty:
          return
        if msg is None:
          return
        if mpid is not None:
          msg_mpid = msg[1:11]
          # print(f"Message received: {msg_mpid}, {msg}")
          if msg_mpid != mpid:
            return
          if msg[1:11] == mpid: # TODO: do not hardcode
            socket.send(msg)
      except zmq.error.Again:
        pass

    while True:
      try:
        msg = connection.recv(flags=zmq.NOBLOCK)
        if mpid is None:
          if msg[0] == 87:
            mpid = msg[1:11] # TODO: do not hardcode
          else:
            print("MPID not set")
            connection.send(b'W')
          continue
        process_inbound_message(msg, port, connection)
      except zmq.error.Again:
        pass
      process_outbound_message(port, connection)
      time.sleep(0.005)


  # def send_order(self, arr: bytearray) -> bytearray:
  #   self.exchange_entry_socket.send(arr)


  def outbound_client_mask_daemon(self):
    """This function needs to read from self.ouch_outbound_exchange and send to the appropriate client by
    reading the MPID from the order and sending it to the correct port. You will need to maintain a dictionary
    of MPID to port mapping, as well as add record this mapping when a new client connects in client_connection_daemon().
    If the MPID is not found in the dictionary, you should log the error and discard the message."""
    while True:
      try:
        msg = self.ouch_outbound_exchange.get_nowait()
      except queue.Empty:
        continue
      if msg is None:
        continue
      for port, q in self.ouch_outbound_client_map.items():
        q.put(msg)
      time.sleep(0.005)

if __name__ == "__main__":
  gateway = Gateway()
  gateway.run()