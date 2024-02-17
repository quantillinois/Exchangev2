from matching_engine import OrderMatchingEngine
from generator import UnderlyingProcessGenerator
from trading_bot import TradingBot
from gateway import Gateway
import multiprocessing


class NetworkTopicInfo:
  def __init__(self, topic: str, hostname_port: str):
    self.topic = topic
    self.hostname_port = hostname_port





if __name__ == "__main__":
  pass


# import time
# import zmq

# context = zmq.Context()
# pub_socket = context.socket(zmq.PUB)
# pub_socket.bind("tcp://*:5555")
# topic = "mytopic"

# sub_socket = context.socket(zmq.SUB)
# sub_socket.connect("tcp://localhost:5555")
# sub_socket.setsockopt_string(zmq.SUBSCRIBE, topic)

# for _ in range(10):
#   time.sleep(1)
#   pub_socket.send_string("%s %d" % (topic, _+5))
#   print(sub_socket.recv_string())



# [TradingBot]
#   gateway = "tcp://localhost:2000"
#   data_feed = "tcp://localhost:10000"

# [Gateway]
#   start_port = 2000
#   max_connections = 2

# [MatchingEngine]
#   underlying_process = "tcp://localhost:10000"
#   ticker_list = ["TPCF"]

