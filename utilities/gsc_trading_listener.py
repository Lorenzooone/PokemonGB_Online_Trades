from time import sleep
from .gsc_trading_strings import GSCTradingStrings

class GSCTradingListener:
    """
    Class which handles high level comunications.
    """
    SLEEP_TIMER = 0.01
    REQ_INFO_POSITION = 0
    LEN_POSITION = 4
    DATA_POSITION = 6
    
    def __init__(self):
        self.to_send = None
        self.on_receive_dict = {}
        self.recv_dict = {}
        self.send_dict = {}

    def prepare_send_data(self, type, data):
        return bytearray(list((GSCTradingStrings.send_request + type).encode()) + [(len(data) >> 8) & 0xFF, len(data) & 0xFF] + data)
    
    def prepare_get_data(self, type):
        return bytearray(list((GSCTradingStrings.get_request + type).encode()))
    
    def reset_dict(self, type, chosen_dict):
        if type in chosen_dict.keys():
            chosen_dict.pop(type)
    
    def reset_recv(self, type):
        self.reset_dict(type, self.recv_dict)
    
    def reset_send(self, type):
        self.reset_dict(type, self.send_dict)
    
    def send_data(self, type, data):
        """
        Sends the data to the other client and prepares the dict's entry
        for responding to GETs.
        """
        self.send_dict[type] = data
        self.to_send = self.prepare_send_data(type, data)
        while self.to_send is not None:
            sleep(GSCTradingListener.SLEEP_TIMER)
    
    def prepare_listener(self, type, listener):
        """
        Function called when a certain type of data is received.
        """
        self.on_receive_dict[type] = listener
    
    def recv_data(self, type, reset=True):
        """
        Checks if the data has been received. If not, it issues a GET.
        """
        if not type in self.recv_dict.keys():
            self.to_send = self.prepare_get_data(type)
            while self.to_send is not None:
                sleep(GSCTradingListener.SLEEP_TIMER)
            return None
        else:
            if reset:
                return self.recv_dict.pop(type)
            return self.recv_dict[type]
    
    def process_received_data(self, data, connection):
        """
        Processes the received data. If it's a send, it stores
        it inside of the received dict.
        If it's a get, it sends the requested data, if present
        inside the send dict.
        """
        req_info = data[GSCTradingListener.REQ_INFO_POSITION:GSCTradingListener.REQ_INFO_POSITION+4].decode()
        req_kind = req_info[0]
        req_type = req_info[1:4]
        if req_kind == GSCTradingStrings.send_request:
            data_len = (data[GSCTradingListener.LEN_POSITION] << 8) + data[GSCTradingListener.LEN_POSITION+1]
            pre_present = False
            if req_type in self.recv_dict.keys():
                pre_present = True
            self.recv_dict[req_type] = list(data[GSCTradingListener.DATA_POSITION:GSCTradingListener.DATA_POSITION+data_len])
            if req_type in self.on_receive_dict.keys():
                self.on_receive_dict[req_type]()
        elif req_kind == GSCTradingStrings.get_request:
            if req_type in self.send_dict.keys():
                connection.send(self.prepare_send_data(req_type, self.send_dict[req_type]))