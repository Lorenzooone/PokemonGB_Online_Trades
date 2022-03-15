import time

class GSCTrading:

    sleep_timer = 0.01
    big_sleep_timer = 1.0
    gsc_enter_room_states = [[0x01, 0xFE, 0x61, 0xD1, 0xFE], [0xFE, 0x61, 0xD1, 0xFE, 0xFE]]
    gsc_start_trading_states = [[0x75, 0x75, 0x76, 0xFD], [0x75, 0, 0xFD, 0xFD]]
    gsc_next_section = 0xFD
    gsc_no_input = 0xFE
    gsc_wait = 0
    gsc_num_waits = 32
    gsc_special_sections_len = [0xA, 0x1BC, 0x24C]
    gsc_stop_trade = 0x7F
    gsc_decline_trade = 0x71
    gsc_accept_trade = 0x72
    
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
            recv = self.swap_byte(next)
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
            next = self.swap_byte(next)

        if buffered:
            buf = [next]
            for i in range(length-1):
                if send_data is not None:
                    next = send_data[i]
                next = self.swap_byte(next)
                buf += [next]
            
            if send_data is not None:
                next = send_data[length-1]
                self.swap_byte(next)
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
                                next = self.swap_byte(recv_buf[i&1][1])
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
    
    def swap_byte(self, send_data):
        self.sleep_func()
        self.sendByte(send_data)
        return self.receiveByte()
    
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
            next = self.swap_byte(self.gsc_stop_trade)
            if(target == self.gsc_stop_trade and next == target):
                target = 0

    def wait_for_input(self, next):
        while(next == self.gsc_no_input):
            next = self.swap_byte(self.gsc_no_input)
        return next

    def wait_for_no_input(self, next):
        while(next != self.gsc_no_input):
            next = self.swap_byte(self.gsc_no_input)
        return next

    def get_accepted(self):
        return self.gsc_accept_trade
                
    def send_accepted(self, choice):
        return not self.is_choice_decline(choice)
        
    def is_choice_decline(self, choice):
        if choice == self.gsc_decline_trade:
            return True
        return False
                
    def get_chosen_mon(self):
        return 0x70
        
    def send_chosen_mon(self, choice):
        return not self.is_choice_stop(choice)

    def is_choice_stop(self, choice):
        if choice == self.gsc_stop_trade:
            return True
        return False

    def do_trade(self):
        trade_completed = False

        while not trade_completed:
            # Get the choice
            next = self.gsc_no_input
            sent_mon = self.wait_for_input(next)

            # Send it to the other player
            self.send_chosen_mon(sent_mon)
            
            # Get the other player's choice
            received_choice = None
            while received_choice is None:
                self.sleep_func()
                received_choice = self.get_chosen_mon()

            if not self.is_choice_stop(received_choice) and not self.is_choice_stop(sent_mon):
                # Send the other player's choice to the game
                next = self.swap_byte(received_choice)

                # Get whether the trade was declined or not
                next = self.wait_for_no_input(next)
                accepted = self.wait_for_input(next)

                # Send it to the other player
                self.send_accepted(accepted)
                
                # Get the other player's choice
                received_accepted = None
                while received_accepted is None:
                    self.sleep_func()
                    received_accepted = self.get_accepted()
                
                # Send the other player's choice to the game
                next = self.swap_byte(received_accepted)

                next = self.wait_for_no_input(next)

                if not self.is_choice_decline(received_accepted) and not self.is_choice_decline(accepted):
                    # Conclude the trade successfully
                    next = self.wait_for_input(next)

                    trade_completed = True
                    next = self.swap_byte(next)
                    
            else:
                # If someone wants to end the trade, do it
                trade_completed = True
                self.end_trade()

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
                self.do_trade()
        else:
            while True:
                data = self.trade_starting_sequence(buffered)
                self.do_trade()
            
        
    # Function needed in order to make sure there is enough time for the slave to prepare the next byte.
    def sleep_func(self, multiplier = 1):
        time.sleep(self.sleep_timer * multiplier)