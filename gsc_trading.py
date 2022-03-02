import time

class GSCTrading:

    sleep_timer = 0.01
    gsc_enter_room_states = [0x01, 0xFE, 0x61, 0xD1, 0xFE]
    gsc_start_trading_states = [0x75, 0x76, 0xFD]
    gsc_next_section = 0xFD
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
        next = states_list[sending]
        sent = False
        while(not sent or sending < len(states_list) - 1):
            self.sleep_func()
            self.sendByte(next)
            sent = True
            recv = self.receiveByte()
            if(sending < (len(states_list) - 1) and recv == states_list[sending + 1]):
                sending += 1
                next = states_list[sending]
                sent = stop_before_last
                
    def read_section(self, index, send_data=None):
        length = self.gsc_special_sections_len[index]
        next = self.gsc_next_section
        
        while(next == self.gsc_next_section):
            self.sleep_func()
            self.sendByte(self.gsc_next_section)
            next = self.receiveByte()
        
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

        return buf

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
        
    def trade_starting_sequence(self, send_data = [None, None, None]):
        self.send_predefined_section(self.gsc_start_trading_states, True)
        random_data = self.read_section(0, send_data[0])
        pokemon_data = self.read_section(1, send_data[1])
        mail_data = self.read_section(2, send_data[2])
        
        return [random_data, pokemon_data, mail_data]
        
    def get_trading_data(self):
        data = self.load_trading_data(self.fileOtherTargetName)
        if data is None:
            data = self.load_trading_data(self.fileBaseTargetName)
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
                print("AAAA")

    def load_trading_data(self, target):
        data = None
        try:
            with open(target, 'rb') as newFile:
                tmpdata = list(newFile.read(sum(self.gsc_special_sections_len)))
                data = [tmpdata[0:self.gsc_special_sections_len[0]], tmpdata[self.gsc_special_sections_len[0]: self.gsc_special_sections_len[0]+self.gsc_special_sections_len[1]], tmpdata[self.gsc_special_sections_len[0]+self.gsc_special_sections_len[1]:self.gsc_special_sections_len[0]+self.gsc_special_sections_len[1]+self.gsc_special_sections_len[2]]]
        except FileNotFoundError as e:
            pass
        return data

    def trade(self):
        self.enter_room()
        while True:
            data = self.get_trading_data()
            data = self.trade_starting_sequence(data)
            self.send_trading_data(data)
            self.end_trade()
        
    # Function needed in order to make sure there is enough time for the slave to prepare the next byte.
    def sleep_func(self):
        time.sleep(self.sleep_timer)