import math
class GSCUtils:
    evolution_ids_path = "useful_data/evolution_ids.bin"
    mail_ids_path = "useful_data/ids_mail.bin"
    no_mail_path = "useful_data/no_mail_section.bin"
    base_stats_path = "useful_data/stats_gsc.bin"
    text_conv_path = "useful_data/text_conv.txt"
    pokemon_names_gs_path = "useful_data/pokemon_names_gs.txt"
    moves_pp_list_path = "useful_data/moves_pp_list.bin"
    learnset_evos_path = "useful_data/learnset_evos.bin"
    everstone_id = 0x70
    end_of_line = 0x50
    name_size = 0xB
    hp_stat_id = 0
    stat_id_base_conv_table = [0,1,2,5,3,4]
    stat_id_iv_conv_table = [0,0,1,2,3,3]
    stat_id_exp_conv_table = [0,1,2,3,4,4]
    
    evolution_ids = None
    mail_ids = None
    base_stats = None
    pokemon_names_gs = None
    no_mail_section = None
    moves_pp_list = None
    learnsets = None
    
    def __init__(self):
        if GSCUtils.evolution_ids is None:
            GSCUtils.evolution_ids = GSCUtils.prepare_evolution_check_list(GSCUtils.read_data(GSCUtils.evolution_ids_path))
        if GSCUtils.mail_ids is None:
            GSCUtils.mail_ids = GSCUtils.prepare_check_list(GSCUtils.read_data(GSCUtils.mail_ids_path))
        if GSCUtils.no_mail_section is None:
            GSCUtils.no_mail_section = GSCUtils.read_data(GSCUtils.no_mail_path)
        if GSCUtils.base_stats is None:
            GSCUtils.base_stats = GSCUtils.prepare_stats(GSCUtils.read_data(GSCUtils.base_stats_path))
        if GSCUtils.pokemon_names_gs is None:
            GSCUtils.pokemon_names_gs = GSCUtils.text_to_bytes(GSCUtils.pokemon_names_gs_path, GSCUtils.text_conv_path)
        if GSCUtils.moves_pp_list is None:
            GSCUtils.moves_pp_list = GSCUtils.read_data(GSCUtils.moves_pp_list_path)
        if GSCUtils.learnsets is None:
            GSCUtils.learnsets = GSCUtils.prepare_learnsets(GSCUtils.read_data(GSCUtils.learnset_evos_path))
    
    def read_data(target):
        data = None
        try:
            with open(target, 'rb') as newFile:
                tmpdata = list(newFile.read())
                data = tmpdata
        except FileNotFoundError as e:
            pass
        return data
    
    def read_nybbles(val):
        return [(val&0xF0) >> 4, val & 0xF]
    
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
    
    def prepare_learnsets(data):
        dict = {}
        entries = data[0]
        for i in range(entries):
            pos = GSCUtils.read_short(data, 1 + (i * 2))
            entry = {}
            species = data[pos]
            levels = data[pos+1]
            pos += 2
            for j in range(levels):
                level = data[pos]
                num_moves = data[pos+1]
                moves_list = []
                pos += 2
                for k in range(num_moves):
                    moves_list += [data[pos]]
                    pos += 1
                entry[level] = moves_list
            dict[species] = entry
        return dict
    
    def final_stat_calc_step(stat_id, level):
        if stat_id != GSCUtils.hp_stat_id:
            return 5
        return level + 10
    
    def get_iv(iv, stat_id):
        if stat_id != GSCUtils.hp_stat_id:
            return iv[GSCUtils.stat_id_iv_conv_table[stat_id]]
        return ((iv[0]&1)<<3) | ((iv[1]&1)<<2) | ((iv[2]&1)<<1) | (iv[3]&1)
    
    def get_exp(stat_exp, stat_id):
        return stat_exp[GSCUtils.stat_id_exp_conv_table[stat_id]]
    
    def get_base_stat(species, stat_id):
        return GSCUtils.base_stats[species][GSCUtils.stat_id_base_conv_table[stat_id]]
    
    def stat_calculation(stat_id, species, ivs, stat_exp, level, do_exp=True):
        inter_value = (GSCUtils.get_base_stat(species, stat_id) + GSCUtils.get_iv(ivs, stat_id)) * 2
        if do_exp:
            inter_value += math.floor(math.ceil(math.sqrt(GSCUtils.get_exp(stat_exp, stat_id))/4))
        inter_value = math.floor((inter_value*level)/100)
        return inter_value + GSCUtils.final_stat_calc_step(stat_id, level)

    def text_to_bytes(target, text_conv_target):
        names = GSCUtils.read_text_file(target)
        text_conv_dict = GSCUtils.prepare_dict(text_conv_target)
        text_conv_dict['\n'] = GSCUtils.end_of_line
        byte_names = []
        for i in range(0x100):
            byte_names += [[GSCUtils.end_of_line]*GSCUtils.name_size]
            for j in range(len(names[i])):
                letter = names[i][j].upper()
                if letter in text_conv_dict:
                    byte_names[i][j] = text_conv_dict[letter]
                else:
                    print("UNRECOGNIZED CHARACTER: " + letter)
        return byte_names

    def prepare_check_list(data):
        ret = [False] * 0x100
        if data is not None:
            for i in data:
                ret[i] = True
        return ret
    
    def prepare_evolution_check_list(data):
        ret = [(False, None, None)] * 0x100
        
        if data is not None:
            data_len = int(len(data)/3)
            for i in range(data_len):
                ret[data[i]] = (True, None, data[i + (2*data_len)])
                if data[i + data_len] != 0:
                    ret[data[i]] = (True, data[i + data_len], data[i + (2*data_len)])
        return ret
        
    def check_normal_list(checking_list, value):
        if value >= 0x100 or value < 0:
            return False
        return checking_list[value]

    def prepare_stats(data):
        ret = [0] * 0x100
        for i in range(0x100):
            ret[i] = data[(i)*6:(i+1)*6]
        return ret
    
    def is_item_mail(item):
        return GSCUtils.check_normal_list(GSCUtils.mail_ids, item)
    
    def is_evolving(species, item):
        if species >= 0x100 or species < 0:
            return False
        evo_info = GSCUtils.evolution_ids[species]
        if evo_info[0]:
            if item != GSCUtils.everstone_id:
                if (evo_info[1] is None) or (item == evo_info[1]):
                    return True
        return False
    
    def get_evolution(species, item):
        if not GSCUtils.is_evolving(species, item):
            return None
        return GSCUtils.evolution_ids[species][2]
    
    def get_evolution_item(species):
        return GSCUtils.evolution_ids[species][1]
    
class GSCTradingText:
    def __init__(self, data, start, length=0xB, data_start=0):
        self.values = data[start:start+length]
        self.start_at = data_start
    
    def values_equal(self, other):
        for i in range(len(self.values)):
            if self.values[i] == GSCUtils.end_of_line and (i >= len(other) or other[i] == GSCUtils.end_of_line):
                return True
            if i >= len(other):
                return False
            if self.values[i] != other[i]:
                return False
        if len(other) == len(self.values) or other[len(self.values)] == GSCUtils.end_of_line:
            return True
        return False
    
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
    
    def is_nicknamed(self, default_name):
        return not self.nickname.values_equal(default_name)
    
    def get_species(self):
        return self.values[0]
    
    def learnable_moves(self):
        if self.get_species() in GSCUtils.learnsets.keys():
            if self.get_level() in GSCUtils.learnsets[self.get_species()].keys():
                return GSCUtils.learnsets[self.get_species()][self.get_level()]
        return None
    
    def set_species(self, data):
        self.values[0] = data & 0xFF
        
    def get_item(self):
        return self.values[1]
        
    def set_item(self, data=0):
        self.values[1] = data & 0xFF
    
    def has_move(self, move):
        for i in range(4):
            if self.get_move(i) == move:
                return True
        return False
    
    def free_move_slots(self):
        free_slots = []
        for i in range(4):
            if self.get_move(i) == GSCChecks.free_value_moves:
                free_slots += [i]
        return free_slots
    
    def get_move(self, pos):
        return self.values[2 + pos]
    
    def set_move(self, pos, val):
        self.values[2 + pos] = val
        self.set_pp(pos, GSCUtils.moves_pp_list[val])
    
    def set_pp(self, pos, val):
        self.values[0x17 + pos] = val
    
    def get_level(self):
        return self.values[0x1F]
    
    def update_stats(self):
        old_max_hps = self.get_max_hp()
        old_current_hps = self.get_curr_hp()
        for i in range(6):
            GSCUtils.write_short(self.values, 0x24 + (i * 2), stat_calculation(i, self.get_species(), self.get_ivs(), self.get_stat_exp(), self.get_level()))
        new_max_hps = self.get_max_hp()
        old_current_hps += new_max_hps-old_max_hps
        GSCUtils.write_short(self.values, 0x22, math.min(old_current_hps, new_max_hps))
        
    def get_stat_exp(self):
        ret = [0,0,0,0,0]
        for i in range(5):
            ret[i] = [GSCUtils.read_short(self.values, 0xB + (i * 2))]
        return ret

    def get_ivs(self):
        ret = [0,0,0,0]
        calc_val = [GSCUtils.read_nybbles(self.values[0x15]), GSCUtils.read_nybbles(self.values[0x16])]
        for i in range(4):
            ret[i] = calc_val[i/2][i&1]
        return ret

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
    
    def __init__(self, data_pokemon, data_mail=None):
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
        return GSCUtils.is_item_mail(self.pokemon[pos].get_item())

    def party_has_mail(self):
        mail_owned = False
        for i in range(self.party_info.get_total()):
            mail_owned |= self.mon_has_mail(i)
        return mail_owned
        
    @check_pos_validity
    def evolve_mon(self, pos):
        evolution = GSCUtils.get_evolution(self.pokemon[pos].get_species(), self.pokemon[pos].get_item())
        if evolution is None:
            return None
        evo_item = GSCUtils.get_evolution_item(self.pokemon[pos].get_species())
        if evo_item is not None:
            self.pokemon[pos].set_item()
        self.pokemon[pos].set_species(evolution)
        self.pokemon[pos].update_stats()
        curr_learning = self.pokemon[pos].learnable_moves()
        if curr_learning is not None:
            for i in range(len(curr_learning)):
                if not self.pokemon[pos].has_move(curr_learning[i]):
                    free_slots = self.pokemon[pos].free_move_slots()
                    if len(free_slots) > 0:
                        self.pokemon[pos].set_move(free_slots[0], curr_learning[i])
                    else:
                        return True
        return False
    
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
        data += [GSCUtils.no_mail_section[:len(GSCUtils.no_mail_section)]]
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
    checks_map_path = "useful_data/checks_map.bin"
    free_value_species = 0xFF
    free_value_moves = 0xFF
    
    def __init__(self, section_sizes):
        self.do_sanity_checks = True
        self.bad_ids_items = GSCUtils.prepare_check_list(GSCUtils.read_data(self.bad_ids_items_path))
        self.bad_ids_moves = GSCUtils.prepare_check_list(GSCUtils.read_data(self.bad_ids_moves_path))
        self.bad_ids_pokemon = GSCUtils.prepare_check_list(GSCUtils.read_data(self.bad_ids_pokemon_path))
        self.bad_ids_text = GSCUtils.prepare_check_list(GSCUtils.read_data(self.bad_ids_text_path))
        self.check_functions = [self.clean_nothing, self.clean_text, self.clean_team_size, self.clean_species, self.clean_move, self.clean_item, self.clean_level, self.check_hp, self.clean_text_final, self.load_stat_exp, self.load_stat_iv, self.check_stat, self.clean_species_sp, self.clean_pp]
        self.checks_map = self.prepare_checks_map(GSCUtils.read_data(self.checks_map_path), section_sizes)
    
    def clean_check_sanity_checks(func):
        def wrapper(*args, **kwargs):
            self = args[0]
            val = args[1]
            if self.do_sanity_checks:
                return func(*args, **kwargs)
            else:
                return val
        return wrapper
    
    def set_sanity_checks(self, new_val):
        self.do_sanity_checks = new_val
    
    def prepare_text_buffer(self):
        self.curr_text = []
        
    def prepare_species_buffer(self):
        self.curr_species_pos = 0

    def prepare_checks_map(self, data, lengths):
        raw_data_sections = [data[0:lengths[0]], data[lengths[0]:lengths[0]+lengths[1]], data[lengths[0]+lengths[1]:lengths[0]+lengths[1]+lengths[2]]]
        call_map = [[],[],[]]
        for i in range(3):
            for j in range(lengths[i]):
                call_map[i] += [self.check_functions[raw_data_sections[i][j]]]
        return call_map
    
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
    def clean_pp(self, pp):
        current_pp = pp & 0x3F
        pp_ups = (pp >> 6) & 3
        max_base_pp = GSCUtils.moves_pp_list[self.moves[self.curr_pp]]
        max_pp = max_base_pp + (math.floor(max_base_pp/5) * pp_ups)
        if max_pp > 61:
            max_pp = 61
        final_pp = pp
        if current_pp > max_pp:
            final_pp = (pp_ups << 6) | max_pp
        self.curr_pp += 1
        return final_pp
    
    @clean_check_sanity_checks
    def clean_move(self, move):
        if move == GSCChecks.free_value_moves and self.curr_move > 0:
            self.curr_move += 1
            return move
        final_move = self.clean_value(move, self.is_move_valid, 0x21)
        self.moves[self.curr_move] = final_move
        self.curr_move += 1
        return final_move
    
    @clean_check_sanity_checks
    def clean_species(self, species):
        self.curr_species = self.clean_value(species, self.is_species_valid, 0x13)
        self.curr_stat_id = 0
        self.iv = [0,0,0,0]
        self.stat_exp = [0,0,0,0,0]
        self.moves = [0,0,0,0]
        self.curr_move = 0
        self.curr_pp = 0
        self.curr_hp = 0
        self.curr_pos = 0
        self.curr_iv_pos = 0
        self.curr_exp_id = 0
        self.curr_exp_pos = 0
        return self.curr_species
    
    @clean_check_sanity_checks
    def clean_species_sp(self, species):
        if species == GSCChecks.free_value_species and self.curr_species_pos >= self.team_size:
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
        calc_val = GSCUtils.read_nybbles(val)
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
            self.stat_range = [GSCUtils.stat_calculation(self.curr_stat_id, self.curr_species, self.iv, self.stat_exp, self.level, do_exp=False), GSCUtils.stat_calculation(self.curr_stat_id, self.curr_species, self.iv, self.stat_exp, self.level)]
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
        val = self.check_stat(val)
        if self.curr_pos == 0:
            if self.curr_hp == 0:
                self.hps = [0,0]
                self.curr_stat_id -= 1
            self.hps[self.curr_hp] = self.stat
            self.curr_hp += 1
            if self.curr_hp == 2:
                if self.hps[0] > self.hps[1]:
                    #Can put a warning for bad data
                    pass
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
        return not GSCUtils.check_normal_list(self.bad_ids_items, item)
    
    def is_move_valid(self, move):
        if not self.do_sanity_checks:
            return True
        return not GSCUtils.check_normal_list(self.bad_ids_moves, move)
    
    def is_species_valid(self, species):
        if not self.do_sanity_checks:
            return True
        return not GSCUtils.check_normal_list(self.bad_ids_pokemon, species)
    
    def is_char_valid(self, char):
        if not self.do_sanity_checks:
            return True
        return not GSCUtils.check_normal_list(self.bad_ids_text, char)
