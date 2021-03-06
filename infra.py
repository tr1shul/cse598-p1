#!/usr/bin/env python3
import os
import re
import sys
import struct
import jinja2

from pylcs import lcs
from fuzzywuzzy import process
from difflib import SequenceMatcher

folder = os.path.dirname(__file__)
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(folder, 'exploit_templates')),
    trim_blocks=True)

lower_limit = 0x7f0000000000
upper_limit = 0x7fffffffffff

def find_difference(file1, file2) -> list:
    diff_lines = []
    for line in file1:
        if line  not in file2:
            diff_lines.append(line)
    return diff_lines

def calculate_address(recv, file2) -> int:
    #similar_line = process.extractOne(recv, file2)[0]
    
    # try a regex match (hex or little-endian byte string)
    try:
        match_hex = re.search(r'7f[0-9A-F]{10}', recv.decode('latin1'), re.I).group()
        return int(match_hex, 16)
    except:
        pass

    try:
        match_bytes = re.search(r'(((\\x[0-9A-F][0-9A-F])|.){5})\\x7f', recv, re.I).group()
        return int.from_bytes(bytes(eval(f'"{match_bytes}"'), encoding='raw_unicode_escape'), byteorder='little')
    except:
        pass

    return 0 

if __name__ == '__main__':

    # read 2 exploits generated by kuin-replayer
    with open(sys.argv[1], 'r') as f:
        file1 = f.readlines()
    with open(sys.argv[2], 'r') as f:
        file2 = f.readlines()

    # find non-similar lines in those exploits (could have leaked addresses/flags)
    diff_lines = find_difference(file1, file2)

    # find recv()'s to calculate the leaked address
    leaked_address = 0
    for line in diff_lines:
        if "recv" in line:
            leaked_address = calculate_address(line, file2)
            if leaked_address != 0:
                assert(leaked_address in range(lower_limit, upper_limit))
                break

    # rebuild exploit
    received = False
    new_exploit = []
    for line in file1:
        if line not in diff_lines:
            new_exploit.append(line)
        else:
            if "recv" in line:
                hex_address = hex(leaked_address)[2:]
                byte_address = str(struct.pack('<Q', leaked_address).strip(b'\x00'))[2:-1]
                if hex_address in line:
                    add_line = "recv(" + str(line.find(hex_address)-7) + ")\n\n"
                    new_exploit.append(add_line)
                    if not received:
                        add_line = "addr = int(recv(" + str(len(hex_address)) + "), 16)\n\n"
                        new_exploit.append(add_line)
                    add_line = "r.clean()\n"
                    new_exploit.append(add_line)
                    received = True
                elif byte_address in line:
                    add_line = "recv(" + str(line.find(byte_address)-7) + ")\n\n"
                    new_exploit.append(add_line)
                    if not received:
                        add_line = "addr = int.from_bytes(recv(" + str(len(byte_address)) + "), byteorder='little')\n\n"
                        new_exploit.append(add_line)
                    add_line = "r.clean()\n"
                    new_exploit.append(add_line)
                    received = True
                else:
                    add_line = "r.clean()\n"
                    new_exploit.append(add_line)
            if "send" in line:
                hex_address = hex(leaked_address)[2:]
                byte_address = str(struct.pack('<Q', leaked_address).strip(b'\x00'))[2:-1]
                send_address = None
                if hex_address in line:
                    send_address = hex_address
                elif byte_address in line:
                    send_address = byte_address
                if send_address is not None:
                    line_split = line.split(send_address)
                    add_line = line_split[0] if len(line_split[0]) else ""
                    add_line += "' + " if line_split[0] else ""
                    add_line += "struct.pack('<Q', addr)"
                    add_line += " + b'" if len(line_split[1]) else ""
                    add_line += line_split[1] if len(line_split[1]) else ""
                    new_exploit.append(add_line)
                else:
                    new_exploit.append(line)

    with open('new_exploit.py', 'w') as f:
        for l in new_exploit:
            f.write(l)
