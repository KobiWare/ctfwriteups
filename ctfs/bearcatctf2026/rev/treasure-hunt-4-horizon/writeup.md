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

## Flag
`BCCTF{5LiD1n6_W1nd0w5_B3_L1k3:1m_C0nvo1v1nG}`
