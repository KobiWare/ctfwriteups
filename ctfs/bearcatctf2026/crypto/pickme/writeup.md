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

### Solve Script

```python
from Crypto.Util.number import long_to_bytes, getPrime, inverse, GCD
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateNumbers,
    RSAPublicNumbers,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PrivateFormat,
    NoEncryption,
)
from cryptography.hazmat.backends import default_backend
import socket

e = 65537

# Find a 512-bit prime where gcd(e, (p-1)^2) = 1
while True:
    p = getPrime(512)
    if GCD(e, (p - 1) ** 2) == 1:
        break

q = p
n = p * q  # p^2
phi_fake = (p - 1) * (q - 1)  # (p-1)^2, what the server computes
d = inverse(e, phi_fake)

dmp1 = d % (p - 1)
dmq1 = d % (q - 1)
# inverse(q, p) doesn't exist when p=q, but iqmp isn't checked by the server
iqmp = 1

pub_numbers = RSAPublicNumbers(e, n)
priv_numbers = RSAPrivateNumbers(
    p=p,
    q=q,
    d=d,
    dmp1=dmp1,
    dmq1=dmq1,
    iqmp=iqmp,
    public_numbers=pub_numbers,
)

key = priv_numbers.private_key(unsafe_skip_rsa_key_validation=True)
pem = key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())

print("[*] Generated PEM key with p = q")
print(pem.decode())

# Connect to server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("chal.bearcatctf.io", 56025))

data = b""
while b"pem format:" not in data:
    data += sock.recv(4096)
print("[*] Got prompt, sending key...")

sock.sendall(pem + b"\n")

# Receive response
response = b""
while True:
    try:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response += chunk
    except:
        break

sock.close()
resp_text = response.decode()
print("[*] Server response:")
print(resp_text)

# Extract ciphertext
if "Maybe you should take a look:" in resp_text:
    c = int(resp_text.split("Maybe you should take a look:")[1].strip())
    print(f"[*] Got ciphertext c")

    # Real totient of p^2 is p*(p-1)
    phi_real = p * (p - 1)
    d_real = inverse(e, phi_real)
    flag_int = pow(c, d_real, n)
    flag = long_to_bytes(flag_int)
    print(f"[+] FLAG: {flag.decode()}")
else:
    print("[-] Exploit failed - decryption didn't fail on the server")
```

### Key Insight

The server validates RSA key parameters thoroughly but misses the fundamental check that `p != q`. Combined with `unsafe_skip_rsa_key_validation=True` (which lets the malformed key load in the first place), this allows an attacker to submit a key where `n = p^2`. The server's totient calculation `(p-1)^2` diverges from the real totient `p*(p-1)`, causing decryption to fail and leaking the ciphertext. The attacker can then decrypt using the correct totient.

## Flag
`BCCTF{R54_Br0K3n_C0nF1rm3d????}`
