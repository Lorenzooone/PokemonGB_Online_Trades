import time
from .gsc_trading import GSCTradingClient, GSCTrading
from .gsc_trading_strings import GSCTradingStrings
from .rse_sp_trading_data_utils import RSESPUtils, RSESPTradingData, RSESPChecks
from .gsc_trading_data_utils import GSCUtilsMisc

class RSESPTradingClient(GSCTradingClient):
    """
    Class which handles sending/receiving trading data
    to/from the other recepient.
    It uses a system of TAGs and IDs.
    """
    base_folder = "useful_data/rse/"
    full_transfer = "FL3S"
    pool_transfer = "P3SI"
    pool_transfer_out = "P3SO"
    choice_transfer = "CH3S"
    accept_transfer = ["A3S1", "A3S2"]
    success_transfer = ["S3S1", "S3S2", "S3S3", "S3S4", "S3S5", "S3S6", "S3S7"]
    possible_transfers = {
        full_transfer: {0x380}, # Total transfer's length - v1.0.0 
        pool_transfer: {1 + 0x95, 1 + 1}, # Counter + Single Pokémon (and mail + version + special ribbons) OR Counter + Fail
        pool_transfer_out: {1 + 0x95, 1}, # Counter + Single Pokémon (and mail + version + special ribbons)
        choice_transfer : {1 + 3}, # Counter + Choice
        accept_transfer[0] : {1 + 3}, # Counter + Accept
        accept_transfer[1] : {1 + 3}, # Counter + Accept2
        success_transfer[0] : {1 + 3}, # Counter + Success
        success_transfer[1] : {1 + 3}, # Counter + Success
        success_transfer[2] : {1 + 3}, # Counter + Success
        success_transfer[3] : {1 + 3}, # Counter + Success
        success_transfer[4] : {1 + 3}, # Counter + Success
        success_transfer[5] : {1 + 3}, # Counter + Success
        success_transfer[6] : {1 + 3}, # Counter + Success
    }
    
    def __init__(self, trader, connection, verbose, stop_trade, party_reader, base_no_trade = base_folder + "base.bin", base_pool = base_folder + "base_pool.bin"):
        super(RSESPTradingClient, self).__init__(trader, connection, verbose, stop_trade, party_reader, base_no_trade=base_no_trade, base_pool=base_pool)
        
    def get_utils_class(self):
        return RSESPUtils
        
    def get_pool_trading_data(self):
        """
        Handles getting the trading data for the mon offered by the server.
        """
        mon = self.get_with_counter(self.pool_transfer)
        if mon is not None:
            if len(mon) == 1:
                print(GSCTradingStrings.pool_fail_str)
                self.trader.kill_function()
                
            # Applies the checks to the received data.
            received_mon = self.utils_class.single_mon_from_data(self.trader.checks, mon)
                
            if received_mon is not None:
                # Insert the received mon into a pre-baked party
                mon = self.party_reader(GSCUtilsMisc.read_data(self.fileBaseTargetName), do_full=False)
                mon.pokemon += [received_mon[0]]
                
                # Handle max level option
                if received_mon[0].get_level() > self.trader.max_level:
                    received_mon[0].set_level(self.trader.max_level)
                
                # Specially handle the egg party IDs
                if not received_mon[1]:
                    mon.party_info.set_id(0, received_mon[0].get_species())
                    # Handle egg options
                    if (self.trader.menu.egg) and (self.trader.menu.gen == 2):
                        received_mon[0].set_hatching_cycles()
                        received_mon[0].set_egg_nickname()
            else:
                mon = None
                    
        return mon
        
    def send_pool_trading_data_out(self, choice):
        """
        Handles getting the trading data for the mon offered by the server.
        """
        index = self.trader.convert_choice(choice)
        own_mon = []
        if not self.trader.is_choice_stop(choice):
            if index < self.trader.own_pokemon.get_party_size():
                if (choice & 0xFFFF) == self.trader.own_pokemon.pokemon[index].get_species():
                    own_mon = self.utils_class.single_mon_to_data(self.trader.own_pokemon.pokemon[index], None)
        self.send_with_counter(self.pool_transfer_out, own_mon)
    
    def get_three_bytes_of_data(self, ret):
        if ret is not None:
            ret = GSCUtilsMisc.from_n_bytes_le(ret, 3)
        return ret
        
    def get_big_trading_data(self):
        """
        Handles getting the other player's entire trading data.
        If it's not ready, it loads a default party in order to get
        the player's entire trading data and prepares the data for 
        closing that trade.
        """
        return self.connection.recv_data(self.full_transfer)

    def get_accepted(self, num_accept):
        """
        Handles getting whether the other player wants to do the trade
        or not.
        """
        return self.get_three_bytes_of_data(self.get_with_counter(self.accept_transfer[num_accept]))
                
    def send_accepted(self, choice, num_accept):
        """
        Handles sending whether the player wants to do the trade or not.
        """
        self.send_with_counter(self.accept_transfer[num_accept], GSCUtilsMisc.to_n_bytes_le(choice, 3))

    def get_success(self, num_success):
        """
        Handles getting the success trade confirmation value.
        """
        return self.get_three_bytes_of_data(self.get_with_counter(self.success_transfer[num_success]))
                
    def send_success(self, choice, num_success):
        """
        Handles sending the success trade confirmation value.
        """
        self.send_with_counter(self.success_transfer[num_success], GSCUtilsMisc.to_n_bytes_le(choice, 3))
                
    def get_chosen_mon(self):
        """
        Handles getting which pokémon the other player wants to trade.
        """
        return self.get_three_bytes_of_data(self.get_with_counter(self.choice_transfer))
        
    def send_chosen_mon(self, choice):
        """
        Handles sending which pokémon the player wants to trade.
        """
        self.send_with_counter(self.choice_transfer, GSCUtilsMisc.to_n_bytes_le(choice, 3))

class RSESPTrading(GSCTrading):
    """
    Class which handles the trading process for the player.
    """
    
    special_sections_len = [0x380]
    num_bytes_per_transfer = 4
    asking_data_nybble = 0xC
    trade_offer_start = 0x80
    trade_cancel = 0x8F
    possible_indexes = set(list(range(trade_offer_start, trade_offer_start+6)) + [trade_cancel])
    stop_trade = (trade_cancel<<16)
    first_trade_index = (trade_offer_start<<16)
    done_control_flag = 0x20
    not_done_control_flag = 0x40
    sending_data_control_flag = 0x10
    in_party_trading_flag = 0x80
    since_last_useful_limit = 10
    base_send_data_start = 1
    base_data_chunk_size = 0xFE
    accept_trade = [0xA2, 0xB2]
    decline_trade = [0xA1, 0xB1]
    success_trade = [0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x9C]
    failed_trade = 0x9F
    decline_trade_value = [decline_trade[0]<<16, decline_trade[1]<<16]
    no_input = 0
    
    def __init__(self, sending_func, receiving_func, connection, menu, kill_function):
        super(RSESPTrading, self).__init__(sending_func, receiving_func, connection, menu, kill_function)
        
    def get_and_init_utils_class(self):
        RSESPUtils()
        return RSESPUtils
    
    def party_reader(self, data, data_mail=None, do_full=True):
        return RSESPTradingData(data, data_mail=data_mail, do_full=do_full)
    
    def get_comms(self, connection, menu):
        return RSESPTradingClient(self, connection, menu.verbose, self.stop_trade, self.party_reader)
    
    def get_checks(self, menu):
        return RSESPChecks(self.special_sections_len, menu.do_sanity_checks)
    
    def get_bytes_from_pos(self, index):
        base_pos = index & 0xFFF
        byte_base = self.base_send_data_start
        while base_pos >= self.base_data_chunk_size:
            base_pos -= self.base_data_chunk_size
            byte_base += 1
        return (byte_base << 8) | base_pos
    
    def get_pos_from_bytes(self, value):
        final_pos = value & 0xFF
        if final_pos >= self.base_data_chunk_size:
            final_pos = 0
        return final_pos + (self.base_data_chunk_size * (((value>>8)&0xF) - self.base_send_data_start))
    
    def swap_trade_data_dump(self):
        return self.interpret_in_data_trade_gen3(self.swap_byte((self.done_control_flag | self.in_party_trading_flag)<<24))
    
    def swap_trade_offer_data_pure(self, in_data, is_cancel=False):
        data = (self.done_control_flag | self.in_party_trading_flag)<<24
        if is_cancel:
            data |= (self.trade_cancel)<<16
        else:
            data |= in_data
        
        return self.interpret_in_data_trade_gen3(self.swap_byte(data))
    
    def swap_trade_raw_data_pure(self, in_data):
        data = (self.done_control_flag | self.in_party_trading_flag)<<24
        data |= in_data

        return self.interpret_in_data_trade_gen3(self.swap_byte(data))
    
    def send_data_multiple_times(self, fun, in_data):
        fun(in_data)
        for i in range(self.option_confirmation_threshold):
            fun(in_data)
        
    def swap_trade_setup_data(self, next, index, is_complete):
        data = next
        if is_complete:
            data |= self.done_control_flag<<24
        else:
            data |= self.not_done_control_flag<<24
        data |= self.sending_data_control_flag<<24
        data |= self.get_bytes_from_pos(index)<<16
        data |= next & 0xFFFF
        
        return self.interpret_in_data_setup_gen3(self.swap_byte(data))
    
    def ask_trade_setup_data(self, start, end):
        data = 0
        data |= (self.not_done_control_flag|self.asking_data_nybble)<<24
        data |= start & 0xFFF
        data |= (end & 0xFFF)<<12
            
        return self.interpret_in_data_setup_gen3(self.swap_byte(data))

    def interpret_in_data_setup_gen3(self, data):
        next = data & 0xFFFF
        position = (data >> 16) & 0xFF
        control_byte = (data >> 24) & 0xFF
        other_pos_gen3 = data & 0xFFF
        other_end_gen3 = (data >> 12) & 0xFFF

        is_valid = False
        is_asking = False
        is_complete = False
        is_done = False
        
        if(control_byte & 0xF) >= self.asking_data_nybble:
            control_byte &= ~self.sending_data_control_flag
            if(control_byte & self.not_done_control_flag) != 0:
                is_asking = True
                if other_end_gen3 > (self.special_sections_len[0] >> 1):
                    other_end_gen3 = self.special_sections_len[0] >> 1
                if other_pos_gen3 >= other_end_gen3:
                    other_pos_gen3 = other_end_gen3
            elif(control_byte & self.done_control_flag) != 0:
                other_pos_gen3 = other_end_gen3;
        if(control_byte & self.sending_data_control_flag) != 0:
            recv_pos = self.get_pos_from_bytes(data >> 16)
            position = recv_pos
            is_valid = True
            if recv_pos >= (self.special_sections_len[0] >> 1):
                recv_pos = 0
                control_byte &= ~self.sending_data_control_flag
                is_valid = False
        if(control_byte & self.done_control_flag) != 0:
            is_done = True
            if(control_byte & self.in_party_trading_flag):
                is_complete = True
        return next, position, is_valid, is_asking, is_complete, is_done, other_pos_gen3, other_end_gen3

    def interpret_in_data_trade_gen3(self, data):
        next = data & 0xFFFFFF
        position = (data >> 16) & 0xFF
        control_byte = (data >> 24) & 0xFF
        
        if control_byte != (self.in_party_trading_flag | self.done_control_flag):
            return None
        
        return next

    def find_uncompleted_range(self, completed_data):
        i = 0
        max_size = 0
        max_start = 0
        max_end = 0
        while i < len(completed_data):
            k = i
            for l in range(i, len(completed_data)):
                if completed_data[l]:
                    break
                k += 1
            if(k - i) > max_size:
                max_size = k - i
                max_start = i
                max_end = k
            if k != i:
                i = k
            else:
                i += 1
        return max_start, max_end
                    
    def read_section(self, send_data):
        """
        Reads a data section and sends it to the device.
        """
        length = self.special_sections_len[0]
        completed_data = []
        buf = []
        for i in range(int(length/2)):
            completed_data += [False]
            buf += [0, 0]
        
        num_uncompleted = int(length/2)
        other_pos_gen3 = 0
        other_end_gen3 = 0
        
        next = 0
        since_last_useful = self.since_last_useful_limit
        transfer_successful = False
        has_all_data = False
        #self.sync_with_cable(self.not_done_control_flag|self.asking_data_nybble)
        
        while not transfer_successful:
            if (since_last_useful >= self.since_last_useful_limit) and not has_all_data:
                start, end = self.find_uncompleted_range(completed_data)
                next, index, is_valid, is_asking, is_complete, is_done, tmp_other_pos_gen3, tmp_other_end_gen3 = self.ask_trade_setup_data(start, end)
                since_last_useful = 0
            else:
                if send_data is not None:
                    if other_pos_gen3 < other_end_gen3:
                        next = (send_data[other_pos_gen3*2]) | (send_data[(other_pos_gen3*2)+1]<<8)
                    else:
                        next = 0
                else:
                    next = 0
                    other_pos_gen3 = 0
                next, index, is_valid, is_asking, is_complete, is_done, tmp_other_pos_gen3, tmp_other_end_gen3 = self.swap_trade_setup_data(next, other_pos_gen3, has_all_data)
                if(other_pos_gen3 < other_end_gen3):
                    other_pos_gen3 += 1
                if(other_pos_gen3 >= int(length/2)):
                    other_pos_gen3 = 0
            since_last_useful += 1
            if is_asking:
                other_pos_gen3 = tmp_other_pos_gen3
                other_end_gen3 = tmp_other_end_gen3
            elif not (is_done and is_complete):
                if (not has_all_data) and is_valid:
                    buf[index*2] = next & 0xFF
                    buf[(index*2)+1] = (next>>8) & 0xFF
                    if not completed_data[index]:
                        since_last_useful = 0
                        completed_data[index] = True
                        num_uncompleted -= 1
                        if num_uncompleted == 0:
                            if RSESPTradingData.are_checksum_valid(RSESPTradingData, buf, self.special_sections_len):
                                has_all_data = True
                                if send_data is None:
                                    transfer_successful = True
                            else:
                                for i in range(int(length/2)):
                                    completed_data[i] = False
                                since_last_useful = self.since_last_useful_limit
                                num_uncompleted = int(length/2)
            else:
                if has_all_data:
                    transfer_successful = True
            self.verbose_print(GSCTradingStrings.transfer_to_hardware_str.format(index=0, completion=GSCTradingStrings.x_out_of_y_str(length-(num_uncompleted*2), length)), end='')

        other_buf = send_data
        self.verbose_print(GSCTradingStrings.separate_section_str, end='')
        return buf, other_buf
                
    def wait_for_set_of_values(self, next, values):
        """
        Waits for the user choosing an option and confirms it's not some
        garbage being sent.
        """
        found_val = None
        consecutive_reads = 0
        while consecutive_reads < self.option_confirmation_threshold:
            next = self.swap_trade_data_dump()
            found = False
            if next is not None:
                command_id = next >> 16
                if command_id in values:
                    if next == found_val:
                        consecutive_reads += 1
                        found = True
            if not found:
                consecutive_reads = 0
            found_val = next
        return next

    def wait_for_accept_decline(self, next, num_accepted):
        """
        Waits for an useful value.
        """
        return self.wait_for_set_of_values(next, set([self.accept_trade[num_accepted], self.decline_trade[num_accepted]]))
    
    def sync_with_cable(self, objective):
        recv = 0
        while recv != objective:
            self.sendByte(0, 1)
            recv = self.receiveByte(1)
        self.sendByte(0, 3)
        recv = self.receiveByte(3)

    def wait_for_success(self, next, num_success):
        """
        Waits for success.
        """
        return self.wait_for_set_of_values(next, set([self.success_trade[num_success], self.failed_trade]))

    def is_choice_stop(self, choice):
        """
        Checks for a request to stop the trade.
        """
        if (choice & 0xFF0000) == self.stop_trade:
            return True
        return False
        
    def is_choice_decline(self, choice, num_accepted):
        """
        Checks for a trade acceptance decline.
        """
        if (choice & 0xFF0000) == self.decline_trade_value[num_accepted]:
            return True
        return False
    
    def convert_choice(self, choice):
        """
        Converts the menu choice to an index.
        """
        return (choice - self.first_trade_index) >> 16
        
    def has_failed(self, value):
        """
        Checks for a trade acceptance decline.
        """
        if (value & 0xFF0000) == self.failed_trade:
            return True
        return False
    
    def end_trade(self):
        """
        Forces a currently open trade menu to be closed.
        """
        next = 0
        while(next is None or ((next & 0xFF0000) != self.stop_trade)):
            next = self.swap_trade_offer_data_pure(0, is_cancel=True)

        self.send_data_multiple_times(self.swap_trade_offer_data_pure, self.stop_trade)

    def do_trade(self, get_mon_function, close=False, to_server=False):
        """
        Handles the trading menu.
        """
        trade_completed = False
        base_autoclose = False
        if to_server:
            base_autoclose = True
        autoclose_on_stop = base_autoclose
        
        if close:
            self.verbose_print(GSCTradingStrings.quit_trade_str)

        while not trade_completed:
            # Get the choice
            sent_mon = self.wait_for_choice(0)

            if not close:
                if autoclose_on_stop and self.is_choice_stop(sent_mon):
                    received_choice = self.stop_trade
                else:
                    # Send it to the other player
                    self.verbose_print(GSCTradingStrings.choice_send_str)
                    if to_server:
                        self.comms.send_pool_trading_data_out(sent_mon)
                    else:
                        self.comms.send_chosen_mon(sent_mon)
            
                    # Get the other player's choice
                    if not to_server:
                        self.verbose_print(GSCTradingStrings.choice_recv_str)
                    received_choice = self.force_receive(get_mon_function)
                    autoclose_on_stop = base_autoclose
            else:
                self.reset_trade()
                received_choice = self.stop_trade

            if not self.is_choice_stop(received_choice) and not self.is_choice_stop(sent_mon):
                # Send the other player's choice to the game
                self.send_data_multiple_times(self.swap_trade_offer_data_pure, received_choice)
                
                for i in range(2):
                    # Get whether the trade was declined or not
                    accepted = self.wait_for_accept_decline(0, i)

                    if to_server and self.is_choice_decline(accepted, i):
                        received_accepted = self.decline_trade_value[i]
                    else:
                        # Send it to the other player
                        if i == 0:
                            self.verbose_print(GSCTradingStrings.accepted_send_str.format(accepted_str=GSCTradingStrings.get_accepted_str(self.is_choice_decline(accepted, i))))
                        self.comms.send_accepted(accepted, i)
                    
                        # Get the other player's choice
                        if i == 0:
                            self.verbose_print(GSCTradingStrings.accepted_wait_str)
                        received_accepted = self.force_receive_multi(self.comms.get_accepted, i)
                    
                    # Send the other player's choice to the game
                    self.send_data_multiple_times(self.swap_trade_raw_data_pure, received_accepted)

                if not self.is_choice_decline(received_accepted, 1) and not self.is_choice_decline(accepted, 1):

                    self.comms.reset_big_trading_data()
                    self.reset_trade()
                    for i in range(7):
                        # Conclude the trade successfully
                        success_result = self.wait_for_success(0, i)
                        if i == 0:
                            self.verbose_print(GSCTradingStrings.success_send_str)
                        self.comms.send_success(success_result, i)
                        if i == 0:
                            self.verbose_print(GSCTradingStrings.success_wait_str)
                        received_success = self.force_receive_multi(self.comms.get_success, i)
                        self.send_data_multiple_times(self.swap_trade_raw_data_pure, received_success)

                    trade_completed = True
                    self.verbose_print(GSCTradingStrings.restart_trade_str)
                    self.exit_or_new = True
                    if(self.has_failed(success_result) or self.has_failed(received_success)):
                        return True
            else:
                if close or (self.is_choice_stop(sent_mon) and self.is_choice_stop(received_choice)):
                    # If both players want to end the trade, do it
                    trade_completed = True
                    self.exit_or_new = True
                    self.verbose_print(GSCTradingStrings.close_str)
                    self.end_trade()
                    return True
                else:
                    # If one player doesn't want that, get the next values.
                    # Prepare to exit at a moment's notice though...
                    autoclose_on_stop = True
                    self.verbose_print(GSCTradingStrings.close_on_next_str)
                    
                    # Send the other player's choice to the game
                    self.send_data_multiple_times(self.swap_trade_offer_data_pure, received_choice)
        self.reset_trade()
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
            self.swap_byte(0)
        return received
    
    def force_receive_multi(self, fun, num):
        """
        Blocking wait for the requested data.
        It also keeps the device clock running properly.
        """
        received = None
        while received is None:
            self.sleep_func()
            received = fun(num)
            self.swap_byte(0)
        return received
        
    def trade_starting_sequence(self, buffered, send_data = [None, None, None, None]):
        """
        Handles exchanging with the device the data section which
        is needed in order to trade.
        """
        # Prepare checks
        self.checks.reset_species_item_list()
        # Send and get the first two sections
        data, data_other = self.read_section(send_data[0])
        self.own_pokemon = self.party_reader(data)
        self.comms.send_big_trading_data(self.own_pokemon.create_trading_data(self.special_sections_len))
        if send_data[0] is None:
            data_other = self.own_pokemon.create_trading_data(self.special_sections_len)
            data_other = self.force_receive(self.comms.get_big_trading_data)
            data, data_other = self.read_section(data_other)

        self.own_pokemon = self.party_reader(data)
        self.other_pokemon = self.party_reader(data_other)
    
    def get_first_mon(self):
        """
        Returns the first index as the choice.
        """
        return self.first_trade_index | self.other_pokemon.pokemon[0].get_species()

    def player_trade(self, buffered):
        """
        Handles trading with another player.
        Optimizes the data exchanges by executing them only
        if necessary and in the way which requires less packet transfers.
        """
        self.trade_type = GSCTradingStrings.two_player_trade_str
        self.reset_trade()
        self.exit_or_new = True
        valid = True
        while True:
            # Get and send the data
            self.trade_starting_sequence(True)

            # Start interacting with the trading menu
            if self.do_trade(self.comms.get_chosen_mon, close=not valid):
                break

    def pool_trade(self):
        """
        Handles trading with the Pool.
        """
        self.trade_type = GSCTradingStrings.pool_trade_str
        self.reset_trade()
        self.max_level = self.menu.max_level
        while True:
            # Get data from the server and then use it to start the trade
            if self.other_pokemon is None:
                self.verbose_print(GSCTradingStrings.pool_receive_data_str)
                self.other_pokemon = self.force_receive(self.comms.get_pool_trading_data)
            else:
                self.verbose_print(GSCTradingStrings.pool_recycle_data_str)
            self.trade_starting_sequence(True, send_data=self.other_pokemon.create_trading_data(self.special_sections_len))

            # Start interacting with the trading menu
            if self.do_trade(self.get_first_mon, to_server=True):
                break
        
    # Function needed in order to make sure there is enough time for the slave to prepare the next byte.
    def sleep_func(self, multiplier = 1):
        time.sleep(self.sleep_timer * multiplier)
