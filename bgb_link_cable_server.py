import socket
import struct
import select
import timeit
import threading
from time import sleep

# Implements the BGB link cable protocol
# See https://bgb.bircd.org/bgblink.html
class BGBLinkCableServer (threading.Thread):
    PACKET_FORMAT = '<4BI'
    PACKET_SIZE_BYTES = 8
    TRADE_AFTER = 0x2000

    def __init__(self, data_handler, verbose=False, host='', port=8765):
        threading.Thread.__init__(self)
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
        self.verbose = verbose
        self.host = host
        self.port = port
        self.to_send = None

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

            server.bind((self.host, self.port))
            server.listen(0)  # One Game Boy to rule them all
            print(f'Listening on {self.host}:{self.port}...')

            connection, client_addr = server.accept()
            print(f'Received connection from {client_addr[0]}:{client_addr[1]}')

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

                    a = True
                    self._last_base_timestamp = self.get_curr_timestamp()
                    while True:
                        ready_to_read, ready_to_write, in_error = \
                           select.select(
                              [connection],
                              [connection],
                              [],
                              0)
                        if len(ready_to_read) > 0:
                            data = connection.recv(self.PACKET_SIZE_BYTES)
                            if not data:
                                print('Connection dropped')
                                break

                            b1, b2, b3, b4, timestamp = struct.unpack(self.PACKET_FORMAT, data)
                            #print(str(b1) + ": " + str(self._last_received_timestamp))
                            if timestamp != 0:
                                self._last_received_timestamp = timestamp
                                self._last_base_timestamp = self.get_curr_timestamp()

                            # Cheat, and say we are exactly in sync with the client
                            

                            handler = self._handlers[b1]
                            response = handler(b2, b3, b4)

                            if response:
                                connection.send(response)
                        
                        if a:
                            a = False
                            self.last_block = self.get_curr_timestamp()
                            send_data = self._send_as_master()
                            if send_data:
                                connection.send(send_data)
                                self.to_send = None
                        if self.get_curr_timestamp()-self.last_block > self.TRADE_AFTER:
                            a = True
                        
                except Exception as e:
                    print('Socket error:', str(e))

    def _handle_version(self, major, minor, patch):
        if self.verbose:
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

    def _send_as_master(self):
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
        if self.verbose:
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
        if self.verbose:
            print('Received sync3 packet')

        # Ack/echo
        if b2 == 1:
            if not self.can_go:
                print("Go!")
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
        if self.verbose:
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