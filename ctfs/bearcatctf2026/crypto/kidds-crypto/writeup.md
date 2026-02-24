---
author: Claude
credit: Claude, Fenix
---
## Solution

### Analysis

We are given a single file `kidd.txt` containing RSA parameters:

```
n = 147411106158287041622784593501613775873740698182074300197321802109276152016347880921444863007
e = 3
c = 114267757154492856513993877195962986022489770009120200367811440852965239059854157313462399351
```

The public exponent `e = 3` is suspiciously small, and `n` is only 93 digits long -- much smaller than a typical RSA modulus.

### Approach

**Attempt 1: Plain cube root.** Since `e = 3`, if the plaintext `m` is small enough that `m^3 < n`, then `c = m^3` exactly (no modular reduction) and we can simply take the integer cube root. This was tried first but the cube root was not exact. Trying `c + k*n` for `k` up to 100,000 also failed to produce an exact cube root.

**Attempt 2: Factor n.** Since `n` is only 93 digits, factoring was attempted using sympy's `factorint`. This succeeded quickly and revealed that `n` is composed of **13 small prime factors**, each approximately 7-8 digits:

```
n = 16249801 * 8532679 * 13856221 * 11908471 * 13164721 * 15607783 *
    9742027 * 11862439 * 10660669 * 15840751 * 14596051 * 11451571 * 9613003
```

**The complication: gcd(e, phi(n)) != 1.** Computing `phi(n) = product of (p-1)` for all 13 primes revealed that `gcd(3, phi(n)) = 3`. This means standard RSA decryption (`d = e^{-1} mod phi(n)`) is impossible because `e` is not invertible modulo `phi(n)`.

**Attempt 3: CRT cube root extraction.** Since `e = 3` and each prime factor `p` satisfies `3 | (p-1)`, there are 3 cube roots of `c` modulo each prime. Using the Chinese Remainder Theorem (CRT), all `3^13 = 1,594,323` combinations were enumerated to find the correct plaintext.

There was an initial stumble with sympy's `crt` function -- the return value is `(result, modulus)` but this was initially unpacked in the wrong order. After fixing that, the search proceeded correctly.

For each combination, the candidate was checked:
1. Verified `m^3 mod n == c`
2. Checked if the bytes decoded to valid ASCII

After iterating through all combinations, the flag was found with a perfect 1.00 printability score.

### Key Insight

The challenge name "kidd" is a reference to the fact that `n` is composed of many small ("kid-sized") primes. With `e = 3` and `3 | phi(n)`, standard decryption fails. The correct approach is to compute cube roots modulo each small prime factor independently, then use CRT to reconstruct the plaintext from all valid combinations.

## Flag
`BCCTF{y0U_h4V3_g0T_70_b3_K1DD1n9_Me}`
