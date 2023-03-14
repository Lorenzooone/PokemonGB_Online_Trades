import usb.core
import usb.util
import signal
import sys
import traceback
import time
import os
from utilities.gsc_trading import GSCTrading
from utilities.gsc_trading_jp import GSCTradingJP
from utilities.rby_trading import RBYTrading
from utilities.rby_trading_jp import RBYTradingJP
from utilities.rse_sp_trading import RSESPTrading
from utilities.websocket_client import PoolTradeRunner, ProxyConnectionRunner
from utilities.gsc_trading_menu import GSCTradingMenu
from utilities.gsc_trading_strings import GSCTradingStrings

dev = None

def transfer_func(sender, receiver):
    menu = GSCTradingMenu(kill_function)
    menu.handle_menu()
    
    if menu.verbose:
        print(GSCTradingStrings.waiting_transfer_start_str)
        
    if menu.trade_type == GSCTradingStrings.two_player_trade_str:
        connection = ProxyConnectionRunner(menu, kill_function)
    elif menu.trade_type == GSCTradingStrings.pool_trade_str:
        connection = PoolTradeRunner(menu, kill_function)
        
    if menu.gen == 2:
        if menu.japanese:
            trade_c = GSCTradingJP(sender, receiver, connection, menu, kill_function)
        else:
            trade_c = GSCTrading(sender, receiver, connection, menu, kill_function)  
    elif menu.gen == 3:
        trade_c = RSESPTrading(sender, receiver, connection, menu, kill_function)
    elif menu.gen == 1:
        if menu.japanese:
            trade_c = RBYTradingJP(sender, receiver, connection, menu, kill_function)
        else:
            trade_c = RBYTrading(sender, receiver, connection, menu, kill_function)
    connection.start()
    
    if menu.trade_type == GSCTradingStrings.two_player_trade_str:
        trade_c.player_trade(menu.buffered)
    elif menu.trade_type == GSCTradingStrings.pool_trade_str:
        trade_c.pool_trade()

# Code dependant on this connection method
def sendByte(byte_to_send, num_bytes):
    epOut.write(byte_to_send.to_bytes(num_bytes, byteorder='big'))
    return

def receiveByte(num_bytes):
    recv = int.from_bytes(epIn.read(epIn.wMaxPacketSize, 100), byteorder='big')
    return recv

# Code dependant on this connection method
def sendByte_win(byte_to_send, num_bytes):
    p.write(byte_to_send.to_bytes(num_bytes, byteorder='big'))

def receiveByte_win(num_bytes):
    recv = int.from_bytes(p.read(size=1), byteorder='big')
    return recv

def kill_function():
    os.kill(os.getpid(), signal.SIGINT)

# Things for the USB connection part
def exit_gracefully():
    if dev is not None:
        usb.util.dispose_resources(dev)
        if(os.name != "nt"):
            if reattach:
                dev.attach_kernel_driver(0)
    os._exit(1)

def signal_handler(sig, frame):
    print(GSCTradingStrings.crtlc_str)
    exit_gracefully()

signal.signal(signal.SIGINT, signal_handler)

# The execution path
try:
    try:
        devices = list(usb.core.find(find_all=True,idVendor=0xcafe, idProduct=0x4011))
        for d in devices:
            #print('Device: %s' % d.product)
            dev = d
    except usb.core.NoBackendError as e:
        pass
        
    sender = sendByte
    receiver = receiveByte

    if dev is None:
        if(os.name == "nt"):
            from winusbcdc import ComPort
            print("Trying WinUSB CDC")
            p = ComPort(vid=0xcafe, pid=0x4011)
            if not p.is_open:
                exit_gracefully()
            #p.baudrate = 115200
            sender = sendByte_win
            receiver = receiveByte_win    
    else:
        reattach = False
        if(os.name != "nt"):
            if dev.is_kernel_driver_active(0):
                try:
                    reattach = True
                    dev.detach_kernel_driver(0)
                    print("kernel driver detached")
                except usb.core.USBError as e:
                    sys.exit("Could not detach kernel driver: %s" % str(e))
            else:
                print("no kernel driver attached")

        dev.reset()

        dev.set_configuration()

        cfg = dev.get_active_configuration()

        #print('Configuration: %s' % cfg)

        intf = cfg[(2,0)]   # Or find interface with class 0xff

        #print('Interface: %s' % intf)

        epIn = usb.util.find_descriptor(
            intf,
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_IN)

        assert epIn is not None

        #print('EP In: %s' % epIn)

        epOut = usb.util.find_descriptor(
            intf,
            # match the first OUT endpoint
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)

        assert epOut is not None

        #print('EP Out: %s' % epOut)

        # Control transfer to enable webserial on device
        #print("control transfer out...")
        dev.ctrl_transfer(bmRequestType = 1, bRequest = 0x22, wIndex = 2, wValue = 0x01)

    transfer_func(sender, receiver)
    
    exit_gracefully()
except:
    traceback.print_exc()
    print("Unexpected exception: ", sys.exc_info()[0])
    exit_gracefully()
