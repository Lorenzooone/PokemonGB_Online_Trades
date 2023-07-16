#!/usr/bin/env python

import datetime
import asyncio
import websockets
import threading
import signal
import os
import boto3
import botocore
from random import Random
from time import sleep
from utilities.trading_version import TradingVersion
from utilities.high_level_listener import HighLevelListener
from utilities.gsc_trading import GSCTradingClient
from utilities.rby_trading import RBYTradingClient
from utilities.rse_sp_trading import RSESPTradingClient
from utilities.gsc_trading_strings import GSCTradingStrings
from utilities.gsc_trading_data_utils import *
from utilities.rby_trading_data_utils import *
from utilities.rse_sp_trading_data_utils import *

s3 = boto3.client("s3")
uploader = None

total_rooms = 100000
link_rooms = [[set()]*total_rooms,[set()]*total_rooms,[set()]*total_rooms]
mons = [[],[],[]]
in_use_mons = [set(),set(),set()]
upload_after = 24

class ServerUtils:
    saved_mons_path = "pool_mons"
    default_path = "pool_default_data/"
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
            elif gen == 2:
                data += RSESPUtils.single_mon_to_data(m[0], m[1])
        GSCUtilsMisc.write_data(ServerUtils.saved_mons_path + str(gen + 1) + ServerUtils.bin_eop, data)
        global uploader
        if uploader is None:
            uploader = DataUploader()
            uploader.start()
        uploader.to_up[gen] = True
    
    def load_mons(checks, gen):
        """
        Loads the Pool's Pokémon from file.
        """
        preparing_mons = []
        
        try:
            s3.download_file(Bucket="pokemon-gb-online-pool-gen1", Key=ServerUtils.saved_mons_path + str(gen + 1) + ServerUtils.bin_eop, Filename="./" + ServerUtils.saved_mons_path + str(gen + 1) + ServerUtils.bin_eop)
            raw_data = GSCUtilsMisc.read_data(ServerUtils.saved_mons_path + str(gen + 1) + ServerUtils.bin_eop)
        except botocore.exceptions.NoCredentialsError:
            raw_data = GSCUtilsMisc.read_data(ServerUtils.default_path + ServerUtils.saved_mons_path + str(gen + 1) + ServerUtils.bin_eop)
        if raw_data is not None:
            single_entry_len = len(checks.single_pokemon_checks_map)
            if gen == 1:
                single_entry_len += 1
            entries = int(len(raw_data)/single_entry_len)
            for i in range(entries):
                if gen == 1:
                    mon = GSCUtils.single_mon_from_data(checks, raw_data[i*single_entry_len:(i+1)*single_entry_len])
                elif gen == 2:
                    mon = RSESPUtils.single_mon_from_data(checks, raw_data[i*single_entry_len:(i+1)*single_entry_len])
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
            if len(in_use_mons[gen]) == len(mons[gen]):
                return None, None
            rnd = Random()
            rnd.seed()
            new_index = rnd.randint(0,len(mons[gen])-1)
            if new_index not in in_use_mons[gen]:
                in_use_mons[gen].add(new_index)
                index = new_index
        return index, mons[gen][index]

class DataUploader(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon=True
        self.to_up = [False, False, False]
    
    def run(self):
        sleep(upload_after*60)
        global uploader
        uploader = None
        for gen in range(2):
            if self.to_up[gen]:
                try:
                    s3.upload_file(Bucket="pokemon-gb-online-pool-gen1", Key=ServerUtils.saved_mons_path + str(gen + 1) + ServerUtils.bin_eop, Filename="./" + ServerUtils.saved_mons_path + str(gen + 1) + ServerUtils.bin_eop)
                except botocore.exceptions.NoCredentialsError:
                    pass

class ServerSpecificTransfers:
    def __init__(self):
        self.prepare_random_data()
    
    def prepare_random_data(self):
        rnd = Random()
        rnd.seed()
        self.random_data = []
        self.last_read = 0
        for i in range(10):
            self.random_data += [rnd.randint(0,0xFC)]

    def handle_get_version(hll, version_transfer):
        return hll.prepare_send_data(version_transfer, TradingVersion.prepare_version_data())

    def handle_get_random(self, hll, random_transfer):
        if self.last_read != 0:
            if (datetime.datetime.now() - self.last_read).total_seconds() > (2 * 60):
                self.prepare_random_data()
        self.last_read = datetime.datetime.now()
        return hll.prepare_send_data(random_transfer, self.random_data)

class PoolTradeServer:
    """
    Class which handles the pool trading part.
    """
    accept_trade = [0x62, 0x72, [0xA20000, 0xB20000]]
    decline_trade = [0x61, 0x71, [0xA10000, 0xB10000]]
    success_value = [0x91, 0x91, [0x900000, 0x910000, 0x920000, 0x930000, 0x940000, 0x950000, 0x9C0000]]
    failure_value = [0x91, 0x91, 0x9F0000]
    num_accepts = [1,1,2]
    num_successes = [1,1,7]
    
    def __init__(self, gen):
        checks_class = RBYChecks
        self.trading_client_class = RBYTradingClient
        self.utils_class = RBYUtils
        if gen == 1:
            checks_class = GSCChecks
            self.trading_client_class = GSCTradingClient
            self.utils_class = GSCUtils
        elif gen == 2:
            checks_class = RSESPChecks
            self.trading_client_class = RSESPTradingClient
            self.utils_class = RSESPUtils
        self.checks = checks_class([0,0,0], True)
        rnd = Random()
        rnd.seed()
        self.gen = gen
        self.own_id = rnd.randint(0,255)
        self.last_accepted = None
        self.last_success = None
        self.clear_pool = True
        self.hll = HighLevelListener()
        self.hll.set_valid_transfers(self.trading_client_class.possible_transfers)
        self.mon_index = None
        self.received_mon = None
        self.received_accepted = None
        self.received_success = None
        self.can_continue = True
        if gen != 2:
            self.get_handlers = {
                self.trading_client_class.pool_transfer: self.handle_get_pool,
                self.trading_client_class.accept_transfer: self.handle_get_accepted,
                self.trading_client_class.success_transfer: self.handle_get_success,
                self.trading_client_class.version_client_transfer: self.handle_get_client_version,
                self.trading_client_class.version_server_transfer: self.handle_get_server_version,
                self.trading_client_class.random_data_transfer: self.handle_get_random_data
            }
            self.send_handlers = {
                self.trading_client_class.choice_transfer: self.handle_recv_mon,
                self.trading_client_class.accept_transfer: self.handle_recv_accepted,
                self.trading_client_class.success_transfer: self.handle_recv_success
            }
        else:
            self.reset_gen3_accepted()
            self.reset_gen3_success()
            self.last_accepted = [None, None]
            self.last_success = [None, None, None, None, None, None, None]
            self.get_handlers = {
                self.trading_client_class.pool_transfer: self.handle_get_pool,
                self.trading_client_class.accept_transfer[0]: self.handle_get_accepted3_0,
                self.trading_client_class.accept_transfer[1]: self.handle_get_accepted3_1,
                self.trading_client_class.success_transfer[0]: self.handle_get_success3_0,
                self.trading_client_class.success_transfer[1]: self.handle_get_success3_1,
                self.trading_client_class.success_transfer[2]: self.handle_get_success3_2,
                self.trading_client_class.success_transfer[3]: self.handle_get_success3_3,
                self.trading_client_class.success_transfer[4]: self.handle_get_success3_4,
                self.trading_client_class.success_transfer[5]: self.handle_get_success3_5,
                self.trading_client_class.success_transfer[6]: self.handle_get_success3_6,
                self.trading_client_class.version_client_transfer: self.handle_get_client_version,
                self.trading_client_class.version_server_transfer: self.handle_get_server_version,
                self.trading_client_class.random_data_transfer: self.handle_get_random_data
            }
            self.send_handlers = {
                self.trading_client_class.pool_transfer_out: self.handle_recv_mon3,
                self.trading_client_class.accept_transfer[0]: self.handle_recv_accepted3_0,
                self.trading_client_class.accept_transfer[1]: self.handle_recv_accepted3_1,
                self.trading_client_class.success_transfer[0]: self.handle_recv_success3_0,
                self.trading_client_class.success_transfer[1]: self.handle_recv_success3_1,
                self.trading_client_class.success_transfer[2]: self.handle_recv_success3_2,
                self.trading_client_class.success_transfer[3]: self.handle_recv_success3_3,
                self.trading_client_class.success_transfer[4]: self.handle_recv_success3_4,
                self.trading_client_class.success_transfer[5]: self.handle_recv_success3_5,
                self.trading_client_class.success_transfer[6]: self.handle_recv_success3_6
            }
    
    def reset_gen3_accepted(self):
        self.received_accepted = [None, None]
    
    def reset_gen3_success(self):
        self.received_success = [None, None, None, None, None, None, None]
    
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
            if self.gen != 2:
                self.received_accepted = None
                self.received_success = None
            else:
                self.reset_gen3_accepted()
                self.reset_gen3_success()
            self.own_id = GSCUtilsMisc.inc_byte(self.own_id)
            self.mon_index = None
            self.clear_pool = False
        self.mon_index, self.mon = ServerUtils.get_mon_index(self.mon_index, self.gen)
        if self.mon_index is None:
            return self.hll.prepare_send_data(self.trading_client_class.pool_transfer, [self.own_id] + [self.trading_client_class.pool_fail_value])
        else:
            return self.hll.prepare_send_data(self.trading_client_class.pool_transfer, [self.own_id] + self.utils_class.single_mon_to_data(self.mon[0], self.mon[1]))
    
    def handle_get_client_version(self):
        return ServerSpecificTransfers.handle_get_version(self.hll, self.trading_client_class.version_client_transfer)
    
    def handle_get_server_version(self):
        return ServerSpecificTransfers.handle_get_version(self.hll, self.trading_client_class.version_server_transfer)
    
    def handle_get_random_data(self):
        """
        Maybe a bit wasteful, but whatever...
        """
        i = ServerSpecificTransfers()
        return i.handle_get_random(self.hll, self.trading_client_class.random_data_transfer)
    
    def handle_get_accepted(self):
        """
        If the proper steps have been taken, it sends whether the data
        will be accepted into the server or not.
        If not, it requests whatever data it is missing.
        The client has to have already sent an accept.
        """
        if self.mon_index is not None:
            ret = self.check_retransmits(1)
            if ret is not None:
                return ret
            if self.last_accepted is None or self.last_accepted != self.received_accepted[0]:
                self.last_accepted = self.received_accepted[0]
                self.own_id = GSCUtilsMisc.inc_byte(self.own_id)
            if self.received_accepted[1] == PoolTradeServer.accept_trade[self.gen] and self.received_mon is not None and self.received_mon[1] is not None:
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
            ret = self.check_retransmits(1 + self.num_accepts[self.gen])
            if ret is not None:
                return ret
            if self.last_success is None or self.last_success != self.received_success[0]:
                self.last_success = self.received_success[0]
                self.own_id = GSCUtilsMisc.inc_byte(self.own_id)
                self.clear_pool = True
                if not self.mon_index in in_use_mons[self.gen]:
                    in_use_mons[self.gen].add(self.mon_index)
                mons[self.gen][self.mon_index] = self.received_mon[1]
                ServerUtils.save_mons(self.gen)
                try:
                    in_use_mons[self.gen].remove(self.mon_index)
                except:
                    pass
            return self.hll.prepare_send_data(self.trading_client_class.success_transfer, [self.own_id] + [PoolTradeServer.success_value[self.gen]])
        return None
    
    def handle_get_accepted3_0(self):
        return self.handle_get_accepted3_i(0)
    
    def handle_get_accepted3_1(self):
        return self.handle_get_accepted3_i(1)
    
    def handle_get_success3_0(self):
        return self.handle_get_success3_i(0)
    
    def handle_get_success3_1(self):
        return self.handle_get_success3_i(1)
    
    def handle_get_success3_2(self):
        return self.handle_get_success3_i(2)
    
    def handle_get_success3_3(self):
        return self.handle_get_success3_i(3)
    
    def handle_get_success3_4(self):
        return self.handle_get_success3_i(4)
    
    def handle_get_success3_5(self):
        return self.handle_get_success3_i(5)
    
    def handle_get_success3_6(self):
        return self.handle_get_success3_i(6)
    
    def handle_get_accepted3_i(self, index):
        """
        If the proper steps have been taken, it sends whether the data
        will be accepted into the server or not.
        If not, it requests whatever data it is missing.
        The client has to have already sent an accept.
        """
        if self.mon_index is not None:
            ret = self.check_retransmits3(index + 1)
            if ret is not None:
                return ret
            if self.last_accepted[index] is None or self.last_accepted[index] != self.received_accepted[index][0]:
                self.last_accepted[index] = self.received_accepted[index][0]
                self.own_id = GSCUtilsMisc.inc_byte(self.own_id)
            success = self.can_continue
            if self.received_mon[1] is None:
                success = False
            if success:
                for i in range(index + 1):
                    if (self.received_accepted[i][1] & 0xFF0000) != PoolTradeServer.accept_trade[self.gen][i]:
                        success = False
            if success:
                for i in range(index + 1):
                    if(self.received_accepted[i][1] & 0xFFFF) != self.received_mon[1][0].get_species():
                        success = False
            if success:
                return self.hll.prepare_send_data(self.trading_client_class.accept_transfer[index], [self.own_id] + GSCUtilsMisc.to_n_bytes_le(PoolTradeServer.accept_trade[self.gen][index] | self.mon[0].get_species(), 3))
            else:
                return self.hll.prepare_send_data(self.trading_client_class.accept_transfer[index], [self.own_id] + GSCUtilsMisc.to_n_bytes_le(PoolTradeServer.decline_trade[self.gen][index], 3))
        return None

    def expected_gen3_success_value(self, index, out_mon, in_mon):
        if index == 0:
            return out_mon.get_species()
        if index == 1:
            return out_mon.pid & 0xFFFF
        if index == 2:
            return out_mon.pid >> 16
        if index == 3:
            return in_mon.get_species()
        if index == 4:
            return in_mon.pid & 0xFFFF
        if index == 5:
            return in_mon.pid >> 16
        return 0
    
    def handle_get_success3_i(self, index):
        """
        If the proper steps have been taken, it sends a success signal.
        If not, it requests whatever data it is missing.
        The client has to have already sent a success.
        """
        if self.mon_index is not None:
            ret = self.check_retransmits3(index + 1 + self.num_accepts[self.gen])
            if ret is not None:
                return ret
            if self.last_success[index] is None or self.last_success[index] != self.received_success[index][0]:
                self.last_success[index] = self.received_success[index][0]
                self.own_id = GSCUtilsMisc.inc_byte(self.own_id)
            success = self.can_continue
            if self.received_mon[1] is None:
                success = False
            if success:
                for i in range(self.num_accepts[self.gen]):
                    if (self.received_accepted[i][1] & 0xFF0000) != PoolTradeServer.accept_trade[self.gen][i]:
                        success = False
            if success:
                for i in range(self.num_accepts[self.gen]):
                    if(self.received_accepted[i][1] & 0xFFFF) != self.received_mon[1][0].get_species():
                        success = False
            if success:
                for i in range(index + 1):
                    if (self.received_success[i][1] & 0xFF0000) != PoolTradeServer.success_value[self.gen][i]:
                        success = False
            if success:
                for i in range(index + 1):
                    if(self.received_success[i][1] & 0xFFFF) != self.expected_gen3_success_value(i, self.received_mon[1][0], self.mon[0]):
                        success = False
            if success:
                if index == (self.num_successes[self.gen]-1):
                    self.clear_pool = True
                    if not self.mon_index in in_use_mons[self.gen]:
                        in_use_mons[self.gen].add(self.mon_index)
                    mons[self.gen][self.mon_index] = self.received_mon[1]
                    ServerUtils.save_mons(self.gen)
                    try:
                        in_use_mons[self.gen].remove(self.mon_index)
                    except:
                        pass
                return self.hll.prepare_send_data(self.trading_client_class.success_transfer[index], [self.own_id] + GSCUtilsMisc.to_n_bytes_le(PoolTradeServer.success_value[self.gen][index] | self.expected_gen3_success_value(index, self.mon[0], self.received_mon[1][0]), 3))
            else:
                self.can_continue = False
                return self.hll.prepare_send_data(self.trading_client_class.success_transfer[index], [self.own_id] + GSCUtilsMisc.to_n_bytes_le(PoolTradeServer.failure_value[self.gen], 3))
        return None

    def check_retransmits(self, counter):
        """
        Handles checking that the requested data is present.
        If not, it prepares a request for retransmission.
        """
        ordered_transfer = [self.received_mon, self.received_accepted, self.received_success, None]
        ordered_transfer_strings = [self.trading_client_class.choice_transfer, self.trading_client_class.accept_transfer, self.trading_client_class.success_transfer, None]
        for i in range(1, counter+1):
            if ordered_transfer[i-1] is None or (ordered_transfer[i] is not None and (ordered_transfer[i][0] != GSCUtilsMisc.inc_byte(ordered_transfer[i-1][0]))):
                return self.hll.prepare_get_data(ordered_transfer_strings[i-1])
        return None

    def check_retransmits3(self, counter):
        """
        Handles checking that the requested data is present.
        If not, it prepares a request for retransmission.
        """
        ordered_transfer = [self.received_mon, self.received_accepted[0], self.received_accepted[1], self.received_success[0], self.received_success[1], self.received_success[2], self.received_success[3], self.received_success[4], self.received_success[5], self.received_success[6], None]
        ordered_transfer_strings = [self.trading_client_class.pool_transfer_out, self.trading_client_class.accept_transfer[0], self.trading_client_class.accept_transfer[1], self.trading_client_class.success_transfer[0], self.trading_client_class.success_transfer[1], self.trading_client_class.success_transfer[2], self.trading_client_class.success_transfer[3], self.trading_client_class.success_transfer[4], self.trading_client_class.success_transfer[5], self.trading_client_class.success_transfer[6], None]
        for i in range(1, counter+1):
            if ordered_transfer[i-1] is None or (ordered_transfer[i] is not None and (ordered_transfer[i][0] != GSCUtilsMisc.inc_byte(ordered_transfer[i-1][0]))):
                return self.hll.prepare_get_data(ordered_transfer_strings[i-1])
        return None
    
    def handle_recv_mon(self, data):
        """
        Gets the pokémon the client wants to put into the Pool.
        """
        if self.mon_index is not None:
            id = data[0]
            mon = self.utils_class.single_mon_from_data(self.checks, data[2:])
            self.received_accepted = None
            self.received_success = None
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
    
    def handle_recv_mon3(self, data):
        """
        Gets the pokémon the client wants to put into the Pool.
        """
        if self.mon_index is not None:
            id = data[0]
            if len(data) > 1:
                mon = self.utils_class.single_mon_from_data(self.checks, data[1:])
            else:
                mon = None
            self.reset_gen3_accepted()
            self.reset_gen3_success()
            self.received_mon = [id, mon]
        return None
    
    def handle_recv_accepted3_0(self, data):
        return self.handle_recv_accepted3_i(data, 0)
    
    def handle_recv_accepted3_1(self, data):
        return self.handle_recv_accepted3_i(data, 1)
    
    def handle_recv_success3_0(self, data):
        return self.handle_recv_success3_i(data, 0)
    
    def handle_recv_success3_1(self, data):
        return self.handle_recv_success3_i(data, 1)
    
    def handle_recv_success3_2(self, data):
        return self.handle_recv_success3_i(data, 2)
    
    def handle_recv_success3_3(self, data):
        return self.handle_recv_success3_i(data, 3)
    
    def handle_recv_success3_4(self, data):
        return self.handle_recv_success3_i(data, 4)
    
    def handle_recv_success3_5(self, data):
        return self.handle_recv_success3_i(data, 5)
    
    def handle_recv_success3_6(self, data):
        return self.handle_recv_success3_i(data, 6)
    
    def handle_recv_accepted3_i(self, data, index):
        failed = False
        if self.mon_index is None or self.received_mon is None:
            failed = True
        if not failed:
            for i in range(index):
                if self.received_accepted[i] is None:
                    failed = True
        if not failed:
            id = data[0]
            for i in range(index+1, self.num_accepts[self.gen]):
                self.received_accepted[i] = None
            self.reset_gen3_success()
            self.received_accepted[index] = [id, GSCUtilsMisc.from_n_bytes_le(data[1:], 3)]
        return None
    
    def handle_recv_success3_i(self, data, index):
        failed = False
        if self.mon_index is None or self.received_mon is None:
            failed = True
        if not failed:
            for i in range(self.num_accepts[self.gen]):
                if self.received_accepted[i] is None:
                    failed = True
        if not failed:
            for i in range(index):
                if self.received_success[i] is None:
                    failed = True
        if not failed:
            id = data[0]
            for i in range(index+1, self.num_successes[self.gen]):
                self.received_success[i] = None
            self.received_success[index] = [id, GSCUtilsMisc.from_n_bytes_le(data[1:], 3)]
        return None
        
class ProxyLinkServer:
    """
    Class which handles the 2-player trading part.
    """
    
    def __init__(self, gen, ws):
        checks_class = RBYChecks
        self.trading_client_class = RBYTradingClient
        self.utils_class = RBYUtils
        if gen == 1:
            checks_class = GSCChecks
            self.trading_client_class = GSCTradingClient
            self.utils_class = GSCUtils
        elif gen == 2:
            checks_class = RSESPChecks
            self.trading_client_class = RSESPTradingClient
            self.utils_class = RSESPUtils
        self.server_data = ServerSpecificTransfers()
        self.other = None
        self.other_ws = None
        self.own_ws = ws
        self.hll = HighLevelListener()
        self.hll.set_valid_transfers(self.trading_client_class.possible_transfers)
    
    async def process(self, data):
        """
        Processes the data. If valid, sends it to the other websocket.
        """
        request = self.hll.is_received_valid(data)
        if request is not None:
            processed = False
            if request[0] == GSCTradingStrings.get_request:
                if request[1] == self.trading_client_class.version_server_transfer:
                    await self.own_ws.send(ServerSpecificTransfers.handle_get_version(self.hll, self.trading_client_class.version_server_transfer))
                    processed = True
                elif request[1] == self.trading_client_class.random_data_transfer:
                    await self.own_ws.send(self.server_data.handle_get_random(self.hll, self.trading_client_class.random_data_transfer))
                    processed = True
            if not processed:
                if (self.other is not None) and (self.other.other == self):
                    await self.other_ws.send(data)
                else:
                    self.other = None
                    self.other_ws = None
                    await self.own_ws.close()
    
class WebsocketServer (threading.Thread):
    '''
    Class which handles responding to the websocket requests.
    '''
    
    def __init__(self, host="", port=11111):
        threading.Thread.__init__(self)
        self.daemon=True
        self.host = host
        try:
            self.port = int(os.environ["PORT"])
        except KeyError as e:
            self.port = port
        self.checks = [RBYChecks([0,0,0], True), GSCChecks([0,0,0], True), RSESPChecks([0,0,0], True)]
        ServerUtils.load_mons(self.checks[0], 0)
        ServerUtils.load_mons(self.checks[1], 1)
        ServerUtils.load_mons(self.checks[2], 2)

    async def link_function(websocket, data, path, link_proxy):
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
            if link_proxy is None:
                link_proxy = ProxyLinkServer(gen, websocket)
            if link_proxy.other_ws is None:
                if len(link_rooms[gen][room]) == 0:
                    if link_proxy not in link_rooms[gen][room]:
                        link_rooms[gen][room].add(link_proxy)
                elif link_proxy not in link_rooms[gen][room]:
                    other_proxy = link_rooms[gen][room].pop()
                    other_proxy.other_ws = link_proxy.own_ws
                    other_proxy.other = link_proxy
                    link_proxy.other = other_proxy
                    link_proxy.other_ws = other_proxy.own_ws
                    repl = ["CLIENT", "CLIENT"]
                    reply_old = repl[0]
                    reply_new = repl[1]
                    await link_proxy.other_ws.send(reply_old)
                    await link_proxy.own_ws.send(reply_new)
            else:
                await link_proxy.process(data)
        return room, link_proxy
    
    async def pool_function(websocket, data, path, pool_trader):
        '''
        Handler which handles pool trading messages.
        '''
        gen = WebsocketServer.get_gen(path)
        if pool_trader is None:
            pool_trader = PoolTradeServer(gen)
        
        await pool_trader.process(data, websocket)
        
        return pool_trader
    
    def get_gen(path):
        gen = int(path[5]) - 1
        if gen >= 3:
            gen = 1
        if gen < 0:
            gen = 0
        return gen
        
    async def cleaner(identifier, processer, path):
        gen = WebsocketServer.get_gen(path)
        if path.startswith("/link"):
            if processer in link_rooms[gen][identifier]:
                link_rooms[gen][identifier].remove(processer)
            if processer is not None and processer.other_ws is not None:
                other = processer.other
                processer.other = None
                processer.other_ws = None
                other.other = None
                other.other_ws = None
                await other.own_ws.close()
        if path.startswith("/pool"):
            if processer is not None and processer.mon_index is not None and not processer.clear_pool:
                if processer.mon_index in in_use_mons[gen]:
                    in_use_mons[gen].remove(processer.mon_index)

    async def handler(websocket, path):
        """
        Gets the data and then calls the proper handler while keeping
        the connection active.
        """
        curr_room = 100000
        processer = None
        while True:
            try:
                data = await websocket.recv()
            except websockets.ConnectionClosed:
                print(f"Terminated")
                await WebsocketServer.cleaner(curr_room, processer, path)
                break
            except Exception as e:
                print('Websocket server error:', str(e))
                await WebsocketServer.cleaner(curr_room, processer, path)
                break
            if path.startswith("/link"):
                curr_room, processer = await WebsocketServer.link_function(websocket, data, path, processer)
            if path.startswith("/pool"):
                processer = await WebsocketServer.pool_function(websocket, data, path, processer)
                
    def run(self):
        """
        Runs the server in a second Thread in order to keep
        the program responsive.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        start_server = websockets.serve(WebsocketServer.handler, self.host, self.port)
        loop.run_until_complete(start_server)
        loop.run_forever()

def exit_gracefully():
    os._exit(1)

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    exit_gracefully()

GSCUtils()
RBYUtils()
RSESPUtils()
ws = WebsocketServer()
ws.start()

signal.signal(signal.SIGINT, signal_handler)

while True:
    sleep(1)
