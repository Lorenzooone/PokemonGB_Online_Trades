import math

class GSCUtilsLoaders:

    def prepare_dict(target):
        lines = GSCUtilsLoaders.read_text_file(target)
        dict = {}
        for i in lines:
            dict[i.split()[0]] = int(i.split()[1])
        return dict

    def prepare_exp_lists(lines):
        exp_lists = [[], [], [], [], [], []]
        for i in range(GSCUtils.max_level):
            columns = lines[i].split()
            for j in range(6):
                exp_lists[j] += [int(columns[j])]
        return exp_lists
    
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
            pos = GSCUtilsMisc.read_short(data, 1 + (i * 2))
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

    def text_to_bytes(target, text_conv_target):
        names = GSCUtilsLoaders.read_text_file(target)
        text_conv_dict = GSCUtilsLoaders.prepare_dict(text_conv_target)
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

    def prepare_stats(data):
        ret = [0] * 0x100
        for i in range(0x100):
            ret[i] = data[(i)*6:(i+1)*6]
        return ret

    def load_trading_data(target, lengths):
        data = None
        try:
            with open(target, 'rb') as newFile:
                data = GSCUtilsMisc.divide_data(list(newFile.read(sum(lengths))), lengths)
        except FileNotFoundError as e:
            pass
        return data

class GSCUtils:
    evolution_ids_path = "useful_data/evolution_ids.bin"
    mail_ids_path = "useful_data/ids_mail.bin"
    no_mail_path = "useful_data/no_mail_section.bin"
    base_stats_path = "useful_data/stats_gsc.bin"
    text_conv_path = "useful_data/text_conv.txt"
    pokemon_names_gs_path = "useful_data/pokemon_names_gs.txt"
    moves_pp_list_path = "useful_data/moves_pp_list.bin"
    learnset_evos_path = "useful_data/learnset_evos.bin"
    exp_groups_path = "useful_data/pokemon_exp_groups_gs.bin"
    exp_lists_path = "useful_data/pokemon_exp_gs.txt"
    everstone_id = 0x70
    end_of_line = 0x50
    name_size = 0xB
    hp_stat_id = 0
    stat_id_base_conv_table = [0,1,2,5,3,4]
    stat_id_iv_conv_table = [0,0,1,2,3,3]
    stat_id_exp_conv_table = [0,1,2,3,4,4]
    min_level = 2
    max_level = 100
    
    evolution_ids = None
    mail_ids = None
    base_stats = None
    pokemon_names_gs = None
    no_mail_section = None
    moves_pp_list = None
    learnsets = None
    exp_groups = None
    exp_lists = None
    
    def __init__(self):
        if GSCUtils.evolution_ids is None:
            GSCUtils.evolution_ids = GSCUtilsLoaders.prepare_evolution_check_list(GSCUtilsMisc.read_data(GSCUtils.evolution_ids_path))
        if GSCUtils.mail_ids is None:
            GSCUtils.mail_ids = GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(GSCUtils.mail_ids_path))
        if GSCUtils.no_mail_section is None:
            GSCUtils.no_mail_section = GSCUtilsMisc.read_data(GSCUtils.no_mail_path)
        if GSCUtils.base_stats is None:
            GSCUtils.base_stats = GSCUtilsLoaders.prepare_stats(GSCUtilsMisc.read_data(GSCUtils.base_stats_path))
        if GSCUtils.pokemon_names_gs is None:
            GSCUtils.pokemon_names_gs = GSCUtilsLoaders.text_to_bytes(GSCUtils.pokemon_names_gs_path, GSCUtils.text_conv_path)
        if GSCUtils.moves_pp_list is None:
            GSCUtils.moves_pp_list = GSCUtilsMisc.read_data(GSCUtils.moves_pp_list_path)
        if GSCUtils.learnsets is None:
            GSCUtils.learnsets = GSCUtilsLoaders.prepare_learnsets(GSCUtilsMisc.read_data(GSCUtils.learnset_evos_path))
        if GSCUtils.exp_groups is None:
            GSCUtils.exp_groups = GSCUtilsMisc.read_data(GSCUtils.exp_groups_path)
        if GSCUtils.exp_lists is None:
            GSCUtils.exp_lists = GSCUtilsLoaders.prepare_exp_lists(GSCUtilsLoaders.read_text_file(GSCUtils.exp_lists_path))
    
    def get_level_exp(species, exp):
        start = GSCUtils.min_level
        end = GSCUtils.max_level
        if exp < GSCUtils.get_exp_level(species, start + 1):
            return start
        if exp >= GSCUtils.get_exp_level(species, end):
            return end
        end_search = False
        while not end_search:
            check_level = math.floor((start+end)/2)
            level_exp = GSCUtils.get_exp_level(species, check_level)
            next_level_exp = GSCUtils.get_exp_level(species, check_level + 1)
            if exp < level_exp:
                end = check_level
            elif exp > next_level_exp:
                start = check_level
            elif exp == next_level_exp:
                return check_level + 1
            else:
                return check_level
        return GSCUtils.max_level
    
    def get_exp_level(species, level):
        return GSCUtils.exp_lists[GSCUtils.exp_groups[species]][level-1]
    
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
    
    def is_item_mail(item):
        return GSCUtilsMisc.check_normal_list(GSCUtils.mail_ids, item)
    
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

class GSCUtilsMisc:

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
        
    def inc_byte(val):
        val += 1
        if val >= 256:
            val = 0
        return val
    
    def copy_to_data(data, pos, values):
        data[pos:pos+len(values)] = values[:len(values)]
        
    def check_normal_list(checking_list, value):
        if value >= 0x100 or value < 0:
            return False
        return checking_list[value]
    
    def divide_data(data, lengths):
        div_data = []
        total_lengths = GSCUtilsMisc.calc_divide_lengths(lengths)
        for i in range(len(lengths)):
            div_data += [data[total_lengths[i]:total_lengths[i+1]]]
        return div_data
    
    def calc_divide_lengths(lengths):
        total_lengths = []
        curr_len = 0
        for i in range(len(lengths)):
            total_lengths += [curr_len]
            curr_len += lengths[i]
        total_lengths += [curr_len]
        return total_lengths
        
    def default_if_none(data, default_data):
        if data is not None:
            return data
        return default_data
    
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
    
    def get_id(self, pos):
        if pos >= self.get_total() or pos >= self.gsc_max_party_mons:
            return None
        return self.actual_mons[pos]
    
    def set_id(self, pos, val):
        if pos < self.get_total() and pos < self.gsc_max_party_mons:
            self.actual_mons[pos] = val
    
    def get_total(self):
        return self.total

class GSCTradingPokémonInfo:
    pokemon_data_len = 0x30
    ot_name_len = 0xB
    nickname_len = 0xB
    mail_len = 0x21
    sender_len = 0xE
    _precalced_lengths = None
    
    no_moves_equality_ranges = [range(0,2), range(6,0x17), range(0x1B, pokemon_data_len)]
    no_moves_equality_weak_ranges = [range(0,2), range(6,0x17), range(0x1B, 0x20), range(0x24, pokemon_data_len)]
    all_lengths = [pokemon_data_len, ot_name_len, nickname_len, mail_len, sender_len]

    def __init__(self, data, start, length=pokemon_data_len):
        self.values = data[start:start+length]
        self.mail = None
        self.mail_sender = None
        if GSCTradingPokémonInfo._precalced_lengths is None:
            GSCTradingPokémonInfo._precalced_lengths = GSCUtilsMisc.calc_divide_lengths(GSCTradingPokémonInfo.all_lengths)

    def add_ot_name(self, data, start):
        self.ot_name = GSCTradingText(data, start, length=GSCTradingPokémonInfo.ot_name_len)

    def add_nickname(self, data, start):
        self.nickname = GSCTradingText(data, start, length=GSCTradingPokémonInfo.nickname_len)

    def add_mail(self, data, start):
        self.mail = GSCTradingText(data, start, length=GSCTradingPokémonInfo.mail_len)
        
    def add_mail_sender(self, data, start):
        self.mail_sender = GSCTradingText(data, start, length=GSCTradingPokémonInfo.sender_len, data_start=4)
    
    def is_nicknamed(self):
        return not self.nickname.values_equal(GSCUtils.pokemon_names_gs[self.get_species()])
    
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
    
    def has_move_index(self, move, start=0):
        for i in range(start,4):
            if self.get_move(i) == move:
                return i
        return 4
    
    def has_move(self, move):
        if self.has_move_index(move) == 4:
            return False
        return True
    
    def free_move_slots(self):
        free_slots = []
        for i in range(4):
            if self.get_move(i) == GSCChecks.free_value_moves:
                free_slots += [i]
        return free_slots
    
    def get_move(self, pos):
        return self.values[2 + pos]
    
    def set_move(self, pos, val, max_pp=True):
        self.values[2 + pos] = val
        if max_pp:
            self.set_pp(pos, GSCUtils.moves_pp_list[val])
    
    def set_pp(self, pos, val):
        self.values[0x17 + pos] = val
    
    def get_pp(self, pos):
        return self.values[0x17 + pos]
    
    def get_level(self):
        return self.values[0x1F]
    
    def update_stats(self):
        old_max_hps = self.get_max_hp()
        old_current_hps = self.get_curr_hp()
        for i in range(6):
            GSCUtilsMisc.write_short(self.values, 0x24 + (i * 2), GSCUtils.stat_calculation(i, self.get_species(), self.get_ivs(), self.get_stat_exp(), self.get_level()))
        new_max_hps = self.get_max_hp()
        old_current_hps += new_max_hps-old_max_hps
        GSCUtilsMisc.write_short(self.values, 0x22, min(old_current_hps, new_max_hps))
        
    def get_stat_exp(self):
        ret = [0,0,0,0,0]
        for i in range(5):
            ret[i] = GSCUtilsMisc.read_short(self.values, 0xB + (i * 2))
        return ret

    def get_ivs(self):
        ret = [0,0,0,0]
        calc_val = [GSCUtilsMisc.read_nybbles(self.values[0x15]), GSCUtilsMisc.read_nybbles(self.values[0x16])]
        for i in range(4):
            ret[i] = calc_val[i>>1][i&1]
        return ret

    def get_curr_hp(self):
        return GSCUtilsMisc.read_short(self.values, 0x22)
    
    def get_max_hp(self):
        return GSCUtilsMisc.read_short(self.values, 0x24)
    
    def has_mail(self):
        return GSCUtils.is_item_mail(self.get_item())
    
    def is_equal(self, other, weak=False):
        ranges = GSCTradingPokémonInfo.no_moves_equality_ranges
        if weak:
            ranges = GSCTradingPokémonInfo.no_moves_equality_weak_ranges
        for i in ranges:
            for j in i:
                if self.values[j] != other.values[j]:
                    return False
        if not self.are_moves_and_pp_same(other):
            return False
        if not (self.ot_name.values_equal(other.ot_name.values) and self.nickname.values_equal(other.nickname.values)):
            return False
        if self.has_mail():
            if not (self.mail.values_equal(other.mail.values) and self.mail_sender.values_equal(other.mail_sender.values)):
                return False
        return True
    
    def get_same_moves(self):
        pos = []
        for i in range(4):
            inner_pos = []
            for j in range(4):
                if self.get_move(i) == self.get_move(j):
                    inner_pos += [i]
            pos += [inner_pos]
        return pos
        
    def are_moves_and_pp_same(self, other):
        corresponding_indexes = self.are_moves_same(other)
        if corresponding_indexes is None:
            return False
        possible_positions = self.get_same_moves()
        found_pos = []
        for i in range(4):
            found = False
            for j in possible_positions[i]:
                if not found and corresponding_indexes[j] not in found_pos and self.get_pp(i) == other.get_pp(corresponding_indexes[j]):
                    found_pos += [corresponding_indexes[j]]
                    found = True
            if not found:
                return False
        return True
    
    def are_moves_same(self, other):
        pos = []
        for i in range(4):
            proper_found = False
            start_index = 0
            while not proper_found:
                index = other.has_move_index(self.get_move(i), start=start_index)
                if index == 4:
                    return None
                elif index in pos:
                    start_index = index + 1
                else:
                    pos += [index]
                    proper_found = True
        return pos
    
    def has_changed_significantly(self, raw):
        if self.get_species() != raw.get_species():
            return True
        if self.are_moves_same(raw) is None:
            return True
        if self.get_level() != raw.get_level():
            return True
        return False

    def get_data(self):
        sources = [self, self.ot_name, self.nickname]
        mail_sources = [self.mail, self.mail_sender]
        data = [0] * GSCTradingPokémonInfo._precalced_lengths[len(sources)+len(mail_sources)]
        for i in range(len(sources)):
            GSCUtilsMisc.copy_to_data(data, GSCTradingPokémonInfo._precalced_lengths[i], sources[i].values)
        if self.has_mail():
            for i in range(len(mail_sources)):
                GSCUtilsMisc.copy_to_data(data, GSCTradingPokémonInfo._precalced_lengths[i+len(sources)], mail_sources[i].values)
        return data

    def set_data(data):
        mon = GSCTradingPokémonInfo(data, GSCTradingPokémonInfo._precalced_lengths[0])
        mon.add_ot_name(data, GSCTradingPokémonInfo._precalced_lengths[1])
        mon.add_nickname(data, GSCTradingPokémonInfo._precalced_lengths[2])
        if mon.has_mail():
            mon.add_mail(data, GSCTradingPokémonInfo._precalced_lengths[3])
            mon.add_mail_sender(data, GSCTradingPokémonInfo._precalced_lengths[4])
        return mon

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
        self.trader_info = GSCUtilsMisc.read_short(data_pokemon, self.gsc_trader_info_pos)
        self.pokemon = []
        for i in range(self.get_party_size()):
            self.pokemon += [GSCTradingPokémonInfo(data_pokemon, self.gsc_trading_pokemon_pos + i * self.gsc_trading_pokemon_length)]
            self.pokemon[i].add_ot_name(data_pokemon, self.gsc_trading_pokemon_ot_pos + i * self.gsc_trading_name_length)
            self.pokemon[i].add_nickname(data_pokemon, self.gsc_trading_pokemon_nickname_pos + i * self.gsc_trading_name_length)
            if data_mail is not None and self.pokemon[i].has_mail():
                self.pokemon[i].add_mail(data_mail, self.gsc_trading_pokemon_mail_pos + i * self.gsc_trading_mail_length)
                self.pokemon[i].add_mail_sender(data_mail, self.gsc_trading_pokemon_mail_sender_pos + i * self.gsc_trading_mail_sender_length)

    def check_pos_validity(func):
        def wrapper(*args, **kwargs):
            self = args[0]
            pos = args[1]
            if pos < 0 or pos >= self.get_party_size():
                print("Index error!")
                return False
            return func(*args, **kwargs)
        return wrapper
    
    def get_party_size(self):
        return self.party_info.get_total()
    
    def get_last_mon_index(self):
        return self.get_party_size()-1
    
    def search_for_mon(self, mon):
        for i in range(self.get_party_size()):
            if mon.is_equal(self.pokemon[i]):
                return i
        for i in range(self.get_party_size()):
            if mon.is_equal(self.pokemon[i], weak=True):
                return i
        return None

    @check_pos_validity
    def mon_has_mail(self, pos):
        return self.pokemon[pos].has_mail()

    def party_has_mail(self):
        mail_owned = False
        for i in range(self.get_party_size()):
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
        if not self.pokemon[pos].is_nicknamed():
            self.pokemon[pos].add_nickname(GSCUtils.pokemon_names_gs[evolution], 0)
        self.pokemon[pos].set_species(evolution)
        self.party_info.set_id(pos, self.pokemon[pos].get_species())
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
        own = self.pokemon[self.get_last_mon_index()]
        self.pokemon[self.get_last_mon_index()] = other.pokemon[other.get_last_mon_index()]
        other.pokemon[other.get_last_mon_index()] = own
        self.party_info.set_id(self.get_last_mon_index(), self.pokemon[self.get_last_mon_index()].get_species())
        other.party_info.set_id(other.get_last_mon_index(), other.pokemon[other.get_last_mon_index()].get_species())
    
    @check_pos_validity
    def reorder_party(self, traded_pos):
        pa_info = self.party_info.get_id(traded_pos)
        po_data = self.pokemon[traded_pos]
        for i in range(traded_pos+1,self.get_party_size()):
            self.party_info.set_id(i-1, self.party_info.get_id(i))
            self.pokemon[i-1] = self.pokemon[i]
        self.party_info.set_id(self.get_last_mon_index(), pa_info)
        self.pokemon[self.get_last_mon_index()] = po_data

    def create_trading_data(self, lengths):
        data = []
        for i in range(2):
            data += [lengths[i]*[0]]
        data += [GSCUtils.no_mail_section[:len(GSCUtils.no_mail_section)]]
        GSCUtilsMisc.copy_to_data(data[1], self.gsc_trader_name_pos, self.trader.values)
        data[1][self.gsc_trading_party_info_pos] = self.get_party_size()
        GSCUtilsMisc.copy_to_data(data[1], self.gsc_trading_party_info_pos + 1, self.party_info.actual_mons)
        data[1][0x12] = 0xFF
        GSCUtilsMisc.write_short(data[1], self.gsc_trader_info_pos, self.trader_info)
        for i in range(self.get_party_size()):
            GSCUtilsMisc.copy_to_data(data[1], self.gsc_trading_pokemon_pos + (i * self.gsc_trading_pokemon_length), self.pokemon[i].values)
            GSCUtilsMisc.copy_to_data(data[1], self.gsc_trading_pokemon_ot_pos + (i * self.gsc_trading_name_length), self.pokemon[i].ot_name.values)
            GSCUtilsMisc.copy_to_data(data[1], self.gsc_trading_pokemon_nickname_pos + (i * self.gsc_trading_name_length), self.pokemon[i].nickname.values)
            if self.pokemon[i].mail is not None:
                GSCUtilsMisc.copy_to_data(data[2], self.gsc_trading_pokemon_mail_pos + (i * self.gsc_trading_mail_length), self.pokemon[i].mail.values)
                GSCUtilsMisc.copy_to_data(data[2], self.gsc_trading_pokemon_mail_sender_pos + (i * self.gsc_trading_mail_sender_length), self.pokemon[i].mail_sender.values)
        return data
    
class GSCChecks:
    bad_ids_items_path = "useful_data/bad_ids_items.bin"
    bad_ids_moves_path = "useful_data/bad_ids_moves.bin"
    bad_ids_pokemon_path = "useful_data/bad_ids_pokemon.bin"
    bad_ids_text_path = "useful_data/bad_ids_text.bin"
    checks_map_path = "useful_data/checks_map.bin"
    single_pokemon_checks_map_path = "useful_data/single_pokemon_checks_map.bin"
    curr_exp_pos_masks = [0, 0xFF0000, 0xFFFF00]
    free_value_species = 0xFF
    free_value_moves = 0
    
    def __init__(self, section_sizes, do_sanity_checks):
        self.do_sanity_checks = do_sanity_checks
        self.bad_ids_items = GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.bad_ids_items_path))
        self.bad_ids_moves = GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.bad_ids_moves_path))
        self.bad_ids_pokemon = GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.bad_ids_pokemon_path))
        self.bad_ids_text = GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.bad_ids_text_path))
        self.check_functions = [
            self.clean_nothing,
            self.clean_text,
            self.clean_team_size,
            self.clean_species,
            self.clean_move,
            self.clean_item,
            self.clean_level,
            self.check_hp,
            self.clean_text_final,
            self.load_stat_exp,
            self.load_stat_iv,
            self.check_stat,
            self.clean_species_sp,
            self.clean_pp,
            self.clean_experience
            ]
        self.checks_map = self.prepare_checks_map(GSCUtilsMisc.read_data(self.checks_map_path), section_sizes)
        self.single_pokemon_checks_map = self.prepare_basic_checks_map(GSCUtilsMisc.read_data(self.single_pokemon_checks_map_path))
    
    def clean_check_sanity_checks(func):
        def wrapper(*args, **kwargs):
            self = args[0]
            val = args[1]
            if self.do_sanity_checks:
                return func(*args, **kwargs)
            else:
                return val
        return wrapper
    
    def valid_check_sanity_checks(func):
        def wrapper(*args, **kwargs):
            self = args[0]
            if self.do_sanity_checks:
                return func(*args, **kwargs)
            else:
                return True
        return wrapper

    def prepare_text_buffer(self):
        self.curr_text = []
        
    def prepare_species_buffer(self):
        self.curr_species_pos = 0

    def prepare_checks_map(self, data, lengths):
        raw_data_sections = GSCUtilsMisc.divide_data(data, lengths)
        call_map = [[],[],[]]
        for i in range(len(raw_data_sections)):
            call_map[i] = self.prepare_basic_checks_map(raw_data_sections[i])
        return call_map

    def prepare_basic_checks_map(self, data):
        call_map = [None] * len(data)
        for i in range(len(data)):
            call_map[i] = self.check_functions[data[i]]
        return call_map
    
    @clean_check_sanity_checks
    def clean_nothing(self, val):
        return val
    
    @clean_check_sanity_checks
    def clean_level(self, level):
        self.level = GSCUtils.get_level_exp(self.curr_species, self.exp)
        return self.level
    
    @clean_check_sanity_checks
    def clean_experience(self, val):
        if self.curr_exp_pos == 0:
            self.exp_range = [GSCUtils.get_exp_level(self.curr_species, GSCUtils.min_level), GSCUtils.get_exp_level(self.curr_species, GSCUtils.max_level)]
            if val >= 0x80:
                self.negative_exp = True
        if self.negative_exp:
            val = 0
        curr_read_val = val << (8 * (2 - self.curr_exp_pos))
        exp_mask = self.curr_exp_pos_masks[self.curr_exp_pos]
        self.exp = self.check_range(self.exp_range, (self.exp & exp_mask) | curr_read_val)
        val = (self.exp >> (8 * (2 - self.curr_exp_pos))) & 0xFF
        self.curr_exp_pos += 1
        return val
    
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
            self.moves[self.curr_move] = GSCChecks.free_value_moves
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
        self.exp = 0
        self.negative_exp = False
        self.curr_exp_pos = 0
        self.curr_hp = 0
        self.curr_pos = 0
        self.curr_iv_pos = 0
        self.curr_exp_id = 0
        self.curr_stat_exp_pos = 0
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
        calc_val = val << (8 * self.curr_stat_exp_pos)
        if self.curr_stat_exp_pos == 0:
            self.stat_exp[self.curr_exp_id] = calc_val
            self.curr_stat_exp_pos += 1
        else:
            self.stat_exp[self.curr_exp_id] |= calc_val
            self.curr_stat_exp_pos = 0
            self.curr_exp_id += 1
        return val
    
    @clean_check_sanity_checks
    def load_stat_iv(self, val):
        calc_val = GSCUtilsMisc.read_nybbles(val)
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
        char_val = GSCUtils.end_of_line
        self.curr_text += [char_val]
        # Possibility to put bad words filters here
        self.prepare_text_buffer()
        return char_val

    def check_range(self, stat_range, curr_stat):
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
        self.stat = self.check_range(self.stat_range, (self.stat & 0xFF00) | curr_read_val)
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
    
    @valid_check_sanity_checks
    def is_team_size_valid(self, team_size):
        if team_size <= 0 or team_size > 6:
            return False
        return True
    
    @valid_check_sanity_checks
    def is_item_valid(self, item):
        return not GSCUtilsMisc.check_normal_list(self.bad_ids_items, item)
    
    @valid_check_sanity_checks
    def is_move_valid(self, move):
        return not GSCUtilsMisc.check_normal_list(self.bad_ids_moves, move)
    
    @valid_check_sanity_checks
    def is_species_valid(self, species):
        return not GSCUtilsMisc.check_normal_list(self.bad_ids_pokemon, species)
    
    @valid_check_sanity_checks
    def is_char_valid(self, char):
        return not GSCUtilsMisc.check_normal_list(self.bad_ids_text, char)
