import math
class GSCUtils:
    def read_data(target):
        data = None
        try:
            with open(target, 'rb') as newFile:
                tmpdata = list(newFile.read())
                data = tmpdata
        except FileNotFoundError as e:
            pass
        return data
    
    def read_short(data, pos):
        return ((data[pos] << 8) + (data[pos+1]))
    
    def write_short(data, pos, short_data):
        data[pos] = (short_data >> 8) & 0xFF
        data[pos+1] = short_data & 0xFF
    
    def copy_to_data(data, pos, values):
        data[pos:pos+len(values)] = values[:len(values)]
    
    def prepare_dict(target):
        lines = GSCUtils.read_text_file(target)
        dict = {}
        for i in lines:
            dict[i.split()[0]] = int(i.split()[1])
        return dict
    
    def read_text_file(target):
        try:
            with open(target,"r", encoding="utf-8") as f:
                lines=f.readlines()
        except FileNotFoundError as e:
            return []
        return lines
    
class GSCTradingText:
    def __init__(self, data, start, length=0xB, data_start=0):
        self.values = data[start:start+length]
        self.start_at = data_start
    
class GSCTradingPartyInfo:
    gsc_max_party_mons = 6
    
    def __init__(self, data, start):
        self.total = data[start]
        if self.total <= 0 or self.total > 6:
            self.total = 1
        self.actual_mons = data[start + 1:start + 1 + self.gsc_max_party_mons]
    
    def get_indexed_id(self, pos):
        if pos > self.total or pos > self.gsc_max_party_mons:
            return None
        return self.actual_mons[pos-1]
    
    def get_total(self):
        return self.total

class GSCTradingPokémonInfo:
    def __init__(self, data, start, length=0x30):
        self.values = data[start:start+length]
        self.mail = None
        self.mail_sender = None

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
        return GSCUtils.read_short(self.values, 0x22)
    
    def get_max_hp(self):
        return GSCUtils.read_short(self.values, 0x24)

class GSCTradingData:
    gsc_trader_name_pos = 0
    gsc_trading_party_info_pos = 0xB
    gsc_trader_info_pos = 0x13
    gsc_trading_pokemon_pos = 0x15
    gsc_trading_pokemon_ot_pos = 0x135
    gsc_trading_pokemon_nickname_pos = 0x177
    gsc_trading_pokemon_mail_pos = 0xCB
    gsc_trading_pokemon_mail_sender_pos = 0x191
    
    gsc_trading_pokemon_length = 0x30
    gsc_trading_name_length = 0xB
    gsc_trading_mail_length = 0x21
    gsc_trading_mail_sender_length = 0xE
    
    def __init__(self, checks, data_pokemon, data_mail=None):
        self.checks = checks
        self.trader = GSCTradingText(data_pokemon, self.gsc_trader_name_pos)
        self.party_info = GSCTradingPartyInfo(data_pokemon, self.gsc_trading_party_info_pos)
        self.trader_info = GSCUtils.read_short(data_pokemon, self.gsc_trader_info_pos)
        self.pokemon = []
        for i in range(self.party_info.get_total()):
            self.pokemon += [GSCTradingPokémonInfo(data_pokemon, self.gsc_trading_pokemon_pos + i * self.gsc_trading_pokemon_length)]
            self.pokemon[i].add_ot_name(data_pokemon, self.gsc_trading_pokemon_ot_pos + i * self.gsc_trading_name_length)
            self.pokemon[i].add_nickname(data_pokemon, self.gsc_trading_pokemon_nickname_pos + i * self.gsc_trading_name_length)
            if data_mail is not None and self.mon_has_mail(i):
                self.pokemon[i].add_mail(data_mail, self.gsc_trading_pokemon_mail_pos + i * self.gsc_trading_mail_length)
                self.pokemon[i].add_mail_sender(data_mail, self.gsc_trading_pokemon_mail_sender_pos + i * self.gsc_trading_mail_sender_length)

    def check_pos_validity(func):
        def wrapper(*args, **kwargs):
            self = args[0]
            pos = args[1]
            if pos < 0 or pos >= self.party_info.get_total():
                print("Index error!")
                return False
            return func(*args, **kwargs)
        return wrapper

    @check_pos_validity
    def mon_has_mail(self, pos):
        return self.checks.is_item_mail(self.pokemon[pos].get_item())

    def party_has_mail(self):
        mail_owned = False
        for i in range(self.party_info.get_total()):
            mail_owned |= self.mon_has_mail(i)
        return mail_owned
        
    def mon_evolves(self):
        return self.checks.is_evolving(self.pokemon[self.party_info.get_total()-1].get_species(), self.pokemon[self.party_info.get_total()-1].get_item())
    
    def trade_mon(self, other, own_index, other_index):
        self.reorder_party(own_index)
        other.reorder_party(other_index)
        own = self.pokemon[self.party_info.get_total()-1]
        self.pokemon[self.party_info.get_total()-1] = other.pokemon[other.party_info.get_total()-1]
        other.pokemon[other.party_info.get_total()-1] = own
        self.party_info.actual_mons[self.party_info.get_total()-1] = self.pokemon[self.party_info.get_total()-1].get_species()
        other.party_info.actual_mons[other.party_info.get_total()-1] = other.pokemon[other.party_info.get_total()-1].get_species()
    
    @check_pos_validity
    def reorder_party(self, traded_pos):
        pa_info = self.party_info.actual_mons[traded_pos]
        po_data = self.pokemon[traded_pos]
        for i in range(traded_pos+1,self.party_info.get_total()):
            self.party_info.actual_mons[i-1] = self.party_info.actual_mons[i]
            self.pokemon[i-1] = self.pokemon[i]
        self.party_info.actual_mons[self.party_info.get_total()-1] = pa_info
        self.pokemon[self.party_info.get_total()-1] = po_data

    def create_trading_data(self, lengths):
        data = []
        for i in range(2):
            data += [lengths[i]*[0]]
        data += [self.checks.no_mail_section[:len(self.checks.no_mail_section)]]
        GSCUtils.copy_to_data(data[1], self.gsc_trader_name_pos, self.trader.values)
        data[1][self.gsc_trading_party_info_pos] = self.party_info.get_total()
        GSCUtils.copy_to_data(data[1], self.gsc_trading_party_info_pos + 1, self.party_info.actual_mons)
        data[1][0x12] = 0xFF
        GSCUtils.write_short(data[1], self.gsc_trader_info_pos, self.trader_info)
        for i in range(self.party_info.get_total()):
            GSCUtils.copy_to_data(data[1], self.gsc_trading_pokemon_pos + (i * self.gsc_trading_pokemon_length), self.pokemon[i].values)
            GSCUtils.copy_to_data(data[1], self.gsc_trading_pokemon_ot_pos + (i * self.gsc_trading_name_length), self.pokemon[i].ot_name.values)
            GSCUtils.copy_to_data(data[1], self.gsc_trading_pokemon_nickname_pos + (i * self.gsc_trading_name_length), self.pokemon[i].nickname.values)
            if self.pokemon[i].mail is not None:
                GSCUtils.copy_to_data(data[2], self.gsc_trading_pokemon_mail_pos + (i * self.gsc_trading_mail_length), self.pokemon[i].mail.values)
                GSCUtils.copy_to_data(data[2], self.gsc_trading_pokemon_mail_sender_pos + (i * self.gsc_trading_mail_sender_length), self.pokemon[i].mail_sender.values)
        return data
    
class GSCChecks:
    bad_ids_items_path = "useful_data/bad_ids_items.bin"
    bad_ids_moves_path = "useful_data/bad_ids_moves.bin"
    bad_ids_pokemon_path = "useful_data/bad_ids_pokemon.bin"
    bad_ids_text_path = "useful_data/bad_ids_text.bin"
    evolution_ids_path = "useful_data/evolution_ids.bin"
    mail_ids_path = "useful_data/ids_mail.bin"
    checks_map_path = "useful_data/checks_map.bin"
    no_mail_path = "useful_data/no_mail_section.bin"
    base_stats_path = "useful_data/stats_gsc.bin"
    text_conv_path = "useful_data/text_conv.txt"
    pokemon_names_gs_path = "useful_data/pokemon_names_gs.txt"
    end_of_line = 0x50
    name_size = 0xB
    everstone_id = 0x70
    hp_stat_id = 0
    stat_id_base_conv_table = [0,1,2,5,3,4]
    stat_id_iv_conv_table = [0,0,1,2,3,3]
    stat_id_exp_conv_table = [0,1,2,3,4,4]
    spdef_stat_id = 5
    
    def __init__(self, section_sizes):
        self.do_sanity_checks = True
        self.bad_ids_items = self.prepare_check_list(GSCUtils.read_data(self.bad_ids_items_path))
        self.bad_ids_moves = self.prepare_check_list(GSCUtils.read_data(self.bad_ids_moves_path))
        self.bad_ids_pokemon = self.prepare_check_list(GSCUtils.read_data(self.bad_ids_pokemon_path))
        self.bad_ids_text = self.prepare_check_list(GSCUtils.read_data(self.bad_ids_text_path))
        self.mail_ids = self.prepare_check_list(GSCUtils.read_data(self.mail_ids_path))
        self.evolution_ids = self.prepare_evolution_check_list(GSCUtils.read_data(self.evolution_ids_path))
        self.check_functions = [self.clean_nothing, self.clean_text, self.clean_team_size, self.clean_species, self.clean_move, self.clean_item, self.clean_level, self.check_hp, self.clean_text_final, self.load_stat_exp, self.load_stat_iv, self.check_stat, self.clean_species_sp]
        self.checks_map = self.prepare_checks_map(GSCUtils.read_data(self.checks_map_path), section_sizes)
        self.no_mail_section = GSCUtils.read_data(self.no_mail_path)
        self.base_stats = self.prepare_stats(GSCUtils.read_data(self.base_stats_path))
        self.pokemon_names_gs = self.text_to_bytes(self.pokemon_names_gs_path, self.text_conv_path)
    
    def clean_check_sanity_checks(func):
        def wrapper(*args, **kwargs):
            self = args[0]
            val = args[1]
            if self.do_sanity_checks:
                return func(*args, **kwargs)
            else:
                return val
        return wrapper

    def text_to_bytes(self, target, text_conv_target):
        names = GSCUtils.read_text_file(target)
        text_conv_dict = GSCUtils.prepare_dict(text_conv_target)
        text_conv_dict['\n'] = self.end_of_line
        byte_names = []
        for i in range(0x100):
            byte_names += [[self.end_of_line]*self.name_size]
            for j in range(len(names[i])):
                letter = names[i][j].upper()
                if letter in text_conv_dict:
                    byte_names[i][j] = text_conv_dict[letter]
                else:
                    print("UNRECOGNIZED CHARACTER: " + letter)
        return byte_names

    def prepare_stats(self, data):
        ret = [0] * 0x100
        for i in range(0x100):
            ret[i] = data[(i)*6:(i+1)*6]
        return ret
    
    def set_sanity_checks(self, new_val):
        self.do_sanity_checks = new_val
    
    def prepare_text_buffer(self):
        self.curr_text = []
        
    def prepare_species_buffer(self):
        self.curr_species_pos = 0

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
    
    @clean_check_sanity_checks
    def clean_nothing(self, val):
        return val
    
    @clean_check_sanity_checks
    def clean_level(self, level):
        self.level = self.clean_value(level, self.is_level_valid, 100)
        return self.level
    
    @clean_check_sanity_checks
    def clean_team_size(self, team_size):
        self.team_size = self.clean_value(team_size, self.is_team_size_valid, 1)
        return self.team_size
    
    @clean_check_sanity_checks
    def clean_item(self, item):
        return self.clean_value(item, self.is_item_valid, 0)
    
    @clean_check_sanity_checks
    def clean_move(self, move):
        return self.clean_value(move, self.is_move_valid, 0x21)
    
    @clean_check_sanity_checks
    def clean_species(self, species):
        self.curr_species = self.clean_value(species, self.is_species_valid, 0x13)
        self.curr_stat_id = 1
        self.iv = [0,0,0,0]
        self.stat_exp = [0,0,0,0,0]
        self.curr_pos = 0
        self.curr_iv_pos = 0
        self.curr_exp_id = 0
        self.curr_exp_pos = 0
        return self.curr_species
    
    @clean_check_sanity_checks
    def clean_species_sp(self, species):
        if species == 0xFF and self.curr_species_pos >= self.team_size:
            self.curr_species_pos += 1
            return species
        found_species = self.clean_value(species, self.is_species_valid, 0x13)
        self.curr_species_pos += 1
        return found_species
    
    @clean_check_sanity_checks
    def load_stat_exp(self, val):
        calc_val = val << (8 * self.curr_exp_pos)
        if self.curr_exp_pos == 0:
            self.stat_exp[self.curr_exp_id] = calc_val
            self.curr_exp_pos += 1
        else:
            self.stat_exp[self.curr_exp_id] |= calc_val
            self.curr_exp_pos = 0
            self.curr_exp_id += 1
        return val
    
    @clean_check_sanity_checks
    def load_stat_iv(self, val):
        calc_val = [(val&0xF0) >> 4, val & 0xF]
        self.iv[self.curr_iv_pos*2] = calc_val[0]
        self.iv[(self.curr_iv_pos*2) + 1] = calc_val[1]
        self.curr_iv_pos += 1
        return val
    
    @clean_check_sanity_checks
    def clean_text(self, char):
        char_val = self.clean_value(char, self.is_char_valid, 0xE6)
        self.curr_text += [char_val]
        # Possibility to put bad words filters here
        return char_val
    
    @clean_check_sanity_checks
    def clean_text_final(self, char):
        char_val = self.clean_value(char, self.is_char_valid, 0xE6)
        self.curr_text += [char_val]
        # Possibility to put bad words filters here
        self.prepare_text_buffer()
        return char_val
    
    def final_stat_calc_step(self, stat_id):
        if stat_id != self.hp_stat_id:
            return 5
        return self.level + 10
    
    def get_iv(self, stat_id):
        if stat_id != self.hp_stat_id:
            return self.iv[self.stat_id_iv_conv_table[stat_id]]
        return ((self.iv[0]&1)<<3) | ((self.iv[1]&1)<<2) | ((self.iv[2]&1)<<1) | (self.iv[3]&1)
    
    def get_exp(self, stat_id):
        return self.stat_exp[self.stat_id_exp_conv_table[stat_id]]
    
    def get_base_stat(self, stat_id):
        return self.base_stats[self.curr_species][self.stat_id_base_conv_table[stat_id]]
    
    def stat_calculation(self, stat_id, do_exp=True):
        inter_value = (self.get_base_stat(stat_id) + self.get_iv(stat_id)) * 2
        if do_exp:
            inter_value += math.floor(math.ceil(math.sqrt(self.get_exp(stat_id))/4))
        inter_value = math.floor((inter_value*self.level)/100)
        return inter_value + self.final_stat_calc_step(stat_id)
    
    def check_stat_range(self, stat_range, curr_stat, pos):
        if curr_stat > stat_range[1]:
            curr_stat = stat_range[1]
        if curr_stat < stat_range[0]:
            curr_stat = stat_range[0]
        return curr_stat
    
    @clean_check_sanity_checks
    def check_stat(self, val):
        if self.curr_pos == 0:
            self.stat = 0
            self.stat_range = [self.stat_calculation(self.curr_stat_id, do_exp=False), self.stat_calculation(self.curr_stat_id)]
        curr_read_val = val << (8 * (1 - (self.curr_pos & 1)))
        self.stat = self.check_stat_range(self.stat_range, (self.stat & 0xFF00) | curr_read_val, self.curr_pos)
        val = (self.stat >> (8 * (1 - (self.curr_pos & 1)))) & 0xFF
        self.curr_pos += 1
        if self.curr_pos >= 2:
            self.curr_stat_id += 1
            self.curr_pos = 0
        return val
    
    @clean_check_sanity_checks
    def check_hp(self, val):
        if self.curr_pos == 0:
            self.hps = [0,0]
            self.hps_range = [self.stat_calculation(self.hp_stat_id, do_exp=False), self.stat_calculation(self.hp_stat_id)]
        curr_read_val = val << (8 * (1 - (self.curr_pos & 1)))
        self.hps[self.curr_pos >> 1] = self.check_stat_range(self.hps_range, (self.hps[self.curr_pos >> 1] & 0xFF00) | curr_read_val, self.curr_pos)
        val = (self.hps[self.curr_pos >> 1] >> (8 * (1 - (self.curr_pos & 1)))) & 0xFF
        self.curr_pos += 1
        if self.curr_pos >= 4:
            if self.hps[1] < self.hps[0]:
                # Possibility to put a warning for bad stats here
                pass
            self.curr_pos = 0
        return val
    
    def clean_value(self, value, checker, default_value):
        if checker(value):
            return value
        return default_value
        
    def is_level_valid(self, level):
        if self.do_sanity_checks and level <= 1 or level > 100:
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