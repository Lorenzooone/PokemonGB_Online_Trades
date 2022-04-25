from .rby_trading import RBYTrading

class RBYTradingJP(RBYTrading):
    """
    Class which handles the trading process for the player.
    """
    next_section = 0xFD
    no_input = 0xFE
    end_of_line = 0x50
    single_text_len = 0xB
    fillers = {
        6: [5, end_of_line, 1],
        0x121 + (single_text_len * 0): [5, end_of_line, 1],
        0x121 + (single_text_len * 1): [5, end_of_line, 1],
        0x121 + (single_text_len * 2): [5, end_of_line, 1],
        0x121 + (single_text_len * 3): [5, end_of_line, 1],
        0x121 + (single_text_len * 4): [5, end_of_line, 1],
        0x121 + (single_text_len * 5): [5, end_of_line, 1],
        0x121 + (single_text_len * 6): [5, end_of_line, 1],
        0x121 + (single_text_len * 7): [5, end_of_line, 1],
        0x121 + (single_text_len * 8): [5, end_of_line, 1],
        0x121 + (single_text_len * 9): [5, end_of_line, 1],
        0x121 + (single_text_len * 10): [5, end_of_line, 1],
        0x121 + (single_text_len * 11): [5, end_of_line, 1],
    }
    drop_bytes_checks = [[0xA, 0x19F, 0xC5], [next_section, next_section, no_input], [0,0,0]]
    
    def __init__(self, sending_func, receiving_func, connection, menu, kill_function):
        super(RBYTradingJP, self).__init__(sending_func, receiving_func, connection, menu, kill_function)
            