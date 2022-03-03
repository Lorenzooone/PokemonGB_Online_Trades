import time

class GSCTrading:

    sleep_timer = 0.01
    big_sleep_timer = 1.0
    gsc_enter_room_states = [[0x01, 0xFE, 0x61, 0xD1, 0xFE], [0xFE, 0x61, 0xD1, 0xFE, 0xFE]]
    gsc_start_trading_states = [[0x75, 0x76, 0xFD], [0x76, 0xFD, 0xFD]]
    gsc_next_section = 0xFD
    gsc_wait = 0
    gsc_num_waits = 32
    gsc_special_sections_len = [0xA, 0x1BC, 0x24C]
    gsc_stop_trade = 0x7F
    
    def __init__(self, sending_func, receiving_func, base_no_trade = "base.bin", target_other="emu.bin", target_self="usb.bin"):
        self.sendByte = sending_func
        self.receiveByte = receiving_func
        self.fileBaseTargetName = base_no_trade
        self.fileOtherTargetName = target_other
        self.fileSelfTargetName = target_self

    def send_predefined_section(self, states_list, stop_before_last):
        sending = 0
        stop_to = 0
        if stop_before_last:
            stop_to = 1
        while(sending < len(states_list[0]) - stop_to):
            next = states_list[0][sending]
            self.sleep_func()
            self.sendByte(next)
            recv = self.receiveByte()
            if(recv == states_list[1][sending]):
                sending += 1
                
    def read_section(self, index, send_data, buffered):
        length = self.gsc_special_sections_len[index]
        next = self.gsc_next_section

        if not buffered:
            # Wait for a connection to be established
            send_buf = [[0xFFFF,0xFF],[0xFFFF,0xFF],[index]]
            self.send_trading_data(self.write_entire_data(send_buf))
            found = False
            while not found:
                received = self.get_trading_data([3,3,1], get_base=False)
                if received is not None:
                    recv_buf = self.read_entire_data(received)
                    if recv_buf[1] is not None and recv_buf[1][0] == 0xFFFF and recv_buf[2][0] == index: 
                        found = True
                if not found:
                    self.sleep_func()

        while next == self.gsc_next_section:
            self.sleep_func()
            self.sendByte(next)
            next = self.receiveByte()

        if buffered:
            buf = [next]
            for i in range(length-1):
                if send_data is not None:
                    next = send_data[i]
                self.sleep_func()
                self.sendByte(next)
                next = self.receiveByte()
                buf += [next]
            
            if send_data is not None:
                next = send_data[length-1]
                self.sleep_func()
                self.sendByte(next)
                self.receiveByte()
        else:
            send_buf = [[0,next],[0xFFFF,0xFF],[index]]
            for i in range(length + 1):
                found = False
                self.send_trading_data(self.write_entire_data(send_buf))
                while not found:
                    received = self.get_trading_data([3,3,1], get_base=False)
                    if received is not None:
                        recv_buf = self.read_entire_data(received)
                        if recv_buf[i&1] is not None: 
                            byte_num = recv_buf[i&1][0]
                            if byte_num == i and i != length:
                                self.sleep_func()
                                self.sendByte(recv_buf[i&1][1])
                                next = self.receiveByte()
                                send_buf[(i+1)&1][0] = i + 1
                                send_buf[(i+1)&1][1] = next
                                found = True
                            elif byte_num == i:
                                found = True
                            elif i == length and recv_buf[2][0] == index + 1:
                                found = True
                    if not found:
                        self.sleep_func()
            buf = None
        return buf
    
    def read_entire_data(self,data):
        return [self.read_sync_data(data[0]), self.read_sync_data(data[1]), data[2]]
        
    def write_entire_data(self,data):
        return [self.write_sync_data(data[0]), self.write_sync_data(data[1]), data[2]]
    
    def read_sync_data(self,data):
        if len(data) > 0:
            return [(data[0]<<8) + data[1], data[2]]
        return None
    
    def write_sync_data(self, data):
        return [(data[0]>>8)&0xFF, data[0]&0xFF, data[1]]

    def end_trade(self):
        next = 0
        target = self.gsc_stop_trade
        while(next != target):
            self.sleep_func()
            self.sendByte(self.gsc_stop_trade)
            next = self.receiveByte()
            if(target == self.gsc_stop_trade and next == target):
                target = 0

    def enter_room(self):
        self.send_predefined_section(self.gsc_enter_room_states, False)
        
    def trade_starting_sequence(self, buffered, send_data = [None, None, None]):
        self.send_predefined_section(self.gsc_start_trading_states, True)
        random_data = self.read_section(0, send_data[0], buffered)
        pokemon_data = self.read_section(1, send_data[1], buffered)
        mail_data = self.read_section(2, send_data[2], buffered)
        
        return [random_data, pokemon_data, mail_data]
        
    def get_trading_data(self, lengths, get_base = True):
        data = self.load_trading_data(self.fileOtherTargetName, lengths)
        if data is None and get_base:
            data = self.load_trading_data(self.fileBaseTargetName, lengths)
        return data

    def send_trading_data(self, data):
        self.save_trading_data(data)
        return
        
    def save_trading_data(self, data):
        if data is not None:            
            try:
                with open(self.fileSelfTargetName, 'wb') as newFile:
                    newFile.write(bytearray(data[0] + data[1] + data[2]))
            except:
                pass

    def load_trading_data(self, target, lengths):
        data = None
        try:
            with open(target, 'rb') as newFile:
                tmpdata = list(newFile.read(sum(lengths)))
                data = [tmpdata[0:lengths[0]], tmpdata[lengths[0]: lengths[0]+lengths[1]], tmpdata[lengths[0]+lengths[1]:lengths[0]+lengths[1]+lengths[2]]]
        except FileNotFoundError as e:
            pass
        return data

    def trade(self, buffered = True):
        self.enter_room()
        if buffered:
            while True:
                data = self.get_trading_data(self.gsc_special_sections_len)
                data = self.trade_starting_sequence(buffered, send_data=data)
                self.send_trading_data(data)
                self.end_trade()
        else:
            while True:
                data = self.trade_starting_sequence(buffered)
                self.end_trade()
            
        
    # Function needed in order to make sure there is enough time for the slave to prepare the next byte.
    def sleep_func(self, multiplier = 1):
        time.sleep(self.sleep_timer * multiplier)