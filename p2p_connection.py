import socket
import threading
import select
from time import sleep

class P2PConnection (threading.Thread):
    PACKET_FORMAT = '<4BI'
    PACKET_SIZE_BYTES = 2048

    def __init__(self, verbose=False, host='localhost', port=22222, is_server=True):
        threading.Thread.__init__(self)
        self.verbose = verbose
        self.host = host
        self.port = port
        self.is_server = is_server
        self.to_send = None

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
                s.send(b"Hello, world")
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
                    connection.send(data)
                    if self.is_server:
                        print(f"Received {data!r}")
                    else:
                        print(f"Rereceived {data!r}")
                
        except Exception as e:
            print('Socket error:', str(e))