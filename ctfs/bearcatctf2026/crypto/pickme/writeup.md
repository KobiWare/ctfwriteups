---
author: Claude
credit: Claude, Fenix
---
## Solution

### Analysis

We are given `server.py`, which implements an RSA key validation service. The server:

1. Accepts an RSA private key in PEM format.
2. Loads it with `unsafe_skip_rsa_key_validation=True` (line 30), which disables the cryptography library's built-in safety checks.
3. Runs a series of validation tests on the key parameters.
4. If all tests pass, encrypts the flag with the submitted public key: `c = pow(FLAG, e, n)`.
5. Attempts decryption: `pow(c, d, n)` and checks if it matches the original flag.
6. If decryption fails (the result does not match the flag), the server leaks the ciphertext in the error message: `"Some unknown error occurred! Maybe you should take a look: {c}"`.

The server's validation checks are:
- `p` and `q` must be prime and at least 512 bits each
- `p * q == n`
- `e >= 65537`, `e` must be prime, `e.bit_count() <= 2` (so e = 65537)
- `gcd(e, phi) == 1` where `phi = (p-1)*(q-1)`
- `e * d mod phi == 1`
- CRT components `dmp1` and `dmq1` must be correct

### Approach

The critical vulnerability is that **the server never checks that p != q**.

When we submit a key with `p = q` (both the same 512-bit prime):
- `n = p^2`
- The server computes `phi = (p-1) * (q-1) = (p-1)^2`
- All validation checks pass (both primes are prime, both are 512+ bits, `e*d mod (p-1)^2 == 1`, etc.)

However, the **real** Euler totient of `n = p^2` is `phi(p^2) = p * (p-1)`, **not** `(p-1)^2`. Since the server's `d` was computed against the wrong totient, `pow(c, d, n)` will not recover the plaintext, causing the decryption check to fail and the server to leak the ciphertext `c`.

Once we have `c = pow(FLAG, e, p^2)`, we can compute the correct private exponent `d_real = e^{-1} mod p*(p-1)` and recover the flag: `FLAG = pow(c, d_real, p^2)`.

**Minor issue encountered:** The initial exploit attempted to compute `inverse(q, p)` for the `iqmp` CRT parameter, which fails when `p = q` (a number is not invertible modulo itself). Since the server does not check `iqmp`, this was simply set to `1`.

### Key Insight

The server validates RSA key parameters thoroughly but misses the fundamental check that `p != q`. Combined with `unsafe_skip_rsa_key_validation=True` (which lets the malformed key load in the first place), this allows an attacker to submit a key where `n = p^2`. The server's totient calculation `(p-1)^2` diverges from the real totient `p*(p-1)`, causing decryption to fail and leaking the ciphertext. The attacker can then decrypt using the correct totient.

## Flag
`BCCTF{R54_Br0K3n_C0nF1rm3d????}`
