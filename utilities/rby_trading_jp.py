from .rby_trading import RBYTrading

class RBYTradingJP(RBYTrading):
    """
    Class which handles the trading process for the player.
    """
    end_of_line = 0x50
    single_text_len = 0xB
    fillers = [{}, {
        6: [5, end_of_line],
        0x121 + (single_text_len * 0): [5, end_of_line],
        0x121 + (single_text_len * 1): [5, end_of_line],
        0x121 + (single_text_len * 2): [5, end_of_line],
        0x121 + (single_text_len * 3): [5, end_of_line],
        0x121 + (single_text_len * 4): [5, end_of_line],
        0x121 + (single_text_len * 5): [5, end_of_line],
        0x121 + (single_text_len * 6): [5, end_of_line],
        0x121 + (single_text_len * 7): [5, end_of_line],
        0x121 + (single_text_len * 8): [5, end_of_line],
        0x121 + (single_text_len * 9): [5, end_of_line],
        0x121 + (single_text_len * 10): [5, end_of_line],
        0x121 + (single_text_len * 11): [5, end_of_line]
    }, {}]
    
    def __init__(self, sending_func, receiving_func, connection, menu, kill_function, pre_sleep):
        super(RBYTradingJP, self).__init__(sending_func, receiving_func, connection, menu, kill_function, pre_sleep)
            