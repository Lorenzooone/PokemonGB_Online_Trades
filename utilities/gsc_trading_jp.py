from .gsc_trading import GSCTrading

class GSCTradingJP(GSCTrading):
    """
    Class which handles the trading process for the player.
    """
    next_section = 0xFD
    no_input = 0xFE
    end_of_line = 0x50
    single_text_len = 0xB
    mail_sender_len = 0xE
    fillers = [{}, {
        6: [5, end_of_line],
        0x13B + (single_text_len * 0): [5, end_of_line],
        0x13B + (single_text_len * 1): [5, end_of_line],
        0x13B + (single_text_len * 2): [5, end_of_line],
        0x13B + (single_text_len * 3): [5, end_of_line],
        0x13B + (single_text_len * 4): [5, end_of_line],
        0x13B + (single_text_len * 5): [5, end_of_line],
        0x13B + (single_text_len * 6): [5, end_of_line],
        0x13B + (single_text_len * 7): [5, end_of_line],
        0x13B + (single_text_len * 8): [5, end_of_line],
        0x13B + (single_text_len * 9): [5, end_of_line],
        0x13B + (single_text_len * 10): [5, end_of_line],
        0x13B + (single_text_len * 11): [5, end_of_line]
    }, {
        0x19A + (mail_sender_len * 0): [5, end_of_line],
        0x19A + (mail_sender_len * 1): [5, end_of_line],
        0x19A + (mail_sender_len * 2): [5, end_of_line],
        0x19A + (mail_sender_len * 3): [5, end_of_line],
        0x19A + (mail_sender_len * 4): [5, end_of_line],
        0x19A + (mail_sender_len * 5): [5, end_of_line],
        0x205: [0x46, 0]
    }]
    drop_bytes_checks = [[0xA, 0x1B9, 0x1E6], [next_section, next_section, no_input], [0,4,0]]
    
    def __init__(self, sending_func, receiving_func, connection, menu, kill_function):
        super(GSCTradingJP, self).__init__(sending_func, receiving_func, connection, menu, kill_function)
            