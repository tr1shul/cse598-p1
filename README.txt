Name - Purv Chauhan
ASUID - 1212982808

Usage - ./infra.py <file1> <file2>

Address Detection in .py's generated by kuin-ng

The goal of the project was to detect libc/stack addresses in pcap's and generate an exploit script. The way it is currently implemented is by reading already generated .py's and using regex's.

Future Improvements:
1. Integrate into kuin-ng framework to read raw pcaps directly.
2. Support offset calculation relative to the leaked addresses.
3. Currently it assumes the first address it sees would be a leak which is not always the case. So implement a way to confirm our hypothesis by using multiple pcap streams.
4. Check for FLAG format in the stream.
