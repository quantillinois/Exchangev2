import asyncio
import websockets


async def send_and_receive():
    uri = "ws://localhost:8765"
    token = input("token: ")

    async with websockets.connect(uri, extra_headers={"Authorization": token}, ping_interval=None) as websocket:
        print("Connected to the server.")

        while True:
            send = input("")
            await websocket.send(send)
            message = await websocket.recv()
            print(f">>>{message}")


if __name__ == "__main__":
    asyncio.run(send_and_receive())
