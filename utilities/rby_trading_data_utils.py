from .gsc_trading_data_utils import GSCUtils, GSCTradingText, GSCTradingPokémonInfo, GSCTradingData, GSCChecks, GSCUtilsMisc

class RBYUtilsLoaders:
    """
    Class which contains methods used to load structures from
    binary or text files.
    """

    def prepare_types(data):
        ret = [0] * 0x100
        for i in range(0x100):
            ret[i] = data[(i)*2:(i+1)*2]
        return ret

class RBYUtils(GSCUtils):
    """
    Class which contains generic methods and data used for
    pokémon-related functions.
    """
    base_folder = "useful_data/rby/"
    types_list_path = "types.bin"
    stat_id_base_conv_table = [0,1,2,3,4]
    stat_id_iv_conv_table = [0,0,1,2,3]
    stat_id_exp_conv_table = [0,1,2,3,4]
    patch_set_base_pos = [0x13]
    patch_set_start_info_pos = [7]
    num_stats = 5
    
    types_list = None
    
    def __init__(self):
        super(RBYUtils, self).__init__()
        curr_class = type(self)
        curr_class.types_list = RBYUtilsLoaders.prepare_types(GSCUtilsMisc.read_data(self.get_path(curr_class.types_list_path)))
        
    def is_item_mail(item):
        return False
    
    def is_evolving(species, item):
        if species >= 0x100 or species < 0:
            return False
        evo_info = RBYUtils.evolution_ids[species]
        if evo_info[0]:
            return True
        return False
    
    def get_evolution(species, item):
        if not RBYUtils.is_evolving(species, item):
            return None
        if item == RBYUtils.everstone_id:
            return species
        return RBYUtils.evolution_ids[species][2]
    
    def get_evolution_item(species):
        return None
    
    def get_patch_set_num_index(is_mail, is_japanese):
        patch_sets_num = 2
        patch_sets_index = 0
        return patch_sets_num, patch_sets_index
    
    def single_mon_from_data(checks, data):
        ret = None
        
        # Prepare sanity checks stuff
        checks.reset_species_item_list()
        checks.set_single_team_size()
        checks.prepare_text_buffer()
        checks.prepare_patch_sets_buffer()
        checks.prepare_species_buffer()
        checker = checks.single_pokemon_checks_map
        
        if len(data) >= len(checker):
            # Applies the checks to the received data.
            # If the sanity checks are off, this will be a simple copy
            checks.species_cleaner(data[0])
            checks.prepare_species_buffer()
            purified_data = checks.apply_checks_to_data(checker, data)
                
            # Prepares the pokémon data. For both the cleaned one and
            # the raw one
            raw = RBYTradingPokémonInfo.set_data(data)
            mon = RBYTradingPokémonInfo.set_data(purified_data)
            
            # If the sanity checks are on, has the pokémon changed
            # too much from the cleaning?
            if not mon.has_changed_significantly(raw):
                ret = [mon, False]
        return ret
    
    def single_mon_to_data(mon, is_egg):
        return mon.get_data()

class RBYTradingText(GSCTradingText):
    """
    Class which contains a text entry from the trading data.
    """
    
    def __init__(self, data, start, length=0xB, data_start=0):
        super(RBYTradingText, self).__init__(data, start, length=length, data_start=data_start)
    
    def get_utils_class(self):
        return RBYUtils
        
class RBYTradingPokémonInfo(GSCTradingPokémonInfo):
    """
    Class which contains information about the pokémon from the trading data.
    """
    pokemon_data_len = 0x2C
    ot_name_len = 0xB
    nickname_len = 0xB
    mail_len = 0
    sender_len = 0
    
    item_pos = 7
    moves_pos = 8
    pps_pos = 0x1D
    level_pos = 0x21
    exp_pos = 0xE
    curr_hp_pos = 1
    stats_pos = 0x22
    evs_pos = 0x11
    ivs_pos = 0x1B
    status_pos = 4
    
    no_moves_equality_ranges = [range(0,3), range(4,8), range(0xC,0x1D), range(0x21, pokemon_data_len)]
    all_lengths = [pokemon_data_len, ot_name_len, nickname_len, mail_len, sender_len]
    
    def __init__(self, data, start, length=pokemon_data_len):
        super(RBYTradingPokémonInfo, self).__init__(data, start, length=length)
    
    def get_utils_class(self):
        return RBYUtils

    def add_ot_name(self, data, start):
        self.ot_name = RBYTradingText(data, start, length=self.ot_name_len)

    def add_nickname(self, data, start):
        self.nickname = RBYTradingText(data, start, length=self.nickname_len)
    
    def set_hatching_cycles(self, val=1):
        pass
    
    def get_hatching_cycles(self):
        return 0xFF

    def add_mail(self, data, start):
        pass
        
    def add_mail_sender(self, data, start):
        pass
    
    def has_mail(self):
        return False

    def set_data(data):
        """
        Creates an entry from the given data.
        """
        mon = RBYTradingPokémonInfo(data, 0)
        mon.add_ot_name(data, mon._precalced_lengths[1])
        mon.add_nickname(data, mon._precalced_lengths[2])
        return mon
        
class RBYTradingData(GSCTradingData):
    """
    Class which contains all the informations about a trader's party.
    """
    trader_name_pos = 0
    trading_party_info_pos = 0xB
    trading_pokemon_pos = 0x13
    trading_pokemon_ot_pos = 0x11B
    trading_pokemon_nickname_pos = 0x15D
    
    trading_pokemon_length = 0x2C
    trading_name_length = 0xB
    trading_mail_length = 0
    trading_mail_sender_length = 0
    
    def __init__(self, data_pokemon, data_mail=None, do_full=True):
        super(RBYTradingData, self).__init__(data_pokemon, data_mail=None, do_full=do_full)
    
    def mon_generator_class(self):
        return RBYTradingPokémonInfo
    
    def text_generator(self, data, pos, length=trading_name_length):
        return RBYTradingText(data, pos, length=length)
    
    def trainer_info_generator(self, data, pos):
        return None
    
    def get_utils_class(self):
        return RBYUtils
    
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
        Returns None if it won't evolve.
        Returns True if it evolved and player input is required.
        Returns False if it evolved and no player input is required.
        """
        evolution = self.utils_class.get_evolution(self.pokemon[pos].get_species(), self.pokemon[pos].get_item())
        if evolution is None:
            return None
        # In Gen 1 to Gen 2, the everstone works only one way!
        if evolution == self.pokemon[pos].get_species():
            return True
        self.evolution_procedure(pos, evolution)
        curr_learning = self.pokemon[pos].learnable_moves()
        # Gen 1 to Gen 2 doesn't allow us to predict which moves will be taught!
        # It may even glitch out!
        if curr_learning is not None:
            return True
        return False

    def create_trading_data(self, lengths):
        """
        Creates the data which can be loaded to the hardware.
        """
        data = []
        for i in range(3):
            data += [lengths[i]*[0]]
        GSCUtilsMisc.copy_to_data(data[1], self.trader_name_pos, self.trader.values, self.trading_name_length)
        data[1][self.trading_party_info_pos] = self.get_party_size()
        GSCUtilsMisc.copy_to_data(data[1], self.trading_party_info_pos + 1, self.party_info.actual_mons)
        data[1][self.trading_party_final_pos] = 0xFF
        for i in range(self.get_party_size()):
            GSCUtilsMisc.copy_to_data(data[1], self.trading_pokemon_pos + (i * self.trading_pokemon_length), self.pokemon[i].values)
            GSCUtilsMisc.copy_to_data(data[1], self.trading_pokemon_ot_pos + (i * self.trading_name_length), self.pokemon[i].ot_name.values, self.trading_name_length)
            GSCUtilsMisc.copy_to_data(data[1], self.trading_pokemon_nickname_pos + (i * self.trading_name_length), self.pokemon[i].nickname.values, self.trading_name_length)
        self.utils_class.create_patches_data(data[1], data[2], self.utils_class)
        return data

class RBYChecks(GSCChecks):
    """
    Class which handles sanity checks and cleaning of the received data.
    checks_map and single_pokemon_checks_map are its product used to apply
    the checks.
    """
    base_folder = "useful_data/rby/"
    rattata_id = 0xA5
    max_evs = 0xFFFF
    max_ivs = 0xF
    
    def __init__(self, section_sizes, do_sanity_checks):
        super(RBYChecks, self).__init__(section_sizes, do_sanity_checks)
    
    def get_utils_class(self):
        return RBYUtils
    
    @GSCChecks.clean_check_sanity_checks
    def clean_species(self, species):
        self.type_pos = 0
        val = super(RBYChecks, self).clean_species(species)
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
