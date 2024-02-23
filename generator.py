import random
import time
from enum import IntEnum
from multiprocessing import Process

import zmq


class CardSuit(IntEnum):
  HEARTS = 1
  DIAMONDS = 2
  CLUBS = 3
  SPADES = 4


class CardValue(IntEnum):
  ACE = 1
  TWO = 2
  THREE = 3
  FOUR = 4
  FIVE = 5
  SIX = 6
  SEVEN = 7
  EIGHT = 8
  NINE = 9
  TEN = 10
  JACK = 11
  QUEEN = 12
  KING = 13


class Sampler:
  def __init__(self):
    self.round_num = 0

  def sample(self):
    pass

  def get_round_num(self) -> int:
    return self.round_num

  def get_turn_num(self) -> int:
    pass

  def get_total_value(self) -> int:
    pass


class TenPokerCardSampler(Sampler):
  def __init__(self):
    super().__init__()
    self.topic = "TPC"
    self.cards = set()
    self.sampled_cards = []
    self.history = []
    self.total_value = 0
    self.generate_cards()

  def generate_cards(self):
    for suit in CardSuit:
      for value in CardValue:
        self.cards.add((value, suit))

  def sample(self):
    if not self.cards:
      return None
    if len(self.sampled_cards) >= 10:
      self.round_num += 1
      self.reset()

    card = random.choice(list(self.cards))
    self.cards.remove(card)
    self.sampled_cards.append(card)
    self.total_value += card[0].value

    if len(self.sampled_cards) == 10:
      self.history.append(self.sampled_cards)

    return card[0].value

  def get_turn_num(self):
    return len(self.sampled_cards)

  def get_sampled_cards(self):
    return self.sampled_cards

  def get_history(self):
    return self.history

  def get_total_value(self):
    return self.total_value

  def reset(self):
    self.sampled_cards = []
    self.total_value = 0

  def __getstate__(self):
    self_dict = self.__dict__.copy()

    return self_dict


def generate_data(sampler, socket, delay):
  context = zmq.Context()
  socket_instance = context.socket(zmq.PUB)
  socket_instance.bind(f"tcp://*:{socket}")

  while True:
    sample = sampler.sample()
    t = sampler.get_turn_num()
    r = sampler.get_round_num()
    tv = sampler.get_total_value()
    print(f"{sampler.topic} {t},{r},{sample},{tv}")
    socket_instance.send_string(f"{sampler.topic} {t},{r},{sample},{tv}")
    time.sleep(delay)


class UnderlyingMultiProcessGenerator:
  def __init__(self, samplers, sockets, delays):
    self.samplers = samplers
    self.sockets = sockets
    self.delays = delays
    self.processes = []

  def start_generators(self):
    for sampler, socket, delay in zip(self.samplers, self.sockets, self.delays):
      process = Process(target=generate_data, args=(sampler, socket, delay))
      process.start()
      self.processes.append(process)

  def stop_generators(self):
    for process in self.processes:
      process.terminate()


class UnderlyingProcessGenerator:
  def __init__(self, sampler: Sampler, socket: int = 7000, delay: float = 1.0):
    self.sampler = sampler
    self.delay = delay

    context = zmq.Context()
    self.socket = context.socket(zmq.PUB)
    self.socket.bind(f"tcp://*:{socket}")
    time.sleep(1)

  def next_turn(self):
    sample = self.sampler.sample()
    t = self.sampler.get_turn_num()
    r = self.sampler.get_round_num()
    tv = self.sampler.get_total_value()
    print(f"{self.sampler.topic} {t},{r},{sample},{tv}")
    self.socket.send_string(
      f"{self.sampler.topic} {t},{r},{sample},{tv}")  # Space is needed to separate topic from message
    return sample


if __name__ == "__main__":
  sockets = [7000, 8000, 9000]  # Example sockets
  delays = [1.0, 2.0, 3.0]  # Example delays
  samplers = [TenPokerCardSampler(), TenPokerCardSampler(), TenPokerCardSampler()]

  generator = UnderlyingMultiProcessGenerator(samplers, sockets, delays)
  generator.start_generators()
