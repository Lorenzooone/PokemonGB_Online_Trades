#!/usr/bin/env python

import asyncio
import websockets
from random import Random
import ipaddress

host = "localhost"
port = 11111

link_rooms = {}

# create handler for each connection

async def link_function(websocket, data, path):
    if len(path) >= 11:
        room = int(path[6:11])
        valid = True
        try:
            ip = ipaddress.ip_address(data.split(":")[0])
        except ValueError:
            if data.split(":")[0] != "localhost":
                valid = False
        if valid:
            if room not in link_rooms.keys():
                link_rooms[room] = [data, websocket]
            else:
                info = link_rooms.pop(room)
                rnd = Random()
                rnd.seed()
                user = rnd.randint(0,1)
                repl = ["SERVER", "CLIENT"]
                if user == 0:
                    repl = ["CLIENT", "SERVER"]
                reply_old = repl[0] + data
                reply_new = repl[1] + info[0]
                await info[1].send(reply_old)
                await websocket.send(reply_new)

async def handler(websocket, path):
    while True:
        try:
            data = await websocket.recv()
        except websockets.ConnectionClosed:
            print(f"Terminated")
            break

        if path.startswith("/link/"):
            await link_function(websocket, data, path)

start_server = websockets.serve(handler, host, port)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()