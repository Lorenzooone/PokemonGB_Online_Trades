#!/usr/bin/env python

import asyncio
import websockets

host = "localhost"
port = 11111

async def hello():
    async with websockets.connect("ws://"+ host +":" + str(port) + "/link/19283", ping_interval=None) as websocket:
        await websocket.send("localhost:8324")
        data = await websocket.recv()
        print(data) 

asyncio.get_event_loop().run_until_complete(hello())