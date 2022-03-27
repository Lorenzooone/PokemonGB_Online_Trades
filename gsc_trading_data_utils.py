class GSCTradingText:
    def __init__(self, data, start, length=0xB, data_start=0):
        self.values = data[start:start+length]
        self.start_at = data_start
        
class GSCTradingPartyInfo:
    gsc_max_party_mons = 6
    
    def __init__(self, data, start):
        self.total = data[start]
        self.actual_mons = data[start + 1:start + 1 + self.gsc_max_party_mons]
    
    def get_indexed_id(self, pos):
        if pos > self.total or pos > self.gsc_max_party_mons:
            return None
        return self.actual_mons[pos-1]

class GSCTradingPokémonInfo:
    def __init__(self, data, start, length=0x30):
        self.values = data[start:start+length]

    def add_ot_name(self, data, start):
        self.ot_name = GSCTradingText(data, start)

    def add_nickname(self, data, start):
        self.nickname = GSCTradingText(data, start)

    def add_mail(self, data, start):
        self.mail = GSCTradingText(data, start, length=0x21)
        
    def add_mail_sender(self, data, start):
        self.mail_sender = GSCTradingText(data, start, length=0xE, data_start=4)
    
    def get_species(self):
        return self.values[0]
        
    def get_item(self):
        return self.values[1]
    
    def get_move(self, pos):
        return self.values[2 + (pos-1)]
    
    def get_level(self):
        return self.values[0x1F]
    
    def get_curr_hp(self):
        return ((self.values[0x22] << 8) + (self.values[0x23]))
    
    def get_max_hp(self):
        return ((self.values[0x24] << 8) + (self.values[0x25]))

class GSCTradingData:
    gsc_trader_name_pos = 0
    gsc_trading_party_info_pos = 0xB
    gsc_trading_pokemon_pos = 0x15
    gsc_trading_pokemon_ot_pos = 0x135
    gsc_trading_pokemon_nickname_pos = 0x167
    gsc_trading_pokemon_mail_pos = 0xCB
    gsc_trading_pokemon_mail_sender_pos = 0x191
    
    gsc_trading_pokemon_length = 0x30
    gsc_trading_name_length = 0xB
    gsc_trading_mail_length = 0x21
    gsc_trading_mail_sender_length = 0xE
    
    def __init__(self, data_pokemon, data_mail):
        self.trader = GSCTradingText(data_pokemon, self.gsc_trader_name_pos)
        self.party_info = GSCTradingPartyInfo(data_pokemon, self.gsc_trading_party_info_pos)
        self.pokemon = []
        for i in range(6):
            self.pokemon += [GSCTradingPokémonInfo(data_pokemon, self.gsc_trading_pokemon_pos + i * self.gsc_trading_pokemon_length)]
            self.pokemon[i].add_ot_name(data_pokemon, self.gsc_trading_pokemon_ot_pos + i * self.gsc_trading_name_length)
            self.pokemon[i].add_nickname(data_pokemon, self.gsc_trading_pokemon_nickname_pos + i * self.gsc_trading_name_length)
            self.pokemon[i].add_mail(data_mail, self.gsc_trading_pokemon_mail_pos + i * self.gsc_trading_mail_length)
            self.pokemon[i].add_mail_sender(data_mail, self.gsc_trading_pokemon_mail_sender_pos + i * self.gsc_trading_mail_sender_length)

class GSCChecks:
    bad_ids_items_path = "useful_data/bad_ids_items.bin"
    bad_ids_moves_path = "useful_data/bad_ids_moves.bin"
    bad_ids_pokemon_path = "useful_data/bad_ids_pokemon.bin"
    bad_ids_text_path = "useful_data/bad_ids_text.bin"
    evolution_ids_path = "useful_data/evolution_ids.bin"
    mail_ids_path = "useful_data/ids_mail.bin"
    checks_map_path = "useful_data/checks_map.bin"
    everstone_id = 0x70
    
    def __init__(self, section_sizes):
        self.do_sanity_checks = True
        self.bad_ids_items = self.prepare_check_list(self.read_data(self.bad_ids_items_path))
        self.bad_ids_moves = self.prepare_check_list(self.read_data(self.bad_ids_moves_path))
        self.bad_ids_pokemon = self.prepare_check_list(self.read_data(self.bad_ids_pokemon_path))
        self.bad_ids_text = self.prepare_check_list(self.read_data(self.bad_ids_text_path))
        self.mail_ids = self.prepare_check_list(self.read_data(self.mail_ids_path))
        self.evolution_ids = self.prepare_evolution_check_list(self.read_data(self.evolution_ids_path))
        self.check_functions = [self.clean_nothing, self.clean_text, self.clean_team_size, self.clean_species, self.clean_move, self.clean_item, self.clean_level, self.check_hp, self.clean_text_final]
        self.checks_map = self.prepare_checks_map(self.read_data(self.checks_map_path), section_sizes)
    
    def set_sanity_checks(self, new_val):
        self.do_sanity_checks = new_val
    
    def prepare_text_buffer(self):
        self.curr_text = []
        
    def prepare_hp_buffers(self):
        self.curr_pos = 0

    def prepare_check_list(self, data):
        ret = [False] * 0x100
        if data is not None:
            for i in data:
                ret[i] = True
        return ret

    def prepare_checks_map(self, data, lengths):
        raw_data_sections = [data[0:lengths[0]], data[lengths[0]:lengths[0]+lengths[1]], data[lengths[0]+lengths[1]:lengths[0]+lengths[1]+lengths[2]]]
        call_map = [[],[],[]]
        for i in range(3):
            for j in range(lengths[i]):
                call_map[i] += [self.check_functions[raw_data_sections[i][j]]]
        return call_map
    
    def prepare_evolution_check_list(self, data):
        ret = [(False, None)] * 0x100
        
        if data is not None:
            data_len = int(len(data)/2)
            for i in range(data_len):
                ret[data[i]] = (True, None)
                if data[i + data_len] != 0:
                    ret[data[i]] = (True, data[i + data_len])
        return ret
        
    def check_normal_list(self, checking_list, value):
        if value >= 0x100 or value < 0:
            return False
        return checking_list[value]
    
    def clean_nothing(self, val):
        return val
    
    def clean_level(self, level):
        return self.clean_value(level, self.is_level_valid, 100)
    
    def clean_team_size(self, team_size):
        return self.clean_value(team_size, self.is_team_size_valid, 1)
    
    def clean_item(self, item):
        return self.clean_value(item, self.is_item_valid, 0)
    
    def clean_move(self, move):
        return self.clean_value(move, self.is_move_valid, 0x21)
    
    def clean_species(self, species):
        return self.clean_value(species, self.is_species_valid, 0x13)
    
    def clean_text(self, char):
        char_val = self.clean_value(char, self.is_char_valid, 0xE6)
        self.curr_text += [char_val]
        # Possibility to put bad words filters here
        return char_val
    
    def clean_text_final(self, char):
        char_val = self.clean_value(char, self.is_char_valid, 0xE6)
        self.curr_text += [char_val]
        # Possibility to put bad words filters here
        self.prepare_text_buffer()
        return char_val
    
    def check_hp(self, val):
        if self.curr_pos == 0:
            self.hps = [0,0]
        curr_read_val = val << (8 * (self.curr_pos & 2))
        self.hps[self.curr_pos >> 1] |= curr_read_val
        self.curr_pos += 1
        if self.curr_pos >= 4:
            if self.hps[1] < self.hps[0]:
                # Possibility to put a warning for bad stats here
                pass
            self.prepare_hp_buffers()
        return val
    
    def clean_value(self, value, checker, default_value):
        if checker(value):
            return value
        return default_value
        
    def is_level_valid(self, level):
        if self.do_sanity_checks and level <= 0 or level > 100:
            return False
        return True
    
    def is_team_size_valid(self, team_size):
        if self.do_sanity_checks and team_size <= 0 or team_size > 6:
            return False
        return True
    
    def is_item_valid(self, item):
        if not self.do_sanity_checks:
            return True
        return not self.check_normal_list(self.bad_ids_items, item)
    
    def is_move_valid(self, move):
        if not self.do_sanity_checks:
            return True
        return not self.check_normal_list(self.bad_ids_moves, move)
    
    def is_species_valid(self, species):
        if not self.do_sanity_checks:
            return True
        return not self.check_normal_list(self.bad_ids_pokemon, species)
    
    def is_char_valid(self, char):
        if not self.do_sanity_checks:
            return True
        return not self.check_normal_list(self.bad_ids_text, char)
    
    def is_item_mail(self, item):
        return self.check_normal_list(self.mail_ids, item)
    
    def is_evolving(self, species, item):
        if species >= 0x100 or species < 0:
            return False
        evo_info = self.evolution_ids[species]
        if evo_info[0]:
            if item != self.everstone_id:
                if (evo_info[1] is None) or (item == evo_info[1]):
                    return True
        return False

    def read_data(self, target):
        data = None
        try:
            with open(target, 'rb') as newFile:
                tmpdata = list(newFile.read())
                data = tmpdata
        except FileNotFoundError as e:
            pass
        return data