#!/usr/bin/python3
import signal
import os
from utilities.bgb_link_cable_server import BGBLinkCableServer
from utilities.websocket_client import PoolTradeRunner, ProxyConnectionRunner
from time import sleep
from utilities.gsc_trading import GSCTrading
from utilities.gsc_trading_jp import GSCTradingJP
from utilities.rby_trading import RBYTrading
from utilities.rby_trading_jp import RBYTradingJP
from utilities.gsc_trading_menu import GSCTradingMenu
from utilities.gsc_trading_strings import GSCTradingStrings

class PokeTrader:
    SLEEP_TIMER = 0.001

    def __init__(self, menu):
        self.curr_recv = None
        self._server = BGBLinkCableServer(self.update_data, menu, kill_function)
        if menu.trade_type == GSCTradingStrings.two_player_trade_str:
            self.connection = ProxyConnectionRunner(menu, kill_function)
        elif menu.trade_type == GSCTradingStrings.pool_trade_str:
            self.connection = PoolTradeRunner(menu, kill_function)

    def run(self):
        self._server.start()
        self.connection.start()
        
    def update_data(self, data):
        self.curr_recv = data

    # Code dependant on this connection method
    def sendByte(self, byte_to_send):
        self._server.to_send = byte_to_send
        while self._server.to_send is not None:
            sleep(self.SLEEP_TIMER)
        return

    def receiveByte(self):
        while self.curr_recv is None:
            sleep(self.SLEEP_TIMER)
        recv = self.curr_recv
        self.curr_recv = None
        return recv

def kill_function():
    os.kill(os.getpid(), signal.SIGINT)

def exit_gracefully():
    os._exit(1)

def signal_handler(sig, frame):
    print(GSCTradingStrings.crtlc_str)
    exit_gracefully()

signal.signal(signal.SIGINT, signal_handler)

def transfer_func(p, menu):
    if menu.verbose:
        print(GSCTradingStrings.waiting_transfer_start_str)
    
    if menu.gen == 2:
        if menu.japanese:
            trade_c = GSCTradingJP(p.sendByte, p.receiveByte, p.connection, menu, kill_function)
        else:
            trade_c = GSCTrading(p.sendByte, p.receiveByte, p.connection, menu, kill_function)
    elif menu.gen == 1:
        if menu.japanese:
            trade_c = RBYTradingJP(p.sendByte, p.receiveByte, p.connection, menu, kill_function)
        else:
            trade_c = RBYTrading(p.sendByte, p.receiveByte, p.connection, menu, kill_function)
    
    if menu.trade_type == GSCTradingStrings.two_player_trade_str:
        trade_c.player_trade(menu.buffered)
    elif menu.trade_type == GSCTradingStrings.pool_trade_str:
        trade_c.pool_trade()

menu = GSCTradingMenu(kill_function, is_emulator=True)
menu.handle_menu()
p = PokeTrader(menu)
p.run()
transfer_func(p, menu)