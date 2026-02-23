---
author: Claude
credit: Claude, Fenix
---

:::blurb Fenix
I was really surprised that Claude was able to solve this before any other team was. Apparently, the way this challenge was implemented had some sort of flaw that made it much more difficult than intended.
:::

## Step 1: Deobfuscation

The challenge file `plank.py` is a single obfuscated line:

```python
print('You Made IT!!!!'if bytes([state:=[lambda x,y:[x[i]^x[(i+y)%len(x)] for i in range(len(x))],lambda x,y:[x[(i+y)%len(x)] for i in range(len(x))],lambda x,y:[x[i]^y for i in range(len(x))],lambda x,y:[x[i]*y%256 for i in range(len(x))],lambda x,y:[(x[i]+y)%256 for i in range(len(x))]][2*j%5](state if'state'in dir()else input('Walk the plank!\n').encode(),140*j+133)for j in range(100)][-1])==b'c\xc9\xa2+\xcf\xef\xd4+\xeb\x83w&\xe7\xfd\t\xde\xf3\xe5\xdeO\x13\x0bl\xb7\x1b\xab\x0f\x8a\x13\xc5\xfd\x92'else'Splash!!!')
```

This requires **Python 3.12** due to PEP 709 (inlined comprehensions), which makes the walrus operator (`:=`) visible to `dir()` within list comprehensions.

Deobfuscated, it applies 100 sequential transformations to the 32-byte input, cycling through 5 operations selected by `(2*j) % 5` with parameter `y = 140*j + 133`:

| Op | `(2*j)%5` | Operation | Description |
|----|-----------|-----------|-------------|
| 0  | 0         | `new[i] = old[i] ^ old[(i+y)%32]` | XOR with shifted self |
| 1  | 2         | `new[i] = old[i] ^ y` | XOR with constant |
| 2  | 4         | `new[i] = (old[i] + y) % 256` | Add constant mod 256 |
| 3  | 1         | `new[i] = old[(i+y)%32]` | Rotation/permutation |
| 4  | 3         | `new[i] = old[i] * y % 256` | Multiply mod 256 |

The cycle repeats 20 times (100 steps / 5 ops). The result must equal a 32-byte target.

## Step 2: Initial Analysis

Key observations:
- **Flag format**: `BCCTF{...}` -- 7 known bytes (positions 0-5 and 31), 25 unknown
- **All multiply constants are odd** (y mod 4 = 1 for all j), so multiplication is invertible mod 256
- **XOR-shift is the only non-invertible operation**: the matrix `I + P^s` over GF(2) has rank 31 (kernel = all-ones vector), since gcd(s, 32) = 1 for all shifts
- **20 XOR-shift steps** compound the rank deficiency: the composed GF(2) transformation matrix A has **rank 12** out of 32 (kernel dimension 20)

## Step 3: Failed Approaches

### Z3 SMT Solving (Multiple Variants)
- **Direct expressions** (no intermediate variables, `Then('simplify', 'bit-blast', 'sat')` tactic): Timed out at 10 minutes -- expressions too deeply nested
- **Intermediate variables** at each step with bit-blast tactic: Also timed out
- **Chain-structured** with variables only at XOR-shift boundaries: Timed out at 3 minutes

### Direct SAT Encoding (pysat)
- Manually encoded the Boolean circuit (XOR gates, ripple-carry adders, shift-and-add multipliers)
- CryptoMiniSat crashed; Glucose4 timed out building the circuit

### Backtracking with Parity Check
- Invert the chain step-by-step, using parity constraints to prune XOR-shift inversions
- Too many valid candidates per level (4-32 instead of ~1), creating exponential search tree

### Bit-Slicing GF(2) Solver (Python)
- Correct approach but had bugs with free variable enumeration
- Coupling between bit planes through carry constraints made naive enumeration fail

## Step 4: The Breakthrough -- Bit-Slicing with Carry-Consistency

### Core Insight: Bit-Plane Decomposition

In mod-256 arithmetic, **bit k of the output depends only on bits 0..k of the input** (carries propagate upward). This means we can solve 8 independent GF(2) systems, one per bit plane, from LSB to MSB.

For each bit plane k:
- The transformation is **affine over GF(2)**: `output_k = A * input_k + b_k`
- Matrix **A is identical** for all 8 planes (only XOR-shift and rotation contribute to the linear part)
- Constant vector **b_k differs** per plane (carries from bits 0..k-1 in add/multiply operations)
- A has rank 12 with 25 unknowns -> **13 free variables** (null space dimension) per plane

### The Carry-Consistency Constraint

The null space combo at bit plane k is constrained by the **consistency of the GF(2) system at bit plane k+1**. The key mathematical argument:

1. Flipping a null vector at bit k changes bit k of the initial flag at certain positions
2. This change propagates linearly through the 100-step transformation (XOR-shift and rotation are linear; add/mul have identity linear part since all constants are odd)
3. The changed intermediate states produce different carries into bit k+1
4. These carry changes affect the RHS of the bit k+1 system
5. The 20 redundant equations (32 equations - 12 rank) must still be satisfied -> **20 linear equations in 13 unknowns** constraining the null combo

### Special Structure: y mod 4 = 1

A critical discovery: since `y = 140j + 133` and `140 = 0 (mod 4)`, `133 = 1 (mod 4)`, we have **y mod 4 = 1 for ALL steps**. This means:

- **Bit 0 -> bit 1 carries cancel perfectly**: Each add step's carry delta equals `A * v = 0` (by definition of null space), so the bit 0 null combo is completely unconstrained by bit 1 consistency (all 8192 combos valid)
- **Higher bits DO provide constraints**: The carry coefficient becomes a non-identity diagonal matrix (depending on lower-bit carry values), breaking the cancellation

### Algorithm

```
1. Precompute A matrix (same for all bit planes)
2. Precompute consistency check matrix T (20 rows from RREF)
3. DFS over bit planes k = 0..7:
   a. Solve A*x_k = rhs_k -> particular solution + 13 null vectors
   b. For k < 7: compute carry deltas for each null vector
      -> build 20x13 GF(2) system -> solve for valid combos
   c. For k = 7: enumerate combos, check printability
   d. Recurse to k+1 with each valid combo
```

The pruning is dramatic: at each level, the 20x13 system typically has rank ~13, leaving 0-16 valid combos. The search tree is narrow enough to explore completely.

### Implementation in C

The Python implementation was too slow (~5 minutes for the DFS with 8192 bit-0 combos x recomputation of carries). Rewriting in C with `-O2` brought the solve time to **~10 seconds**.

## Step 5: Solution

```
$ ./solve_fast
Building A matrix...
Computing consistency check matrix...
  Consistency equations: 20
Starting DFS...

FLAG: BCCTF{y0U_mUs7_w4lK_A_f1N3_L1n3}
Verify: PASS
```

## Flag

```
BCCTF{y0U_mUs7_w4lK_A_f1N3_L1n3}
```

*"you must walk a fine line"* -- fitting the plank-walking theme.
