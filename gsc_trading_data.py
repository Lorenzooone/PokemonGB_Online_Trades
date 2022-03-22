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

class GSCAuxData:
    bad_ids_items_path = "useful_data/bad_ids_items.bin"
    bad_ids_moves_path = "useful_data/bad_ids_moves.bin"
    bad_ids_pokemon_path = "useful_data/bad_ids_pokemon.bin"
    bad_ids_text_path = "useful_data/bad_ids_text.bin"
    evolution_ids_path = "useful_data/evolution_ids.bin"
    mail_ids_path = "useful_data/ids_mail.bin"
    
    def __init__(self):
        self.bad_ids_items = self.prepare_check_list(self.read_data(self.bad_ids_items_path))
        self.bad_ids_moves = self.prepare_check_list(self.read_data(self.bad_ids_moves_path))
        self.bad_ids_pokemon = self.prepare_check_list(self.read_data(self.bad_ids_pokemon_path))
        self.bad_ids_text = self.prepare_check_list(self.read_data(self.bad_ids_text_path))
        self.mail_ids = self.prepare_check_list(self.read_data(self.mail_ids_path))
        self.evolution_ids = self.prepare_evolution_check_list(self.read_data(self.evolution_ids_path))

    def prepare_check_list(self, data):
        ret = [False] * 0x100
        if data is not None:
            for i in data:
                ret[i] = True
        return ret
    
    def prepare_evolution_check_list(self, data):
        ret = [(False, None)] * 0x100
        
        if data is not None:
            data_len = int(len(data)/2)
            for i in range(data_len):
                ret[data[i]] = (True, None)
                if data[i + data_len] != 0:
                    ret[data[i]] = (True, data[i + data_len])
        return ret

    def read_data(self, target):
        data = None
        try:
            with open(target, 'rb') as newFile:
                tmpdata = list(newFile.read())
                data = tmpdata
        except FileNotFoundError as e:
            pass
        return data