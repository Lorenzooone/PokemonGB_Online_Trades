import usb.core
import usb.util
import signal
import sys
import traceback
import time
import os
from gsc_trading import GSCTrading
from p2p_connection import P2PConnection

dev = None

def transfer_func():
    print("Waiting for the transfer to start...")
    
    trade_c = GSCTrading(sendByte, receiveByte)
    res = trade_c.trade() # Read the starting information
    
    return

# Code dependant on this connection method
def sendByte(byte_to_send):
    #print("send: 0x%02x" % byte_to_send)
    epOut.write(byte_to_send.to_bytes(1, byteorder='big'))
    return

def receiveByte():
    recv = int.from_bytes(epIn.read(epIn.wMaxPacketSize, 100), byteorder='big')
    #print("recv: 0x%02x" % recv)
    return recv

# Things for the USB connection part
def exit_gracefully():
    if dev is not None:
        usb.util.dispose_resources(dev)
        if(os.name != "nt"):
            if reattach:
                dev.attach_kernel_driver(0)
    print('Done.')

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    exit_gracefully()

signal.signal(signal.SIGINT, signal_handler)

# The execution path
try:
    devices = list(usb.core.find(find_all=True,idVendor=0xcafe, idProduct=0x4011))
    for d in devices:
        #print('Device: %s' % d.product)
        dev = d

    if dev is None:
        raise ValueError('Device not found')

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

    transfer_func()
    
    exit_gracefully()
except:
    traceback.print_exc()
    print("Unexpected exception: ", sys.exc_info()[0])
    exit_gracefully()