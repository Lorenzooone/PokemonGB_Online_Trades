import time
from random import Random
from gsc_trading_data_utils import *

class GSCTradingClient:
    gsc_full_transfer = "FLL"
    gsc_single_transfer = "SNG"
    gsc_moves_transfer = "MVS"
    gsc_mail_transfer = "MAI"
    gsc_choice_transfer = "CHC"
    gsc_accept_transfer = "ACP"
    gsc_success_transfer = "SUC"
    gsc_buffered_transfer = "BUF"
    gsc_negotiation_transfer = "NEG"
    gsc_buffered_value = 0x85
    gsc_not_buffered_value = 0x12
    gsc_success_value = 0x91
    max_message_id = 255
    max_negotiation_id = 255
    
    def __init__(self, trader, connection, base_no_trade = "useful_data/base.bin"):
        self.fileBaseTargetName = base_no_trade
        self.connection = connection
        self.trader = trader
        self.own_id = None
        self.other_id = None
    
    def get_mail_data_only(self):
        return self.connection.recv_data(GSCTradingClient.gsc_mail_transfer)
        
    def send_mail_data_only(self, data):
        self.connection.send_data(GSCTradingClient.gsc_mail_transfer, data)
    
    def get_success(self):
        return self.get_single_byte(GSCTradingClient.gsc_success_transfer)
        
    def send_success(self):
        self.send_single_byte(GSCTradingClient.gsc_success_transfer, GSCTradingClient.gsc_success_value)
    
    def get_move_data_only(self):
        val = self.connection.recv_data(GSCTradingClient.gsc_moves_transfer)
        if val is not None:
            for i in range(4):
                self.trader.other_pokemon.pokemon[self.trader.other_pokemon.get_last_mon_index()].set_move(i, val[i], max_pp=False)
                self.trader.other_pokemon.pokemon[self.trader.other_pokemon.get_last_mon_index()].set_pp(i, val[4+i])
        return val
        
    def send_move_data_only(self):
        val = [0,0,0,0,0,0,0,0]
        for i in range(4):
            val[i] = self.trader.own_pokemon.pokemon[self.trader.own_pokemon.get_last_mon_index()].get_move(i)
            val[4+i] = self.trader.own_pokemon.pokemon[self.trader.own_pokemon.get_last_mon_index()].get_pp(i)
        self.connection.send_data(GSCTradingClient.gsc_moves_transfer, val)
    
    def send_single_byte(self, dest, byte):
        if self.own_id is None:
            r = Random()
            self.own_id = r.randint(0, GSCTradingClient.max_message_id)
        else:
            self.own_id = GSCUtilsMisc.inc_byte(self.own_id)
        self.connection.send_data(dest, [self.own_id, byte])
    
    def get_single_byte(self, dest):
        ret = self.connection.recv_data(dest)
        if ret is not None:
            if self.other_id is None:
                self.other_id = ret[0]
            elif self.other_id != ret[0]:
                return None
            self.other_id = GSCUtilsMisc.inc_byte(self.other_id)
            return ret[1]
        return ret
    
    def get_accepted(self):
        return self.get_single_byte(GSCTradingClient.gsc_accept_transfer)
                
    def send_accepted(self, choice):
        self.send_single_byte(GSCTradingClient.gsc_accept_transfer, choice)
                
    def get_chosen_mon(self):
        return self.get_single_byte(GSCTradingClient.gsc_choice_transfer)
        
    def send_chosen_mon(self, choice):
        self.send_single_byte(GSCTradingClient.gsc_choice_transfer, choice)
        
    def get_big_trading_data(self, lengths):
        success = True
        data = self.connection.recv_data(GSCTradingClient.gsc_full_transfer)
        if data is None:
            success = False
            data = GSCUtilsLoaders.load_trading_data(self.fileBaseTargetName, lengths)
        else:
            data = GSCUtilsMisc.divide_data(data, lengths)
        return data, success

    def send_big_trading_data(self, data):
        self.connection.send_data(GSCTradingClient.gsc_full_transfer, data[0]+data[1]+data[2])
        
    def get_trading_data(self):
        return self.connection.recv_data(GSCTradingClient.gsc_single_transfer)

    def send_trading_data(self, data):
        self.connection.send_data(GSCTradingClient.gsc_single_transfer, data)
    
    def send_buffered_data(self, buffered):
        val = GSCTradingClient.gsc_not_buffered_value
        if buffered:
            val = GSCTradingClient.gsc_buffered_value
        self.send_single_byte(GSCTradingClient.gsc_buffered_transfer, val)
    
    def get_buffered_data(self):
        buffered = None
        val = self.get_single_byte(GSCTradingClient.gsc_buffered_transfer)
        if val is not None:
            if val == GSCTradingClient.gsc_buffered_value:
                buffered = True
            elif val == GSCTradingClient.gsc_not_buffered_value:
                buffered = False
        return buffered
    
    def send_negotiation_data(self):
        r = Random()
        val = r.randint(0, GSCTradingClient.max_negotiation_id)
        self.send_single_byte(GSCTradingClient.gsc_negotiation_transfer, val)
        return val
    
    def get_negotiation_data(self):
        return self.get_single_byte(GSCTradingClient.gsc_negotiation_transfer)


class GSCTrading:
    sleep_timer = 0.01
    gsc_enter_room_states = [[0x01, 0xFE, 0x61, 0xD1, 0xFE], [0xFE, 0x61, 0xD1, 0xFE, 0xFE]]
    gsc_start_trading_states = [[0x75, 0x75, 0x76, 0xFD], [0x75, 0, 0xFD, 0xFD]]
    gsc_max_consecutive_no_data = 0x100
    gsc_next_section = 0xFD
    gsc_no_input = 0xFE
    gsc_no_data = 0
    gsc_special_sections_len = [0xA, 0x1BC, 0x24C]
    gsc_drop_bytes_checks = [[0xA, 0x1B9, 0x1E6], [gsc_next_section, gsc_next_section, gsc_no_input]]
    gsc_stop_trade = 0x7F
    gsc_first_trade_index = 0x70
    gsc_decline_trade = 0x71
    gsc_accept_trade = 0x72
    
    def __init__(self, sending_func, receiving_func, connection, menu, kill_function):
        self.sendByte = sending_func
        self.receiveByte = receiving_func
        self.checks = GSCChecks(self.gsc_special_sections_len, menu.do_sanity_checks)
        self.comms = GSCTradingClient(self, connection)
        self.menu = menu
        self.kill_function = kill_function
        GSCUtils()

    def send_predefined_section(self, states_list, stop_to=0, die_on_no_data=False):
        sending = 0
        consecutive_no_data = 0
        while(sending < len(states_list[0]) - stop_to):
            next = states_list[0][sending]
            recv = self.swap_byte(next)
            if(recv == states_list[1][sending]):
                sending += 1
            elif die_on_no_data and sending == 0:
                if  recv == self.gsc_no_data:
                    consecutive_no_data += 1
                    if consecutive_no_data >= self.gsc_max_consecutive_no_data:
                        return False
                else:
                    consecutive_no_data = 0
        return True
        
    def has_transfer_failed(self, byte, byte_index, section_index):
        if byte_index >= self.gsc_drop_bytes_checks[0][section_index]:
            if byte_index < self.gsc_special_sections_len[section_index]:
                if byte == self.gsc_drop_bytes_checks[1][section_index]:
                    return True
            else:
                if byte != self.gsc_drop_bytes_checks[1][section_index]:
                    return True
        return False
    
    def check_bad_data(self, byte, byte_index, section_index):
        if self.has_transfer_failed(byte, byte_index, section_index):
            if self.menu.kill_on_byte_drops:
                print("Error! At least one byte was not properly transfered!")
                self.kill_function()
            elif not self.printed_warning_drop:
                if self.menu.verbose:
                    print("Warning! At least one byte was not properly transfered!")
                self.printed_warning_drop = True
                    
                
    def read_section(self, index, send_data, buffered):
        length = self.gsc_special_sections_len[index]
        next = self.gsc_next_section
        
        # Prepare sanity checks stuff
        self.checks.prepare_text_buffer()
        self.checks.prepare_species_buffer()

        if not buffered:
            # Wait for a connection to be established
            send_buf = [[0xFFFF,0xFF],[0xFFFF,0xFF],[index]]
            self.comms.send_trading_data(self.write_entire_data(send_buf))
            found = False
            while not found:
                received = self.comms.get_trading_data()
                if received is not None:
                    recv_buf = self.read_entire_data(received)
                    if recv_buf[1] is not None and recv_buf[1][0] == 0xFFFF and recv_buf[2][0] == index: 
                        found = True
                if not found:
                    self.sleep_func()
                    self.swap_byte(self.gsc_no_input)

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
            self.printed_warning_drop = False
            buf = [next]
            other_buf = []
            send_buf = [[0,next],[0xFFFF,0xFF],[index]]
            for i in range(length + 1):
                found = False
                self.comms.send_trading_data(self.write_entire_data(send_buf))
                while not found:
                    received = self.comms.get_trading_data()
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
                                self.check_bad_data(cleaned_byte, i, index)
                                self.check_bad_data(next, i + 1, index)
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
        return [self.read_sync_data(data, 0), self.read_sync_data(data, 3), [data[6]]]
        
    def write_entire_data(self, data):
        return self.write_sync_data(data[0]) + self.write_sync_data(data[1]) + data[2]
    
    def read_sync_data(self, data, pos):
        if data is not None and len(data) > 0:
            return [(data[pos]<<8) + data[pos+1], data[pos+2]]
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
        
    def is_choice_decline(self, choice):
        if choice == self.gsc_decline_trade:
            return True
        return False
    
    def convert_choice(self, choice):
        return choice - self.gsc_first_trade_index

    def is_choice_stop(self, choice):
        if choice == self.gsc_stop_trade:
            return True
        return False
    
    def check_mon_validity(self, choice, party):
        index = self.convert_choice(choice)
        mon_party_id = party.party_info.get_id(index)
        if mon_party_id is None or mon_party_id != party.pokemon[index].get_species():
            return False
        return True
    
    def is_trade_valid(self, own_choice, other_choice):
        return self.check_mon_validity(own_choice, self.own_pokemon) and self.check_mon_validity(other_choice, self.other_pokemon)
    
    def force_receive(self, fun, send_nothing=True):
        received = None
        while received is None:
            self.sleep_func()
            received = fun()
            if send_nothing:
                self.swap_byte(self.gsc_no_input)
        return received

    def do_trade(self, close=False):
        trade_completed = False

        while not trade_completed:
            # Get the choice
            next = self.gsc_no_input
            sent_mon = self.wait_for_input(next)

            if not close:
                # Send it to the other player
                self.comms.send_chosen_mon(sent_mon)
            
                # Get the other player's choice
                received_choice = self.force_receive(self.comms.get_chosen_mon)
            else:
                received_choice = self.gsc_stop_trade

            if not self.is_choice_stop(received_choice) and not self.is_choice_stop(sent_mon):
                # Send the other player's choice to the game
                next = self.swap_byte(received_choice)

                # Get whether the trade was declined or not
                next = self.wait_for_no_data(next, received_choice)
                next = self.wait_for_no_input(next)
                accepted = self.wait_for_input(next)
                
                # Check validity of trade (if IDs don't match, the game will refuse the trade automatically)
                valid_trade = self.is_trade_valid(sent_mon, received_choice)
                if not valid_trade:
                    accepted = self.gsc_decline_trade

                # Send it to the other player
                self.comms.send_accepted(accepted)
                
                # Get the other player's choice
                received_accepted = self.force_receive(self.comms.get_accepted)
                
                # Check validity of trade (if IDs don't match, the game will refuse the trade automatically)
                if not valid_trade:
                    received_accepted = self.gsc_decline_trade
                
                # Send the other player's choice to the game
                next = self.swap_byte(received_accepted)

                next = self.wait_for_no_data(next, received_accepted)
                next = self.wait_for_no_input(next)

                if not self.is_choice_decline(received_accepted) and not self.is_choice_decline(accepted):
                    # Apply the trade to the data
                    self.own_pokemon.trade_mon(self.other_pokemon, self.convert_choice(sent_mon), self.convert_choice(received_choice))
                    self.own_blank_trade = GSCUtilsMisc.default_if_none(self.own_pokemon.evolve_mon(self.own_pokemon.get_last_mon_index()), False)
                    self.other_blank_trade = GSCUtilsMisc.default_if_none(self.other_pokemon.evolve_mon(self.other_pokemon.get_last_mon_index()), False)

                    # Conclude the trade successfully
                    next = self.wait_for_input(next)

                    # Send it to the other player
                    self.comms.send_success()

                    # Get the other player's choice
                    self.force_receive(self.comms.get_success)

                    trade_completed = True
                    next = self.swap_byte(next)
                    
            else:
                # If someone wants to end the trade, do it
                trade_completed = True
                self.end_trade()

    def enter_room(self):
        self.send_predefined_section(self.gsc_enter_room_states)
        
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
                self.comms.send_mail_data_only(mail_data)
        elif not pokemon_own_mail and pokemon_other_mail:
            if not buffered:
                send_data[2] = self.force_receive(self.comms.get_mail_data_only)
            mail_data, mail_data_other = self.read_section(2, send_data[2], True)
        else:
            mail_data, mail_data_other = self.read_section(2, send_data[2], buffered)
        
        return [random_data, pokemon_data, mail_data], [random_data_other, pokemon_data_other, mail_data_other]
    
    def synchronous_trade(self):
        data, data_other = self.trade_starting_sequence(False)
        self.own_pokemon = GSCTradingData(data[1], data_mail=data[2])
        self.other_pokemon = GSCTradingData(data_other[1], data_mail=data_other[2])
        return True
    
    def buffered_trade(self):
        data, valid = self.comms.get_big_trading_data(self.gsc_special_sections_len)
        data, data_other = self.trade_starting_sequence(True, send_data=data)
        self.comms.send_big_trading_data(data)
        self.own_pokemon = GSCTradingData(data[1], data_mail=data[2])
        self.other_pokemon = GSCTradingData(data_other[1], data_mail=data_other[2])
        return valid
    
    def choose_if_buffered(self, curr_buffered):
        buffered = curr_buffered
        self.comms.send_buffered_data(buffered)
        other_buffered = self.force_receive(self.comms.get_buffered_data, send_nothing=False)
        if buffered == other_buffered:
            return buffered
        change_buffered = None
        while change_buffered is None:
            own_val = self.comms.send_negotiation_data()
            other_val = self.force_receive(self.comms.get_negotiation_data, send_nothing=False)
            if other_val > own_val:
                change_buffered = True
            elif other_val < own_val:
                change_buffered = False
        while buffered != other_buffered:
            if not change_buffered:
                other_buffered = self.force_receive(self.comms.get_buffered_data, send_nothing=False)
            else:
                buffered = self.menu.handle_buffered_change_offer(buffered)
                self.comms.send_buffered_data(buffered)
            change_buffered = not change_buffered
        return buffered

    def player_trade(self, buffered):
        self.own_blank_trade = True
        self.other_blank_trade = True
        buffered = self.choose_if_buffered(buffered)
        if self.menu.verbose:
            self.menu.chosen_buffered_print(buffered)
        self.enter_room()
        continue_trading = True
        while True:
            if not self.send_predefined_section(self.gsc_start_trading_states, stop_to=1, die_on_no_data=True):
                break
            if self.own_blank_trade and self.other_blank_trade:
                if buffered:
                    valid = self.buffered_trade()
                else:
                    valid = self.synchronous_trade()
            else:
                if self.other_blank_trade:
                    self.force_receive(self.comms.get_move_data_only)
                data, data_other = self.trade_starting_sequence(True, send_data=self.other_pokemon.create_trading_data(GSCTrading.gsc_special_sections_len))
                if  self.own_blank_trade:
                    self.own_pokemon = GSCTradingData(data[1], data_mail=data[2])
                    self.comms.send_move_data_only()
            self.own_blank_trade = True
            self.other_blank_trade = True
            self.do_trade(close=not valid)
        
    # Function needed in order to make sure there is enough time for the slave to prepare the next byte.
    def sleep_func(self, multiplier = 1):
        time.sleep(self.sleep_timer * multiplier)