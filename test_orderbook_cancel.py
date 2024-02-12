import unittest
from matching_engine import OrderBook, Timer, TradeIDGenerator, Order
from orderclass import TickerConfiguration

class TestOrderbookCancel(unittest.TestCase):
  TPCF0101_CONFIG = TickerConfiguration(
    symbol="TPCF0101",
    max_price=99999,
    min_price=1,
    lot_size=100,
    decimals=2,
    settlement='cash',
    multiplier=100
  )

  def test_cancel_buy_order(self):
    timer = Timer()
    trade_id_gen = TradeIDGenerator()
    ob = OrderBook(TestOrderbookCancel.TPCF0101_CONFIG, timer, trade_id_gen)
    enter_order = Order("00001", "TPCF0101", 100, 100, "MPID1", "MPID1OrderID", 0, "B")
    cancel_orderid = "00001"

    self.assertEqual(len(ob.orderbook), TestOrderbookCancel.TPCF0101_CONFIG.max_price - TestOrderbookCancel.TPCF0101_CONFIG.min_price + 1)

    ob.add_order(enter_order)
    self.assertEqual(ob.total_bid_orders, 1)
    self.assertEqual(ob.total_ask_orders, 0)
    self.assertEqual(ob.total_bid_volume, 100)
    self.assertEqual(ob.total_ask_volume, 0)
    self.assertEqual(len(ob.orderbook[100].bids), 1)
    self.assertEqual(ob.orderbook[100].bid_total_volume, 100)
    self.assertEqual(ob.orderbook[100].bid_total_orders, 1)
    self.assertEqual(ob.orderbook[100].ask_total_volume, 0)
    self.assertEqual(ob.orderbook[100].ask_total_orders, 0)

    ob.cancel_order(cancel_orderid)
    self.assertEqual(ob.total_bid_orders, 0)
    self.assertEqual(ob.total_ask_orders, 0)
    self.assertEqual(ob.total_bid_volume, 0)
    self.assertEqual(ob.total_ask_volume, 0)
    self.assertEqual(len(ob.orderbook[100].bids), 0)
    self.assertEqual(ob.orderbook[100].bid_total_volume, 0)
    self.assertEqual(ob.orderbook[100].bid_total_orders, 0)
    self.assertEqual(ob.orderbook[100].ask_total_volume, 0)
    self.assertEqual(ob.orderbook[100].ask_total_orders, 0)


  def test_cancel_sell_order(self):
    timer = Timer()
    trade_id_gen = TradeIDGenerator()
    ob = OrderBook(TestOrderbookCancel.TPCF0101_CONFIG, timer, trade_id_gen)
    enter_order = Order("00001", "TPCF0101", 100, 100, "MPID1", "MPID1OrderID", 0, "S")
    cancel_orderid = "00001"

    self.assertEqual(len(ob.orderbook), TestOrderbookCancel.TPCF0101_CONFIG.max_price - TestOrderbookCancel.TPCF0101_CONFIG.min_price + 1)

    ob.add_order(enter_order)
    self.assertEqual(ob.total_bid_orders, 0)
    self.assertEqual(ob.total_ask_orders, 1)
    self.assertEqual(ob.total_bid_volume, 0)
    self.assertEqual(ob.total_ask_volume, 100)
    self.assertEqual(len(ob.orderbook[100].asks), 1)
    self.assertEqual(ob.orderbook[100].ask_total_volume, 100)
    self.assertEqual(ob.orderbook[100].ask_total_orders, 1)
    self.assertEqual(ob.orderbook[100].bid_total_volume, 0)
    self.assertEqual(ob.orderbook[100].bid_total_orders, 0)

    ob.cancel_order(cancel_orderid)
    self.assertEqual(ob.total_bid_orders, 0)
    self.assertEqual(ob.total_ask_orders, 0)
    self.assertEqual(ob.total_bid_volume, 0)
    self.assertEqual(ob.total_ask_volume, 0)
    self.assertEqual(len(ob.orderbook[100].asks), 0)
    self.assertEqual(ob.orderbook[100].ask_total_volume, 0)
    self.assertEqual(ob.orderbook[100].ask_total_orders, 0)
    self.assertEqual(ob.orderbook[100].bid_total_volume, 0)
    self.assertEqual(ob.orderbook[100].bid_total_orders, 0)


  def test_cancel_order_with_no_order(self):
    timer = Timer()
    trade_id_gen = TradeIDGenerator()
    ob = OrderBook(TestOrderbookCancel.TPCF0101_CONFIG, timer, trade_id_gen)
    cancel_orderid = "00001"

    self.assertEqual(len(ob.orderbook), TestOrderbookCancel.TPCF0101_CONFIG.max_price - TestOrderbookCancel.TPCF0101_CONFIG.min_price + 1)

    ob.cancel_order(cancel_orderid)
    self.assertEqual(ob.total_bid_orders, 0)
    self.assertEqual(ob.total_ask_orders, 0)
    self.assertEqual(ob.total_bid_volume, 0)
    self.assertEqual(ob.total_ask_volume, 0)
    self.assertEqual(len(ob.orderbook[100].asks), 0)
    self.assertEqual(ob.orderbook[100].ask_total_volume, 0)
    self.assertEqual(ob.orderbook[100].ask_total_orders, 0)
    self.assertEqual(ob.orderbook[100].bid_total_volume, 0)
    self.assertEqual(ob.orderbook[100].bid_total_orders, 0)


if __name__ == '__main__':
  unittest.main()