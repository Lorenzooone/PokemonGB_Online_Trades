from .rby_trading import RBYTrading

class RBYTradingJP(RBYTrading):
    """
    Class which handles the trading process for the player.
    """
    end_of_line = 0x50
    single_text_len = 0xB
    end_of_player_name_pos = 6
    end_of_rby_data_pos = 0x121
    player_name_len_diff = 5
    pokemon_name_len_diff = 5
    fillers = [{}, {
        end_of_player_name_pos: [player_name_len_diff, end_of_line],
        end_of_rby_data_pos + (single_text_len * 0): [player_name_len_diff, end_of_line],
        end_of_rby_data_pos + (single_text_len * 1): [player_name_len_diff, end_of_line],
        end_of_rby_data_pos + (single_text_len * 2): [player_name_len_diff, end_of_line],
        end_of_rby_data_pos + (single_text_len * 3): [player_name_len_diff, end_of_line],
        end_of_rby_data_pos + (single_text_len * 4): [player_name_len_diff, end_of_line],
        end_of_rby_data_pos + (single_text_len * 5): [player_name_len_diff, end_of_line],
        end_of_rby_data_pos + (single_text_len * 6): [pokemon_name_len_diff, end_of_line],
        end_of_rby_data_pos + (single_text_len * 7): [pokemon_name_len_diff, end_of_line],
        end_of_rby_data_pos + (single_text_len * 8): [pokemon_name_len_diff, end_of_line],
        end_of_rby_data_pos + (single_text_len * 9): [pokemon_name_len_diff, end_of_line],
        end_of_rby_data_pos + (single_text_len * 10): [pokemon_name_len_diff, end_of_line],
        end_of_rby_data_pos + (single_text_len * 11): [pokemon_name_len_diff, end_of_line]
    }, {}]
    
    def __init__(self, sending_func, receiving_func, connection, menu, kill_function, pre_sleep):
        super(RBYTradingJP, self).__init__(sending_func, receiving_func, connection, menu, kill_function, pre_sleep)
            
