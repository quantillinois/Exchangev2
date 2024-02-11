from matching_engine import OrderMatchingEngine, Timer, TickerConfiguration
from orderclass import OrderEntry, CancelOrder




if __name__ == "__main__":
  ticker_configs = [TickerConfiguration(
    symbol="TPCF0101",
    max_price=99999,
    min_price=1,
    lot_size=100,
    decimals=2,
    settlement='cash',
    multiplier=100
  )]

  orderid = 0
  orderid_map = {}
  def new_id(orderid: int) -> str:
    orderid += 1
    return str(orderid:=orderid+1).rjust(10, '0')

  init_orders = [
  OrderEntry("O", "MPID1", "TPCF0101", "B", 100, 100, str(orderid:=orderid+1).rjust(10, '0')),
  OrderEntry("O", "MPID1", "TPCF0101", "B", 100, 100, str(orderid:=orderid+1).rjust(10, '0')),
  OrderEntry("O", "MPID1", "TPCF0101", "S", 100, 100, str(orderid:=orderid+1).rjust(10, '0')),
  OrderEntry("O", "MPID1", "TPCF0101", "S", 101, 100, str(orderid:=orderid+1).rjust(10, '0')),
  OrderEntry("O", "MPID1", "TPCF0101", "B", 101, 50,  str(orderid:=orderid+1).rjust(10, '0')),
  ]

  orders = [
    CancelOrder("C", "MPID1", init_orders[0].order_id),
    CancelOrder("C", "MPID1", init_orders[1].order_id)
  ]

  me = OrderMatchingEngine(ticker_configs, Timer())

  print(me.orderbooks["TPCF0101"])
  for order in init_orders:
    print("Adding orderid: ", order.order_id)
    me.process_order(order.serialize())
    print(me.orderbooks["TPCF0101"])

  for order in orders:
    me.process_order(order.serialize())
    print(me.orderbooks["TPCF0101"])
