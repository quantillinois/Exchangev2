import asyncio
import websockets


class Server:
    def __init__(self, respond, filename='tokens.txt', host='localhost', port=8765):
        self.token_to_id_mapping = {}
        self.filename = filename
        self.host = host
        self.port = port
        self.respond = respond

        self.map_tokens_to_ids()

        asyncio.run(self.run_server())

    async def handle(self, websocket, path):
        token = websocket.request_headers.get('Authorization', None)

        if token is None or token not in self.token_to_id_mapping:
            await websocket.send('Invalid token')
            return

        userid = self.token_to_id_mapping[token]

        async for message in websocket:
            print(f"<<<{userid}: {message}")
            response = self.respond(message, userid)
            print(f">>>{userid}: {response}")
            await websocket.send(response)

    def map_tokens_to_ids(self):
        id_counter = 0

        with open(self.filename, 'r') as file:
            for line in file:
                token = line.strip()

                if token not in self.token_to_id_mapping:
                    self.token_to_id_mapping[token] = id_counter
                    id_counter += 1

    async def run_server(self):
        async with websockets.serve(self.handle, self.host, self.port, ping_interval=None):
            await asyncio.Future()  # run forever


if __name__ == "__main__":
    def hi(message, userid):
        return f"hi {userid}, message: {message}"

    server = Server(hi)
