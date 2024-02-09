from matching_engine import OrderBook, Timer, TradeIDGenerator, Order
import unittest
# from orderclass import OrderEntry, CancelOrder

class TestOrderbook(unittest.TestCase):
  timer = Timer()
  trade_id_gen = TradeIDGenerator()

  def test_buy_order_no_cross(self):
    ob = OrderBook("TPCF0101", self.timer, self.trade_id_gen)
    enter_order = Order("00001", "TPCF0101", 100, 100, "MPID1", "MPID1OrderID", 0, "B")
    ob.add_order(enter_order)

    orderbook = ob.orderbook

    self.assertEqual(len(orderbook), 1)
    self.assertEqual(len(orderbook[100].bids), 1)
    self.assertEqual(orderbook[100].bid_total_volume, 100)
    self.assertEqual(orderbook[100].bid_total_orders, 1)
    self.assertEqual(orderbook[100].ask_total_volume, 0)
    self.assertEqual(orderbook[100].ask_total_orders, 0)

    order = orderbook[100].bids[0]

    self.assertEqual(order.mpid, 'MPID1')
    self.assertEqual(order.price, 100)
    self.assertEqual(order.volume, 100)
    self.assertEqual(order.order_id, '00001')


  def test_sell_order_no_cross(self):
    ob = OrderBook("TPCF0101", self.timer, self.trade_id_gen)
    enter_order = Order("00001", "TPCF0101", 100, 100, "MPID1", "MPID1OrderID", 0, "S")
    ob.add_order(enter_order)

    orderbook = ob.orderbook

    self.assertEqual(len(orderbook), 1)
    self.assertEqual(orderbook[100].ask_total_volume, 100)
    self.assertEqual(orderbook[100].ask_total_orders, 1)
    self.assertEqual(orderbook[100].bid_total_volume, 0)
    self.assertEqual(orderbook[100].bid_total_orders, 0)

  def test_buy_order_with_cross_same_volume(self):
    ob = OrderBook("TPCF0101", self.timer, self.trade_id_gen)
    sell_enter_order = Order("00001", "TPCF0101", 100, 100, "MPID1", "MPID1OrderID", 0, "S")
    buy_enter_order = Order("00002", "TPCF0101", 100, 100, "MPID2", "MPID2OrderID", 0, "B")
    ob.add_order(sell_enter_order)
    ob.add_order(buy_enter_order)

    orderbook = ob.orderbook

    self.assertEqual(len(orderbook), 1)
    self.assertEqual(orderbook[100].ask_total_volume, 0)
    self.assertEqual(orderbook[100].ask_total_orders, 0)
    self.assertEqual(orderbook[100].bid_total_volume, 0)
    self.assertEqual(orderbook[100].bid_total_orders, 0)

    trades = ob.outbound_msgs

    self.assertEqual(len(trades), 1)
    trade = trades[0]
    self.assertEqual(trade.price, 100)
    self.assertEqual(trade.volume, 100)
    self.assertEqual(trade.buyer_mpid, "MPID2")
    self.assertEqual(trade.buyer_order_id, "MPID2OrderID")
    self.assertEqual(trade.seller_mpid, "MPID1")
    self.assertEqual(trade.seller_order_id, "MPID1OrderID")
    self.assertEqual(trade.trade_id, "1")


if __name__ == "__main__":
  unittest.main()