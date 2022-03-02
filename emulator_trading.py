#!/usr/bin/python3
from bgb_link_cable_server import BGBLinkCableServer
from time import sleep
from gsc_trading import GSCTrading

class PokeTrader:
    SLEEP_TIMER = 0.001
    _server = None
    curr_recv = None

    def __init__(self):
        PokeTrader.curr_recv = None
        PokeTrader._server = BGBLinkCableServer(self.update_data, verbose=False, )

    def run(self):
        PokeTrader._server.start()
        
    def update_data(self, data):
        PokeTrader.curr_recv = data

    # Code dependant on this connection method
    def sendByte(self, byte_to_send):
        PokeTrader._server.to_send = byte_to_send
        while PokeTrader._server.to_send is not None:
            sleep(PokeTrader.SLEEP_TIMER)
        return

    def receiveByte(self):
        while PokeTrader.curr_recv is None:
            sleep(PokeTrader.SLEEP_TIMER)
        recv = PokeTrader.curr_recv
        PokeTrader.curr_recv = None
        return recv


def transfer_func(p):
    print("Waiting for the transfer to start...")
    
    trade_c = GSCTrading(p.sendByte, p.receiveByte, target_other = "usb.bin", target_self = "emu.bin")
    res = trade_c.trade() # Read the starting information
    
    return

p = PokeTrader()
p.run()
transfer_func(p)