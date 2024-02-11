import unittest
from matching_engine import OrderMatchingEngine, Timer, TradeIDGenerator, OrderBook, TickerConfiguration
from orderclass import OrderEntry, CancelOrder

class TestMatchingEngine(unittest.TestCase):
  timer = Timer()

  orderbooks = [
    TickerConfiguration(
      symbol="TPCF0101",
      max_price=99999,
      min_price=1,
      lot_size=100,
      decimals=2,
      settlement='cash',
      multiplier=100
    )
  ]


  def test_insert_buy_order(self):
    me = OrderMatchingEngine(TestMatchingEngine.orderbooks, TestMatchingEngine.timer)
    order = OrderEntry("O", "MPID1", "TPCF0101", "B", 100, 100, "00001")
    order_arr = order.serialize()
    me.process_order(order_arr)

    orderbook = me.orderbooks

    self.assertEqual(len(orderbook), 1)
    self.assertEqual(len(orderbook["TPCF0101"].orderbook[100].bids), 1)
    self.assertEqual(orderbook["TPCF0101"].orderbook[100].bid_total_volume, 100)
    self.assertEqual(orderbook["TPCF0101"].orderbook[100].bids[0].mpid, "MPID1")
    self.assertEqual(orderbook["TPCF0101"].orderbook[100].bids[0].price, 100)
    self.assertEqual(orderbook["TPCF0101"].orderbook[100].bids[0].order_id, "00001")

  def test_insert_sell_order(self):
    me = OrderMatchingEngine(TestMatchingEngine.orderbooks, TestMatchingEngine.timer)
    order = OrderEntry("O", "MPID1", "TPCF0101", "S", 100, 100, "00001")
    order_arr = order.serialize()
    me.process_order(order_arr)

    orderbook = me.orderbooks

    self.assertEqual(len(orderbook), 1)
    self.assertEqual(len(orderbook["TPCF0101"].orderbook[100].asks), 1)
    self.assertEqual(orderbook["TPCF0101"].orderbook[100].ask_total_volume, 100)
    self.assertEqual(orderbook["TPCF0101"].orderbook[100].asks[0].mpid, "MPID1")
    self.assertEqual(orderbook["TPCF0101"].orderbook[100].asks[0].price, 100)
    self.assertEqual(orderbook["TPCF0101"].orderbook[100].asks[0].order_id, "00001")


if __name__ == '__main__':
  unittest.main()