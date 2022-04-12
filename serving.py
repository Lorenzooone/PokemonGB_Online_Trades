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

link_rooms = {}
user_pools = {}
mons = []
in_use_mons = set()

class ServerUtils:
    saved_mons_path = "pool_mons.bin"
    
    def save_mons():
        """
        Saves the currently loaded Pokémon to file.
        """
        data = []
        for m in mons:
            data += GSCUtils.single_mon_to_data(m[0], m[1])
        GSCUtilsMisc.write_data(ServerUtils.saved_mons_path, data)
    
    def load_mons(checks):
        """
        Loads the Pool's Pokémon from file.
        """
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
        """
        If the index is None, it randomly selects a free one.
        Returns the pokémon in that slot.
        """
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
    gsc_accept_trade = 0x72
    gsc_decline_trade = 0x71
    gsc_success_value = 0x91
    
    def __init__(self):
        self.checks = GSCChecks([0,0,0], True)
        rnd = Random()
        rnd.seed()
        self.own_id = rnd.randint(0,255)
        self.last_accepted = None
        self.last_success = None
        self.clear_pool = True
        self.hll = GSCTradingListener()
        self.mon_index = None
        self.received_mon = None
        self.received_accepted = None
        self.received_success = None
        self.get_handlers = {
            GSCTradingClient.gsc_pool_transfer: self.handle_get_pool,
            GSCTradingClient.gsc_accept_transfer: self.handle_get_accepted,
            GSCTradingClient.gsc_success_transfer: self.handle_get_success
        }
        self.send_handlers = {
            GSCTradingClient.gsc_choice_transfer: self.handle_recv_mon,
            GSCTradingClient.gsc_accept_transfer: self.handle_recv_accepted,
            GSCTradingClient.gsc_success_transfer: self.handle_recv_success
        }
    
    async def process(self, data, connection):
        """
        Processes the data. Either calls the send handlers
        ot the get handlers. After that, it sends a message,
        if there is the need to do so.
        """
        request = self.hll.process_received_data(data, connection, send_data=False)
        to_send = None
        if request[0] == GSCTradingStrings.get_request:
            if request[1] in self.get_handlers.keys():
                to_send = self.get_handlers[request[1]]()
        elif request[0] == GSCTradingStrings.send_request:
            if request[1] in self.send_handlers.keys():
                to_send = self.send_handlers[request[1]](self.hll.recv_dict[request[1]])
                
        if to_send is not None:
            await connection.send(to_send)
    
    def handle_get_pool(self):
        """
        Gets the pokémon from the pool and sends it to the client.
        """
        if self.mon_index is None or self.clear_pool:
            self.received_mon = None
            self.received_accepted = None
            self.received_success = None
            self.own_id = GSCUtilsMisc.inc_byte(self.own_id)
            self.mon_index = None
            self.clear_pool = False
        self.mon_index, mon = ServerUtils.get_mon_index(self.mon_index)
        return self.hll.prepare_send_data(GSCTradingClient.gsc_pool_transfer, [self.own_id] + GSCUtils.single_mon_to_data(mon[0], mon[1]))
    
    def handle_get_accepted(self):
        """
        If the proper steps have been taken, it sends whether the data
        will be accepted into the server or not.
        If not, it requests whatever data it is missing.
        The client has to have already sent an accept.
        """
        if self.mon_index is not None:
            ret = self.check_retransmits()
            if ret is not None:
                return ret
            if self.last_accepted is None or self.last_accepted != self.received_accepted[0]:
                self.last_accepted = self.received_accepted[0]
                self.own_id = GSCUtilsMisc.inc_byte(self.own_id)
            if self.received_accepted[1] == PoolTradeServer.gsc_accept_trade and self.received_mon[1] is not None:
                return self.hll.prepare_send_data(GSCTradingClient.gsc_accept_transfer, [self.own_id] + [PoolTradeServer.gsc_accept_trade])
            else:
                return self.hll.prepare_send_data(GSCTradingClient.gsc_accept_transfer, [self.own_id] + [PoolTradeServer.gsc_decline_trade])
        return None
    
    def handle_get_success(self):
        """
        If the proper steps have been taken, it sends a success signal.
        If not, it requests whatever data it is missing.
        The client has to have already sent a success.
        """
        if self.mon_index is not None:
            ret = self.check_retransmits(counter=2)
            if ret is not None:
                return ret
            if self.last_success is None or self.last_success != self.received_success[0]:
                self.last_success = self.received_success[0]
                self.own_id = GSCUtilsMisc.inc_byte(self.own_id)
                self.clear_pool = True
                mons[self.mon_index] = self.received_mon[1]
                ServerUtils.save_mons()
                in_use_mons.remove(self.mon_index)
            return self.hll.prepare_send_data(GSCTradingClient.gsc_success_transfer, [self.own_id] + [PoolTradeServer.gsc_success_value])
        return None

    def check_retransmits(self, counter=1):
        """
        Handles checking that the requested data is present.
        If not, it prepares a request for retransmission.
        """
        if self.received_mon is None or (self.received_accepted is not None and (self.received_accepted[0] != GSCUtilsMisc.inc_byte(self.received_mon[0]))):
            return self.hll.prepare_get_data(GSCTradingClient.gsc_choice_transfer)
        if counter > 0:
            if self.received_accepted is None or (self.received_success is not None and (self.received_success[0] != GSCUtilsMisc.inc_byte(self.received_accepted[0]))):
                return self.hll.prepare_get_data(GSCTradingClient.gsc_accept_transfer)
        if counter > 1:
            if self.received_success is None or self.received_mon[1] is None:
                return self.hll.prepare_get_data(GSCTradingClient.gsc_success_transfer)
        return None
    
    def handle_recv_mon(self, data):
        """
        Gets the pokémon the client wants to put into the Pool.
        """
        if self.mon_index is not None:
            id = data[0]
            mon = GSCUtils.single_mon_from_data(self.checks, data[2:])
            self.received_accepted = None
            self.received_mon = [id, mon]
        return None
    
    def handle_recv_accepted(self, data):
        if self.mon_index is not None and self.received_mon is not None:
            id = data[0]
            self.received_success = None
            self.received_accepted = [id, data[1]]
        return None
    
    def handle_recv_success(self, data):
        if self.mon_index is not None and self.received_mon is not None and self.received_accepted is not None:
            id = data[0]
            self.received_success = [id, data[1]]
        return None
    
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
                if curr_room in user_pools.keys():
                    user_pools.pop(curr_room)
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