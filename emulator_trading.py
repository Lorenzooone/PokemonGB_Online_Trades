#!/usr/bin/python3
import signal
import os
from bgb_link_cable_server import BGBLinkCableServer
from p2p_connection import P2PConnection
from time import sleep
from gsc_trading import GSCTrading
from gsc_trading_menu import GSCTradingMenu

class PokeTrader:
    SLEEP_TIMER = 0.001

    def __init__(self, menu):
        self.curr_recv = None
        self._server = BGBLinkCableServer(self.update_data, menu, kill_function)
        self._p2p_conn = P2PConnection(menu, kill_function)

    def run(self):
        self._server.start()
        self._p2p_conn.start()
        
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
    print('You pressed Ctrl+C!')
    exit_gracefully()

signal.signal(signal.SIGINT, signal_handler)

def transfer_func(p, menu):
    if menu.verbose:
        print("Waiting for the transfer to start...")
    
    trade_c = GSCTrading(p.sendByte, p.receiveByte, p._p2p_conn, menu)
    res = trade_c.player_trade(menu.buffered) # Read the starting information
    
    return

menu = GSCTradingMenu(is_emulator=True)
menu.handle_menu()
p = PokeTrader(menu)
p.run()
transfer_func(p, menu)