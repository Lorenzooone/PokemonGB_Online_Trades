import time
from gsc_trading_data_utils import *

class GSCTrading:

    sleep_timer = 0.01
    big_sleep_timer = 1.0
    gsc_enter_room_states = [[0x01, 0xFE, 0x61, 0xD1, 0xFE], [0xFE, 0x61, 0xD1, 0xFE, 0xFE]]
    gsc_start_trading_states = [[0x75, 0x75, 0x76, 0xFD], [0x75, 0, 0xFD, 0xFD]]
    gsc_next_section = 0xFD
    gsc_no_input = 0xFE
    gsc_no_data = 0
    gsc_num_waits = 32
    gsc_special_sections_len = [0xA, 0x1BC, 0x24C]
    gsc_stop_trade = 0x7F
    gsc_first_trade_index = 0x70
    gsc_decline_trade = 0x71
    gsc_accept_trade = 0x72
    
    def __init__(self, sending_func, receiving_func, base_no_trade = "useful_data/base.bin", target_other="emu.bin", target_self="usb.bin"):
        self.sendByte = sending_func
        self.receiveByte = receiving_func
        self.fileBaseTargetName = base_no_trade
        self.fileOtherTargetName = target_other
        self.fileSelfTargetName = target_self
        self.checks = GSCChecks(self.gsc_special_sections_len)
        GSCUtils()

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
        
        # Prepare sanity checks stuff
        self.checks.prepare_text_buffer()
        self.checks.prepare_species_buffer()

        if not buffered:
            # Wait for a connection to be established
            send_buf = [[0xFFFF,0xFF],[0xFFFF,0xFF],[index]]
            self.send_trading_data(self.write_entire_data(send_buf))
            found = False
            while not found:
                received, valid = self.get_trading_data([3,3,1], get_base=False)
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
                    next = self.checks.checks_map[index][i](send_data[i])
                    send_data[i] = next
                next = self.swap_byte(next)
                buf += [next]
            
            if send_data is not None:
                next = self.checks.checks_map[index][length-1](send_data[length-1])
                send_data[length-1] = next
            self.swap_byte(next)
            other_buf = send_data
        else:
            buf = [next]
            other_buf = []
            send_buf = [[0,next],[0xFFFF,0xFF],[index]]
            for i in range(length + 1):
                found = False
                self.send_trading_data(self.write_entire_data(send_buf))
                while not found:
                    received, valid = self.get_trading_data([3,3,1], get_base=False)
                    if received is not None:
                        recv_buf = self.read_entire_data(received)
                        if recv_buf[i&1] is not None:
                            byte_num = recv_buf[i&1][0]
                            if byte_num == i and i != length:
                                cleaned_byte = self.checks.checks_map[index][i](recv_buf[i&1][1])
                                next = self.swap_byte(cleaned_byte)
                                send_buf[(i+1)&1][0] = i + 1
                                send_buf[(i+1)&1][1] = next
                                buf += [next]
                                other_buf += [cleaned_byte]
                                found = True
                            elif byte_num == i:
                                found = True
                            elif i == length and recv_buf[2][0] == index + 1:
                                found = True
                    if not found:
                        self.sleep_func()
        return buf, other_buf
    
    def swap_byte(self, send_data):
        self.sleep_func()
        self.sendByte(send_data)
        recv = self.receiveByte()
        #print(str(send_data) + " - " + str(recv))
        return recv
    
    def read_entire_data(self, data):
        return [self.read_sync_data(data[0]), self.read_sync_data(data[1]), data[2]]
        
    def write_entire_data(self, data):
        return [self.write_sync_data(data[0]), self.write_sync_data(data[1]), data[2]]
    
    def read_sync_data(self, data):
        if data is not None and len(data) > 0:
            return [(data[0]<<8) + data[1], data[2]]
        return None
    
    def write_sync_data(self, data):
        return [(data[0]>>8)&0xFF, data[0]&0xFF, data[1]]
    
    def get_mail_data_only(self):
        print("IMPLEMENT get_mail_data_only !!!")
        return GSCUtils.no_mail_section
        
    def send_mail_data_only(self, data):
        print("IMPLEMENT send_mail_data_only !!!")
        pass
    
    def get_move_data_only(self):
        print("IMPLEMENT get_move_data_only !!!")
        val = [0x21,0,0,0,0,0,0,0]
        for i in range(4):
            self.other_pokemon.pokemon[self.other_pokemon.get_last_mon_index()].set_move(i, val[i], max_pp=False)
            self.other_pokemon.pokemon[self.other_pokemon.get_last_mon_index()].set_pp(i, val[4+i])
        
    def send_move_data_only(self):
        print("IMPLEMENT send_move_data_only !!!")
        val = [0,0,0,0,0,0,0,0]
        for i in range(4):
            val[i] = self.own_pokemon.pokemon[self.own_pokemon.get_last_mon_index()].get_move(i)
            val[4+i] = self.own_pokemon.pokemon[self.own_pokemon.get_last_mon_index()].get_pp(i)

    def end_trade(self):
        next = 0
        target = self.gsc_stop_trade
        while(next != target):
            next = self.swap_byte(self.gsc_stop_trade)
            if(target == self.gsc_stop_trade and next == target):
                target = 0

    def wait_for_input(self, next):
        while(next == self.gsc_no_input or next == self.gsc_no_data):
            next = self.swap_byte(self.gsc_no_input)
        return next

    def wait_for_no_data(self, next, resent_byte):
        while(next != self.gsc_no_data):
            next = self.swap_byte(resent_byte)
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
    
    def convert_choice(self, choice):
        return choice - self.gsc_first_trade_index
                
    def get_chosen_mon(self, close):
        if close:
            return self.gsc_stop_trade
        return self.gsc_first_trade_index
        
    def send_chosen_mon(self, choice):
        return not self.is_choice_stop(choice)

    def is_choice_stop(self, choice):
        if choice == self.gsc_stop_trade:
            return True
        return False

    def do_trade(self, close=False):
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
                received_choice = self.get_chosen_mon(close)

            if not self.is_choice_stop(received_choice) and not self.is_choice_stop(sent_mon):
                # Send the other player's choice to the game
                next = self.swap_byte(received_choice)

                # Get whether the trade was declined or not
                next = self.wait_for_no_data(next, received_choice)
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

                next = self.wait_for_no_data(next, received_accepted)
                next = self.wait_for_no_input(next)

                if not self.is_choice_decline(received_accepted) and not self.is_choice_decline(accepted):
                    # Apply the trade to the data
                    self.own_pokemon.trade_mon(self.other_pokemon, self.convert_choice(sent_mon), self.convert_choice(received_choice))
                    evo_own = self.own_pokemon.evolve_mon(self.own_pokemon.get_last_mon_index())
                    evo_other = self.other_pokemon.evolve_mon(self.other_pokemon.get_last_mon_index())
                    if evo_own is not None:
                        self.own_blank_trade = evo_own
                    else:
                        self.own_blank_trade = False
                    if evo_other is not None:
                        self.other_blank_trade = evo_other
                    else:
                        self.other_blank_trade = False
                    
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
        random_data, random_data_other = self.read_section(0, send_data[0], buffered)
        pokemon_data, pokemon_data_other = self.read_section(1, send_data[1], buffered)
        
        # Trade mail data only if needed
        pokemon_own = GSCTradingData(pokemon_data)
        pokemon_other = GSCTradingData(pokemon_data_other)
        pokemon_own_mail = pokemon_own.party_has_mail()
        pokemon_other_mail = pokemon_other.party_has_mail()
        
        if not pokemon_own_mail and not pokemon_other_mail:
            mail_data, mail_data_other = self.read_section(2, GSCUtils.no_mail_section, True)
        elif pokemon_own_mail and not pokemon_other_mail:
            mail_data, mail_data_other = self.read_section(2, GSCUtils.no_mail_section, True)
            if not buffered:
                self.send_mail_data_only(mail_data)
        elif not pokemon_own_mail and pokemon_other_mail:
            if not buffered:
                send_data[2] = self.get_mail_data_only()
            mail_data, mail_data_other = self.read_section(2, send_data[2], True)
        else:
            mail_data, mail_data_other = self.read_section(2, send_data[2], buffered)
        
        return [random_data, pokemon_data, mail_data], [random_data_other, pokemon_data_other, mail_data_other]
        
    def get_trading_data(self, lengths, get_base = True):
        success = True
        data = self.load_trading_data(self.fileOtherTargetName, lengths)
        if data is None and get_base:
            success = False
            data = self.load_trading_data(self.fileBaseTargetName, lengths)
        return data, success

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
    
    def synchronous_trade(self):
        data, data_other = self.trade_starting_sequence(False)
        self.own_pokemon = GSCTradingData(data[1], data_mail=data[2])
        self.other_pokemon = GSCTradingData(data_other[1], data_mail=data_other[2])
        return True
    
    def buffered_trade(self):
        data, valid = self.get_trading_data(self.gsc_special_sections_len)
        data, data_other = self.trade_starting_sequence(True, send_data=data)
        self.send_trading_data(data)
        self.own_pokemon = GSCTradingData(data[1], data_mail=data[2])
        self.other_pokemon = GSCTradingData(data_other[1], data_mail=data_other[2])
        return valid

    def trade(self, buffered = True):
        self.own_blank_trade = True
        self.other_blank_trade = True
        self.enter_room()
        while True:
            self.send_predefined_section(self.gsc_start_trading_states, True)
            if self.own_blank_trade and self.other_blank_trade:
                if buffered:
                    valid = self.buffered_trade()
                else:
                    valid = self.synchronous_trade()
            else:
                if self.other_blank_trade:
                    self.get_move_data_only()
                data, data_other = self.trade_starting_sequence(True, send_data=self.other_pokemon.create_trading_data(GSCTrading.gsc_special_sections_len))
                if  self.own_blank_trade:
                    self.own_pokemon = GSCTradingData(data[1], data_mail=data[2])
                    self.send_move_data_only()
            self.own_blank_trade = True
            self.other_blank_trade = True
            self.do_trade(close=not valid)
        
    # Function needed in order to make sure there is enough time for the slave to prepare the next byte.
    def sleep_func(self, multiplier = 1):
        time.sleep(self.sleep_timer * multiplier)