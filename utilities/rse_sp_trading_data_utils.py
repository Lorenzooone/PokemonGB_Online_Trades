import math
from .gsc_trading_data_utils import GSCUtils, GSCTradingText, GSCTradingPokémonInfo, GSCTradingPartyInfo, GSCTradingData, GSCChecks, GSCUtilsMisc

class RSESPUtils(GSCUtils):
    """
    Class which contains generic methods and data used for
    pokémon-related functions.
    """
    base_folder = "useful_data/rse/"
    invalid_held_items_path = "invalid_held_items.bin"
    invalid_pokemon_path = "invalid_pokemon.bin"
    abilities_path = "abilities.bin"
    
    invalid_held_items = None
    invalid_pokemon = None
    abilities = None
    num_entries = 0x1BD
    last_valid_pokemon = 411
    last_valid_item = 376
    last_valid_move = 354
    struggle_id = 165
    
    def __init__(self):
        super(RSESPUtils, self).__init__()
        curr_class = type(self)
        curr_class.init_enc_positions(curr_class)
        curr_class.invalid_held_items = GSCUtilsMisc.read_data(self.get_path(curr_class.invalid_held_items_path))
        curr_class.invalid_pokemon = GSCUtilsMisc.read_data(self.get_path(curr_class.invalid_pokemon_path))
        curr_class.abilities = GSCUtilsMisc.read_data(self.get_path(curr_class.abilities_path))

    def init_enc_positions(curr_class):
        curr_class.enc_positions = []
        for i in range(4):
            for j in range(4):
                if(j != i):
                    for k in range(4):
                        if((k != i) and (k != j)):
                            for l in range(4):
                                if((l != i) and (l != j) and (l != k)):
                                    curr_class.enc_positions += [(0<<(i*2)) | (1<<(j*2)) | (2<<(k*2)) | (3<<(l*2))]
    
    def get_iv(iv, stat_id, utils_class):
        return iv[utils_class.stat_id_base_conv_table[stat_id]]
    
    def get_exp(stat_exp, stat_id, utils_class):
        return stat_exp[utils_class.stat_id_base_conv_table[stat_id]]

    def get_stat_exp_contribution(stat_exp):
        return math.floor(stat_exp / 4)
    
    def stat_calculation(stat_id, species, ivs, stat_exp, level, utils_class, nature=0, do_exp=True):
        inter_value = ((2 * utils_class.get_base_stat(species, stat_id, utils_class)) + utils_class.get_iv(ivs, stat_id, utils_class))
        if do_exp:
            inter_value += utils_class.get_stat_exp_contribution(utils_class.get_exp(stat_exp, stat_id, utils_class))
        inter_value = math.floor((inter_value*level)/100)
        
        stat_boosted = int(nature / 5) + 1
        stat_nerfed = (nature  % 5) + 1
        if stat_boosted == stat_nerfed:
            stat_boosted = -1
            stat_nerfed = -1
        precise_stat_boost = 1.0
        if(stat_id == stat_boosted):
            precise_stat_boost = 1.1
        if(stat_id == stat_nerfed):
            precise_stat_boost = 0.9
        return int((inter_value + utils_class.final_stat_calc_step(stat_id, level, utils_class))*precise_stat_boost)
    
    def is_item_mail(item):
        return (item >= 0x79) and (item <= 0x84)
    
    def is_move_valid(move, utils_class):
        if move > utils_class.last_valid_move:
            return 0
        if move == utils_class.struggle_id:
            return 0
        return 1

    def is_item_valid(item, utils_class):
        if item > utils_class.last_valid_item:
            return 0
        if (utils_class.invalid_held_items_bin[item>>3] & (1<<(item&7))) != 0:
            return 0
        return 1

    def is_species_valid(species, utils_class):
        if species > utils_class.last_valid_pokemon:
            return 0
        if (utils_class.invalid_pokemon[species>>3] & (1<<(species&7))) != 0:
            return 0
        return 1
    
    def is_evolving(species, item):
        return False
    
    def get_evolution(species, item):
        return None
    
    def get_evolution_item(species):
        return None
    
    def get_patch_set_num_index(is_mail, is_japanese):
        patch_sets_num = 0
        patch_sets_index = 0
        return patch_sets_num, patch_sets_index
    
    def single_mon_from_data(checks, data):
        ret = None
        
        if len(data) >= (RSESPTradingPokémonInfo.pokemon_data_len + RSESPTradingPokémonInfo.mail_len + RSESPTradingPokémonInfo.version_info_len + RSESPTradingPokémonInfo.ribbon_info_len):
            # Prepares the pokémon data. For both the cleaned one and
            # the raw one
            mon = RSESPTradingPokémonInfo.set_data(data)
            
            # If the sanity checks are on, has the pokémon changed
            # too much from the cleaning?
            if not mon.has_changed_significantly(None):
                ret = [mon, mon.get_is_egg()]
        return ret
    
    def single_mon_to_data(mon, is_egg):
        return mon.get_data()

class RSESPTradingText(GSCTradingText):
    """
    Class which contains a text entry from the trading data.
    """
    
    def __init__(self, data, start, length=0xB, data_start=0):
        super(RSESPTradingText, self).__init__(data, start, length=length, data_start=data_start)
    
    def get_utils_class(self):
        return RSESPUtils
        
class RSESPTradingPokémonInfo(GSCTradingPokémonInfo):
    """
    Class which contains information about the pokémon from the trading data.
    """
    pokemon_data_len = 0x64
    japanese_language_id = 1
    num_unown_letters = 28
    unown_b_start = 415
    unown_species = 201
    deoxys_species = 410
    egg_species = 412
    deoxys_forms_start = 442
    unown_real_name_index = 445
    trade_location = 0xFE
    event_location = 0xFF
    colosseum_game = 0xF
    ot_name_len = 7
    nickname_len = 10
    pid_pos = 0
    ot_id_pos = 4
    nickname_pos = 8
    language_pos = 18
    use_egg_name_pos = 19
    ot_name_pos = 20
    checksum_pos = 28
    enc_data_pos = 32
    enc_data_len = 48
    status_pos = 80
    level_pos = 84
    mail_info_pos = 85
    curr_hp_pos = 86
    stats_pos = 88
    mail_len = 0x24
    version_info_len = 2
    ribbon_info_len = 11
    
    all_lengths = [pokemon_data_len, mail_len, version_info_len, ribbon_info_len]
    
    def __init__(self, data, start, length=pokemon_data_len, is_encrypted=True):
        super(RSESPTradingPokémonInfo, self).__init__(data, start, length=length)
        self.pid = GSCUtilsMisc.read_int_le(self.values, self.pid_pos)
        self.ot_id = GSCUtilsMisc.read_int_le(self.values, self.ot_id_pos)
        self.is_valid = True
        decrypted_data = []
        enc_positions = self.utils_class.enc_positions
        enc_data_len = self.enc_data_len
        checksum = 0
        self.checksum_failed = False
        if not is_encrypted:
            for i in range(int(enc_data_len/4)):
                single_entry_dec = GSCUtilsMisc.read_int_le(self.values, self.enc_data_pos+(i*4))
                checksum = (checksum + single_entry_dec) & 0xFFFF
                checksum = (checksum + (single_entry_dec>>16)) & 0xFFFF
            if checksum != GSCUtilsMisc.read_short_le(self.values, self.checksum_pos):
                self.is_valid = False
                self.checksum_failed = True
            self.growth = self.values[self.enc_data_pos + (int(enc_data_len/4)*0):self.enc_data_pos + (int(enc_data_len/4)*1)]
            self.attacks = self.values[self.enc_data_pos + (int(enc_data_len/4)*1):self.enc_data_pos + (int(enc_data_len/4)*2)]
            self.evs = self.values[self.enc_data_pos + (int(enc_data_len/4)*2):self.enc_data_pos + (int(enc_data_len/4)*3)]
            self.misc = self.values[self.enc_data_pos + (int(enc_data_len/4)*3):self.enc_data_pos + (int(enc_data_len/4)*4)]
            self.encrypt_data()
        checksum = 0
        for i in range(int(enc_data_len/4)):
            single_entry_dec = GSCUtilsMisc.read_int_le(self.values, self.enc_data_pos+(i*4))^self.pid^self.ot_id
            for j in range(4):
                decrypted_data += [(single_entry_dec>>(8*j)) & 0xFF]
            checksum = (checksum + single_entry_dec) & 0xFFFF
            checksum = (checksum + (single_entry_dec>>16)) & 0xFFFF
        if checksum != GSCUtilsMisc.read_short_le(self.values, self.checksum_pos):
            self.is_valid = False
            self.checksum_failed = True
        index = self.pid % len(enc_positions)
        self.growth = decrypted_data[int(enc_data_len/4)*((enc_positions[index]>>0)&3):int(enc_data_len/4)*(((enc_positions[index]>>0)&3)+1)]
        self.attacks = decrypted_data[int(enc_data_len/4)*((enc_positions[index]>>2)&3):int(enc_data_len/4)*(((enc_positions[index]>>2)&3)+1)]
        self.evs = decrypted_data[int(enc_data_len/4)*((enc_positions[index]>>4)&3):int(enc_data_len/4)*(((enc_positions[index]>>4)&3)+1)]
        self.misc = decrypted_data[int(enc_data_len/4)*((enc_positions[index]>>6)&3):int(enc_data_len/4)*(((enc_positions[index]>>6)&3)+1)]
        self.version_info = [0, 0]
        self.ribbon_info = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if self.is_valid:
            if not self.utils_class.is_species_valid(self.get_species(), self.utils_class):
                self.is_valid = False
        if self.is_valid:
            if not self.has_valid_moves():
                self.is_valid = False
        if self.is_valid:
            if not self.is_ability_valid():
                self.is_valid = False
        if self.is_valid:
            if self.get_is_bad_egg():
                self.is_valid = False
    
    def get_utils_class(self):
        return RSESPUtils

    def add_ot_name(self, data, start):
        while len(data[start:]) < self.ot_name_len:
            data += [0]
        self.values[self.ot_name_pos:self.ot_name_pos+self.ot_name_len] = data[start:start+self.ot_name_len]

    def add_nickname(self, data, start):
        while len(data[start:]) < self.nickname_len:
            data += [0]
        self.values[self.nickname_pos:self.nickname_pos+self.nickname_len] = data[start:start+self.nickname_len]

    def add_version_info(self, data, start):
        while len(data[start:]) < self.version_info_len:
            data += [0]
        self.version_info = data[start:start+self.version_info_len]

    def add_ribbon_info(self, data, start):
        while len(data[start:]) < self.ribbon_info_len:
            data += [0]
        self.ribbon_info = data[start:start+self.ribbon_info_len]
    
    def set_default_nickname(self):
        self.add_nickname(self.utils_class.pokemon_names[self.get_species()], 0)
    
    def set_egg_nickname(self):
        self.add_nickname(self.utils_class.egg_nick, 0)
        self.values[self.language_pos] = self.japanese_language_id
        self.values[self.use_egg_name_pos] |= 4
        self.misc[7] |= 0x40
        
    def get_is_bad_egg(self):
        return (self.values[self.use_egg_name_pos] & 1) != 0

    def get_is_egg(self):
        if (self.misc[7] & 0x40) != 0:
            return 1
        return 0

    def encrypt_data(self):
        enc_positions = self.utils_class.enc_positions
        enc_data_len = self.enc_data_len
        index = self.pid % len(enc_positions)
        decrypted_data = []
        encrypted_data = []
        for i in range(4):
            for j in range(4):
                value = (enc_positions[index]>>(2*j))&3
                if value == i:
                    if j == 0:
                        decrypted_data += self.growth
                    elif j == 1:
                        decrypted_data += self.attacks
                    elif j == 2:
                        decrypted_data += self.evs
                    elif j == 3:
                        decrypted_data += self.misc
        checksum = 0
        for i in range(int(enc_data_len/4)):
            single_entry_dec = GSCUtilsMisc.read_int_le(decrypted_data, i*4)
            checksum = (checksum + single_entry_dec) & 0xFFFF
            checksum = (checksum + (single_entry_dec>>16)) & 0xFFFF
            single_entry_dec ^= self.pid^self.ot_id
            for j in range(4):
                encrypted_data += [(single_entry_dec>>(8*j)) & 0xFF]
        if self.checksum_failed:
            checksum += 1
        self.values[self.enc_data_pos:self.enc_data_pos + (int(enc_data_len/4)*4)] = encrypted_data
        GSCUtilsMisc.write_short_le(self.values, self.checksum_pos, checksum)
    
    def get_has_second_ability(self):
        if (self.misc[7] & 0x80) != 0:
            return 1
        return 0
    
    def get_met_location(self):
        return self.misc[1]
    
    def get_origin_game(self):
        return (GSCUtilsMisc.read_short_le(self.misc, 2) >> 7) & 0xF
    
    def is_ability_valid(self):
        mon_index = self.get_mon_index()
        abilities = self.utils_class.abilities[mon_index*2:(mon_index+1)*2]
        abilities_same = abilities[0] == abilities[1]
    
        if abilities_same and (self.get_has_second_ability() == 1):
            return 0
    
        if ((self.pid&1) ^ self.get_has_second_ability()) == 0:
            return 1
    
        if self.get_met_location() == self.trade_location:
            return 1
        
        if self.get_met_location() == self.event_location:
            return 1
        
        if self.get_origin_game() == self.colosseum_game:
            return 1
        
        if abilities_same:
            return 1
        
        return 0
    
    def get_species(self):
        return GSCUtilsMisc.read_short_le(self.growth, 0)
    
    def learnable_moves(self):
        """
        Returns the moves the pokémon could learn at its current level.
        """
        return None
    
    def set_species(self, data):
        GSCUtilsMisc.write_short_le(self.growth, 0, data)
        
    def get_item(self):
        return GSCUtilsMisc.read_short_le(self.growth, 2)
        
    def set_item(self, data=0):
        GSCUtilsMisc.write_short_le(self.growth, 2, data)
    
    def get_move(self, pos):
        move = GSCUtilsMisc.read_short_le(self.attacks, pos*2)
        if not self.utils_class.is_move_valid(move, self.utils_class):
            move = 0
        return move
    
    def set_move(self, pos, val, max_pp=True):
        GSCUtilsMisc.write_short_le(self.attacks, pos*2, val)
        if max_pp:
            self.set_pp(pos, self.utils_class.moves_pp_list[val])
    
    def has_valid_moves(self):
        for i in range(4):
            if self.get_move(i) != 0:
                return 1
        return 0
    
    def get_unown_letter(self):
        return ((self.pid & 3) + (((self.pid >> 8) & 3) << 2) + (((self.pid >> 16) & 3) << 4) + (((self.pid >> 24) & 3) << 6)) % self.num_unown_letters
    
    def get_deoxys_form(self):
        if self.version_info[0] == 2:
            return 3
        if self.version_info[0] == 1:
            if self.version_info[1] == 1:
                return 2
            return 1
        return 0
    
    def set_hatching_cycles(self, val=0):
        self.growth[9] = val
    
    def get_hatching_cycles(self):
        return self.growth[9]
    
    def set_pp(self, pos, val):
        self.attacks[8 + pos] = val
    
    def get_pp(self, pos):
        return self.attacks[8 + pos]
    
    def get_mon_index(self, ignore_egg=True):
        index = self.get_species()
        if not self.is_valid:
            return 0
        if not self.utils_class.is_species_valid(index, self.utils_class):
            self.is_valid = False
            return 0
        if (not ignore_egg) and self.get_is_egg():
            return self.egg_species
        if index == self.unown_species:
            letter = self.get_unown_letter()
            if letter == 0:
                return self.unown_species
            return self.unown_b_start+letter-1
        elif(index == self.deoxys_species):
            form = self.get_deoxys_form()
            if form == 0:
                return self.deoxys_species
            return self.deoxys_forms_start+form-1
        return index
    
    def set_exp(self, val):
        GSCUtilsMisc.write_int_le(self.growth, 4, val)
    
    def get_exp(self):
        return GSCUtilsMisc.read_int_le(self.growth, 4)
    
    def update_stats(self):
        """
        Updates the stats after they're changed (from evolving/changing level).
        """
        old_max_hps = self.get_max_hp()
        old_current_hps = self.get_curr_hp()
        for i in range(self.utils_class.num_stats):
            GSCUtilsMisc.write_short_le(self.values, self.stats_pos + (i * 2), self.utils_class.stat_calculation(i, self.get_mon_index(), self.get_ivs(), self.get_stat_exp(), self.get_level(), self.utils_class))
        new_max_hps = self.get_max_hp()
        old_current_hps += new_max_hps-old_max_hps
        GSCUtilsMisc.write_short_le(self.values, self.curr_hp_pos, min(max(0, old_current_hps), new_max_hps))
        
    def get_stat_exp(self):
        return self.evs[:6]

    def get_ivs(self):
        ret = [0,0,0,0,0,0]
        total_val = GSCUtilsMisc.read_int_le(self.misc, 4)
        for i in range(6):
            ret[i] = (total_val >> (5*i)) & 0x1F
        return ret

    def get_curr_hp(self):
        return GSCUtilsMisc.read_short_le(self.values, self.curr_hp_pos)

    def heal(self):
        GSCUtilsMisc.write_short_le(self.values, self.curr_hp_pos, self.get_max_hp())
        self.values[self.status_pos] = 0

    def faint(self):
        GSCUtilsMisc.write_short_le(self.values, self.curr_hp_pos, 0)
        self.values[self.status_pos] = 0
    
    def get_max_hp(self):
        return GSCUtilsMisc.read_short_le(self.values, self.stats_pos)
    
    def get_mail_id(self):
        return self.values[self.mail_info_pos]

    def has_mail(self):
        if self.utils_class.is_item_mail(self.get_item()):
            if self.get_mail_id() < 6:
                return True
        return False
    
    def is_equal(self, other, weak=False):
        """
        The protocol itself will figure this out.
        """
        return True
    
    def has_changed_significantly(self, raw):
        """
        Returns whether a pokémon has changed too much due to the sanity
        checks cleaning it.
        """
        if not self.is_valid:
            return True
        return False
        
    def add_mail_sender(self, data, start):
        pass

    def get_data(self):
        """
        Returns all the data used to represent this pokemon.
        """
        sources = [self, self.mail]
        data = [0] * self._precalced_lengths[len(sources)+1]
        if self.is_valid:
            for i in range(len(sources)):
                GSCUtilsMisc.copy_to_data(data, self._precalced_lengths[i], sources[i].values)
            GSCUtilsMisc.copy_to_data(data, self._precalced_lengths[len(sources)], self.version_info)
            GSCUtilsMisc.copy_to_data(data, self._precalced_lengths[len(sources)+1], self.ribbon_info)
        return data

    def set_data(data, is_encrypted=True):
        """
        Creates an entry from the given data.
        """
        mon = RSESPTradingPokémonInfo(data, 0, is_encrypted=is_encrypted)
        mon.add_mail(data, mon._precalced_lengths[1])
        mon.add_version_info(data, mon._precalced_lengths[2])
        mon.add_ribbon_info(data, mon._precalced_lengths[3])
        return mon
    
class RSESPTradingPartyInfo(GSCTradingPartyInfo):
    """
    Class which contains information about the party size and species
    from the trading data.
    """
    max_party_mons = 6
    
    def __init__(self, data, start):
        self.total = GSCUtilsMisc.read_int_le(data, start)
        if self.total <= 0 or self.total > self.max_party_mons:
            self.total = 1
    
    def get_id(self, pos):
        return None
    
    def set_id(self, pos, val):
        pass
    
    def get_total(self):
        return self.total
        
class RSESPTradingData(GSCTradingData):
    """
    Class which contains all the informations about a trader's party.
    """
    trader_name_pos = 0x353
    version_pos = 4
    game_id_pos = 0x344
    trader_info_pos = 0x378
    ribbon_info_pos = 0x348
    trading_party_info_pos = 0xE4
    trading_pokemon_pos = 0xE8
    trading_mail_pos = 8
    
    trading_party_max_size = 6
    trading_pokemon_length = 0x64
    trading_name_length = 8
    trading_mail_length = 0x24
    trading_version_info_length = 2
    
    def __init__(self, data_pokemon, data_mail=None, do_full=True):
        super(RSESPTradingData, self).__init__(data_pokemon, data_mail=None, do_full=False)
        if do_full:
            for i in range(self.get_party_size()):
                self.pokemon += [self.mon_generator(data_pokemon, self.trading_pokemon_pos + i * self.trading_pokemon_length)]
                if self.pokemon[i].has_mail():
                    self.pokemon[i].add_mail(data_pokemon, self.trading_mail_pos + self.pokemon[i].get_mail_id() * self.trading_mail_length)
                else:
                    self.pokemon[i].add_mail(self.get_empty_mail(), 0)
                self.pokemon[i].add_version_info(data_pokemon, self.game_id_pos + 1)
                self.pokemon[i].add_ribbon_info(data_pokemon, self.ribbon_info_pos)

    def are_checksum_valid(cls, buf, lengths):
        checksum = 0
        for i in range(cls.trading_party_max_size):
            for j in range(int(cls.trading_mail_length/4)):
                checksum = (checksum + GSCUtilsMisc.read_int_le(buf, (i*cls.trading_mail_length) + (j*4) + cls.trading_mail_pos)) & 0xFFFFFFFF
        
        if(GSCUtilsMisc.read_int_le(buf, cls.trading_mail_pos+(cls.trading_party_max_size*cls.trading_mail_length)) != checksum):
            return 0

        checksum = GSCUtilsMisc.read_int_le(buf, cls.trading_party_info_pos)
        
        for i in range(cls.trading_party_max_size):
            for j in range(int(cls.trading_pokemon_length/4)):
                checksum = (checksum + GSCUtilsMisc.read_int_le(buf, (i*cls.trading_pokemon_length) + (j*4) + cls.trading_pokemon_pos)) & 0xFFFFFFFF
        
        if(GSCUtilsMisc.read_int_le(buf, cls.trading_pokemon_pos+(cls.trading_party_max_size*cls.trading_pokemon_length)) != checksum):
            return 0
        
        checksum = 0;
        
        for i in range(int((lengths[0]-4)/4)):
            checksum = (checksum + GSCUtilsMisc.read_int_le(buf, i*4)) & 0xFFFFFFFF
        
        if(GSCUtilsMisc.read_int_le(buf, lengths[0]-4) != checksum):
            return 0
        
        return 1
    
    def get_empty_mail(self):
        return [0] * self.trading_mail_length
    
    def generate_checksum(cls, buf, lengths):
        checksum = 0
        for i in range(cls.trading_party_max_size):
            for j in range(int(cls.trading_mail_length/4)):
                checksum = (checksum + GSCUtilsMisc.read_int_le(buf, (i*cls.trading_mail_length) + (j*4) + cls.trading_mail_pos)) & 0xFFFFFFFF
        
        GSCUtilsMisc.write_int_le(buf, cls.trading_mail_pos+(cls.trading_party_max_size*cls.trading_mail_length), checksum)

        checksum = GSCUtilsMisc.read_int_le(buf, cls.trading_party_info_pos)
        
        for i in range(cls.trading_party_max_size):
            for j in range(int(cls.trading_pokemon_length/4)):
                checksum = (checksum + GSCUtilsMisc.read_int_le(buf, (i*cls.trading_pokemon_length) + (j*4) + cls.trading_pokemon_pos)) & 0xFFFFFFFF
        
        GSCUtilsMisc.write_int_le(buf, cls.trading_pokemon_pos+(cls.trading_party_max_size*cls.trading_pokemon_length), checksum)
        
        checksum = 0;
        
        for i in range(int((lengths[0]-4)/4)):
            checksum = (checksum + GSCUtilsMisc.read_int_le(buf, i*4)) & 0xFFFFFFFF
        
        GSCUtilsMisc.write_int_le(buf, lengths[0]-4, checksum)
    
    def party_generator(self, data, pos):
        return RSESPTradingPartyInfo(data, pos)
    
    def mon_generator_class(self):
        return RSESPTradingPokémonInfo
    
    def text_generator(self, data, pos, length=trading_name_length):
        return RSESPTradingText(data, pos, length=length)
    
    def trainer_info_generator(self, data, pos):
        return GSCUtilsMisc.read_int_le(data, pos)
    
    def get_utils_class(self):
        return RSESPUtils
    
    def search_for_mon(self, mon, is_egg):
        """
        Returns None if a provided pokémon is not in the party.
        Otherwise, it returns their index.
        """
        for i in range(self.get_party_size()):
            if mon.is_equal(self.pokemon[i]):
                return i
        for i in range(self.get_party_size()):
            if mon.is_equal(self.pokemon[i], weak=True):
                return i
        return None

    @GSCTradingData.check_pos_validity
    def is_mon_egg(self, pos):
        return False

    def party_has_mail(self):
        return False
        
    @GSCTradingData.check_pos_validity
    def evolve_mon(self, pos):
        """
        Handles evolving a pokémon in the party.
        Leave it to the homebrew.
        """
        return None

    def create_trading_data(self, lengths):
        """
        Creates the data which can be loaded to the hardware.
        """
        data = []
        for i in range(lengths[0]):
            data += [0]
        GSCUtilsMisc.copy_to_data(data, self.trader_name_pos, self.trader.values, self.trading_name_length)
        GSCUtilsMisc.write_int_le(data, self.trading_party_info_pos, self.get_party_size())
        for i in range(self.get_party_size()):
            mon_data = self.pokemon[i].get_data()
            GSCUtilsMisc.copy_to_data(data, self.trading_pokemon_pos + (i * self.trading_pokemon_length), mon_data[self.pokemon[i]._precalced_lengths[0]:self.pokemon[i]._precalced_lengths[1]])
            if self.pokemon[i].has_mail():
                GSCUtilsMisc.copy_to_data(data, self.trading_mail_pos + (self.pokemon[i].get_mail_id() * self.trading_mail_length), mon_data[self.pokemon[i]._precalced_lengths[1]:self.pokemon[i]._precalced_lengths[2]])
            if i == 0:
                GSCUtilsMisc.copy_to_data(data, self.game_id_pos + 1, mon_data[self.pokemon[i]._precalced_lengths[2]:self.pokemon[i]._precalced_lengths[3]])
                GSCUtilsMisc.copy_to_data(data, self.ribbon_info_pos, mon_data[self.pokemon[i]._precalced_lengths[3]:self.pokemon[i]._precalced_lengths[4]])
        type(self).generate_checksum(type(self), data, lengths)
        return [data]

class RSESPChecks(GSCChecks):
    """
    Class which handles sanity checks and cleaning of the received data.
    checks_map and single_pokemon_checks_map are its product used to apply
    the checks.
    """
    base_folder = "useful_data/rse/"
    rattata_id = 0xA5
    max_evs = 0xFFFF
    max_ivs = 0xF
    
    def __init__(self, section_sizes, do_sanity_checks):
        super(RSESPChecks, self).__init__(section_sizes, do_sanity_checks)
    
    def get_utils_class(self):
        return RSESPUtils
    
    @GSCChecks.clean_check_sanity_checks
    def clean_species(self, species):
        self.type_pos = 0
        val = super(RSESPChecks, self).clean_species(species)
        # In Gen 1 you get the current hp before the level and the
        # ivs/evs, so the best one can do is making sure
        # they don't go over the maximum possible value
        self.iv = [self.max_ivs,self.max_ivs,self.max_ivs,self.max_ivs]
        self.stat_exp = [self.max_evs,self.max_evs,self.max_evs,self.max_evs,self.max_evs]
        self.level = self.utils_class.max_level
        return val
    
    def is_egg(self):
        return False
    
    @GSCChecks.clean_check_sanity_checks
    def clean_species_sp(self, species):
        if species == self.free_value_species or self.species_list_size >= self.team_size:
            self.add_to_species_list(self.free_value_species)
            self.curr_species_pos += 1
            return self.free_value_species
        found_species = self.clean_value(species, self.is_species_valid, self.rattata_id)
        self.add_to_species_list(found_species)
        self.curr_species_pos += 1
        return found_species
    
    @GSCChecks.clean_check_sanity_checks
    def clean_item(self, item):
        return item
    
    @GSCChecks.clean_check_sanity_checks
    def clean_type(self, typing):
        ret = self.utils_class.types_list[self.curr_species][self.type_pos]
        self.type_pos += 1
        return ret
