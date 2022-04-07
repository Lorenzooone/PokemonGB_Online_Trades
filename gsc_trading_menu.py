import threading
from random import Random

class GSCTradingMenu:
    default_server = ["localhost", 11111]
    default_emulator = ["localhost", 8765]
    two_player_trade_str = "2P"
    pool_trade_str = "PS"

    def __init__(self, server_host=default_server[0], server_port=default_server[1], buffered=False, is_emulator=False, do_sanity_checks=True, kill_on_byte_drops=True, emulator_host=default_emulator[0], emulator_port=default_emulator[1], verbose=True):
        self.server = [server_host, server_port]
        self.buffered = buffered
        self.is_emulator = is_emulator
        self.emulator = [emulator_host, emulator_port]
        self.do_sanity_checks = do_sanity_checks
        self.kill_on_byte_drops = kill_on_byte_drops
        self.verbose = verbose
        self.trade_type = None
        self.room = self.get_default_room()
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
            "3": self.handle_sanity_option,
            "4": self.handle_verbose_option,
            "5": self.handle_buffered_option,
            "6": self.handle_kill_on_byte_drop_option
            }
        if is_emulator:
            self.options_menu_handlers["7"] = self.handle_emulator_host_option
            self.options_menu_handlers["8"] = self.handle_emulator_port_option
    
    def get_buffered_str(self, buffered):
        str_type_of_trade = "Buffered"
        if not buffered:
            str_type_of_trade = "Synchronous"
        return str_type_of_trade
    
    def buffered_negotiation_print(self, buffered):
        print("\nThe other player wants to do a " + self.get_buffered_str(not buffered) + " trade.\nWould you like to switch to a " + self.get_buffered_str(not buffered) + " trade?")
        print("Choice (y = Yes, n=No): ", end = '')
    
    def chosen_buffered_print(self, buffered):
        print("\nDecided to do a " + self.get_buffered_str(buffered) + " trade.")
            
    def top_menu_print(self):
        print("\n=============== Top level Menu ===============")
        print("1) Start 2-Player trade (Default)")
        print("2) Start Pool trade")
        print("3) Options")
    
    def options_menu_print(self):
        print("\n=============== General Options ===============")
        print("0) Exit (Default)")
        print("1) Server for connection: " + self.server[0])
        print("2) Port for connection: " + str(self.server[1]))
        if self.do_sanity_checks:
            print("3) Disable Sanity checks (Current: Enabled)")
        else:
            print("3) Enable Sanity checks (Current: Disabled)")
        print("4) Change Verbosity (Current: " + str(self.verbose) + ")")
        
        print("\n=============== 2-Player trade Options ===============")
        print("5) Change to " + self.get_buffered_str(not self.buffered) + " Trading (Current: " + self.get_buffered_str(self.buffered) + ")")
        if self.kill_on_byte_drops:
            print("6) Disable Crash on synchronous byte drop (Current: Enabled)")
        else:
            print("6) Enable Crash on synchronous byte drop (Current: Disabled)")

        if self.is_emulator:
            print("\n=============== Emulator Options ===============")
            print("7) Host for emulator connection: " + self.emulator[0])
            print("8) Port for emulator connection: " + str(self.emulator[1]))

    def get_int(self, default_value):
        x = input()
        try:
            ret_val = int(x)
        except ValueError:
            ret_val = default_value
        return ret_val

    def choice_print(self):
        print("\nInput the action's number: ", end='')
    
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
    
    def handle_buffered_change_offer(self, buffered):
        decided = False
        while not decided:
            self.buffered_negotiation_print(buffered)
            x = input().lower()
            if x == "y" or x == "yes":
                buffered = not buffered
                decided = True
            elif x == "n" or x == "no":
                decided = True
        return buffered
    
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
    
    def handle_kill_on_byte_drop_option(self):
        self.kill_on_byte_drops = not self.kill_on_byte_drops
        return False
    
    def handle_verbose_option(self):
        self.verbose = not self.verbose
        return False

class GSCBufferedNegotiator(threading.Thread):

    def __init__(self, menu, comms, buffered, sleep_func):
        threading.Thread.__init__(self)
        self.setDaemon(True)
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
            self.menu.chosen_buffered_print(self.final_buffered)