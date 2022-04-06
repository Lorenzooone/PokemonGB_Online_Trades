#!/usr/bin/env python

import asyncio
import websockets

class WebsocketClient:
    host = None
    port = None
    SLEEP_TIMER = 0.01
    
    def __init__(self, host, port):
        WebsocketClient.host = host
        WebsocketClient.port = port

    async def hello(serving_host, serving_port, room):
        async with websockets.connect("ws://"+ WebsocketClient.host +":" + str(WebsocketClient.port) + "/link/"+str(room).zfill(5), ping_interval=None) as websocket:
            await websocket.send(serving_host + ":" + str(serving_port))
            data = await websocket.recv()
            return data
    
    def get_peer(self, serving_host, serving_port, room):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(WebsocketClient.hello(serving_host, serving_port, room))