from enum import Enum
import random
import zmq
from dataclasses import dataclass

class CardSuit(Enum):
  HEARTS = 1
  DIAMONDS = 2
  CLUBS = 3
  SPADES = 4

class CardValue(Enum):
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


@dataclass
class TenPokerCardSample:
  round_num : int = 0
  turn_num : int = 0
  sampled_card : int = 0
  total_round_sum : int = 0

  def serialize(self) -> bytearray:
    arr = bytearray()
    print(f"Serializing: {self.round_num}, {self.turn_num}, {self.sampled_card}, {self.total_round_sum}")
    arr.extend(self.round_num.to_bytes(4, 'big'))
    arr.extend(self.turn_num.to_bytes(4, 'big'))
    arr.extend(self.sampled_card.to_bytes(4, 'big'))
    arr.extend(self.total_round_sum.to_bytes(4, 'big'))
    print(f"Serialized: {arr}")
    return arr

  def deserialize(self, msg: bytearray):
    print(f"Deserializing: {msg}")
    self.round_num = int.from_bytes(msg[0:4], 'big')
    self.turn_num = int.from_bytes(msg[4:8], 'big')
    self.sampled_card = int.from_bytes(msg[8:12], 'big')
    self.total_round_sum = int.from_bytes(msg[12:16], 'big')
    print(f"Deserialized: {self.round_num}, {self.turn_num}, {self.sampled_card}, {self.total_round_sum}")

class Sampler:
  def __init__(self):
    self.round_num : int = 0

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

    sample = TenPokerCardSample(self.round_num, len(self.sampled_cards), card[0].value, self.total_value)
    return sample

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


class UnderlyingProcessGenerator:
  def __init__(self, sampler: Sampler, socket: int = 7000, delay : float = 1.0):
    self.sampler = sampler
    self.delay = delay

    context = zmq.Context()
    self.socket = context.socket(zmq.PUB)
    self.socket.bind(f"tcp://*:{socket}")
    time.sleep(1)

  def run_rounds(self, num_rounds: int):
    for i in range(num_rounds):
      self.next_turn()
      time.sleep(self.delay)

  def next_turn(self):
    sample = self.sampler.sample()
    print(f"Sampled: {sample}")
    data = bytearray()
    data.extend(f"GEN-{self.sampler.topic}".encode())
    data.extend(b'@')
    data.extend(sample.serialize())
    # self.socket.send_string(f"GEN-{self.sampler.topic}@{t},{r},{sample},{tv}") # Space is needed to separate topic from message
    print(f"Sending message: {data}")
    self.socket.send(data)
    return sample


if __name__ == "__main__":
  import time
  sampler = TenPokerCardSampler()
  generator = UnderlyingProcessGenerator(sampler)

  try:
    generator.run_rounds(10)
  except KeyboardInterrupt:
    print("Exiting")