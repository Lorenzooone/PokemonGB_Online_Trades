import time
from random import Random
from gsc_trading_data_utils import *
from gsc_trading_menu import GSCBufferedNegotiator
from gsc_trading_strings import GSCTradingStrings

class GSCTradingClient:
    """
    Class which handles sending/receiving trading data
    to/from the other recepient.
    It uses a system of TAGs and IDs.
    """
    gsc_full_transfer = "FLL"
    gsc_single_transfer = "SNG"
    gsc_pool_transfer = "POL"
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
    egg_value = 0x38
    max_negotiation_id = 255
    
    def __init__(self, trader, connection, verbose, base_no_trade = "useful_data/base.bin", base_pool = "useful_data/base_pool.bin"):
        self.fileBaseTargetName = base_no_trade
        self.fileBasePoolTargetName = base_pool
        self.connection = connection
        self.received_one = False
        self.verbose = verbose
        connection.prepare_listener(GSCTradingClient.gsc_full_transfer, self.on_get_big_trading_data)
        self.trader = trader
        self.own_id = None
        self.other_id = None
    
    def get_mail_data_only(self):
        """
        Handles getting the mail data when only the other player has mail.
        """
        return self.connection.recv_data(GSCTradingClient.gsc_mail_transfer)
        
    def send_mail_data_only(self, data):
        """
        Handles sending the mail data when the other player has no mail.
        """
        self.connection.send_data(GSCTradingClient.gsc_mail_transfer, data)
    
    def get_success(self):
        """
        Handles getting the success trade confirmation value.
        """
        return self.get_single_byte(GSCTradingClient.gsc_success_transfer)
        
    def send_success(self):
        """
        Handles sending the success trade confirmation value.
        """
        self.send_single_byte(GSCTradingClient.gsc_success_transfer, GSCTradingClient.gsc_success_value)
    
    def get_move_data_only(self):
        """
        Handles getting the new move data when only the other player
        has user input.
        It also loads it into the correct pokémon.
        """
        val = self.connection.recv_data(GSCTradingClient.gsc_moves_transfer)
        if val is not None:
            for i in range(4):
                self.trader.other_pokemon.pokemon[self.trader.other_pokemon.get_last_mon_index()].set_move(i, val[i], max_pp=False)
                self.trader.other_pokemon.pokemon[self.trader.other_pokemon.get_last_mon_index()].set_pp(i, val[4+i])
        return val
        
    def send_move_data_only(self):
        """
        Handles sending the new move data when only the player
        has user input.
        It gets it from the correct pokémon.
        """
        val = [0,0,0,0,0,0,0,0]
        for i in range(4):
            val[i] = self.trader.own_pokemon.pokemon[self.trader.own_pokemon.get_last_mon_index()].get_move(i)
            val[4+i] = self.trader.own_pokemon.pokemon[self.trader.own_pokemon.get_last_mon_index()].get_pp(i)
        self.connection.send_data(GSCTradingClient.gsc_moves_transfer, val)
    
    def send_with_counter(self, dest, data):
        """
        Sends data with an attached counter to detect passage of steps.
        """
        if self.own_id is None:
            r = Random()
            self.own_id = r.randint(0, GSCTradingClient.max_message_id)
        else:
            self.own_id = GSCUtilsMisc.inc_byte(self.own_id)
        self.connection.send_data(dest, [self.own_id] + data)
    
    def get_with_counter(self, dest):
        """
        Gets data and checks the attached counter to make sure it's
        what the program currently expects.
        """
        ret = self.connection.recv_data(dest)
        if ret is not None:
            if self.other_id is None:
                self.other_id = ret[0]
            elif self.other_id != ret[0]:
                return None
            self.other_id = GSCUtilsMisc.inc_byte(self.other_id)
            return ret[1:]
        return ret
    
    def get_single_byte(self, dest):
        """
        Gets data and checks the attached counter to make sure it's
        what the program currently expects. Single byte version.
        """
        ret = self.get_with_counter(dest)
        if ret is not None:
            return ret[0]
        return ret
    
    def send_single_byte(self, dest, byte):
        """
        Sends data with an attached counter to detect passage of steps.
        Single byte version.
        """
        self.send_with_counter(dest, [byte])

    def get_accepted(self):
        """
        Handles getting whether the other player wants to do the trade
        or not.
        """
        return self.get_single_byte(GSCTradingClient.gsc_accept_transfer)
                
    def send_accepted(self, choice):
        """
        Handles sending whether the player wants to do the trade or not.
        """
        self.send_single_byte(GSCTradingClient.gsc_accept_transfer, choice)
                
    def get_chosen_mon(self):
        """
        Handles getting which pokémon the other player wants to trade.
        If the sanity checks are on, it also makes sure no weird index
        is selected in case of failure and prepares the data to close
        the current trade offer.
        It's done like this to make it so buffered trading works even
        if the players change their party's order or their moves' order
        between consecutive tries.
        """
        valid = True
        ret = self.get_with_counter(GSCTradingClient.gsc_choice_transfer)
        
        if ret is not None:
            # Gets the failsafe value. If the sanity checks are on,
            # it cleans it too
            base_index = self.trader.convert_choice(ret[0])
            if ret[0] != GSCTrading.gsc_stop_trade:
                if self.trader.checks.do_sanity_checks and base_index >= self.trader.other_pokemon.get_party_size():
                    base_index = self.trader.other_pokemon.get_last_mon_index()
                
                # Applies the checks to the received data.
                # If the sanity checks are off, this will be a simple copy
                actual_data = ret[1:]
                new_actual_data = ret[1:]
                checker = self.trader.checks.single_pokemon_checks_map
                if len(new_actual_data) > len(checker):
                    for i in range(len(checker)):
                        new_actual_data[i] = checker[i](actual_data[i])

                    # Prepares the pokémon data. For both the cleaned one and
                    # the raw one
                    loaded_mon = GSCTradingPokémonInfo.set_data(new_actual_data)
                    unfiltered_mon = GSCTradingPokémonInfo.set_data(actual_data)
                    
                    # Handle getting/sending eggs. That requires one extra byte
                    is_egg = False
                    if actual_data[len(checker)] == GSCTradingClient.egg_value:
                        is_egg = True
                    
                    # Searches for the pokémon. If it's not found, it uses
                    # the failsafe value. If the sanity checks are on,
                    # it will prepare to close the current trade offer
                    found_index = self.trader.other_pokemon.search_for_mon(loaded_mon, is_egg)
                    if found_index is None:
                        found_index = base_index
                        if self.trader.checks.do_sanity_checks:
                            valid = False
                    elif self.trader.checks.do_sanity_checks and loaded_mon.has_changed_significantly(unfiltered_mon):
                        
                        # If the sanity checks are on, and the pokémon was changed
                        # too much from the cleaning, it prepares to close the
                        # current trade offer
                        valid = False
                else:
                    found_index = base_index
                    if self.trader.checks.do_sanity_checks:
                        valid = False

                ret = [self.trader.convert_index(found_index), valid]
            else:
                # Received data for closing the trade
                ret = [ret[0], True]
        return ret
        
    def send_chosen_mon(self, choice):
        """
        Handles sending which pokémon the player wants to trade.
        """
        index = self.trader.convert_choice(choice)
        own_mon = []
        if choice != GSCTrading.gsc_stop_trade:
            if index < self.trader.own_pokemon.get_party_size():
                own_mon = self.trader.own_pokemon.pokemon[index].get_data()
                if self.trader.own_pokemon.is_mon_egg(index):
                    own_mon += [GSCTradingClient.egg_value]
                else:
                    own_mon += [0]
        self.send_with_counter(GSCTradingClient.gsc_choice_transfer, [choice] + own_mon)
    
    def on_get_big_trading_data(self):
        """
        Signals to the user that the buffered trade is ready!
        """
        if not self.received_one:
            self.received_one = True
            if self.verbose:
                print(GSCTradingStrings.received_buffered_data_str)
    
    def reset_big_trading_data(self):
        """
        Make it so if we need to resend stuff, the buffers are clean.
        """
        self.connection.reset_send(GSCTradingClient.gsc_full_transfer)
        self.connection.reset_recv(GSCTradingClient.gsc_full_transfer)
        self.received_one = False
        
    def get_big_trading_data(self, lengths):
        """
        Handles getting the other player's entire trading data.
        If it's not ready, it loads a default party in order to get
        the player's entire trading data and prepares the data for 
        closing that trade.
        """
        success = True
        data = self.connection.recv_data(GSCTradingClient.gsc_full_transfer)
        if data is None:
            success = False
            data = GSCUtilsLoaders.load_trading_data(self.fileBaseTargetName, lengths)
        else:
            data = GSCUtilsMisc.divide_data(data, lengths)
        return data, success

    def send_big_trading_data(self, data):
        """
        Handles sending the player's entire trading data.
        """
        self.connection.send_data(GSCTradingClient.gsc_full_transfer, data[0]+data[1]+data[2])
        
    def get_pool_trading_data(self, lengths):
        """
        Handles getting the trading data for the mon offered by the server.
        """
        mon = self.connection.recv_data(GSCTradingClient.gsc_pool_transfer)
        if mon is not None:
            # Applies the checks to the received data.
            # If the sanity checks are off, this will be a simple copy
            actual_data = [0] * len(mon)
            checker = self.trader.checks.single_pokemon_checks_map
            if len(actual_data) > len(checker):
                for i in range(len(checker)):
                    actual_data[i] = checker[i](mon[i])
            
            
                # Handle getting/sending eggs. That requires one extra byte
                is_egg = False
                if actual_data[len(checker)] == GSCTradingClient.egg_value:
                    is_egg = True

                # Insert the received mon into a pre-baked party
                received_mon = GSCTradingPokémonInfo.set_data(actual_data)
                mon = GSCTradingData(GSCUtilsMisc.read_data(self.fileBasePoolTargetName), do_full=False)
                mon.pokemon += [received_mon]
                
                # Specially handle the egg party IDs
                if not is_egg:
                    mon.party_info.set_id(0, mon.pokemon[0].get_species())
        return mon
        
    def get_trading_data(self):
        """
        Handles getting the other player's current bytes of trading data.
        """
        return self.connection.recv_data(GSCTradingClient.gsc_single_transfer)

    def send_trading_data(self, data):
        """
        Handles sending the player's current bytes of trading data.
        """
        self.connection.send_data(GSCTradingClient.gsc_single_transfer, data)
    
    def send_buffered_data(self, buffered):
        """
        Handles sending the client's choice for the type of trade.
        """
        val = GSCTradingClient.gsc_not_buffered_value
        if buffered:
            val = GSCTradingClient.gsc_buffered_value
        self.send_single_byte(GSCTradingClient.gsc_buffered_transfer, val)
    
    def get_buffered_data(self):
        """
        Handles getting the other client's choice for the type of trade.
        """
        buffered = None
        val = self.get_single_byte(GSCTradingClient.gsc_buffered_transfer)
        if val is not None:
            if val == GSCTradingClient.gsc_buffered_value:
                buffered = True
            elif val == GSCTradingClient.gsc_not_buffered_value:
                buffered = False
        return buffered
    
    def send_negotiation_data(self):
        """
        Handles sending the client's convergence value for the type of trade.
        """
        r = Random()
        val = r.randint(0, GSCTradingClient.max_negotiation_id)
        self.send_single_byte(GSCTradingClient.gsc_negotiation_transfer, val)
        return val
    
    def get_negotiation_data(self):
        """
        Handles getting the other client's convergence value
        for the type of trade.
        """
        return self.get_single_byte(GSCTradingClient.gsc_negotiation_transfer)

class GSCTrading:
    """
    Class which handles the trading process for the player.
    """
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
        self.comms = GSCTradingClient(self, connection, menu.verbose)
        self.menu = menu
        self.kill_function = kill_function
        self.extremely_verbose = False
        GSCUtils()

    def send_predefined_section(self, states_list, stop_to=0, die_on_no_data=False):
        """
        Sends a specific and fixed section of data to the player.
        It waits for the next step until it gets to it.
        It can also detect when the player is done trading.
        """
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
        """
        Checks if the transfer dropped any bytes.
        """
        if byte_index >= self.gsc_drop_bytes_checks[0][section_index]:
            if byte_index < self.gsc_special_sections_len[section_index]:
                if byte == self.gsc_drop_bytes_checks[1][section_index]:
                    return True
            else:
                if byte != self.gsc_drop_bytes_checks[1][section_index]:
                    return True
        return False
    
    def check_bad_data(self, byte, byte_index, section_index):
        """
        If any byte was dropped, either drop a warning
        or an error depending on kill_on_byte_drops.
        """
        if self.has_transfer_failed(byte, byte_index, section_index):
            if self.menu.kill_on_byte_drops:
                print(GSCTradingStrings.error_byte_dropped_str)
                self.kill_function()
            elif not self.printed_warning_drop:
                if self.menu.verbose:
                    print(GSCTradingStrings.warning_byte_dropped_str)
                self.printed_warning_drop = True
                    
    def read_section(self, index, send_data, buffered):
        """
        Reads a data section and sends it to the device.
        """
        length = self.gsc_special_sections_len[index]
        next = self.gsc_next_section
        
        # Prepare sanity checks stuff
        self.checks.prepare_text_buffer()
        self.checks.prepare_species_buffer()

        if not buffered:
            # Wait for a connection to be established if it's synchronous
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

        # Sync with the device and start the actual trade
        while next == self.gsc_next_section:
            next = self.swap_byte(next)
        # next now contains the first received byte from the device!

        if buffered:
            buf = [next]
            # If the trade is buffered, just send the data from the buffer
            for i in range(length-1):
                if send_data is not None:
                    next = self.checks.checks_map[index][i](send_data[i])
                    send_data[i] = next
                next = self.swap_byte(next)
                buf += [next]
            
            if send_data is not None:
                # Send the last byte too
                next = self.checks.checks_map[index][length-1](send_data[length-1])
                send_data[length-1] = next
            self.swap_byte(next)
            other_buf = send_data
        else:
            # If the trade is synchronous, prepare small send buffers
            self.printed_warning_drop = False
            buf = [next]
            other_buf = []
            send_buf = [[0,next],[0xFFFF,0xFF],[index]]
            for i in range(length + 1):
                found = False
                # Send the current byte (and the previous one) to the
                # other client
                self.comms.send_trading_data(self.write_entire_data(send_buf))
                while not found:
                    received = self.comms.get_trading_data()
                    if received is not None:
                        recv_buf = self.read_entire_data(received)
                        if recv_buf[i&1] is not None:
                            byte_num = recv_buf[i&1][0]
                            # Check whether the other client's data has
                            # the byte the device needs
                            if byte_num == i and i != length:
                                # If it does, clean it and send it
                                cleaned_byte = self.checks.checks_map[index][i](recv_buf[i&1][1])
                                next = self.swap_byte(cleaned_byte)
                                # This will, in turn, get the next byte
                                # the other client needs
                                send_buf[(i+1)&1][0] = i + 1
                                send_buf[(i+1)&1][1] = next
                                buf += [next]
                                other_buf += [cleaned_byte]
                                # Check for "bad transfer" clues
                                self.check_bad_data(cleaned_byte, i, index)
                                self.check_bad_data(next, i + 1, index)
                                found = True
                            # Handle the last byte differently
                            elif byte_num == i:
                                found = True
                            elif i == length and recv_buf[2][0] == index + 1:
                                found = True
                    if not found:
                        self.sleep_func()
        return buf, other_buf
    
    def swap_byte(self, send_data):
        """
        Swaps a byte with the device. First send, and then receives.
        It's a high level abstraction which emulates how real hardware works.
        """
        self.sleep_func()
        self.sendByte(send_data)
        recv = self.receiveByte()
        if self.extremely_verbose:
            print(GSCTradingStrings.byte_transfer_str.format(send_data=send_data, recv=recv))
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
        """
        Forces a currently open trade menu to be closed.
        """
        next = 0
        target = self.gsc_stop_trade
        while(next != target):
            next = self.swap_byte(self.gsc_stop_trade)
            if(target == self.gsc_stop_trade and next == target):
                target = 0

    def wait_for_input(self, next):
        """
        Waits for an useful value.
        """
        while(next == self.gsc_no_input or next == self.gsc_no_data):
            next = self.swap_byte(self.gsc_no_input)
        return next

    def wait_for_no_data(self, next, resent_byte):
        """
        Waits for gsc_no_data.
        """
        while(next != self.gsc_no_data):
            next = self.swap_byte(resent_byte)
        return next

    def wait_for_no_input(self, next):
        """
        Waits for gsc_no_input.
        """
        while(next != self.gsc_no_input):
            next = self.swap_byte(self.gsc_no_input)
        return next
        
    def is_choice_decline(self, choice):
        """
        Checks for a trade acceptance decline.
        """
        if choice == self.gsc_decline_trade:
            return True
        return False
    
    def convert_choice(self, choice):
        """
        Converts the menu choice to an index.
        """
        return choice - self.gsc_first_trade_index
    
    def convert_index(self, index):
        """
        Converts the index to a menu choice.
        """
        return index + self.gsc_first_trade_index

    def is_choice_stop(self, choice):
        """
        Checks for a request to stop the trade.
        """
        if choice == self.gsc_stop_trade:
            return True
        return False
    
    def force_receive(self, fun):
        """
        Blocking wait for the requested data.
        It also keeps the device clock running properly.
        """
        received = None
        while received is None:
            self.sleep_func()
            received = fun()
            self.swap_byte(self.gsc_no_input)
        return received
    
    def reset_trade(self):
        """
        Reset the trade data...
        """
        self.own_pokemon = None
        self.other_pokemon = None
    
    def check_reset_trade(self):
        """
        Reset the trade if the data can't be used anymore...
        """
        if self.own_blank_trade and self.other_blank_trade:
            # We got here. The other player is in the menu too.
            # Prepare the buffered trade buffers for reuse.
            self.comms.reset_big_trading_data()
            self.reset_trade()

    def do_trade(self, close=False):
        """
        Handles the trading menu.
        """
        trade_completed = False
        autoclose_on_stop = False

        while not trade_completed:
            # Get the choice
            next = self.gsc_no_input
            sent_mon = self.wait_for_input(next)

            if not close:
                if autoclose_on_stop and self.is_choice_stop(sent_mon):
                    received_choice = self.gsc_stop_trade
                else:
                    # Send it to the other player
                    self.comms.send_chosen_mon(sent_mon)
            
                    # Get the other player's choice
                    received_data = self.force_receive(self.comms.get_chosen_mon)
                    autoclose_on_stop = False
                    received_choice = received_data[0]
                    received_valid = received_data[1]
            else:
                self.reset_trade()
                received_choice = self.gsc_stop_trade

            if not self.is_choice_stop(received_choice) and not self.is_choice_stop(sent_mon):
                # Send the other player's choice to the game
                next = self.swap_byte(received_choice)

                # Get whether the trade was declined or not
                next = self.wait_for_no_data(next, received_choice)
                next = self.wait_for_no_input(next)
                accepted = self.wait_for_input(next)
                
                # Check validity of trade
                valid_trade = received_valid
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
                    
                    # Check whether we need to restart entirely.
                    self.check_reset_trade()

                    # Conclude the trade successfully
                    next = self.wait_for_input(next)

                    # Send it to the other player
                    self.comms.send_success()

                    # Get the other player's choice
                    self.force_receive(self.comms.get_success)

                    trade_completed = True
                    next = self.swap_byte(next)
                    
            else:
                if self.is_choice_stop(sent_mon) and self.is_choice_stop(received_choice):
                    # If both players want to end the trade, do it
                    trade_completed = True
                    self.end_trade()
                else:
                    # If one player doesn't want that, get the next values.
                    # Prepare to exit at a moment's notice though...
                    autoclose_on_stop = True
                    
                    # Send the other player's choice to the game
                    next = self.swap_byte(received_choice)
                    next = self.wait_for_no_data(next, received_choice)
                    next = self.wait_for_no_input(next)

    def enter_room(self):
        """
        Makes it so the device can enter the trading room.
        """
        self.send_predefined_section(self.gsc_enter_room_states)
        
    def trade_starting_sequence(self, buffered, send_data = [None, None, None]):
        """
        Handles exchanging with the device the three data sections which
        are needed in order to trade.
        Optimizes the synchronous mail_data exchange by executing it only
        if necessary and in the way which requires less packet transfers.
        Returns the player's data and the other player's data.
        """
        # Send and get the first two sections
        random_data, random_data_other = self.read_section(0, send_data[0], buffered)
        pokemon_data, pokemon_data_other = self.read_section(1, send_data[1], buffered)
        
        pokemon_own = GSCTradingData(pokemon_data)
        pokemon_other = GSCTradingData(pokemon_data_other)
        pokemon_own_mail = pokemon_own.party_has_mail()
        pokemon_other_mail = pokemon_other.party_has_mail()
        
        # Trade mail data only if needed
        if (pokemon_own_mail and pokemon_other_mail) or buffered:
            mail_data, mail_data_other = self.read_section(2, send_data[2], buffered)
        else:
            send_data[2] = GSCUtils.no_mail_section
            # Get mail data if only the other client has it
            if pokemon_other_mail:
                send_data[2] = self.force_receive(self.comms.get_mail_data_only)
                
            # Exchange mail data with the device
            mail_data, mail_data_other = self.read_section(2, send_data[2], True)
            
            # Send mail data if only this client has it
            if pokemon_own_mail:
                self.comms.send_mail_data_only(mail_data)
        
        return [random_data, pokemon_data, mail_data], [random_data_other, pokemon_data_other, mail_data_other]
    
    def synchronous_trade(self):
        """
        Handles launching a synchronous trade.
        Returns True.
        """
        if self.other_pokemon is None:
            data, data_other = self.trade_starting_sequence(False)
        else:
            # Generate the trading data for the device
            # from the other player's one and use it
            data, data_other = self.trade_starting_sequence(True, send_data=self.other_pokemon.create_trading_data(GSCTrading.gsc_special_sections_len))
        self.own_pokemon = GSCTradingData(data[1], data_mail=data[2])
        self.other_pokemon = GSCTradingData(data_other[1], data_mail=data_other[2])
        return True
    
    def buffered_trade(self):
        """
        Handles launching a buffered trade.
        Returns whether the data is the default one or the one
        of another player.
        """
        if self.other_pokemon is None:
            data, valid = self.comms.get_big_trading_data(self.gsc_special_sections_len)
        else:
            # Generate the trading data for the device
            # from the other player's one and use it
            data = self.other_pokemon.create_trading_data(GSCTrading.gsc_special_sections_len)
            valid = True
        data, data_other = self.trade_starting_sequence(True, send_data=data)
        self.comms.send_big_trading_data(data)
        self.own_pokemon = GSCTradingData(data[1], data_mail=data[2])
        self.other_pokemon = GSCTradingData(data_other[1], data_mail=data_other[2])
        return valid

    def player_trade(self, buffered):
        """
        Handles trading with another player.
        Optimizes the data exchanges by executing them only
        if necessary and in the way which requires less packet transfers.
        """
        self.own_blank_trade = True
        self.other_blank_trade = True
        self.reset_trade()
        buf_neg = GSCBufferedNegotiator(self.menu, self.comms, buffered, self.sleep_func)
        buf_neg.start()
        # Start of what the player sees. Enters the room
        self.enter_room()
        while True:
            # Wait for the player to sit to the table
            if not self.send_predefined_section(self.gsc_start_trading_states, stop_to=1, die_on_no_data=True):
                break
            # If necessary, start a normal transfer
            if self.own_blank_trade and self.other_blank_trade:
                buffered = self.force_receive(buf_neg.get_chosen_buffered)
                if buffered:
                    valid = self.buffered_trade()
                else:
                    valid = self.synchronous_trade()
            else:
                # If only the other client requires user inputs,
                # wait for its data
                if self.other_blank_trade:
                    self.force_receive(self.comms.get_move_data_only)
                    
                # Generate the trading data for the device
                # from the other player's one and use it
                data, data_other = self.trade_starting_sequence(True, send_data=self.other_pokemon.create_trading_data(GSCTrading.gsc_special_sections_len))
                
                # If only this client requires user inputs,
                # send its data
                if  self.own_blank_trade:
                    self.own_pokemon = GSCTradingData(data[1], data_mail=data[2])
                    self.comms.send_move_data_only()
            
            self.own_blank_trade = True
            self.other_blank_trade = True
            # Start interacting with the trading menu
            self.do_trade(close=not valid)

    def pool_trade(self, buffered):
        """
        Handles trading with the Pool.
        """
        self.reset_trade()
        # Start of what the player sees. Enters the room
        self.enter_room()
        while True:
            # Wait for the player to sit to the table
            if not self.send_predefined_section(self.gsc_start_trading_states, stop_to=1, die_on_no_data=True):
                break

            # If necessary, start a normal transfer
            if self.own_blank_trade and self.other_blank_trade:
                buffered = self.force_receive(buf_neg.get_chosen_buffered)
                if buffered:
                    valid = self.buffered_trade()
                else:
                    valid = self.synchronous_trade()

            # Start interacting with the trading menu
            self.do_trade(close=not valid)
        
    # Function needed in order to make sure there is enough time for the slave to prepare the next byte.
    def sleep_func(self, multiplier = 1):
        time.sleep(self.sleep_timer * multiplier)