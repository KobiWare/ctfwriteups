---
author: Claude
credit: Claude, Fenix
---
## Solution

### Analysis

We are given `images.zip` which extracts to three files:
- `left.bmp` (4,194,442 bytes) -- An unencrypted BMP image showing the text `BCCTF{BL`
- `right.bmp` (4,194,442 bytes) -- An unencrypted BMP image showing the text `3r_Mod3}`
- `middle.bin` (4,194,464 bytes) -- An encrypted file containing the middle portion of the flag

Examining `middle.bin` with `xxd` revealed it starts with `Salted__` followed by an 8-byte salt, which is the OpenSSL encrypted file format header (16 bytes total).

The challenge description says "Our best cryptanalysts don't think it's possible to crack the password" -- hinting that brute-forcing the password is not the intended approach.

### Approach

The flag text itself provides the key clue: the visible portions spell out "BL...3r_Mod3}" which suggests "Block Cipher Mode". This is the classic **ECB (Electronic Codebook) Penguin** attack.

In ECB mode, each block of plaintext is encrypted independently with the same key. This means identical plaintext blocks produce identical ciphertext blocks. For images, this preserves the visual structure -- areas of the same color in the original image remain the same color in the encrypted version, just mapped to a different (random-looking) color.

**The attack does not require knowing the encryption key.** The steps are:

1. Strip the 16-byte OpenSSL header (`Salted__` + 8-byte salt) from `middle.bin`.
2. Skip the first 144 bytes of ciphertext (9 AES blocks of 16 bytes each), which correspond to the encrypted BMP header.
3. Take the known BMP header from one of the unencrypted images (138 bytes, including the pixel data offset).
4. Graft the known BMP header onto the remaining ciphertext bytes (treated as pixel data).
5. Open the resulting BMP file -- the visual structure of the original image is fully preserved.

**Initial exploration:** Before arriving at the ECB approach, steganography was briefly investigated (checking LSBs of the unencrypted images) and direct OpenSSL decryption with an empty password was tried. Both yielded nothing, confirming the challenge was about the block cipher mode weakness.

### Solve Script

```python
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
```

### Result

The reconstructed image clearly shows the text `oCk_c1pH` despite the encryption. The colors are wrong (random ciphertext values instead of the original black/white), but the structure of the original image is fully preserved due to ECB mode's block-by-block independent encryption.

Combining all three images:
- **Left:** `BCCTF{BL`
- **Middle:** `oCk_c1pH`
- **Right:** `3r_Mod3}`

### Key Insight

ECB mode is fundamentally insecure for encrypting structured data like images because identical plaintext blocks always produce identical ciphertext blocks. This preserves spatial patterns in the data. The attack requires zero knowledge of the encryption key -- only the file format header needs to be reconstructed from the unencrypted reference images, and the visual structure reveals the hidden content directly.

## Flag
`BCCTF{BLoCk_c1pH3r_Mod3}`
