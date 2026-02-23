---
author: Claude
credit: Claude, Fenix
---
## Solution

### Analysis

The challenge provides two files:
- `crazy_curve.sage` -- a SageMath script implementing a custom "CrazyCurve" class and a Diffie-Hellman key exchange
- `output.txt` -- the public keys of Alice and Bob, plus an AES-CBC encrypted flag

The "CrazyCurve" is defined by the equation `(x - a)^2 + (y - b)^2 = c^2` over GF(p). This is a **circle** in a finite field, not an elliptic curve. The addition law defined in the code:

```python
xval = (ptx*qtx - qty*pty) / c + a
yval = (ptx*qty + qtx*pty) / c + b
```

where `ptx = P.x - a`, `pty = P.y - b`, etc., is equivalent to **complex number multiplication**. Specifically, if we map each point `(x, y)` to the element `w = ((x-a) + i*(y-b)) / c` in GF(p^2), then point addition becomes multiplication and scalar multiplication becomes exponentiation. The group is the norm-1 subgroup of GF(p^2)*, which has order `p + 1`.

This means the discrete logarithm problem on this "curve" reduces to a DLP in GF(p^2)*, which is much easier to solve than ECDLP on a real elliptic curve.

The challenge defines many named curves with different primes. The key exchange picks one curve and generates 128-bit private keys.

### Approach

1. **Identify the correct curve**: By testing which curve's parameters match the public key points in `output.txt`, the curve "Daquavious Pork" was identified. Its prime `p` satisfies `p = 3 mod 4`, meaning `sqrt(-1)` does not exist in GF(p), so we work in GF(p^2) using `i^2 = -1`.

2. **Map to GF(p^2)**: Each point `(x, y)` on the circle maps to `w = ((x-a)/c, (y-b)/c)` in GF(p^2), where the tuple represents `(real, imag)` components. The generator `G`, Alice's public key `A`, and Bob's public key `B` were all converted to this representation.

3. **Compute the group order**: The order of the norm-1 subgroup is `p + 1`. Factoring this gave:
   ```
   p + 1 = 2^3 * 3 * 7 * 17 * 149 * 457 * 4517 * 5749 * 717427 * 1966366126889 * 25391461992785507 * 511215348081772579342664383
   ```

4. **Pohlig-Hellman with BSGS and Pollard's rho**: Since the private key is only 128 bits, we only needed enough small prime factors whose product exceeds 2^128. The solver used:
   - **Baby-step giant-step (BSGS)** for factors up to ~10^13
   - **Pollard's rho** for larger factors like 25391461992785507 (~55 bits)
   - **Chinese Remainder Theorem (CRT)** to combine the partial discrete logs

5. **Recover the shared secret and decrypt**: After finding Alice's private key modulo the product of small factors, the shared secret point was computed as `B * n_alice`. The x-coordinate was used to derive the AES key via `sha1(str(ss).encode()).digest()[:16]`, and the ciphertext was decrypted.

### Solve Script

The final working solver (`solve2.py`) is a pure Python implementation (no SageMath required) that:
- Implements GF(p^2) arithmetic (multiplication, exponentiation, inversion)
- Performs Pohlig-Hellman decomposition of the DLP
- Uses BSGS for small subgroups and Pollard's rho for larger ones
- Combines results via CRT and decrypts the flag

Key excerpt:

```python
# Map points to GF(p^2) elements
def point_to_w(px, py):
    real = ((px - a) * c_inv) % p
    imag = ((py - b) * c_inv) % p
    return (real % p, imag % p)

# Group order is p+1 for the norm-1 subgroup of GF(p^2)*
order = p + 1

# Pohlig-Hellman: solve DLP for each prime power factor
for prime, exp, pe in needed_factors:
    cofactor = order // pe
    gi = fp2_pow(wG, cofactor)
    hi = fp2_pow(wA, cofactor)
    xi = solve_dlp_fp2(gi, hi, pe)  # BSGS or Pollard's rho
    remainders.append(xi)
    moduli.append(pe)

# CRT to recover full private key
n_alice, M = crt(remainders, moduli)

# Compute shared secret and decrypt
w_ss = fp2_pow(wB, n_alice)
x_ss = (w_ss[0] * c + a) % p
key = sha1(str(int(x_ss)).encode()).digest()[:16]
cipher = AES.new(key, AES.MODE_CBC, iv_bytes)
pt = unpad(cipher.decrypt(ct_bytes), 16)
```

An initial attempt using a SageMath solve script (`solve.sage`) failed because SageMath was not installed. A first Python solver (`solve.py`) had import path issues and suboptimal BSGS limits. The final `solve2.py` fixed these and successfully recovered the flag.

## Flag
`BCCTF{y0U_sp1n_mE_r1gt_r0und}`
