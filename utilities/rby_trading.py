from .gsc_trading import GSCTradingClient, GSCTrading
from .rby_trading_data_utils import RBYUtils

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
    
    def __init__(self, trader, connection, verbose, stop_trade, party_reader, base_no_trade = base_folder + "base.bin", base_pool = base_folder + "base_pool.bin"):
        super(RBYTradingClient, self).__init__(trader, connection, verbose, stop_trade, party_reader, base_no_trade=base_no_trade, base_pool=base_pool)
        
    def get_utils_class(self):
        return RBYUtils

class RBYTrading(GSCTrading):
    """
    Class which handles the trading process for the player.
    """
    
    enter_room_states = [[0x01, 0x60, 0xD4, 0xFE], [{0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x6F}, {0xD0, 0xD1, 0xD2, 0xD3, 0xD4}, {0xFE}, {0xFE}]]
    start_trading_states = [[0x60, 0x60, 0xFD], [{0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x6F}, {0}, {0xFD}]]
    special_sections_len = [0xA, 0x1A2, 0xC5]
    next_section = 0xFD
    no_input = 0xFE
    drop_bytes_checks = [[0xA, 0x19F, 0xC5], [next_section, next_section, no_input]]
    stop_trade = 0x6F
    first_trade_index = 0x60
    decline_trade = 0x61
    accept_trade = 0x62
    
    def __init__(self, sending_func, receiving_func, connection, menu, kill_function):
        super(RBYTrading, self).__init__(sending_func, receiving_func, connection, menu, kill_function)
        
    def get_and_init_utils_class(self):
        RBYUtils()
        return RBYUtils
    
    def get_comms(self, connection, menu):
        return RBYTradingClient(self, connection, menu.verbose, self.stop_trade, self.party_reader)
            