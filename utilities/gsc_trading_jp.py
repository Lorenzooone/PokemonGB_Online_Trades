from .gsc_trading import GSCTrading
from .gsc_trading_data_utils import GSCUtilsLoaders, GSCUtilsMisc

class GSCJPMailConverter:
    """
    Class which handles converting the GSC Japanese mail data
    to the international format.
    """
    base_folder = "useful_data/gsc/"
    table_to_jp_path = "mail_conversion_table_en_to_jp.bin"
    table_to_int_path = "mail_conversion_table_jp_to_en.bin"
    mail_jp_checks_path = "mail_checks_jp.bin"
    
    end_of_line = 0x50
    
    extra_distance_jp = 5
    extra_distance_int = 0xA
    full_mail_jp_len = 0x2A
    mail_len = 0x21
    sender_int_len = 0xE
    mail_pos_jp = [
        (0*full_mail_jp_len),
        (1*full_mail_jp_len),
        (2*full_mail_jp_len),
        (3*full_mail_jp_len),
        (4*full_mail_jp_len),
        (5*full_mail_jp_len)
    ]
    mail_pos_int = [
        (0*mail_len),
        (1*mail_len),
        (2*mail_len),
        (3*mail_len),
        (4*mail_len),
        (5*mail_len)
    ]
    sender_pos_jp = [
        0x21 + (0*full_mail_jp_len),
        0x21 + (1*full_mail_jp_len),
        0x21 + (2*full_mail_jp_len),
        0x21 + (3*full_mail_jp_len),
        0x21 + (4*full_mail_jp_len),
        0x21 + (5*full_mail_jp_len)
    ]
    sender_pos_int = [
        0xC6 + (0*sender_int_len),
        0xC6 + (1*sender_int_len),
        0xC6 + (2*sender_int_len),
        0xC6 + (3*sender_int_len),
        0xC6 + (4*sender_int_len),
        0xC6 + (5*sender_int_len)
    ]

    def __init__(self, checks):
        self.conversion_functions = [
            self.do_zero,
            self.mail_conversion,
            self.sender_conversion,
            self.extra_conversion,
            self.do_ff,
            self.do_20,
            self.start_mail_conversion,
            self.do_eol,
            self.start_sender_conversion
        ]
        self.mail_conversion_table_jp = GSCUtilsLoaders.prepare_functions_map(GSCUtilsMisc.read_data(self.get_path(self.table_to_jp_path)), self.conversion_functions)
        self.mail_conversion_table_int = GSCUtilsLoaders.prepare_functions_map(GSCUtilsMisc.read_data(self.get_path(self.table_to_int_path)), self.conversion_functions)
        self.mail_checker = GSCUtilsLoaders.prepare_functions_map(GSCUtilsMisc.read_data(self.get_path(self.mail_jp_checks_path)), checks.check_functions)
        
    def get_path(self, target):
        return self.base_folder + target
        
    def convert_to_jp(self, data):
        self.mail_converter_pos = self.mail_pos_int
        self.sender_converter_pos = self.sender_pos_int
        self.extra_distance = self.extra_distance_int
        return self.convert(data, self.mail_conversion_table_jp)
        
    def convert_to_int(self, data):
        self.mail_converter_pos = self.mail_pos_jp
        self.sender_converter_pos = self.sender_pos_jp
        self.extra_distance = self.extra_distance_jp
        return self.convert(data, self.mail_conversion_table_int)
        
    def convert(self, to_convert, converter):
        self.mail_conv_pos = -1
        self.sender_conv_pos = -1
        ret = [0] * len(converter)
        for i in range(len(converter)):
            ret[i] = converter[i](to_convert)
        return ret
    
    def do_zero(self, data):
        return 0
        
    def mail_conversion(self, data):
        self.single_mail_pos += 1
        return data[self.mail_converter_pos[self.mail_conv_pos] + self.single_mail_pos]
        
    def sender_conversion(self, data):
        self.single_sender_pos += 1
        return data[self.sender_converter_pos[self.sender_conv_pos] + self.single_sender_pos]
        
    def extra_conversion(self, data):
        self.extra_conversion_pos += 1
        return data[self.sender_converter_pos[self.sender_conv_pos] + self.extra_distance + self.extra_conversion_pos]
    
    def start_mail_conversion(self, data):
        self.mail_conv_pos += 1
        self.single_mail_pos = 0
        return data[self.mail_converter_pos[self.mail_conv_pos] + self.single_mail_pos]
    
    def start_sender_conversion(self, data):
        self.sender_conv_pos += 1
        self.single_sender_pos = 0
        self.extra_conversion_pos = -1
        return data[self.sender_converter_pos[self.sender_conv_pos] + self.single_sender_pos]
    
    def do_ff(self, data):
        return 0xFF
    
    def do_eol(self, data):
        return self.end_of_line
    
    def do_20(self, data):
        return 0x20

class GSCTradingJP(GSCTrading):
    """
    Class which handles the trading process for the player.
    """
    next_section = 0xFD
    mail_next_section = 0x20
    no_input = 0xFE
    end_of_line = 0x50
    single_text_len = 0xB
    mail_sender_len = 0xE
    end_of_player_name_pos = 6
    end_of_gsc_data_pos = 0x13B
    player_name_len_diff = 5
    pokemon_name_len_diff = 5
    fillers = [{}, {
        end_of_player_name_pos: [player_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 0): [player_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 1): [player_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 2): [player_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 3): [player_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 4): [player_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 5): [player_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 6): [pokemon_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 7): [pokemon_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 8): [pokemon_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 9): [pokemon_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 10): [pokemon_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 11): [pokemon_name_len_diff, end_of_line]
    }, {}, {}, {}]
    special_sections_starter = [next_section, next_section, next_section, mail_next_section, mail_next_section]
    special_sections_sync = [True, True, True, False, False]
    drop_bytes_checks = [[0xA, 0x1B9, 0xC5, 0x181, 0x11D], [next_section, next_section, mail_next_section, no_input, no_input], [0,4,0,0,0]]
    
    def __init__(self, sending_func, receiving_func, connection, menu, kill_function, pre_sleep):
        super(GSCTradingJP, self).__init__(sending_func, receiving_func, connection, menu, kill_function, pre_sleep)
        self.jp_mail_converter = GSCJPMailConverter(self.checks)

    def get_mail_section_id(self):
        return 4

    def get_printable_index(self, index):
        if index != self.get_mail_section_id():
            return index+1
        return index

    def get_section_length(self, index):
        if index != self.get_mail_section_id():
            return self.special_sections_len[index]
        return len(self.jp_mail_converter.mail_checker)

    def get_checker(self, index):
        if index != self.get_mail_section_id():
            return self.checks.checks_map[index]
        return self.jp_mail_converter.mail_checker

    def convert_mail_data(self, data, to_device):
        """
        Handles converting the mail data.
        """
        if data is not None:
            if to_device:
                self.utils_class.apply_patches(data, data, self.utils_class, is_mail=True)
                data = self.jp_mail_converter.convert_to_jp(data)
                self.utils_class.create_patches_data(data, data, self.utils_class, is_mail=True, is_japanese=True)
            else:
                self.utils_class.apply_patches(data, data, self.utils_class, is_mail=True, is_japanese=True)
                data = self.jp_mail_converter.convert_to_int(data)
                self.utils_class.create_patches_data(data, data, self.utils_class, is_mail=True)
        return data
