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
    mail_transfer = "MAI1"
    choice_transfer = "CHC1"
    accept_transfer = "ACP1"
    success_transfer = "SUC1"
    buffered_transfer = "BUF1"
    negotiation_transfer = "NEG1"
    possible_transfers = {
        full_transfer: {0x271}, # Sum of special_sections_len
        single_transfer: {7},
        pool_transfer: {1 + 0x42, 1 + 1}, # Counter + Single Pokémon OR Counter + Fail
        moves_transfer: {1 + 1 + 8}, # Counter + Species + Moves
        mail_transfer : {1 + 0xC5}, # Counter + Mail
        choice_transfer : {1 + 1 + 0x42, 1 + 1}, # Counter + Choice + Single Pokémon OR Counter + Stop
        accept_transfer : {1 + 1}, # Counter + Accept
        success_transfer : {1 + 1}, # Counter + Success
        buffered_transfer : {1 + 1}, # Counter + Buffered or not
        negotiation_transfer : {1 + 1} # Counter + Convergence value
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
    
    enter_room_states = [[0x01, 0x60, 0xD0, 0xD4], [{0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x6F}, {0xD0, 0xD1, 0xD2, 0xD3, 0xD4}, {0xFE}, {0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x6F}]]
    start_trading_states = [[0x60, 0x60], [{0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x6F}, {0xFD}]]
    special_sections_len = [0xA, 0x1A2, 0xC5]
    success_values = {0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x6F}
    possible_indexes = {0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x6F}
    next_section = 0xFD
    no_input = 0xFE
    drop_bytes_checks = [[0xA, 0x19F, 0xC5], [next_section, next_section, no_input], [0,0,0]]
    stop_trade = 0x6F
    first_trade_index = 0x60
    decline_trade = 0x61
    accept_trade = 0x62
    
    def __init__(self, sending_func, receiving_func, connection, menu, kill_function):
        super(RBYTrading, self).__init__(sending_func, receiving_func, connection, menu, kill_function)
        
    def get_and_init_utils_class(self):
        RBYUtils()
        return RBYUtils
    
    def party_reader(self, data, data_mail=None, do_full=True):
        return RBYTradingData(data, data_mail=data_mail, do_full=do_full)
    
    def get_comms(self, connection, menu):
        return RBYTradingClient(self, connection, menu.verbose, self.stop_trade, self.party_reader)
    
    def get_checks(self, menu):
        return RBYChecks(self.special_sections_len, menu.do_sanity_checks)
            