from matching_engine import OrderMatchingEngine, Timer
from generator import UnderlyingProcessGenerator, TenPokerCardSampler
from trading_bot import TradingBot
from gateway import Gateway
from orderclass import TickerConfiguration
import multiprocessing


class NetworkTopicInfo:
  def __init__(self, topic: str, hostname_port: str):
    self.topic = topic
    self.hostname_port = hostname_port





if __name__ == "__main__":
  timer = Timer()
  ticker_config_list = [
    TickerConfiguration("TPCF0101", 1300, 1, 4, 2, "cash", 1),
    TickerConfiguration("TPCF0202", 2600, 2, 4, 2, "cash", 1),
    TickerConfiguration("TPCF0303", 3900, 3, 4, 2, "cash", 1),
    TickerConfiguration("TPCF0404", 5200, 4, 4, 2, "cash", 1),
    TickerConfiguration("TPCF0505", 6400, 5, 4, 2, "cash", 1),
    TickerConfiguration("TPCF0606", 7600, 6, 4, 2, "cash", 1)
  ]

  gen1 = UnderlyingProcessGenerator(sampler=TenPokerCardSampler(), socket=7000, delay=1)
  gen2 = UnderlyingProcessGenerator(sampler=TenPokerCardSampler(), socket=7001, delay=1)


  # Set up some other shit

  gen1.start()
  gen2.start()


  gen1.join()
  gen2.join()


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

