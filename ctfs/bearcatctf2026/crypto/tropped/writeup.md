---
author: Claude
credit: Claude, Fenix
---
## Solution

### Analysis

We are given two files:
- `tropped.py` -- The encryption implementation using tropical (min-plus) semiring matrix multiplication.
- `output.txt` -- A JSONL file where the first line contains a shared 64x64 matrix `M`, and each subsequent line (41 total) contains `aM` (a 1x64 row vector), `Mb` (a 64x1 column vector), and an encrypted character `enc_char`.

The tropical semiring replaces standard addition with `min` and standard multiplication with `+`. Matrix "multiplication" in this semiring computes:

```
(A * B)[i][j] = min over k of (A[i][k] + B[k][j])
```

The scheme implements a Diffie-Hellman-like key exchange:
1. A shared matrix `M` (64x64) is public.
2. Alice picks a secret row vector `a` (1x64), Bob picks a secret column vector `b` (64x1).
3. Alice publishes `aM` (1x64), Bob publishes `Mb` (64x1).
4. The shared secret is the scalar `aMb = min_j(aM[j] + b[j])`.
5. Each flag character is encrypted as `chr((aMb % 32) ^ ord(plaintext_char))`.

A MITM attacker sees `M`, `aM`, and `Mb` for each character but not `a` or `b`.

### Approach

The key insight is **tropical residuation**. Even though traditional matrix inverses do not exist in the tropical semiring, we can recover a functional equivalent of Bob's secret vector `b` using residuation.

Given `Mb` and `M`, we compute:

```
b'[j] = max over i of (Mb[i] - M[i][j])
```

This `b'` is the **greatest** vector satisfying `M (tropical-multiply) b' = Mb`. Since the true `b` is a solution (it produced `Mb`), and `b'` is the greatest such solution, we are guaranteed that `M (tropical-multiply) b' = Mb` exactly.

Therefore:

```
aM (tropical-multiply) b' = aMb
```

This gives us the shared secret scalar, and we can decrypt each character.

No false starts were encountered -- the tropical residuation approach worked on the first attempt.

### Key Insight

The tropical semiring cryptosystem is insecure because **tropical residuation** acts as a functional substitute for matrix inversion. Given the public matrix `M` and one side's public output `Mb`, an attacker can compute a vector `b'` that produces the same shared secret as the real `b`. This completely breaks the one-way assumption the cryptosystem relies on.

## Flag
`BCCTF{1_h4T3_M7_Tr0p93D_4Hh_CRyp705ysT3m}`
