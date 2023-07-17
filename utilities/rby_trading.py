from .gsc_trading import GSCTradingClient, GSCTrading
from .gsc_trading_strings import GSCTradingStrings
from .rby_trading_data_utils import RBYUtils, RBYTradingData, RBYChecks

class RBYTradingClient(GSCTradingClient):
    """
    Class which handles sending/receiving trading data
    to/from the other recepient.
    It uses a system of TAGs and IDs.
    """
    base_folder = "useful_data/rby/"
    full_transfer = "FLL1"
    single_transfer = "SNG1"
    pool_transfer = "POL1"
    moves_transfer = "MVS1"
    choice_transfer = "CHC1"
    accept_transfer = "ACP1"
    success_transfer = "SUC1"
    buffered_transfer = "BUF1"
    negotiation_transfer = "NEG1"
    version_client_transfer = "VEC1"
    version_server_transfer = "VES1"
    random_data_transfer = "RAN1"
    need_data_transfer = "ASK1"
    possible_transfers = {
        full_transfer: {0x271}, # Sum of special_sections_len
        single_transfer: {7, 32},
        pool_transfer: {1 + 0x42, 1 + 1}, # Counter + Single Pokémon OR Counter + Fail
        moves_transfer: {1 + 1 + 8}, # Counter + Species + Moves
        choice_transfer : {1 + 1 + 0x42, 1 + 1}, # Counter + Choice + Single Pokémon OR Counter + Stop
        accept_transfer : {1 + 1}, # Counter + Accept
        success_transfer : {1 + 1}, # Counter + Success
        buffered_transfer : {1 + 1}, # Counter + Buffered or not
        negotiation_transfer : {1 + 1}, # Counter + Convergence value
        version_client_transfer : {6}, # Client's version value
        version_server_transfer : {6}, # Server's version value
        random_data_transfer : {10}, # Random values from server
        need_data_transfer : {1 + 1} # Counter + Whether it needs the other player's data
    }
    
    def __init__(self, trader, connection, verbose, stop_trade, party_reader, base_no_trade = base_folder + "base.bin", base_pool = base_folder + "base_pool.bin"):
        super(RBYTradingClient, self).__init__(trader, connection, verbose, stop_trade, party_reader, base_no_trade=base_no_trade, base_pool=base_pool)
        
    def get_utils_class(self):
        return RBYUtils
    
    def get_move_data_only(self):
        """
        Handles getting the new move data when only the other player
        has user input and the species of the pokémon.
        It also loads it into the correct pokémon and evolves it if necessary.
        """
        val = self.get_with_counter(self.moves_transfer)
        if val is not None:
            updating_mon = self.trader.other_pokemon.pokemon[self.trader.other_pokemon.get_last_mon_index()]
            self.trader.checks.prepare_species_buffer()
            data = self.trader.checks.apply_checks_to_data(self.trader.checks.moves_checks_map, val)
            for i in range(4):
                updating_mon.set_move(i, data[i+1], max_pp=False)
                updating_mon.set_pp(i, data[i+5])
            if data[0] != updating_mon.get_species():
                self.trader.other_pokemon.evolution_procedure(self.trader.other_pokemon.get_last_mon_index(), data[0])
        return val
        
    def send_move_data_only(self):
        """
        Handles sending the new move data and the species of the pokémon
        when only the player has user input.
        It gets it from the correct pokémon.
        """
        val = [0,0,0,0,0,0,0,0,0]
        updated_mon = self.trader.own_pokemon.pokemon[self.trader.own_pokemon.get_last_mon_index()]
        val[0] = updated_mon.get_species()
        for i in range(4):
            val[i+1] = updated_mon.get_move(i)
            val[i+5] = updated_mon.get_pp(i)
        self.send_with_counter(self.moves_transfer, val)

class RBYTrading(GSCTrading):
    """
    Class which handles the trading process for the player.
    """
    
    enter_room_states = [[0x01, 0x60, 0xD0, 0xD4], [{0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x6F}, {0xD0, 0xD1, 0xD2, 0xD3, 0xD4}, {0xD0, 0xD1, 0xD2, 0xD3, 0xD4}, {0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x6F}]]
    start_trading_states = [[0x60, 0x60], [{0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x6F}, {0xFD}]]
    special_sections_len = [0xA, 0x1A2, 0xC5]
    special_sections_preamble_len = [7, 6, 3]
    success_base_value = 0x60
    success_values = set(range(success_base_value, success_base_value+0x10))
    possible_indexes = set(range(0x60, 0x70))
    articuno_species = 74
    zapdos_species = 75
    moltres_species = 73
    mew_species = 21
    special_mons = set([moltres_species, zapdos_species, articuno_species])
    next_section = 0xFD
    no_input = 0xFE
    drop_bytes_checks = [[0xA, 0x19F, 0xC5], [next_section, next_section, no_input], [0,0,0]]
    stop_trade = 0x6F
    first_trade_index = 0x60
    decline_trade = 0x61
    accept_trade = 0x62
    
    def __init__(self, sending_func, receiving_func, connection, menu, kill_function, pre_sleep):
        super(RBYTrading, self).__init__(sending_func, receiving_func, connection, menu, kill_function, pre_sleep)
        
    def get_and_init_utils_class(self):
        RBYUtils()
        return RBYUtils
    
    def create_success_set(self, traded_mons):
        """
        Everything is valid...
        """
        return self.success_values
    
    def party_reader(self, data, data_mail=None, do_full=True):
        return RBYTradingData(data, data_mail=data_mail, do_full=do_full)
    
    def get_comms(self, connection, menu):
        return RBYTradingClient(self, connection, menu.verbose, self.stop_trade, self.party_reader)
    
    def get_checks(self, menu):
        return RBYChecks(self.special_sections_len, menu.do_sanity_checks)

    def trade_starting_sequence(self, buffered, send_data = [None, None, None, None]):
        """
        Handles exchanging with the device the three data sections which
        are needed in order to trade.
        Optimizes the synchronous mail_data exchange by executing it only
        if necessary and in the way which requires less packet transfers.
        Returns the player's data and the other player's data.
        """
        # Prepare checks
        self.checks.reset_species_item_list()
        # Send and get the sections
        send_data[0] = self.utils_class.base_random_section
        just_sent = None
        self.is_running_compat_3_mode = True
        self.comms.send_client_version()
        server_version = self.attempt_receive(self.comms.get_server_version, 5)
        if server_version is not None:
            send_data[0] = self.force_receive(self.comms.get_random)
            other_client_version = self.attempt_receive(self.comms.get_client_version, 5)
            if other_client_version is not None:
                self.is_running_compat_3_mode = False
        if self.is_running_compat_3_mode:
            random_data, random_data_other, just_sent = self.read_section(0, send_data[0], buffered, just_sent, 0)
        else:
            random_data, random_data_other, just_sent = self.read_section(0, send_data[0], True, just_sent, 0)
        pokemon_data, pokemon_data_other, just_sent = self.read_section(1, send_data[1], buffered, just_sent, 0)
        patches_data, patches_data_other, just_sent = self.read_section(2, send_data[2], buffered, just_sent, 1)
        
        self.utils_class.apply_patches(pokemon_data, patches_data, self.utils_class)
        self.utils_class.apply_patches(pokemon_data_other, patches_data_other, self.utils_class)
        
        return [random_data, pokemon_data, None], [random_data_other, pokemon_data_other, None]
