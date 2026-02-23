from PIL import Image
import numpy as np

# Read the BMP header from left.bmp (138 bytes based on the pixel data offset)
with open('left.bmp', 'rb') as f:
    bmp_header = f.read(138)

# Read the encrypted file
with open('middle.bin', 'rb') as f:
    enc_data = f.read()

# Strip OpenSSL "Salted__" + 8-byte salt = 16 bytes
ciphertext = enc_data[16:]

# The BMP header is 138 bytes. In ECB mode, blocks 0-8 (144 bytes)
# correspond to the encrypted header. The pixel data starts at byte 138
# of the plaintext, which is within the 9th block (starting at byte 144).
# Skip the first 144 bytes of ciphertext (encrypted header blocks)
# and use the rest as pixel data.
pixel_data_needed = 4194442 - 138  # total BMP size minus header
pixel_ciphertext = ciphertext[144:]

# Pad or trim to match expected pixel data size
if len(pixel_ciphertext) < pixel_data_needed:
    pixel_ciphertext += b'\x00' * (pixel_data_needed - len(pixel_ciphertext))
else:
    pixel_ciphertext = pixel_ciphertext[:pixel_data_needed]

# Write BMP with real header + ciphertext as pixel data
with open('middle_ecb.bmp', 'wb') as f:
    f.write(bmp_header)
    f.write(pixel_ciphertext)

print("Written middle_ecb.bmp -- open to view the text pattern")
