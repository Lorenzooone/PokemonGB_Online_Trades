import usb.core
import usb.util
import signal
import sys
import traceback
import time
import os
import multiboot
from utilities.gsc_trading import GSCTrading
from utilities.gsc_trading_jp import GSCTradingJP
from utilities.rby_trading import RBYTrading
from utilities.rby_trading_jp import RBYTradingJP
from utilities.rse_sp_trading import RSESPTrading
from utilities.websocket_client import PoolTradeRunner, ProxyConnectionRunner
from utilities.gsc_trading_menu import GSCTradingMenu
from utilities.gsc_trading_strings import GSCTradingStrings

dev = None

path = "pokemon_gen3_to_genx_mb.gba"

def transfer_func(sender, receiver, list_sender, raw_receiver):
    menu = GSCTradingMenu(kill_function)
    menu.handle_menu()
    
    if menu.verbose:
        print(GSCTradingStrings.waiting_transfer_start_str)
        
    if menu.trade_type == GSCTradingStrings.two_player_trade_str:
        connection = ProxyConnectionRunner(menu, kill_function)
    elif menu.trade_type == GSCTradingStrings.pool_trade_str:
        connection = PoolTradeRunner(menu, kill_function)
    
    if menu.multiboot:
        menu.gen = 3

    if menu.gen == 3:
        config_base = multiboot.get_configure_list(1000, 4)
    else:
        config_base = multiboot.get_configure_list(1000, 1)

    multiboot.read_all(raw_receiver)
    list_sender(config_base, chunk_size=len(config_base))
    ret = multiboot.read_all(raw_receiver)
    
    if(menu.gen == 3) and (ret != 1):
        print("Non-reconfigurable firmware found!\nIt's best if you update to the one available at:\nhttps://github.com/Lorenzooone/gb-link-firmware-reconfigurable/releases")
    
    pre_sleep = False
    if(ret == 1) and (menu.gen == 3):
        pre_sleep = True

    if menu.multiboot:
        multiboot.multiboot(raw_receiver, sender, list_sender, path)
        return
    if menu.gen == 2:
        if menu.japanese:
            trade_c = GSCTradingJP(sender, receiver, connection, menu, kill_function, pre_sleep)
        else:
            trade_c = GSCTrading(sender, receiver, connection, menu, kill_function, pre_sleep)
    elif menu.gen == 3:
        trade_c = RSESPTrading(sender, receiver, connection, menu, kill_function, pre_sleep)
    elif menu.gen == 1:
        if menu.japanese:
            trade_c = RBYTradingJP(sender, receiver, connection, menu, kill_function, pre_sleep)
        else:
            trade_c = RBYTrading(sender, receiver, connection, menu, kill_function, pre_sleep)
    connection.start()
    
    if menu.trade_type == GSCTradingStrings.two_player_trade_str:
        trade_c.player_trade(menu.buffered)
    elif menu.trade_type == GSCTradingStrings.pool_trade_str:
        trade_c.pool_trade()

# Code dependant on this connection method
def sendByte(byte_to_send, num_bytes):
    epOut.write(byte_to_send.to_bytes(num_bytes, byteorder='big'))
    return

# Code dependant on this connection method
def sendList(data, chunk_size=8):
    num_iters = int(len(data)/chunk_size)
    for i in range(num_iters):
        epOut.write(data[i*chunk_size:(i+1)*chunk_size])
    #print(num_iters*chunk_size)
    #print(len(data))
    if (num_iters*chunk_size) != len(data):
        epOut.write(data[num_iters*chunk_size:])
        

def receiveByte(num_bytes):
    recv = int.from_bytes(epIn.read(epIn.wMaxPacketSize, 100), byteorder='big')
    return recv

def receiveByte_raw(num_bytes):
    return epIn.read(epIn.wMaxPacketSize, 100)

# Code dependant on this connection method
def sendByte_win(byte_to_send, num_bytes):
    p.write(byte_to_send.to_bytes(num_bytes, byteorder='big'))

# Code dependant on this connection method
def sendList_win(data, chunk_size=8):
    num_iters = int(len(data)/chunk_size)
    for i in range(num_iters):
        p.write(bytes(data[i*chunk_size:(i+1)*chunk_size]))
    #print(num_iters*chunk_size)
    #print(len(data))
    if (num_iters*chunk_size) != len(data):
        p.write(bytes(data[num_iters*chunk_size:]))

def receiveByte_win(num_bytes):
    recv = int.from_bytes(p.read(size=num_bytes), byteorder='big')
    return recv

def receiveByte_raw_win(num_bytes):
    return p.read(size=num_bytes)

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
    list_sender = sendList
    raw_receiver = receiveByte_raw

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
            list_sender = sendList_win
            raw_receiver = receiveByte_raw_win
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

    transfer_func(sender, receiver, list_sender, raw_receiver)
    
    exit_gracefully()
except:
    traceback.print_exc()
    print("Unexpected exception: ", sys.exc_info()[0])
    exit_gracefully()
