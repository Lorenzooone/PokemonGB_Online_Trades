#!/usr/bin/env python

import asyncio
import websockets
import threading
import signal
import os
from random import Random
from time import sleep
import ipaddress
from utilities.gsc_trading_listener import GSCTradingListener
from utilities.gsc_trading import GSCTradingClient
from utilities.gsc_trading_strings import GSCTradingStrings
from utilities.gsc_trading_data_utils import *

#GSCTradingClient.gsc_pool_transfer
#GSCTradingClient.gsc_choice_transfer
#GSCTradingClient.gsc_accept_transfer
#GSCTradingClient.gsc_success_transfer
link_rooms = {}
user_pools = {}
mons = []
in_use_mons = set()

class ServerUtils:
    saved_mons_path = "pool_mons.bin"
    
    def save_mons():
        data = []
        for m in mons:
            data += GSCUtils.single_mon_to_data(m[0], m[1])
        GSCUtilsMisc.write_data(ServerUtils.saved_mons_path, data)
    
    def load_mons(checks):
        global mons, in_use_mons
        preparing_mons = []
        raw_data = GSCUtilsMisc.read_data(ServerUtils.saved_mons_path)
        if raw_data is not None:
            single_entry_len = len(checks.single_pokemon_checks_map) + 1
            entries = int(len(raw_data)/single_entry_len)
            for i in range(entries):
                mon = GSCUtils.single_mon_from_data(checks, raw_data[i*single_entry_len:(i+1)*single_entry_len])
                if mon is not None:
                    preparing_mons += [mon]
            in_use_mons = set()
            mons = preparing_mons
    
    def get_mon_index(index):
        while index is None:
            rnd = Random()
            rnd.seed()
            new_index = rnd.randint(0,len(mons)-1)
            if new_index not in in_use_mons:
                in_use_mons.add(new_index)
                index = new_index
        return index, mons[index]

class PoolTradeServer:
    """
    Class which handles the pool trading part.
    """
    
    def __init__(self):
        self.checks = GSCChecks([0,0,0], True)
        self.checker = self.checks.single_pokemon_checks_map
        self.state = None
        rnd = Random()
        rnd.seed()
        self.own_id = rnd.randint(0,255)
        self.hll = GSCTradingListener()
        self.mon_index = None
        self.received_mon = None
        self.received_accepted = False
        self.received_success = False
    
    async def process(self, data, connection):
        request = self.hll.process_received_data(data, connection, send_data=False)
        if request[0] == GSCTradingStrings.get_request:
            if request[1] == GSCTradingClient.gsc_pool_transfer:
                self.mon_index, mon = ServerUtils.get_mon_index(self.mon_index)
                await connection.send(self.hll.prepare_send_data(request[1], [0] + GSCUtils.single_mon_to_data(mon[0], mon[1])))
    
class WebsocketServer (threading.Thread):
    '''
    Class which handles responding to the websocket requests.
    '''
    
    def __init__(self, host="localhost", port=11111):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.host = host
        self.port = port
        self.checks = GSCChecks([0,0,0], True)
        self.checker = self.checks.single_pokemon_checks_map
        ServerUtils.load_mons(self.checks)

    async def link_function(websocket, data, path):
        '''
        Handler which either registers a client to a room, or links
        two clients together.
        Decides which one is the client and which one is the server in the
        P2P connection randomly.
        '''
        room = 100000
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
        return room
    
    async def pool_function(websocket, data, room):
        '''
        Handler which handles pool trading messages.
        '''
        # Assign an ID to the user
        if room >= 100000:
            rnd = Random()
            rnd.seed()
            completed = False
            while not completed:
                room = rnd.randint(0,99999)
                if not room in user_pools.keys():
                    user_pools[room] = PoolTradeServer()
                    completed = True
        
        await user_pools[room].process(data, websocket)
        
        return room

    async def handler(websocket, path):
        """
        Gets the data and then calls the proper handler while keeping
        the connection active.
        """
        curr_room = 100000
        while True:
            try:
                data = await websocket.recv()
            except websockets.ConnectionClosed:
                print(f"Terminated")
                if curr_room in link_rooms.keys():
                    link_rooms.pop(curr_room)
                if curr_room in user_pools.keys():
                    user_pools.pop(curr_room)
                break
            except Exception as e:
                print('Websocket server error:', str(e))
                if curr_room in link_rooms.keys():
                    link_rooms.pop(curr_room)
            if path.startswith("/link/"):
                curr_room = await WebsocketServer.link_function(websocket, data, path)
            if path.startswith("/pool"):
                curr_room = await WebsocketServer.pool_function(websocket, data, curr_room)
                
    def run(self):
        """
        Runs the server in a second Thread in order to keep
        the program responsive.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        start_server = websockets.serve(WebsocketServer.handler, self.host, self.port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

def exit_gracefully():
    os._exit(1)

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    exit_gracefully()

GSCUtils()
ws = WebsocketServer()
ws.start()

signal.signal(signal.SIGINT, signal_handler)

while True:
    sleep(1)