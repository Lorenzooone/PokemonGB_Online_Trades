import os
import time

def get_configure_list(us_between_transfer, bytes_for_transfer):
    config_base = [0xCA, 0xFE, 0xCA, 0xFE, 0xCA, 0xFE, 0xCA, 0xFE, 0xCA, 0xFE, 0xCA, 0xFE, 0xCA, 0xFE, 0xCA, 0xFE, 0xDE, 0xAD, 0xBE, 0xEF, 0xDE, 0xAD, 0xBE, 0xEF, 0xDE, 0xAD, 0xBE, 0xEF, 0xDE, 0xAD, 0xBE, 0xEF]
    config_base += [us_between_transfer & 0xFF, (us_between_transfer >> 8) & 0xFF, (us_between_transfer >> 16) & 0xFF, bytes_for_transfer & 0xFF]
    return config_base

def read_all(receiver, debug=False):
    output = 0
    prev_len = 0
    while True:
        try:
            data = receiver(0x40)
            output <<= (8*prev_len)
            output |= int.from_bytes(data, byteorder='big')
            prev_len = len(data)
        except:
            break
    if debug:
        print("0x%02x " % output)
    return output

def multiboot(receiver, sender, list_sender, path):
    content = 0
    print("Preparing data...")
    content = bytearray(open(path, 'rb').read())
    fsize = os.path.getsize(path)
    # Padding to avoid errors
    content = content.ljust(fsize + 64, b'\0')

    if fsize > 0x3FF40:
        print("File size error, max " + 0x3FF40 + " bytes")
        exit()
    
    fsize += 0xF
    fsize &= ~0xF

    sending_data = [0]*((fsize-0xC0)>>2)
    complete_sending_data = [0]*(fsize-0xC0)
    crcC = 0xC387
    for i in range(0xC0, fsize, 4):
        dat = int(content[i])
        dat |= int(content[i + 1]) << 8
        dat |= int(content[i + 2]) << 16
        dat |= int(content[i + 3]) << 24

        tmp = dat

        for b in range(32):
            bit = (crcC ^ tmp) & 1
            if bit == 0:
                crcC = (crcC >> 1) ^ 0
            else:
                crcC = (crcC >> 1) ^ 0xc37b
            tmp >>= 1
            
        dat = dat ^ (0xFE000000 - i) ^ 0x43202F2F
        sending_data[(i-0xC0)>>2] = dat & 0xFFFFFFFF
        
    print("Data preloaded...")
    
    read_all(receiver)
    config_base = get_configure_list(36, 4)

    list_sender(config_base, chunk_size = len(config_base))
    val = read_all(receiver)

    recv = 0
    while True:
        sender(0x6202, 4)
        recv = read_all(receiver)
        if (recv >> 16) == 0x7202:
            break
    print("Lets do this thing!")
    sender(0x6102, 4)

    for i in range(96):
        out = (int(content[(i*2)])) + (int(content[(i*2)+1]) << 8)
        sender(out, 4)

    sender(0x6200, 4)
    sender(0x6200, 4)
    sender(0x63D1, 4)
    #Clear buffer
    read_all(receiver)

    sender(0x63D1, 4)
    token = read_all(receiver)
    if (token >> 24) != 0x73:
        print("Failed handshake!")
        return
    else:
        print("Handshake successful!")

    crcA = (token >> 16) & 0xFF
    seed = 0xFFFF00D1 | (crcA << 8)
    crcA = (crcA + 0xF) & 0xFF

    sender((0x6400 | crcA), 4)
    read_all(receiver)

    sender((fsize - 0x190) // 4, 4)
    token = read_all(receiver)
    crcB = (token >> 16) & 0xFF
    print(fsize)
    print("Sending data!")
    
    for i in range(len(sending_data)):
        seed = (seed * 0x6F646573 + 1) & 0xFFFFFFFF
        complete_sending_data[(i*4)] = ((sending_data[i] ^ seed)>>24) & 0xFF
        complete_sending_data[(i*4)+1] = ((sending_data[i] ^ seed)>>16) & 0xFF
        complete_sending_data[(i*4)+2] = ((sending_data[i] ^ seed)>>8) & 0xFF
        complete_sending_data[(i*4)+3] = ((sending_data[i] ^ seed)>>0) & 0xFF
        
    time_transfer = time.time()
    list_sender(complete_sending_data, chunk_size = 0x40)
    time_transfer = time.time()-time_transfer
    print(time_transfer)
    
    print("Data sent")

    tmp = 0xFFFF0000 | (crcB << 8) | crcA

    for b in range(32):
        bit = (crcC ^ tmp) & 1
        if bit == 0:
            crcC = (crcC >> 1) ^ 0
        else:
            crcC = (crcC >> 1) ^ 0xc37b
        tmp >>= 1

    sender(0x0065, 4)
    while True:
        sender(0x0065, 4)
        recv = read_all(receiver)
        if (recv >> 16) == 0x0075:
            break

    sender(0x0066, 4)
    sender(crcC & 0xFFFF, 4)
    print("DONE!")
