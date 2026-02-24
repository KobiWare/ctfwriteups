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
