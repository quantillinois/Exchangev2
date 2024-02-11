import asyncio
import websockets

token_to_id_mapping = {}


async def handle(websocket):
    token = websocket.request_headers['Authorization'] if 'Authorization' in websocket.request_headers else None

    if token is None or token not in token_to_id_mapping:
        await websocket.send('Invalid token')
        return

    userid = token_to_id_mapping[token]

    async for message in websocket:
        print(f"<<<{userid}: {message}")
        greeting = f"Hello {userid}! {message}"
        print(f">>>{userid}: {greeting}")
        await websocket.send(greeting)


def map_tokens_to_ids(filename):
    id_counter = 0

    with open(filename, 'r') as file:
        for line in file:
            token = line.strip()

            if token not in token_to_id_mapping:
                token_to_id_mapping[token] = id_counter
                id_counter += 1


async def main():
    map_tokens_to_ids('tokens.txt')
    async with websockets.serve(handle, "localhost", 8765, ping_interval=None):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
