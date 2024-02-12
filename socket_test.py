import asyncio

from matching_engine import TickerConfiguration
from orderclass import OrderEntry, CancelOrder
from socket_client import Client
from socket_server import Server

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
        return str(orderid := orderid + 1).rjust(10, '0')


    init_orders = [
        OrderEntry("O", "MPID1", "TPCF0101", "B", 100, 100, str(orderid := orderid + 1).rjust(10, '0')),
        OrderEntry("O", "MPID1", "TPCF0101", "B", 100, 100, str(orderid := orderid + 1).rjust(10, '0')),
        OrderEntry("O", "MPID2", "TPCF0101", "S", 100, 100, str(orderid := orderid + 1).rjust(10, '0')),
        OrderEntry("O", "MPID2", "TPCF0101", "S", 101, 100, str(orderid := orderid + 1).rjust(10, '0')),
        OrderEntry("O", "MPID1", "TPCF0101", "B", 101, 50, str(orderid := orderid + 1).rjust(10, '0')),
    ]

    orders = [
        CancelOrder("C", "MPID1", init_orders[0].order_id),
        CancelOrder("C", "MPID1", init_orders[1].order_id)
    ]


    # server deserializes and then reserializes

    def process(message, userid):
        oe = OrderEntry(None, None, None, None, None, None, None)
        oe.deserialize(message)

        print(f"{userid} submitted order {oe.order_id} of {oe}")

        return oe.serialize()


    async def run():
        server = Server(process)
        client = Client('b')
        await client.connect()

        response_orders = []

        for order in init_orders:
            response = await client.send(order.serialize())

            oe = OrderEntry(None, None, None, None, None, None, None)
            oe.deserialize(response)

            response_orders.append(oe)

        print(response_orders)


    asyncio.run(run())
