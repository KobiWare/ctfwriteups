---
author: Claude
credit: Claude, Fenix
---
## Solution

### Analysis

We are given two files:
- `twisted.py` -- The encryption script.
- `output.txt` -- The output containing RSA parameters `e`, `n`, `c`, and a "twisted" pair `(re, rd)`.

The encryption script does standard RSA encryption of the flag:

```python
pub, priv = genRSA()
n, e = pub
phi, d = priv
c = pow(m, e, n)
```

It then generates a "twisted" keypair:

```python
big_phi = random.randint(0, n) * phi
while True:
    re = random.randint(0, big_phi)
    if GCD(re, big_phi) == 1:
        break
rd = pow(re, -1, big_phi)
pair = (re, rd)
```

So `re * rd = 1 (mod big_phi)`, where `big_phi = k * phi(n)` for some random `k`.

### Approach

The critical observation is straightforward: since `re * rd = 1 (mod k * phi(n))`, the value `re * rd - 1` is a **multiple of phi(n)**.

For RSA decryption, we do not actually need `phi(n)` itself -- any multiple of `phi(n)` works as the modulus for computing the private exponent. Specifically:

```
d = e^{-1} mod (re * rd - 1)
```

Since `re * rd - 1` is a multiple of `phi(n)`, and `gcd(e, phi(n)) = 1`, this inverse exists and produces a valid decryption exponent. Then:

```
m = pow(c, d, n)
```

This was solved in a single step with no false starts.

### Key Insight

The "twisted" pair `(re, rd)` satisfies `re * rd = 1 (mod k * phi(n))`, which means `re * rd - 1` is a multiple of `phi(n)`. Since RSA decryption works with any multiple of `phi(n)` as the modulus for computing `d`, the private exponent can be derived directly from the leaked pair without needing to factor `n` or recover `phi(n)` exactly.

## Flag
`BCCTF{D0n7_g37_m3_Tw157eD}`
