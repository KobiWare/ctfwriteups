---
author: Claude
credit: Claude, Fenix
---
## Solution

### Analysis
The challenge provides a single ELF 64-bit x86-64 binary called `horizon`. Running it displays:

```
You see a fleet of pirates approaching on the horizon. In order to survive this encounter, you must raise their flag:
```

It then reads user input via `scanf` and checks it against some internal data. If correct, it prints a congratulations message; otherwise, it says you did not raise the correct flag.

### Approach

**Step 1: Static Analysis**

Using `objdump` to disassemble the binary revealed the core logic in `main`:
1. The binary reads user input into a buffer.
2. It treats the input as a raw bit array (MSB-first per byte).
3. For each of 337 positions `i` (0 to 336, i.e., `0x150`), it computes a **sliding window** of 16 consecutive bits starting at position `i`.
4. It counts the number of set bits (popcount) in each window.
5. It compares each popcount against a table of 337 expected values stored in the `.data` section at virtual address `0x4020`.

The total number of bits needed is 337 + 16 - 1 = 352 bits = 44 bytes, which is exactly the length of the flag string `BCCTF{5LiD1n6_W1nd0w5_B3_L1k3:1m_C0nvo1v1nG}`.

**Step 2: Extracting the Expected Values**

The expected popcount values were extracted from the binary at file offset `0x3020` (since `.data` section has VA `0x4000` mapped to file offset `0x3000`, so `0x4020` maps to `0x3020`):

```python
with open('horizon', 'rb') as f:
    binary = f.read()
E = list(binary[0x3020:0x3020+337])
```

The values ranged from 5 to 11 (popcount of a 16-bit window).

**Step 3: Solving the Constraint System**

The key mathematical insight is that consecutive windows overlap by 15 bits. The difference between consecutive expected values tells us whether the new bit entering the window is the same as the bit leaving:

- `d[i] = E[i+1] - E[i]` gives the net change, which equals `bit[i+16] - bit[i]`.

For each residue class `r mod 16`, the bits at positions `r, r+16, r+32, ...` form an independent chain where each successive bit is determined by the differences. The solver:

1. Computed cumulative sums for each of the 16 residue classes.
2. For each residue, determined whether the initial bit must be 0 or 1 (or either) based on the constraint that all bits in the chain remain in {0, 1}.
3. Used backtracking to enumerate all valid combinations of the 16 initial bits that sum to `E[0]` (the first window's popcount).
4. Reconstructed the full 352-bit array and converted to bytes.

An initial attempt had byte-swap issues at indices 316 and 317, which was resolved by reading the expected values directly from the binary rather than a hand-transcribed hex dump.

**Step 4: Verification**

The recovered flag was piped into the binary and confirmed:

```bash
$ echo "BCCTF{5LiD1n6_W1nd0w5_B3_L1k3:1m_C0nvo1v1nG}" | ./horizon
You see a fleet of pirates approaching on the horizon. In order to survive this encounter, you must raise their flag: Congratulations! You raised the right flag and the pirates didn't think twice!
```

### Solve Script

```python
#!/usr/bin/env python3
# CTF Challenge: horizon
# Read actual expected values from binary

with open('/home/kali/work/chal60/horizon', 'rb') as f:
    binary = f.read()

# VA 0x4020 -> file offset 0x3020 (data section: VA 0x4000, file 0x3000)
E = list(binary[0x3020:0x3020+337])
N_windows = 337
W = 16  # window size: bits i to i+15 inclusive
N = N_windows + W - 1  # = 352 total bits needed

# Compute differences: d[i] = E[i+1] - E[i] for i in 0..335
d = [E[i+1] - E[i] for i in range(N_windows - 1)]

# For each residue r mod W:
# Positions: r, r+W, r+2W, ...
# x[r + W*k] = x[r] + cumsum[k]
# Constraint: x[r + W*k] in {0, 1} for all k

solutions_per_residue = {}
for r in range(W):
    positions = list(range(r, N, W))
    K = len(positions)

    cumsum = [0] * K
    for k in range(1, K):
        d_idx = r + W*(k-1)
        cumsum[k] = cumsum[k-1] + d[d_idx]

    valid0 = all(c in (0, 1) for c in cumsum)
    valid1 = all(c in (-1, 0) for c in cumsum)

    solutions_per_residue[r] = (valid0, valid1, cumsum, positions, K)

# Collect valid choices
valid_choices = []
for r in range(W):
    valid0, valid1, _, _, _ = solutions_per_residue[r]
    choices = []
    if valid0: choices.append(0)
    if valid1: choices.append(1)
    valid_choices.append(choices)

# Enumerate combinations with sum = E[0]
target_sum = E[0]
found_solutions = []

def backtrack(r, current_sum, chosen):
    if r == W:
        if current_sum == target_sum:
            found_solutions.append(chosen[:])
        return
    remaining = W - r
    for b in valid_choices[r]:
        new_sum = current_sum + b
        if new_sum > target_sum:
            continue
        if new_sum + (remaining - 1) < target_sum:
            continue
        chosen.append(b)
        backtrack(r+1, new_sum, chosen)
        chosen.pop()

backtrack(0, 0, [])

def reconstruct_bits(initial_bits):
    bits = [0] * N
    for r in range(W):
        _, _, cumsum, positions, K = solutions_per_residue[r]
        b = initial_bits[r]
        for k, pos in enumerate(positions):
            bits[pos] = b + cumsum[k]
    return bits

def bits_to_bytes(bits):
    result = []
    for bi in range(len(bits) // 8):
        val = 0
        for j in range(8):
            val |= bits[bi*8 + j] << (7-j)
        result.append(val)
    return bytes(result)

for idx, sol in enumerate(found_solutions):
    bits = reconstruct_bits(sol)
    ok = all(sum(bits[i:i+W]) == E[i] for i in range(N_windows))
    if ok:
        data = bits_to_bytes(bits)
        text = data.decode('ascii', errors='replace')
        print(f"Solution {idx}: {repr(text)}")
```

## Flag
`BCCTF{5LiD1n6_W1nd0w5_B3_L1k3:1m_C0nvo1v1nG}`
