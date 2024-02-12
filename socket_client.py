import asyncio
import websockets


class Client:
    uri = "ws://localhost:8765"

    def __init__(self, token):
        self.token = token
        self.websocket = None
        self.dict = {}
        self.counter = 0

    async def connect(self):
        self.websocket = await websockets.connect(
            self.uri, extra_headers={"Authorization": self.token}, ping_interval=None
        )

    async def send(self, message):
        await self.websocket.send(message)
        response = await self.websocket.recv()

        return response

    async def close(self):
        await self.websocket.close()


async def main():
    client = Client("a")
    await client.connect()

    res = await client.send("ligma")

    print(res)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
