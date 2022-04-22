import socket
import struct
import select
import timeit
import threading
from time import sleep
from .gsc_trading_strings import GSCTradingStrings
from .gsc_trading_data_utils import GSCUtilsMisc

# Implements the BGB link cable protocol
# See https://bgb.bircd.org/bgblink.html
# Base from: https://github.com/mwpenny/gbplay

class BGBLinkCableSender(threading.Thread):
    SLEEP_TIMER = 0.01
    def __init__(self, server, connection):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._server = server
        self._connection = connection
    
    def run(self):
        while True:
            try:
                send_data = self._server.send_as_master()
                if send_data:
                    self._connection.send(send_data)
                    self._server.to_send = None
                sleep(BGBLinkCableSender.SLEEP_TIMER)
                        
            except Exception as e:
                print(GSCTradingStrings.socket_error_str, str(e))
                self._server.kill_function()
        

class BGBLinkCableServer(threading.Thread):
    PACKET_FORMAT = '<4BI'
    PACKET_SIZE_BYTES = 8
    SLEEP_TIMER = 0.01

    def __init__(self, data_handler, menu, kill_function, very_verbose=False):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._handlers = {
            1: self._handle_version,
            101: self._handle_joypad_update,
            104: self._handle_sync1,
            105: self._handle_sync2,
            106: self._handle_sync3,
            108: self._handle_status,
            109: self._handle_want_disconnect
        }
        self._last_received_timestamp = 0
        self._client_data_handler = data_handler
        self.can_go = False
        self.verbose = menu.verbose
        self.very_verbose = very_verbose
        self.host = menu.emulator[0]
        self.port = menu.emulator[1]
        self.kill_function = kill_function
        self.to_send = None
    
    def verbose_print(self, to_print, end='\n'):
        """
        Print if verbose...
        """
        GSCUtilsMisc.verbose_print(to_print, self.verbose, end=end)

    def get_curr_timestamp(self):
        return int(timeit.default_timer()*(2**21)) & 0x7FFFFFFF
        
    def get_offset(self):
        return int((self.get_curr_timestamp() - self._last_base_timestamp))

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            '''
            server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,
                    1)  # requires nodelay
            '''
            try:
                server.bind((self.host, self.port))
            except Exception as e:
                print(GSCTradingStrings.socket_error_str, str(e))
                self.kill_function()
                    
            server.listen(1)  # One Game Boy to rule them all
            self.verbose_print(GSCTradingStrings.bgb_listening_str.format(host=self.host, port=self.port))

            connection, client_addr = server.accept()
            self.verbose_print(GSCTradingStrings.bgb_server_str.format(host=client_addr[0], port=client_addr[1]))

            with connection:
                try:
                    # Initial handshake - send protocol version number
                    connection.send(struct.pack(
                        self.PACKET_FORMAT,
                        1,  # Version packet
                        1,  # Major
                        4,  # Minor
                        0,  # Patch
                        0   # Timestamp
                    ))
                    
                    self._last_base_timestamp = self.get_curr_timestamp()
                    sender = BGBLinkCableSender(self, connection)
                    sender.start()

                    while True:
                        data = connection.recv(self.PACKET_SIZE_BYTES)
                        if not data:
                            print(GSCTradingStrings.connection_dropped_str)
                            self.kill_function()
                            break

                        b1, b2, b3, b4, timestamp = struct.unpack(self.PACKET_FORMAT, data)
                        if timestamp != 0:
                            self._last_received_timestamp = timestamp
                            self._last_base_timestamp = self.get_curr_timestamp()

                        # Cheat, and say we are exactly in sync with the client
                        
                        handler = self._handlers[b1]
                        response = handler(b2, b3, b4)

                        if response:
                            connection.send(response)
                        
                except Exception as e:
                    print(GSCTradingStrings.socket_error_str, str(e))
                    self.kill_function()

    def _handle_version(self, major, minor, patch):
        if self.very_verbose:
            print(f'Received version packet: {major}.{minor}.{patch}')

        if (major, minor, patch) != (1, 4, 0):
            raise Exception(f'Unsupported protocol version {major}.{minor}.{patch}')

        return self._get_status_packet()

    def _handle_joypad_update(self, _b2, _b3, _b4):
        # Do nothing. This is intended to control an emulator remotely.
        pass

    def _handle_sync1(self, data, control, _b4):
        return struct.pack(
            self.PACKET_FORMAT,
            105,        # Sync3 packet
            0,          # Not doing a passive transfer
            0x80,       # Deprecated
            0,          # Deprecated
            self._last_received_timestamp
        )

    def send_as_master(self):
        if self._last_received_timestamp != 0:
            response = self.to_send
            if response is not None:
                return struct.pack(
                    self.PACKET_FORMAT,
                    104,        # Master data packet
                    response,   # Data value
                    0x80,       # Control value
                    0,          # Unused
                    self._last_received_timestamp + self.get_offset()
                )
            elif not self.can_go:
                return struct.pack(
                    self.PACKET_FORMAT,
                    104,        # Master data packet
                    0,          # Data value
                    0x80,       # Control value
                    0,          # Unused
                    self._last_received_timestamp + self.get_offset()
                )
        else:
            return self._send_sync()

    def _send_sync(self):
        if self.very_verbose:
            print('Sending sync3 packet')

        # Ack/echo
        return struct.pack(
            self.PACKET_FORMAT,
            106,    # Sync3 packet
            0,
            0,
            0,
            self._last_received_timestamp + self.get_offset()
        )

    def _handle_sync2(self, data, control, _b4):
        if self.can_go:
            self._client_data_handler(data)

    def _handle_sync3(self, b2, b3, b4):
        if self.very_verbose:
            print('Received sync3 packet')

        # Ack/echo
        if b2 == 1:
            if not self.can_go:
                self.verbose_print("Go!")
                self.can_go = True
            self._client_data_handler(0)
        else:
            return struct.pack(
                self.PACKET_FORMAT,
                106,    # Sync3 packet
                b2,
                b3,
                b4,
                self._last_received_timestamp + self.get_offset()
            )

    def _handle_status(self, b2, _b3, _b4):
        # TODO: stop logic when client is paused
        if self.very_verbose:
            print('Received status packet:')
            print('\tRunning:', (b2 & 1) == 1)
            print('\tPaused:', (b2 & 2) == 2)
            print('\tSupports reconnect:', (b2 & 4) == 4)

        # The docs say not to respond to status with status,
        # but not doing this causes link instability
        return self._get_status_packet()

    def _handle_want_disconnect(self, _b2, _b3, _b4):
        print('Client has initiated disconnect')

    def _get_status_packet(self):
        return struct.pack(
            self.PACKET_FORMAT,
            108,    # Status packet
            1,      # State=running
            0,      # Unused
            0,      # Unused
            self._last_received_timestamp
        )