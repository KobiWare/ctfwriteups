#!/usr/bin/env python3
import hashlib, struct

# Initial tomb_key from .data section at 0x8413E0
tomb_key = bytearray.fromhex(
    "f90016370414b822ed3bb7cf2158773a"
    "d28c726aeadff133e8241092ad08dd0d"
)

# Step 1: proc() XOR - sum(0..99) = 4950 = 0x1356
xor_val = 0x1356
for i in range(0, 32, 4):
    word = struct.unpack_from('<I', tomb_key, i)[0]
    word ^= xor_val
    struct.pack_into('<I', tomb_key, i, word)

# Step 2: puts() shellcode XOR - pattern 01 02 03 04 00 00 00 00
pattern = bytes([0x01, 0x02, 0x03, 0x04, 0x00, 0x00, 0x00, 0x00])
for i in range(32):
    tomb_key[i] ^= pattern[i % 8]

# Step 3: SHA256("BCCTF{") XOR
sha_prefix = hashlib.sha256(b"BCCTF{").digest()
for i in range(32):
    tomb_key[i] ^= sha_prefix[i]

# Step 4: XOR with 0x7D ('}')
for i in range(32):
    tomb_key[i] ^= 0x7D

# Step 5: Lock table - recover characters from SHA256 reverse lookup
# Pre-compute SHA256 of all byte values
sha_table = {}
for b in range(256):
    h = hashlib.sha256(bytes([b])).digest()
    sha_table[h[1:]] = b  # bytes 1-31 as key

# Lock table entries (20 x 32 bytes) extracted from the binary
lock_entries = [...]  # 20 entries extracted via GDB/objdump

# Recover flag[7..26] from lock entries bytes 1-31
flag_chars = [0] * 46
flag_chars[0:6] = list(b"BCCTF{")
flag_chars[45] = 0  # null terminator
flag_chars[44] = ord('}')

for i in range(20):
    entry = lock_entries[i]
    flag_chars[7 + i] = sha_table[bytes(entry[1:])]

# Recover flag[6] from byte 0 of first lock entry
for c in range(256):
    h = hashlib.sha256(bytes([c])).digest()
    if h[0] ^ hashlib.sha256(bytes([flag_chars[7]])).digest()[0] == lock_entries[0][0]:
        flag_chars[6] = c
        break

# Apply lock table XOR to tomb_key
for i in range(20):
    entry = lock_entries[i]
    for j in range(32):
        tomb_key[j] ^= entry[j]

# Step 6: Shellcode recovery - flag[26+i] = tomb_key[i] ^ (5*i + 0x40)
for i in range(18):
    flag_chars[26 + i] = tomb_key[i] ^ (5 * i + 0x40)

flag = ''.join(chr(c) for c in flag_chars[:45])
print(f"Flag: {flag}")
