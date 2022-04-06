from random import Random

class GSCTradingMenu:
    default_server = ["localhost", 11111]
    default_emulator = ["localhost", 8765]
    two_player_trade_str = "2P"
    pool_trade_str = "PS"

    def __init__(self, server_host=default_server[0], server_port=default_server[1], buffered=False, is_emulator=False, do_sanity_checks=True, emulator_host=default_emulator[0], emulator_port=default_emulator[1], verbose=True):
        self.server = [server_host, server_port]
        self.buffered = buffered
        self.is_emulator = is_emulator
        self.emulator = [emulator_host, emulator_port]
        self.do_sanity_checks = do_sanity_checks
        self.verbose = verbose
        self.trade_type = None
        self.room = self.get_default_room()
        self.top_menu_handlers = {"0": self.start_2p_trading, "1": self.start_2p_trading, "2": self.start_pool_trading, "3": self.handle_options}
        self.options_menu_handlers = {"0": self.handle_exit_option, "1": self.handle_server_option, "2": self.handle_port_option, "3": self.handle_buffered_option, "4": self.handle_sanity_option, "5": self.handle_verbose_option}
        if is_emulator:
            self.options_menu_handlers["6"] = self.handle_emulator_host_option
            self.options_menu_handlers["7"] = self.handle_emulator_port_option
            
    def top_menu_print(self):
        print("1) Start 2-Player trade (Default)")
        print("2) Start Pool trade")
        print("3) Options")
    
    def options_menu_print(self):
        print("1) Server for connection: " + self.server[0])
        print("2) Port for connection: " + str(self.server[1]))
        if self.buffered:
            print("3) Change to Synchronous Trading (Current: Buffered)")
        else:
            print("3) Change to Buffered Trading (Current: Synchronous)")
        if self.do_sanity_checks:
            print("4) Disable Sanity checks (Current: Enabled)")
        else:
            print("4) Enable Sanity checks (Current: Disabled)")
        print("5) Change Verbosity (Current: " + str(self.verbose) + ")")
        if self.is_emulator:
            print("6) Host for emulator connection: " + self.emulator[0])
            print("7) Port for emulator connection: " + str(self.emulator[1]))
        print("0) Exit (Default)")

    def get_int(self, default_value):
        x = input()
        try:
            ret_val = int(x)
        except ValueError:
            ret_val = default_value
        return ret_val

    def choice_print(self):
        print("Input the action's number: ", end='')
    
    def change_server_print(self):
        print("Server: ", end='')
    
    def change_port_print(self):
        print("Port: ", end='')
    
    def change_room_print(self):
        print("Room (Default = " + str(self.room) + "): ", end='')
    
    def change_emu_server_print(self):
        print("Emulator's host: ", end='')
    
    def change_emu_port_print(self):
        print("Emulator's port: ", end='')
    
    def handle_menu(self):
        ret_val = False
        while not ret_val:
            self.top_menu_print()
            self.choice_print()
            ret_val = self.top_menu_handlers.get(input(), self.top_menu_handlers["0"])()
    
    def get_default_room(self):
        r = Random()
        return r.randint(0,99999)
    
    def start_2p_trading(self):
        self.trade_type = GSCTradingMenu.two_player_trade_str
        self.change_room_print()
        self.room = self.get_int(self.room)
        return True
    
    def start_pool_trading(self):
        self.trade_type = GSCTradingMenu.pool_trade_str
        return True
    
    def handle_options(self):
        ret_val = False
        while not ret_val:
            self.options_menu_print()
            self.choice_print()
            ret_val = self.options_menu_handlers.get(input(), self.options_menu_handlers["0"])()
        return False
    
    def handle_exit_option(self):
        return True
    
    def handle_server_option(self):
        self.change_server_print()
        self.server[0] = input()
        return False
    
    def handle_port_option(self):
        self.change_port_print()
        self.server[1] = self.get_int(self.server[1])
        return False
    
    def handle_emulator_host_option(self):
        self.change_emu_server_print()
        self.emulator[0] = input()
        return False
    
    def handle_emulator_port_option(self):
        self.change_emu_port_print()
        self.emulator[1] = self.get_int(self.emulator[1])
        return False
    
    def handle_buffered_option(self):
        self.buffered = not self.buffered
        return False
    
    def handle_sanity_option(self):
        self.do_sanity_checks = not self.do_sanity_checks
        return False
    
    def handle_verbose_option(self):
        self.verbose = not self.verbose
        return False