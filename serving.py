#!/usr/bin/env python

import asyncio
import websockets
import threading
import signal
import os
from random import Random
from time import sleep
import ipaddress
from utilities.high_level_listener import HighLevelListener
from utilities.gsc_trading import GSCTradingClient
from utilities.rby_trading import RBYTradingClient
from utilities.gsc_trading_strings import GSCTradingStrings
from utilities.gsc_trading_data_utils import *
from utilities.rby_trading_data_utils import *

link_rooms = [{},{}]
user_pools = [{},{}]
mons = [[],[]]
in_use_mons = [set(),set()]

class ServerUtils:
    saved_mons_path = "pool_mons"
    bin_eop = ".bin"
    
    def save_mons(gen):
        """
        Saves the currently loaded Pokémon to file.
        """
        data = []
        for m in mons[gen]:
            if gen == 1:
                data += GSCUtils.single_mon_to_data(m[0], m[1])
            elif gen == 0:
                data += RBYUtils.single_mon_to_data(m[0], m[1])
        GSCUtilsMisc.write_data(ServerUtils.saved_mons_path + str(gen + 1) + ServerUtils.bin_eop, data)
    
    def load_mons(checks, gen):
        """
        Loads the Pool's Pokémon from file.
        """
        preparing_mons = []
        raw_data = GSCUtilsMisc.read_data(ServerUtils.saved_mons_path + str(gen + 1) + ServerUtils.bin_eop)
        if raw_data is not None:
            single_entry_len = len(checks.single_pokemon_checks_map)
            if gen == 1:
                single_entry_len += 1
            entries = int(len(raw_data)/single_entry_len)
            for i in range(entries):
                if gen == 1:
                    mon = GSCUtils.single_mon_from_data(checks, raw_data[i*single_entry_len:(i+1)*single_entry_len])
                elif gen == 0:
                    mon = RBYUtils.single_mon_from_data(checks, raw_data[i*single_entry_len:(i+1)*single_entry_len])
                if mon is not None:
                    preparing_mons += [mon]
            in_use_mons[gen] = set()
            mons[gen] = preparing_mons
    
    def get_mon_index(index, gen):
        """
        If the index is None, it randomly selects a free one.
        Returns the pokémon in that slot.
        """
        while index is None:
            rnd = Random()
            rnd.seed()
            new_index = rnd.randint(0,len(mons[gen])-1)
            if new_index not in in_use_mons[gen]:
                in_use_mons[gen].add(new_index)
                index = new_index
        return index, mons[gen][index]

class PoolTradeServer:
    """
    Class which handles the pool trading part.
    """
    accept_trade = [0x62, 0x72]
    decline_trade = [0x61, 0x71]
    success_value = [0x91, 0x91]
    
    def __init__(self, gen):
        checks_class = RBYChecks
        self.trading_client_class = RBYTradingClient
        self.utils_class = RBYUtils
        if gen == 1:
            checks_class = GSCChecks
            self.trading_client_class = GSCTradingClient
            self.utils_class = GSCUtils
        self.checks = checks_class([0,0,0], True)
        rnd = Random()
        rnd.seed()
        self.gen = gen
        self.own_id = rnd.randint(0,255)
        self.last_accepted = None
        self.last_success = None
        self.clear_pool = True
        self.hll = HighLevelListener()
        self.mon_index = None
        self.received_mon = None
        self.received_accepted = None
        self.received_success = None
        self.get_handlers = {
            self.trading_client_class.pool_transfer: self.handle_get_pool,
            self.trading_client_class.accept_transfer: self.handle_get_accepted,
            self.trading_client_class.success_transfer: self.handle_get_success
        }
        self.send_handlers = {
            self.trading_client_class.choice_transfer: self.handle_recv_mon,
            self.trading_client_class.accept_transfer: self.handle_recv_accepted,
            self.trading_client_class.success_transfer: self.handle_recv_success
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
        self.mon_index, mon = ServerUtils.get_mon_index(self.mon_index, self.gen)
        return self.hll.prepare_send_data(self.trading_client_class.pool_transfer, [self.own_id] + self.utils_class.single_mon_to_data(mon[0], mon[1]))
    
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
            if self.received_accepted[1] == PoolTradeServer.accept_trade[self.gen] and self.received_mon[1] is not None:
                return self.hll.prepare_send_data(self.trading_client_class.accept_transfer, [self.own_id] + [PoolTradeServer.accept_trade[self.gen]])
            else:
                return self.hll.prepare_send_data(self.trading_client_class.accept_transfer, [self.own_id] + [PoolTradeServer.decline_trade[self.gen]])
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
                mons[self.gen][self.mon_index] = self.received_mon[1]
                ServerUtils.save_mons(self.gen)
                in_use_mons[self.gen].remove(self.mon_index)
            return self.hll.prepare_send_data(self.trading_client_class.success_transfer, [self.own_id] + [PoolTradeServer.success_value[self.gen]])
        return None

    def check_retransmits(self, counter=1):
        """
        Handles checking that the requested data is present.
        If not, it prepares a request for retransmission.
        """
        if self.received_mon is None or (self.received_accepted is not None and (self.received_accepted[0] != GSCUtilsMisc.inc_byte(self.received_mon[0]))):
            return self.hll.prepare_get_data(self.trading_client_class.choice_transfer)
        if counter > 0:
            if self.received_accepted is None or (self.received_success is not None and (self.received_success[0] != GSCUtilsMisc.inc_byte(self.received_accepted[0]))):
                return self.hll.prepare_get_data(self.trading_client_class.accept_transfer)
        if counter > 1:
            if self.received_success is None or self.received_mon[1] is None:
                return self.hll.prepare_get_data(self.trading_client_class.success_transfer)
        return None
    
    def handle_recv_mon(self, data):
        """
        Gets the pokémon the client wants to put into the Pool.
        """
        if self.mon_index is not None:
            id = data[0]
            mon = self.utils_class.single_mon_from_data(self.checks, data[2:])
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
        self.checks = [RBYChecks([0,0,0], True), GSCChecks([0,0,0], True)]
        ServerUtils.load_mons(self.checks[0], 0)
        ServerUtils.load_mons(self.checks[1], 1)

    async def link_function(websocket, data, path):
        '''
        Handler which either registers a client to a room, or links
        two clients together.
        Decides which one is the client and which one is the server in the
        P2P connection randomly.
        '''
        room = 100000
        if len(path) >= 12:
            gen = WebsocketServer.get_gen(path)
            room = int(path[7:12])
            valid = True
            try:
                ip = ipaddress.ip_address(data.split(":")[0])
            except ValueError:
                if data.split(":")[0] != "localhost":
                    valid = False
            if valid:
                if room not in link_rooms[gen].keys():
                    link_rooms[gen][room] = [data, websocket]
                else:
                    info = link_rooms[gen].pop(room)
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
    
    async def pool_function(websocket, data, room, path):
        '''
        Handler which handles pool trading messages.
        '''
        gen = WebsocketServer.get_gen(path)
        # Assign an ID to the user
        if room >= 100000:
            rnd = Random()
            rnd.seed()
            completed = False
            while not completed:
                room = rnd.randint(0,99999)
                if not room in user_pools[gen].keys():
                    user_pools[gen][room] = PoolTradeServer(gen)
                    completed = True
        
        await user_pools[gen][room].process(data, websocket)
        
        return room
    
    def get_gen(path):
        gen = int(path[5]) - 1
        if gen >= 2:
            gen = 1
        if gen < 0:
            gen = 0
        return gen
        
    def cleaner(identifier, path):
        gen = WebsocketServer.get_gen(path)
        if path.startswith("/link") and identifier in link_rooms[gen].keys():
            link_rooms[gen].pop(identifier)
        if path.startswith("/pool") and identifier in user_pools[gen].keys():
            pool = user_pools[gen].pop(identifier)
            if pool.mon_index is not None:
                if pool.mon_index in in_use_mons[gen]:
                    in_use_mons[gen].remove(pool.mon_index)

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
                WebsocketServer.cleaner(curr_room, path)
                break
            except Exception as e:
                print('Websocket server error:', str(e))
                WebsocketServer.cleaner(curr_room, path)
                break
            if path.startswith("/link"):
                curr_room = await WebsocketServer.link_function(websocket, data, path)
            if path.startswith("/pool"):
                curr_room = await WebsocketServer.pool_function(websocket, data, curr_room, path)
                
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
RBYUtils()
ws = WebsocketServer()
ws.start()

signal.signal(signal.SIGINT, signal_handler)

while True:
    sleep(1)