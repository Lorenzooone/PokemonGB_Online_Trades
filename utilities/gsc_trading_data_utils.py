import math
import sys
from .gsc_trading_strings import GSCTradingStrings

class GSCUtilsLoaders:
    """
    Class which contains methods used to load structures from
    binary or text files.
    """

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
                    print(GSCTradingStrings.unrecognized_character_str.format(letter=letter))
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

    def prepare_stats(data, num_stats):
        ret = [0] * 0x100
        for i in range(0x100):
            ret[i] = data[(i)*num_stats:(i+1)*num_stats]
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
    """
    Class which contains generic methods and data used for
    pokémon-related functions.
    """
    base_folder = "useful_data/gsc/"
    evolution_ids_path = "evolution_ids.bin"
    mail_ids_path = "ids_mail.bin"
    no_mail_path = "no_mail_section.bin"
    base_stats_path = "stats.bin"
    text_conv_path = "text_conv.txt"
    pokemon_names_path = "pokemon_names.txt"
    moves_pp_list_path = "moves_pp_list.bin"
    learnset_evos_path = "learnset_evos.bin"
    exp_groups_path = "pokemon_exp_groups.bin"
    exp_lists_path = "pokemon_exp.txt"
    egg_nick_path = "egg_nick.bin"
    
    everstone_id = 0x70
    egg_id = 0xFD
    end_of_line = 0x50
    name_size = 0xB
    hp_stat_id = 0
    stat_id_base_conv_table = [0,1,2,5,3,4]
    stat_id_iv_conv_table = [0,0,1,2,3,3]
    stat_id_exp_conv_table = [0,1,2,3,4,4]
    egg_value = 0x38
    min_level = 2
    max_level = 100
    num_stats = 6
    
    evolution_ids = None
    mail_ids = None
    base_stats = None
    pokemon_names = None
    no_mail_section = None
    moves_pp_list = None
    learnsets = None
    exp_groups = None
    exp_lists = None
    egg_nick = None
    
    def __init__(self):
        curr_class = type(self)
        curr_class.evolution_ids = GSCUtilsLoaders.prepare_evolution_check_list(GSCUtilsMisc.read_data(self.get_path(curr_class.evolution_ids_path)))
        curr_class.mail_ids = GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.get_path(curr_class.mail_ids_path)))
        curr_class.no_mail_section = GSCUtilsMisc.read_data(self.get_path(curr_class.no_mail_path))
        curr_class.base_stats = GSCUtilsLoaders.prepare_stats(GSCUtilsMisc.read_data(self.get_path(curr_class.base_stats_path)), curr_class.num_stats)
        curr_class.pokemon_names = GSCUtilsLoaders.text_to_bytes(self.get_path(curr_class.pokemon_names_path), self.get_path(curr_class.text_conv_path))
        curr_class.moves_pp_list = GSCUtilsMisc.read_data(self.get_path(curr_class.moves_pp_list_path))
        curr_class.learnsets = GSCUtilsLoaders.prepare_learnsets(GSCUtilsMisc.read_data(self.get_path(curr_class.learnset_evos_path)))
        curr_class.exp_groups = GSCUtilsMisc.read_data(self.get_path(curr_class.exp_groups_path))
        curr_class.exp_lists = GSCUtilsLoaders.prepare_exp_lists(GSCUtilsLoaders.read_text_file(self.get_path(curr_class.exp_lists_path)))
        curr_class.egg_nick = GSCUtilsMisc.read_data(self.get_path(curr_class.egg_nick_path))
    
    def get_path(self, target):
        return self.base_folder + target
    
    def get_level_exp(species, exp, utils_class):
        start = utils_class.min_level
        end = utils_class.max_level
        if exp < utils_class.get_exp_level(species, start + 1, utils_class):
            return start
        if exp >= utils_class.get_exp_level(species, end, utils_class):
            return end
        end_search = False
        while not end_search:
            check_level = math.floor((start+end)/2)
            level_exp = utils_class.get_exp_level(species, check_level, utils_class)
            next_level_exp = utils_class.get_exp_level(species, check_level + 1, utils_class)
            if exp < level_exp:
                end = check_level
            elif exp > next_level_exp:
                start = check_level
            elif exp == next_level_exp:
                return check_level + 1
            else:
                return check_level
        return utils_class.max_level
    
    def get_exp_level(species, level, utils_class):
        return utils_class.exp_lists[utils_class.exp_groups[species]][level-1]
    
    def final_stat_calc_step(stat_id, level, utils_class):
        if stat_id != utils_class.hp_stat_id:
            return 5
        return level + 10
    
    def get_iv(iv, stat_id, utils_class):
        if stat_id != utils_class.hp_stat_id:
            return iv[utils_class.stat_id_iv_conv_table[stat_id]]
        return ((iv[0]&1)<<3) | ((iv[1]&1)<<2) | ((iv[2]&1)<<1) | (iv[3]&1)
    
    def get_exp(stat_exp, stat_id, utils_class):
        return stat_exp[utils_class.stat_id_exp_conv_table[stat_id]]
    
    def get_base_stat(species, stat_id, utils_class):
        return utils_class.base_stats[species][utils_class.stat_id_base_conv_table[stat_id]]
    
    def stat_calculation(stat_id, species, ivs, stat_exp, level, utils_class, do_exp=True):
        inter_value = (utils_class.get_base_stat(species, stat_id, utils_class) + utils_class.get_iv(ivs, stat_id, utils_class)) * 2
        if do_exp:
            inter_value += math.floor(math.ceil(math.sqrt(utils_class.get_exp(stat_exp, stat_id, utils_class))/4))
        inter_value = math.floor((inter_value*level)/100)
        return inter_value + utils_class.final_stat_calc_step(stat_id, level, utils_class)
    
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
    
    def single_mon_from_data(checks, data):
        ret = None
        
        # Prepare sanity checks stuff
        checks.prepare_text_buffer()
        checker = checks.single_pokemon_checks_map
        
        if len(data) > len(checker):
            # Applies the checks to the received data.
            # If the sanity checks are off, this will be a simple copy
            purified_data = checks.apply_checks_to_data(checker, data)
                
            # Prepares the pokémon data. For both the cleaned one and
            # the raw one
            raw = GSCTradingPokémonInfo.set_data(data)
            mon = GSCTradingPokémonInfo.set_data(purified_data)
            
            # Handle getting/sending eggs. That requires one extra byte
            is_egg = False
            if purified_data[len(checker)] == GSCUtils.egg_value:
                is_egg = True
            
            # If the sanity checks are on, has the pokémon changed
            # too much from the cleaning?
            if not mon.has_changed_significantly(raw):
                ret = [mon, is_egg]
        return ret
    
    def single_mon_to_data(mon, is_egg):
        egg_val = 0
        if is_egg:
            egg_val = GSCUtils.egg_value
        return mon.get_data() + [egg_val]

class GSCUtilsMisc:
    """
    Class which contains generic methods and data used for
    general functions.
    """

    def read_data(target):
        data = None
        try:
            with open(target, 'rb') as newFile:
                tmpdata = list(newFile.read())
                data = tmpdata
        except FileNotFoundError as e:
            pass
        return data

    def write_data(target, data):
        try:
            with open(target, 'wb') as newFile:
                newFile.write(bytearray(data))
        except IOError as e:
           print(GSCTradingStrings.io_error_str.format(e.errno, e.strerror))
        except: #handle other exceptions such as attribute errors
           print(GSCTradingStrings.unknown_error_str, sys.exc_info()[0])
    
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
    
    def copy_to_data(data, pos, values, length=None):
        if length is None:
            length = len(values)
        data[pos:pos+length] = values[:length]
        
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
    
    def verbose_print(to_print, verbose, end='\n'):
        if verbose:
            print(to_print, end=end)
    
class GSCTradingText:
    """
    Class which contains a text entry from the trading data.
    """

    def __init__(self, data, start, length=0xB, data_start=0):
        self.values = data[start:start+length]
        self.start_at = data_start
        self.utils_class = self.get_utils_class()
    
    def get_utils_class(self):
        return GSCUtils
    
    def values_equal(self, other):
        """
        :param other: Bytes, to be compared to the ones from its own values.
        """
        for i in range(len(self.values)):
            if self.values[i] == self.utils_class.end_of_line and (i >= len(other) or other[i] == self.utils_class.end_of_line):
                return True
            if i >= len(other):
                return False
            if self.values[i] != other[i]:
                return False
        if len(other) == len(self.values) or other[len(self.values)] == self.utils_class.end_of_line:
            return True
        return False
    
class GSCTradingPartyInfo:
    """
    Class which contains information about the party size and species
    from the trading data.
    """
    max_party_mons = 6
    
    def __init__(self, data, start):
        self.total = data[start]
        if self.total <= 0 or self.total > 6:
            self.total = 1
        self.actual_mons = data[start + 1:start + 1 + self.max_party_mons]
    
    def get_id(self, pos):
        if pos >= self.get_total() or pos >= self.max_party_mons:
            return None
        return self.actual_mons[pos]
    
    def set_id(self, pos, val):
        if pos < self.get_total() and pos < self.max_party_mons:
            self.actual_mons[pos] = val
    
    def get_total(self):
        return self.total

class GSCTradingPokémonInfo:
    """
    Class which contains information about the pokémon from the trading data.
    """
    pokemon_data_len = 0x30
    ot_name_len = 0xB
    nickname_len = 0xB
    mail_len = 0x21
    sender_len = 0xE
    
    species_pos = 0
    item_pos = 1
    moves_pos = 2
    pps_pos = 0x17
    level_pos = 0x1F
    exp_pos = 8
    curr_hp_pos = 0x22
    stats_pos = 0x24
    evs_pos = 0xB
    ivs_pos = 0x15
    egg_cycles_pos = 0x1B
    status_pos = 0x20
    
    no_moves_equality_ranges = [range(0,2), range(6,0x17), range(0x1B, pokemon_data_len)]
    all_lengths = [pokemon_data_len, ot_name_len, nickname_len, mail_len, sender_len]

    def __init__(self, data, start, length=pokemon_data_len):
        self.values = data[start:start+length]
        self.mail = None
        self.mail_sender = None
        self._precalced_lengths = GSCUtilsMisc.calc_divide_lengths(self.all_lengths)
        self.utils_class = self.get_utils_class()
        self.text_class = self.get_text_class()
    
    def get_utils_class(self):
        return GSCUtils
    
    def get_text_class(self):
        return GSCTradingText

    def add_ot_name(self, data, start):
        self.ot_name = self.text_class(data, start, length=self.ot_name_len)

    def add_nickname(self, data, start):
        self.nickname = self.text_class(data, start, length=self.nickname_len)

    def add_mail(self, data, start):
        self.mail = self.text_class(data, start, length=self.mail_len)
        
    def add_mail_sender(self, data, start):
        self.mail_sender = self.text_class(data, start, length=self.sender_len, data_start=3)
    
    def is_nicknamed(self):
        return not self.nickname.values_equal(self.utils_class.pokemon_names[self.get_species()])
    
    def set_default_nickname(self):
        self.add_nickname(self.utils_class.pokemon_names[self.get_species()], 0)
    
    def set_egg_nickname(self):
        self.add_nickname(self.utils_class.egg_nick, 0)
    
    def get_species(self):
        return self.values[self.species_pos]
    
    def learnable_moves(self):
        """
        Returns the moves the pokémon could learn at its current level.
        """
        if self.get_species() in self.utils_class.learnsets.keys():
            if self.get_level() in self.utils_class.learnsets[self.get_species()].keys():
                return self.utils_class.learnsets[self.get_species()][self.get_level()]
        return None
    
    def set_species(self, data):
        self.values[self.species_pos] = data & 0xFF
        
    def get_item(self):
        return self.values[self.item_pos]
        
    def set_item(self, data=0):
        self.values[self.item_pos] = data & 0xFF
    
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
        return self.values[self.moves_pos + pos]
    
    def set_move(self, pos, val, max_pp=True):
        self.values[self.moves_pos + pos] = val
        if max_pp:
            self.set_pp(pos, self.utils_class.moves_pp_list[val])
    
    def set_hatching_cycles(self, val=1):
        self.values[self.egg_cycles_pos] = val
    
    def get_hatching_cycles(self):
        return self.values[self.egg_cycles_pos]
    
    def set_pp(self, pos, val):
        self.values[self.pps_pos + pos] = val
    
    def get_pp(self, pos):
        return self.values[self.pps_pos + pos]
    
    def get_level(self):
        return self.values[self.level_pos]
    
    def set_level(self, val):
        self.values[self.level_pos] = val
        self.set_exp(self.utils_class.get_exp_level(self.get_species(), val, self.utils_class))
        self.update_stats()
    
    def set_exp(self, val):
        self.values[self.exp_pos] = (val >> 0x10) & 0xFF
        self.values[self.exp_pos+1] = (val >> 8) & 0xFF
        self.values[self.exp_pos+2] = (val) & 0xFF
    
    def update_stats(self):
        """
        Updates the stats after they're changed (from evolving/changing level).
        """
        old_max_hps = self.get_max_hp()
        old_current_hps = self.get_curr_hp()
        for i in range(self.utils_class.num_stats):
            GSCUtilsMisc.write_short(self.values, self.stats_pos + (i * 2), self.utils_class.stat_calculation(i, self.get_species(), self.get_ivs(), self.get_stat_exp(), self.get_level(), self.utils_class))
        new_max_hps = self.get_max_hp()
        old_current_hps += new_max_hps-old_max_hps
        GSCUtilsMisc.write_short(self.values, self.curr_hp_pos, min(max(0, old_current_hps), new_max_hps))
        
    def get_stat_exp(self):
        ret = [0,0,0,0,0]
        for i in range(5):
            ret[i] = GSCUtilsMisc.read_short(self.values, self.evs_pos + (i * 2))
        return ret

    def get_ivs(self):
        ret = [0,0,0,0]
        calc_val = [GSCUtilsMisc.read_nybbles(self.values[self.ivs_pos]), GSCUtilsMisc.read_nybbles(self.values[self.ivs_pos+1])]
        for i in range(4):
            ret[i] = calc_val[i>>1][i&1]
        return ret

    def get_curr_hp(self):
        return GSCUtilsMisc.read_short(self.values, self.curr_hp_pos)

    def heal(self):
        GSCUtilsMisc.write_short(self.values, self.curr_hp_pos, self.get_max_hp())
        self.status_pos = 0

    def faint(self):
        GSCUtilsMisc.write_short(self.values, self.curr_hp_pos, 0)
        self.status_pos = 0
    
    def get_max_hp(self):
        return GSCUtilsMisc.read_short(self.values, self.stats_pos)
    
    def has_mail(self):
        return self.utils_class.is_item_mail(self.get_item())
    
    def is_equal(self, other, weak=False):
        ranges = self.no_moves_equality_ranges
        for i in ranges:
            for j in i:
                if self.values[j] != other.values[j]:
                    return False
        if not self.are_moves_and_pp_same(other):
            return False
        if not weak:
            if not (self.ot_name.values_equal(other.ot_name.values) and self.nickname.values_equal(other.nickname.values)):
                return False
            if self.has_mail():
                if not (self.mail.values_equal(other.mail.values) and self.mail_sender.values_equal(other.mail_sender.values)):
                    return False
        return True
    
    def get_same_moves(self):
        """
        Returns for each index the list of indexes with the same move.
        """
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
        """
        Returns None if the moves are different.
        If they're the same, it returns the index in which they're found.
        """
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
        """
        Returns whether a pokémon has changed too much due to the sanity
        checks cleaning it.
        """
        if self.get_species() != raw.get_species():
            return True
        if self.are_moves_same(raw) is None:
            return True
        if self.get_level() != raw.get_level():
            return True
        return False

    def get_data(self):
        """
        Returns all the data used to represent this pokemon.
        """
        sources = [self, self.ot_name, self.nickname]
        mail_sources = [self.mail, self.mail_sender]
        data = [0] * self._precalced_lengths[len(sources)+len(mail_sources)]
        for i in range(len(sources)):
            GSCUtilsMisc.copy_to_data(data, self._precalced_lengths[i], sources[i].values)
        if self.has_mail():
            for i in range(len(mail_sources)):
                GSCUtilsMisc.copy_to_data(data, self._precalced_lengths[i+len(sources)], mail_sources[i].values)
        return data

    def set_data(data):
        """
        Creates an entry from the given data.
        """
        mon = GSCTradingPokémonInfo(data, 0)
        mon.add_ot_name(data, mon._precalced_lengths[1])
        mon.add_nickname(data, mon._precalced_lengths[2])
        if mon.has_mail():
            mon.add_mail(data, mon._precalced_lengths[3])
            mon.add_mail_sender(data, mon._precalced_lengths[4])
        return mon

class GSCTradingData:
    """
    Class which contains all the informations about a trader's party.
    """
    trader_name_pos = 0
    trading_party_info_pos = 0xB
    trading_party_final_pos = 0x12
    trader_info_pos = 0x13
    trading_pokemon_pos = 0x15
    trading_pokemon_ot_pos = 0x135
    trading_pokemon_nickname_pos = 0x177
    trading_pokemon_mail_pos = 0xCB
    trading_pokemon_mail_sender_pos = 0x191
    
    trading_pokemon_length = 0x30
    trading_name_length = 0xB
    trading_mail_length = 0x21
    trading_mail_sender_length = 0xE
    
    def __init__(self, data_pokemon, data_mail=None, do_full=True):
        self.utils_class = self.get_utils_class()
        self.trader = self.text_generator(data_pokemon, self.trader_name_pos)
        self.party_info = self.party_generator(data_pokemon, self.trading_party_info_pos)
        self.trader_info = self.trainer_info_generator(data_pokemon, self.trader_info_pos)
        self.pokemon = []
        if do_full:
            for i in range(self.get_party_size()):
                self.pokemon += [self.mon_generator(data_pokemon, self.trading_pokemon_pos + i * self.trading_pokemon_length)]
                self.pokemon[i].add_ot_name(data_pokemon, self.trading_pokemon_ot_pos + i * self.trading_name_length)
                self.pokemon[i].add_nickname(data_pokemon, self.trading_pokemon_nickname_pos + i * self.trading_name_length)
                if data_mail is not None and self.pokemon[i].has_mail():
                    self.pokemon[i].add_mail(data_mail, self.trading_pokemon_mail_pos + i * self.trading_mail_length)
                    self.pokemon[i].add_mail_sender(data_mail, self.trading_pokemon_mail_sender_pos + i * self.trading_mail_sender_length)
    
    def mon_generator(self, data, pos):
        return self.mon_generator_class()(data, pos)
    
    def mon_generator_class(self):
        return GSCTradingPokémonInfo
    
    def text_generator(self, data, pos):
        return GSCTradingText(data, pos)
    
    def party_generator(self, data, pos):
        return GSCTradingPartyInfo(data, pos)
    
    def trainer_info_generator(self, data, pos):
        return GSCUtilsMisc.read_short(data, pos)
    
    def get_utils_class(self):
        return GSCUtils

    def check_pos_validity(func):
        def wrapper(*args, **kwargs):
            self = args[0]
            pos = args[1]
            if pos < 0 or pos >= self.get_party_size():
                print(GSCTradingStrings.index_error_str)
                return False
            return func(*args, **kwargs)
        return wrapper
    
    def get_party_size(self):
        return self.party_info.get_total()
    
    def get_last_mon_index(self):
        return self.get_party_size()-1
    
    def search_for_mon(self, mon, is_egg):
        """
        Returns None if a provided pokémon is not in the party.
        Otherwise, it returns their index.
        """
        for i in range(self.get_party_size()):
            if mon.is_equal(self.pokemon[i]) and (self.is_mon_egg(i) == is_egg):
                return i
        for i in range(self.get_party_size()):
            if mon.is_equal(self.pokemon[i], weak=True) and (self.is_mon_egg(i) == is_egg):
                return i
        return None

    @check_pos_validity
    def mon_has_mail(self, pos):
        return self.pokemon[pos].has_mail()

    @check_pos_validity
    def is_mon_egg(self, pos):
        return self.party_info.get_id(pos) == self.utils_class.egg_id

    def party_has_mail(self):
        mail_owned = False
        for i in range(self.get_party_size()):
            mail_owned |= self.mon_has_mail(i)
        return mail_owned
    
    def evolution_procedure(self, pos, evolution):
        """
        Procedure which actually evolves the Pokémon in the data.
        """
        if not self.pokemon[pos].is_nicknamed():
            self.pokemon[pos].add_nickname(self.utils_class.pokemon_names[evolution], 0)
        self.pokemon[pos].set_species(evolution)
        self.party_info.set_id(pos, self.pokemon[pos].get_species())
        self.pokemon[pos].update_stats()
        
    @check_pos_validity
    def evolve_mon(self, pos):
        """
        Handles evolving a pokémon in the party.
        Returns None if it won't evolve.
        Returns True if it evolved and player input is required.
        Returns False if it evolved and no player input is required.
        """
        evolution = self.utils_class.get_evolution(self.pokemon[pos].get_species(), self.pokemon[pos].get_item())
        if evolution is None or self.is_mon_egg(pos):
            return None
        evo_item = self.utils_class.get_evolution_item(self.pokemon[pos].get_species())
        if evo_item is not None:
            self.pokemon[pos].set_item()
        self.evolution_procedure(pos, evolution)
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
    
    def trade_mon(self, other, own_index, other_index, checks):
        """
        Trades a pokémon between two parties.
        """
        self.reorder_party(own_index)
        other.reorder_party(other_index)
        own = self.mon_generator_class().set_data(checks.apply_checks_to_data(checks.single_pokemon_checks_map, self.pokemon[self.get_last_mon_index()].get_data()))
        self.pokemon[self.get_last_mon_index()] = other.pokemon[other.get_last_mon_index()]
        other.pokemon[other.get_last_mon_index()] = own
        checks.curr_species_pos = self.get_last_mon_index()
        checks.team_size = self.get_party_size()
        own_id = checks.species_cleaner(self.party_info.get_id(self.get_last_mon_index()))
        self.party_info.set_id(self.get_last_mon_index(), other.party_info.get_id(other.get_last_mon_index()))
        other.party_info.set_id(other.get_last_mon_index(), own_id)
    
    @check_pos_validity
    def reorder_party(self, traded_pos):
        """
        Moves a pokémon at the end of the party.
        """
        pa_info = self.party_info.get_id(traded_pos)
        po_data = self.pokemon[traded_pos]
        for i in range(traded_pos+1,self.get_party_size()):
            self.party_info.set_id(i-1, self.party_info.get_id(i))
            self.pokemon[i-1] = self.pokemon[i]
        self.party_info.set_id(self.get_last_mon_index(), pa_info)
        self.pokemon[self.get_last_mon_index()] = po_data

    def create_trading_data(self, lengths):
        """
        Creates the data which can be loaded to the hardware.
        """
        data = []
        for i in range(2):
            data += [lengths[i]*[0]]
        data += [self.utils_class.no_mail_section[:len(self.utils_class.no_mail_section)]]
        GSCUtilsMisc.copy_to_data(data[1], self.trader_name_pos, self.trader.values, self.trading_name_length)
        data[1][self.trading_party_info_pos] = self.get_party_size()
        GSCUtilsMisc.copy_to_data(data[1], self.trading_party_info_pos + 1, self.party_info.actual_mons)
        data[1][self.trading_party_final_pos] = 0xFF
        if self.trader_info is not None:
            GSCUtilsMisc.write_short(data[1], self.trader_info_pos, self.trader_info)
        for i in range(self.get_party_size()):
            GSCUtilsMisc.copy_to_data(data[1], self.trading_pokemon_pos + (i * self.trading_pokemon_length), self.pokemon[i].values)
            GSCUtilsMisc.copy_to_data(data[1], self.trading_pokemon_ot_pos + (i * self.trading_name_length), self.pokemon[i].ot_name.values, self.trading_name_length)
            GSCUtilsMisc.copy_to_data(data[1], self.trading_pokemon_nickname_pos + (i * self.trading_name_length), self.pokemon[i].nickname.values, self.trading_name_length)
            if self.pokemon[i].mail is not None:
                GSCUtilsMisc.copy_to_data(data[2], self.trading_pokemon_mail_pos + (i * self.trading_mail_length), self.pokemon[i].mail.values)
                GSCUtilsMisc.copy_to_data(data[2], self.trading_pokemon_mail_sender_pos + (i * self.trading_mail_sender_length), self.pokemon[i].mail_sender.values, self.trading_mail_sender_length)
        return data
    
class GSCChecks:
    """
    Class which handles sanity checks and cleaning of the received data.
    checks_map and single_pokemon_checks_map are its product used to apply
    the checks.
    """
    base_folder = "useful_data/gsc/"
    bad_ids_items_path = "bad_ids_items.bin"
    bad_ids_moves_path = "bad_ids_moves.bin"
    bad_ids_pokemon_path = "bad_ids_pokemon.bin"
    bad_ids_text_path = "bad_ids_text.bin"
    checks_map_path = "checks_map.bin"
    single_pokemon_checks_map_path = "single_pokemon_checks_map.bin"
    moves_checks_map_path = "moves_checks_map.bin"
    curr_exp_pos_masks = [0, 0xFF0000, 0xFFFF00]
    free_value_species = 0xFF
    free_value_moves = 0
    tackle_id = 0x21
    rattata_id = 0x13
    question_mark = 0xE6
    
    def __init__(self, section_sizes, do_sanity_checks):
        self.utils_class = self.get_utils_class()
        self.do_sanity_checks = do_sanity_checks
        self.bad_ids_items = GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.get_path(self.bad_ids_items_path)))
        self.bad_ids_moves = GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.get_path(self.bad_ids_moves_path)))
        self.bad_ids_pokemon = GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.get_path(self.bad_ids_pokemon_path)))
        self.bad_ids_text = GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.get_path(self.bad_ids_text_path)))
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
            self.clean_experience,
            self.clean_egg_cycles_friendship,
            self.clean_type
            ]
        self.checks_map = self.prepare_checks_map(GSCUtilsMisc.read_data(self.get_path(self.checks_map_path)), section_sizes)
        self.single_pokemon_checks_map = self.prepare_basic_checks_map(GSCUtilsMisc.read_data(self.get_path(self.single_pokemon_checks_map_path)))
        self.moves_checks_map = self.prepare_basic_checks_map(GSCUtilsMisc.read_data(self.get_path(self.moves_checks_map_path)))
        self.species_cleaner = self.clean_species_sp
    
    def get_path(self, target):
        return self.base_folder + target
    
    def get_utils_class(self):
        return GSCUtils
    
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
    
    def apply_checks_to_data(self, checker, data):
        new_data = list(data)
        for j in range(len(checker)):
            new_data[j] = checker[j](data[j])
        return new_data

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
        self.level = self.utils_class.get_level_exp(self.curr_species, self.exp, self.utils_class)
        return self.level
    
    def exp_range_calculations(self):
        return [self.utils_class.get_exp_level(self.curr_species, self.utils_class.min_level, self.utils_class), self.utils_class.get_exp_level(self.curr_species, self.utils_class.max_level, self.utils_class)]
    
    @clean_check_sanity_checks
    def clean_experience(self, val):
        if self.curr_exp_pos == 0:
            self.exp_range = self.exp_range_calculations()
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
        max_base_pp = self.utils_class.moves_pp_list[self.moves[self.curr_pp]]
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
        final_move = self.clean_value(move, self.is_move_valid, self.tackle_id)
        self.moves[self.curr_move] = final_move
        self.curr_move += 1
        return final_move
    
    @clean_check_sanity_checks
    def clean_species(self, species):
        self.curr_species = self.clean_value(species, self.is_species_valid, self.rattata_id)
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
        if species == self.free_value_species or self.curr_species_pos >= self.team_size:
            self.curr_species_pos += 1
            return self.free_value_species
        found_species = self.clean_value(species, self.is_species_valid, self.rattata_id)
        if species == self.utils_class.egg_id:
            found_species = species
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
        char_val = self.clean_value(char, self.is_char_valid, self.question_mark)
        self.curr_text += [char_val]
        # Possibility to put bad words filters here
        return char_val
    
    @clean_check_sanity_checks
    def clean_text_final(self, char):
        char_val = self.utils_class.end_of_line
        self.curr_text += [char_val]
        # Possibility to put bad words filters here
        self.prepare_text_buffer()
        return char_val
    
    @clean_check_sanity_checks
    def clean_type(self, typing):
        return typing

    def check_range(self, stat_range, curr_stat):
        if curr_stat > stat_range[1]:
            curr_stat = stat_range[1]
        if curr_stat < stat_range[0]:
            curr_stat = stat_range[0]
        return curr_stat
    
    @clean_check_sanity_checks
    def check_stat(self, val, zero_min=False):
        if self.curr_pos == 0:
            self.stat = 0
            min_stat = self.utils_class.stat_calculation(self.curr_stat_id, self.curr_species, self.iv, self.stat_exp, self.level, self.utils_class, do_exp=False)
            if zero_min:
                min_stat = 0
            self.stat_range = [min_stat, self.utils_class.stat_calculation(self.curr_stat_id, self.curr_species, self.iv, self.stat_exp, self.level, self.utils_class)]
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
        start_zero = False
        if self.curr_hp == 0:
            start_zero = True
        val = self.check_stat(val, zero_min=start_zero)
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
        
    @clean_check_sanity_checks
    def clean_egg_cycles_friendship(self, cycles_friendship):
        return cycles_friendship
    
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
