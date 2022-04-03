import socket
import threading
import select
from time import sleep

class P2PConnection (threading.Thread):
    PACKET_SIZE_BYTES = 2048
    SLEEP_TIMER = 0.01
    REQ_INFO_POSITION = 0
    DATA_POSITION = 4
    send_request = "S"
    get_request = "G"

    def __init__(self, verbose=False, host='localhost', port=22222, is_server=True):
        threading.Thread.__init__(self)
        self.verbose = verbose
        self.host = host
        self.port = port
        self.is_server = is_server
        self.to_send = None
        self.recv_dict = {}
        self.send_dict = {}
    
    def prepare_send_data(self, type, data):
        return bytearray(list((P2PConnection.send_request + type).encode()) + data)
    
    def prepare_get_data(self, type):
        return bytearray(list((P2PConnection.get_request + type).encode()))
    
    def reset_dict(self, type, chosen_dict):
        if type in chosen_dict.keys():
            chosen_dict.pop(type)
    
    def reset_recv(self, type):
        self.reset_dict(type, self.recv_dict)
    
    def reset_send(self, type):
        self.reset_dict(type, self.send_dict)
    
    def send_data(self, type, data):
        self.send_dict[type] = data
        self.to_send = self.prepare_send_data(type, data)
        while self.to_send is not None:
            sleep(P2PConnection.SLEEP_TIMER)
    
    def recv_data(self, type, reset=True):
        if not type in self.recv_dict.keys():
            self.to_send = self.prepare_get_data(type)
            while self.to_send is not None:
                sleep(P2PConnection.SLEEP_TIMER)
            return None
        else:
            if reset:
                return self.recv_dict.pop(type)
            return self.recv_dict[type]

    def run(self):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if self.is_server:
                s.bind((self.host, self.port))
                s.listen(0)
                print(f'Listening on {self.host}:{self.port}...')
                
                #Get client's connection
                connection, client_addr = s.accept()
                print(f'Received connection from {client_addr[0]}:{client_addr[1]}')

                with connection:
                    self.socket_conn(connection)
            else:
                s.connect((self.host, self.port))
                self.socket_conn(s)
    
    def socket_conn(self, connection):
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
                        print('Connection dropped')
                        break
                    req_info = data[P2PConnection.REQ_INFO_POSITION:P2PConnection.REQ_INFO_POSITION+4].decode()
                    req_kind = req_info[0]
                    req_type = req_info[1:4]
                    if req_kind == P2PConnection.send_request:
                        self.recv_dict[req_type] = list(data[P2PConnection.DATA_POSITION:])
                    elif req_kind == P2PConnection.get_request:
                        if req_type in self.send_dict.keys():
                            connection.send(self.prepare_send_data(req_type, self.send_dict[req_type]))
                if len(ready_to_write) > 0 and self.to_send is not None:
                    connection.send(self.to_send)
                    self.to_send = None
                sleep(P2PConnection.SLEEP_TIMER)
                
        except Exception as e:
            print('Socket error:', str(e))