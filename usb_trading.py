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
reattach = False
serial_port = None
epIn = None
epOut = None
p = None
max_usb_timeout_w = 5
max_usb_timeout_r = 0.1
max_packet_size = 0x40

VID = 0xcafe
PID = 0x4011

path = "pokemon_gen3_to_genx_mb.gba"

def kill_function():
    os.kill(os.getpid(), signal.SIGINT)

def transfer_func(sender, receiver, list_sender, raw_receiver, is_serial):
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

    result = 1
    while result != 0:
        result = multiboot.read_all(raw_receiver)
    list_sender(config_base, chunk_size=len(config_base))
    ret = multiboot.read_all(raw_receiver)

    if is_serial and (ret != 1):
        print("WARNING: Firmware not recognized!\nWhen using Serial, you MUST use a firmware which doesn't alter the output!\nIt's best if you update to the one available at:\nhttps://github.com/Lorenzooone/gb-link-firmware-reconfigurable/releases")

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
    epOut.write(byte_to_send.to_bytes(num_bytes, byteorder='big'), timeout=int(max_usb_timeout_w * 1000))
    return

# Code dependant on this connection method
def sendList(data, chunk_size=8):
    num_iters = int(len(data)/chunk_size)
    for i in range(num_iters):
        epOut.write(data[i*chunk_size:(i+1)*chunk_size], timeout=int(max_usb_timeout_w * 1000))
    #print(num_iters*chunk_size)
    #print(len(data))
    if (num_iters*chunk_size) != len(data):
        epOut.write(data[num_iters*chunk_size:], timeout=int(max_usb_timeout_w * 1000))

def receiveByte(num_bytes=None):
    if num_bytes is None:
        num_bytes = max_packet_size
    recv = int.from_bytes(epIn.read(num_bytes, timeout=int(max_usb_timeout_r * 1000)), byteorder='big')
    return recv

def receiveByte_raw(num_bytes=None):
    if num_bytes is None:
        num_bytes = max_packet_size
    return epIn.read(num_bytes, timeout=int(max_usb_timeout_r * 1000))

# Code dependant on this connection method
def sendByte_serial(byte_to_send, num_bytes):
    serial_port.write(byte_to_send.to_bytes(num_bytes, byteorder='big'))
    return

# Code dependant on this connection method
def sendList_serial(data, chunk_size=8):
    num_iters = int(len(data)/chunk_size)
    for i in range(num_iters):
        serial_port.write(bytes(data[i*chunk_size:(i+1)*chunk_size]))
    #print(num_iters*chunk_size)
    #print(len(data))
    if (num_iters*chunk_size) != len(data):
        serial_port.write(bytes(data[num_iters*chunk_size:]))

def receiveByte_serial(num_bytes=None):
    if num_bytes is None:
        num_bytes = max_packet_size
    recv = int.from_bytes(serial_port.read(num_bytes), byteorder='big')
    return recv

def receiveByte_raw_serial(num_bytes=None):
    if num_bytes is None:
        num_bytes = max_packet_size
    return serial_port.read(num_bytes)

# Code dependant on this connection method
def sendByte_win(byte_to_send, num_bytes):
    p.write(byte_to_send.to_bytes(num_bytes, byteorder='big'))

# Code dependant on this connection method
def sendList_win(data, chunk_size=8):
    #Why? Idk. But it fixes it... :/
    if(chunk_size > 0x3C):
        chunk_size = 0x3C
    num_iters = int(len(data)/chunk_size)
    for i in range(num_iters):
        p.write(bytes(data[i*chunk_size:(i+1)*chunk_size]))
    #print(num_iters*chunk_size)
    #print(len(data))
    if (num_iters*chunk_size) != len(data):
        p.write(bytes(data[num_iters*chunk_size:]))

# Code dependant on this connection method
# The original was so slow, I had to rewrite it a bit to make it work for time sensitive applications
def read_win(self, size=None):
    if not self.is_open:
        return None
    rx = [self._rxremaining]
    length = len(self._rxremaining)
    self._rxremaining = b''
    end_timeout = time.time() + (self.timeout or 0.2)
    if size:
        super(ComPort, self).set_timeout(self._ep_in, (self.timeout or 0.2) * 10)
        while length < size:
            c = super(ComPort, self).read(self._ep_in, size-length)
            if c is not None and len(c):
                rx.append(c)
                length += len(c)
                if len(c) == self.maximum_packet_size:
                    end_timeout += (self.timeout or 0.2)
            if time.time() > end_timeout:
                break
    else:
        super(ComPort, self).set_timeout(self._ep_in, (self.timeout or 0.2))
        while True:
            c = super(ComPort, self).read(self._ep_in, self.maximum_packet_size)
            if c is not None and len(c):
                rx.append(c)
                length += len(c)
                if len(c) == self.maximum_packet_size:
                    end_timeout += (self.timeout or 0.2)
                else:
                    break
            else:
                break
            if time.time() > end_timeout:
                break
    chunk = b''.join(rx)
    if size and len(chunk) >= size:
        if self._rxremaining:
            self._rxremaining = chunk[size:] + self._rxremaining
        else:
            self._rxremaining = chunk[size:]
        chunk = chunk[0:size]
    return chunk

def receiveByte_win(num_bytes=None):
    recv = int.from_bytes(read_win(p, size=num_bytes), byteorder='big')
    return recv

def receiveByte_raw_win(num_bytes=None):
    return read_win(p, size=num_bytes)

# Things for the USB connection part
def exit_gracefully():
    if dev is not None:
        usb.util.dispose_resources(dev)
        if(os.name != "nt"):
            if reattach:
                dev.attach_kernel_driver(0)
    if serial_port is not None:
        serial_port.reset_input_buffer()
        serial_port.reset_output_buffer()
        serial_port.close()
    os._exit(1)

def exit_no_device():
    print("Device not found!")
    exit_gracefully()

def signal_handler(sig, frame):
    print("You pressed Ctrl+C!")
    exit_gracefully()

def libusb_method():
    global dev, epIn, epOut, reattach
    try:
        devices = list(usb.core.find(find_all=True,idVendor=VID, idProduct=PID))
        for d in devices:
            #print('Device: %s' % d.product)
            dev = d
        if dev is None:
            return False
        reattach = False
        if(os.name != "nt"):
            if dev.is_kernel_driver_active(0):
                try:
                    reattach = True
                    dev.detach_kernel_driver(0)
                except usb.core.USBError as e:
                    sys.exit("Could not detach kernel driver: %s" % str(e))
            else:
                pass
                #print("no kernel driver attached")
        
        dev.reset()

        dev.set_configuration()

        cfg = dev.get_active_configuration()

        intf = cfg[(2,0)]   # Or find interface with class 0xff

        epIn = usb.util.find_descriptor(
            intf,
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_IN)

        assert epIn is not None

        epOut = usb.util.find_descriptor(
            intf,
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)

        assert epOut is not None

        dev.ctrl_transfer(bmRequestType = 1, bRequest = 0x22, wIndex = 2, wValue = 0x01)
    except:
        return False
    return True

def winusbcdc_method():
    global p
    if(os.name == "nt"):
        try:
            print("Trying WinUSB CDC")
            p = ComPort(vid=VID, pid=PID)
            if not p.is_open:
                return False
            #p.baudrate = 115200
            p.settimeout(max_usb_timeout_r)
        except:
            return False
    else:
        return False
    return True

def serial_method():
    global serial_port
    try:
        ports = list(serial.tools.list_ports.comports())
        serial_success = False
        port = None
        for device in ports:
            if(device.vid is not None) and (device.pid is not None):
                if(device.vid == VID) and (device.pid == PID):
                    port = device.device
                    break
        if port is None:
            return False
        serial_port = serial.Serial(port=port, bytesize=8, timeout=max_usb_timeout_r, write_timeout = max_usb_timeout_w)
    except Exception as e:
        return False
    return True

signal.signal(signal.SIGINT, signal_handler)

try_serial = False
try_libusb = False
try_winusbcdc = False
is_serial = False
try:
    import usb.core
    import usb.util
    try_libusb = True
except:
    pass

if(os.name == "nt"):
    try:
        from winusbcdc import ComPort
        try_winusbcdc = True
    except:
        pass
try:
    import serial
    import serial.tools.list_ports
    try_serial = True
except:
    pass

sender = None
receiver = None
list_sender = None
raw_receiver = None
found = False

# The execution path
try:
    if (not found) and try_libusb:
        if(libusb_method()):
            sender = sendByte
            receiver = receiveByte
            list_sender = sendList
            raw_receiver = receiveByte_raw
            found = True
    if (not found) and try_winusbcdc:
        if(winusbcdc_method()):
            sender = sendByte_win
            receiver = receiveByte_win
            list_sender = sendList_win
            raw_receiver = receiveByte_raw_win
            found = True
    if (not found) and try_serial:
        if(serial_method()):
            sender = sendByte_serial
            receiver = receiveByte_serial
            list_sender = sendList_serial
            raw_receiver = receiveByte_raw_serial
            found = True
            is_serial = True

    if found:
        print("USB connection established!")
        transfer_func(sender, receiver, list_sender, raw_receiver, is_serial)
    else:
        print("Couldn't find USB device!")
        missing = ""
        if not try_serial:
            missing += "PySerial, "
        if not try_libusb:
            missing += "PyUSB, "
        if(os.name == "nt") and (not try_winusbcdc):
            missing += "WinUsbCDC, "
        if missing != "":
            print("If the device is attached, try installing " + missing[:-2])
    
    exit_gracefully()
except:
    traceback.print_exc()
    print("Unexpected exception: ", sys.exc_info()[0])
    exit_gracefully()
