import socket
import threading
import select
from .websocket_client import WebsocketClient
from time import sleep
from .gsc_trading_strings import GSCTradingStrings
from .gsc_trading_listener import GSCTradingListener

class P2PConnection (threading.Thread):
    """
    Class which handles sending/receiving from another client.
    """
    PACKET_SIZE_BYTES = 2048
    SLEEP_TIMER = 0.01

    def __init__(self, menu, kill_function, host='localhost', port=0):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.verbose = menu.verbose
        self.host = host
        self.port = port
        self.room = menu.room
        self.hll = GSCTradingListener()
        self.kill_function = kill_function
        self.ws = WebsocketClient(menu.server[0], menu.server[1], kill_function)

    def run(self):
        """
        Does the initial connection, gets the peer's role (client or server)
        and then executes socket_conn for handling the rest.
        """
        is_client = False
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        
            try:
                s.bind((self.host, self.port))
            except Exception as e:
                print(GSCTradingStrings.socket_error_str, str(e))
                self.kill_function()
                
            s.listen(1)
            real_port = int(s.getsockname()[1])
            if self.verbose:
                print(GSCTradingStrings.p2p_listening_str.format(host=self.host, port=real_port))
                
            response = self.ws.get_peer(self.host, real_port, self.room)
            if response.startswith("SERVER"):
                is_server = True
            else:
                other_host = response[6:].split(':')[0]
                other_port = int(response[6:].split(':')[1])
                is_server = False
            
            if is_server:
                #Get client's connection
                connection, client_addr = s.accept()
                if self.verbose:
                    print(GSCTradingStrings.p2p_server_str.format(host=client_addr[0], port=client_addr[1]))

                with connection:
                    self.socket_conn(connection)
            else:
                is_client = True
        
        if not is_server:            
            #Connect to the other client
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if self.verbose:
                    print(GSCTradingStrings.p2p_client_str.format(host=other_host, port=other_port))
                s.connect((other_host, other_port))
                self.socket_conn(s)
    
    def socket_conn(self, connection):
        """
        Handles both reading the received data and sending.
        """
        try:
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
                        print(GSCTradingStrings.connection_dropped_str)
                        break
                    self.hll.process_received_data(data, connection)
                if len(ready_to_write) > 0 and self.hll.to_send is not None:
                    connection.send(self.hll.to_send)
                    self.hll.to_send = None
                sleep(P2PConnection.SLEEP_TIMER)
                
        except Exception as e:
            print(GSCTradingStrings.socket_error_str, str(e))
            self.kill_function()