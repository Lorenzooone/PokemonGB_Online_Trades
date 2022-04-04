#!/usr/bin/env python

import asyncio
import websockets

class WebsocketClient:
    host = "localhost"
    port = 11111
    
    def __init__(self):
        pass

    async def hello(serving_host, serving_port):
        async with websockets.connect("ws://"+ WebsocketClient.host +":" + str(WebsocketClient.port) + "/link/19283", ping_interval=None) as websocket:
            await websocket.send(serving_host + ":" + str(serving_port))
            data = await websocket.recv()
            return data
    
    def get_peer(self, serving_host, serving_port):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(WebsocketClient.hello(serving_host, serving_port))