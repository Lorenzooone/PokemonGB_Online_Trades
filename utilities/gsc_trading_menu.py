import threading
from random import Random
from .trading_version import TradingVersion
from .gsc_trading_strings import GSCTradingStrings
from argparse import ArgumentParser

class GSCTradingMenu:
    """
    Class used to handle the various possible menus.
    """
    default_server = ["pokemon-gb-online-trades.herokuapp.com", None]
    default_emulator = ["localhost", 8765]
    default_max_level = 100

    def __init__(self, kill_function, is_emulator=False):
        try:
            args = self.handle_args(is_emulator)
        except SystemExit as e:
            kill_function()
        
        # Initialize the menu
        self.server = [args.server_host, args.server_port]
        self.buffered = args.buffered
        self.japanese = args.japanese
        self.max_level = args.max_level
        self.egg = args.egg
        self.is_emulator = is_emulator
        self.multiboot = False
        if is_emulator:
            self.emulator = [args.emulator_host, args.emulator_port]
        self.do_sanity_checks = args.do_sanity_checks
        self.kill_on_byte_drops = args.kill_on_byte_drops
        self.verbose = args.verbose
        self.gen = args.gen_number
        self.trade_type = args.trade_type
        self.room = args.room
        self.toppest_menu_handlers = {
            "1": self.start_gen1_trading,
            "2": self.start_gen2_trading,
            "3": self.start_gen1_trading,
            "4": self.start_gen3_trading,
            "m": self.start_multiboot_gen3
            }
        self.top_menu_handlers = {
            "0": self.start_2p_trading,
            "1": self.start_2p_trading,
            "2": self.start_pool_trading,
            "3": self.handle_options
            }
        self.options_menu_handlers = {
            "0": self.handle_exit_option,
            "1": self.handle_server_option,
            "2": self.handle_port_option,
            "3": self.handle_japanese_option,
            "4": self.handle_sanity_option,
            "5": self.handle_verbose_option,
            "6": self.handle_buffered_option,
            "7": self.handle_kill_on_byte_drop_option,
            "8": self.handle_max_level_option,
            "9": self.handle_eggs_option
            }
        if is_emulator:
            self.options_menu_handlers["10"] = self.handle_emulator_host_option
            self.options_menu_handlers["11"] = self.handle_emulator_port_option

    def get_int(self, default_value):
        x = input()
        try:
            ret_val = int(x)
        except ValueError:
            ret_val = default_value
        return ret_val
    
    def handle_buffered_change_offer(self, buffered):
        decided = False
        while not decided:
            GSCTradingStrings.buffered_negotiation_print(buffered)
            x = input().lower()
            if x == "y" or x == "yes":
                buffered = not buffered
                decided = True
            elif x == "n" or x == "no":
                decided = True
        return buffered
    
    def handle_game_selector(self):
        if self.gen is None or ((self.gen != 1) and (self.gen != 2) and (self.gen != 3)):
            ret_val = None
            while ret_val is None:
                GSCTradingStrings.game_selector_menu_print()
                GSCTradingStrings.choice_print()
                ret_val = self.toppest_menu_handlers.get(input(), None)
                if ret_val is not None:
                    ret_val = ret_val()
    
    def handle_menu(self):
        GSCTradingStrings.version_print(TradingVersion.version_major, TradingVersion.version_minor, TradingVersion.version_build)
        if self.multiboot:
            self.start_pool_trading()
        elif self.trade_type is None or ((self.trade_type != GSCTradingStrings.two_player_trade_str) and (self.trade_type != GSCTradingStrings.pool_trade_str)):
            self.handle_game_selector()
            if not self.multiboot:
                ret_val = False
                while not ret_val:
                    GSCTradingStrings.top_menu_print()
                    GSCTradingStrings.choice_print()
                    ret_val = self.top_menu_handlers.get(input(), self.top_menu_handlers["0"])()
        else:
            if self.trade_type == GSCTradingStrings.two_player_trade_str:
                self.start_2p_trading()
            elif self.trade_type == GSCTradingStrings.pool_trade_str:
                self.start_pool_trading()
    
    def get_default_room(self):
        r = Random()
        return r.randint(0,99999)
    
    def start_2p_trading(self):
        self.trade_type = GSCTradingStrings.two_player_trade_str
        if self.room is None:
            self.room = self.get_default_room()
            GSCTradingStrings.change_room_print(self.room)
            self.room = self.get_int(self.room)
        return True
    
    def start_pool_trading(self):
        self.trade_type = GSCTradingStrings.pool_trade_str
        return True
    
    def start_gen1_trading(self):
        self.gen = 1
        return True
    
    def start_gen2_trading(self):
        self.gen = 2
        return True
    
    def start_gen3_trading(self):
        self.gen = 3
        return True
    
    def start_multiboot_gen3(self):
        self.gen = 3
        self.multiboot = True
        return True
    
    def handle_options(self):
        ret_val = False
        while not ret_val:
            GSCTradingStrings.options_menu_print(self)
            GSCTradingStrings.choice_print()
            ret_val = self.options_menu_handlers.get(input(), self.options_menu_handlers["0"])()
        return False
    
    def handle_exit_option(self):
        return True
    
    def handle_server_option(self):
        GSCTradingStrings.change_server_print()
        self.server[0] = input()
        return False
    
    def handle_port_option(self):
        GSCTradingStrings.change_port_print()
        self.server[1] = self.get_int(self.server[1])
        return False
    
    def handle_emulator_host_option(self):
        GSCTradingStrings.change_emu_server_print()
        self.emulator[0] = input()
        return False
    
    def handle_emulator_port_option(self):
        GSCTradingStrings.change_emu_port_print()
        self.emulator[1] = self.get_int(self.emulator[1])
        return False
    
    def handle_buffered_option(self):
        self.buffered = not self.buffered
        return False
    
    def handle_max_level_option(self):
        GSCTradingStrings.change_max_level_print(self.max_level)
        self.max_level = self.get_int(self.max_level)
        if self.max_level < 2:
            self.max_level = 2
        if self.max_level > 100:
            self.max_level = 100
        return False
    
    def handle_eggs_option(self):
        self.egg = not self.egg
        return False
    
    def handle_japanese_option(self):
        self.japanese = not self.japanese
        return False
    
    def handle_sanity_option(self):
        self.do_sanity_checks = not self.do_sanity_checks
        return False
    
    def handle_kill_on_byte_drop_option(self):
        self.kill_on_byte_drops = not self.kill_on_byte_drops
        return False
    
    def handle_verbose_option(self):
        self.verbose = not self.verbose
        return False
    
    def handle_args(self, is_emulator):
        # Parse program's arguments
        parser = ArgumentParser()
        parser.add_argument("-g", "--generation", dest="gen_number", default = None,
                            help="generation (1 = RBY/Timecapsule, 2 = GSC, 3 = RSE Special)", type=int)
        parser.add_argument("-t", "--trade_type", dest="trade_type", default = None,
                            help="trade type (" + GSCTradingStrings.two_player_trade_str + " = 2-Player Trade, " + GSCTradingStrings.pool_trade_str + " = Pool Trade)")
        parser.add_argument("-r", "--room", dest="room", default = None,
                            help="2-Player Trade's room", type=int)
        parser.add_argument("-b", "--buffered",
                            action="store_true", dest="buffered", default=False,
                            help="default to buffered trading instead of synchronous")
        parser.add_argument("-j", "--japanese",
                            action="store_true", dest="japanese", default=False,
                            help="use it if your game is Japanese")
        parser.add_argument("-dsc", "--disable_sanity_checks",
                            action="store_false", dest="do_sanity_checks", default=True,
                            help="don't perform sanity checks for data sent to the device")
        parser.add_argument("-dkb", "--disable_kill_drops",
                            action="store_false", dest="kill_on_byte_drops", default=True,
                            help="don't kill the process for dropped bytes")
        parser.add_argument("-mlp", "--max_level_pool", dest="max_level", default = self.default_max_level,
                            help="Pool's max level", type=int)
        parser.add_argument("-egp", "--eggify_pool",
                            action="store_true", dest="egg", default=False,
                            help="turns Pool Pokémon into ready-to-hatch eggs")
        parser.add_argument("-q", "--quiet",
                            action="store_false", dest="verbose", default=True,
                            help="don't print status messages to stdout")
        parser.add_argument("-sh", "--server_host", dest="server_host", default = self.default_server[0],
                            help="server's host")
        parser.add_argument("-sp", "--server_port", dest="server_port", default = self.default_server[1],
                            help="server's port", type=int)
        if is_emulator:
            parser.add_argument("-eh", "--emulator_host", dest="emulator_host", default = self.default_emulator[0],
                                help="emulator's local host")
            parser.add_argument("-ep", "--emulator_port", dest="emulator_port", default = self.default_emulator[1],
                                help="emulator's local port", type=int)
        return parser.parse_args()

class GSCBufferedNegotiator(threading.Thread):
    """
    Class used to handle the negotiation when the two clients'
    buffered variable doesn't match up
    """

    def __init__(self, menu, comms, buffered, sleep_func):
        threading.Thread.__init__(self)
        self.daemon=True
        self.comms = comms
        self.menu = menu
        self.final_buffered = None
        self.buffered = buffered
        self.sleep_func = sleep_func
    
    def force_receive(self, fun):
        received = None
        while received is None:
            self.sleep_func()
            received = fun()
        return received
        
    def choose_if_buffered(self):
        buffered = self.buffered
        self.comms.send_buffered_data(buffered)
        other_buffered = self.force_receive(self.comms.get_buffered_data)
        if buffered == other_buffered:
            return buffered
        change_buffered = None
        while change_buffered is None:
            own_val = self.comms.send_negotiation_data()
            other_val = self.force_receive(self.comms.get_negotiation_data)
            if other_val > own_val:
                change_buffered = True
            elif other_val < own_val:
                change_buffered = False
        while buffered != other_buffered:
            if not change_buffered:
                GSCTradingStrings.buffered_other_negotiation_print(buffered)
                other_buffered = self.force_receive(self.comms.get_buffered_data)
            else:
                buffered = self.menu.handle_buffered_change_offer(buffered)
                self.comms.send_buffered_data(buffered)
            change_buffered = not change_buffered
        return buffered
    
    def get_chosen_buffered(self):
        return self.final_buffered

    def run(self):
        self.final_buffered = self.choose_if_buffered()
        if self.menu.verbose:
            GSCTradingStrings.chosen_buffered_print(self.final_buffered)
