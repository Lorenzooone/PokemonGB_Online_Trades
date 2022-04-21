from time import sleep
from .gsc_trading_strings import GSCTradingStrings

class HighLevelListener:
    """
    Class which handles high level comunications.
    """
    SLEEP_TIMER = 0.01
    REQ_INFO_POSITION = 0
    LEN_POSITION = 5
    DATA_POSITION = LEN_POSITION + 2
    
    def __init__(self):
        self.to_send = None
        self.on_receive_dict = {}
        self.recv_dict = {}
        self.send_dict = {}
        self.valid_transfers = None

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
    
    def set_valid_transfers(self, valid_transfers):
        self.valid_transfers = valid_transfers
    
    def send_data(self, type, data):
        """
        Sends the data to the other client and prepares the dict's entry
        for responding to GETs.
        """
        self.send_dict[type] = data
        self.to_send = self.prepare_send_data(type, data)
        while self.to_send is not None:
            sleep(HighLevelListener.SLEEP_TIMER)
    
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
                sleep(HighLevelListener.SLEEP_TIMER)
            return None
        else:
            if reset:
                return self.recv_dict.pop(type)
            return self.recv_dict[type]
    
    def connection_normal_sender(self, req_type, connection):
        """
        Sends the data, if it's there.
        """
        connection.send(self.prepare_send_data(req_type, self.send_dict[req_type]))
    
    def connection_prepare_sender(self, req_type):
        """
        Prepares the data which will be sent, if it's there.
        """
        return self.prepare_send_data(req_type, self.send_dict[req_type])
    
    def is_received_valid(self, data):
        """
        Returns whether the received data is valid or not.
        """
        # Is the data long enough to be a valid request?
        if (data is not None) and (len(data) >= HighLevelListener.LEN_POSITION):
            req_info = data[HighLevelListener.REQ_INFO_POSITION:HighLevelListener.REQ_INFO_POSITION+HighLevelListener.LEN_POSITION].decode()
            req_kind = req_info[0]
            req_type = req_info[1:HighLevelListener.LEN_POSITION]
            # If it's a send request, is it long enough to have the data length field?
            if (req_kind == GSCTradingStrings.send_request) and (self.valid_transfers is not None) and (len(data) > HighLevelListener.DATA_POSITION):
                data_len = (data[HighLevelListener.LEN_POSITION] << 8) + data[HighLevelListener.LEN_POSITION+1]
                # If it has a length, is it a valid request? Is its length right? Is the advertised length real?
                if (len(data) >= (HighLevelListener.DATA_POSITION + data_len)) and (req_type in self.valid_transfers.keys()) and (data_len in self.valid_transfers[req_type]):
                    return [req_kind, req_type, data_len]
            elif req_kind == GSCTradingStrings.get_request:
                return [req_kind, req_type]
        return None
        
    def process_received_data(self, data, connection, send_data=True, preparer=False):
        """
        Processes the received data. If it's a send, it stores
        it inside of the received dict.
        If it's a get, it sends the requested data, if present
        inside the send dict.
        """
        ret = self.is_received_valid(data)
        if ret is None:
            return ["", "", None]
            
        req_kind = ret[0]
        req_type = ret[1]
        prepared = None
        if req_kind == GSCTradingStrings.send_request:
            data_len = ret[2]
            self.recv_dict[req_type] = list(data[HighLevelListener.DATA_POSITION:HighLevelListener.DATA_POSITION+data_len])
            if req_type in self.on_receive_dict.keys():
                self.on_receive_dict[req_type]()
        elif req_kind == GSCTradingStrings.get_request:
            if req_type in self.send_dict.keys() and send_data:
                if not preparer:
                    self.connection_normal_sender(req_type, connection)
                else:
                    prepared = self.connection_prepare_sender(req_type)
        return [req_kind, req_type, prepared]