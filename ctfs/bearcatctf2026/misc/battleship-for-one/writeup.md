---
author: Claude
credit: Claude, Fenix
---
## Solution

### Analysis

The challenge (`battleship.py`) implements a "find the battleship" game:

1. A board of size `n x n` is initialized with a fixed basis of values `0` to `n^2 - 1` (not in order -- each difficulty has a specific basis layout).
2. The board is **shuffled** using a random seed by repeatedly applying row and column permutations.
3. The player must find cell containing `0` (the "battleship") within a limited number of guesses.
4. The **Ultimate Challenge** requires winning 30 consecutive games: 10 easy (3x3, 5 attempts), 10 medium (10x10, 20 attempts), and 10 hard (30x30, 30 attempts).

The key code in the shuffle:

```python
def shuffle(self, seed):
    while seed:
        self.row_round(self.gen_map(seed % self.round_size))
        seed //= self.round_size
        self.col_round(self.gen_map(seed % self.round_size))
        seed //= self.round_size
```

`row_round` and `col_round` apply permutations to rows and columns respectively. Crucially, the composition of multiple row permutations is still a single row permutation, and likewise for columns. So the entire shuffle reduces to **one row permutation + one column permutation**.

### Approach

#### Key Insight: Diagonal Probing

Since the shuffle is just a row permutation `sigma` composed with a column permutation `tau`, a value originally at position `(r, c)` in the basis ends up at position `(sigma(r), tau(c))` in the shuffled board.

By **guessing along the diagonal** `(0,0), (1,1), (2,2), ...`:

- When we guess `(i, i)` and receive value `v`, we know that `v` was originally at position `(orig_r, orig_c)` in the basis (which we can precompute).
- Since the value ended up at row `i`, we know `sigma(orig_r) = i`, giving us one entry of the row permutation inverse: `sigma_inv[i] = orig_r`.
- Since the value ended up at column `i`, we know `tau(orig_c) = i`, giving us one entry of the column permutation inverse: `tau_inv[i] = orig_c`.

After `n-1` diagonal guesses, both permutations are fully determined by elimination (the remaining unmapped row/column is determined). We can then compute exactly where `0` ended up and guess it with our final attempt.

#### Budget Analysis

- **Easy (3x3, 5 attempts)**: 2 diagonal + 1 final = 3 guesses needed (2 spare)
- **Medium (10x10, 20 attempts)**: 9 diagonal + 1 final = 10 guesses needed (10 spare)
- **Hard (30x30, 30 attempts)**: 29 diagonal + 1 final = 30 guesses needed (exactly fits!)

The hard mode is perfectly tight -- every single guess must be used optimally.

### Solve Script

```python
#!/usr/bin/env python3
from pwn import *
import sys

# Board configurations from the source
easy_basis = [2, 3, 1, 6, 0, 8, 5, 4, 7]
medium_basis = [25, 32, 97, 0, 18, ...]  # full list from source
hard_basis = [97, 726, 67, 4, 578, ...]  # full list from source

configs = [
    ("easy",   3,  5,  easy_basis),
    ("medium", 10, 20, medium_basis),
    ("hard",   30, 30, hard_basis),
]

def build_val_pos(size, basis):
    """Map each value to its original (row, col) position."""
    val_pos = {}
    for i, v in enumerate(basis):
        val_pos[v] = (i // size, i % size)
    return val_pos

def play_round(r, size, attempts, basis, diff_name, round_num):
    val_pos = build_val_pos(size, basis)
    zero_orig_r, zero_orig_c = val_pos[0]

    sigma_inv = {}  # new_row -> orig_row
    tau_inv = {}    # new_col -> orig_col

    r.recvuntil(b'Where is the battleship > ')

    for diag in range(size - 1):
        r.sendline(f'{diag} {diag}'.encode())
        response = r.recvuntil([
            b'Where is the battleship > ',
            b'Yay you won!',
            b'Try again'
        ])

        if b'Yay you won!' in response:
            return True
        if b'Try again' in response:
            return False

        # Parse revealed value at (diag, diag)
        value = parse_revealed_value(response.decode(), diag, size)
        orig_r, orig_c = val_pos[value]
        sigma_inv[diag] = orig_r
        tau_inv[diag] = orig_c

    # Last mapping determined by elimination
    all_indices = set(range(size))
    remaining_row = (all_indices - set(sigma_inv.values())).pop()
    remaining_col = (all_indices - set(tau_inv.values())).pop()
    sigma_inv[size - 1] = remaining_row
    tau_inv[size - 1] = remaining_col

    # Build forward maps
    sigma = {orig: new for new, orig in sigma_inv.items()}
    tau = {orig: new for new, orig in tau_inv.items()}

    # Compute where 0 ended up
    zero_new_r = sigma[zero_orig_r]
    zero_new_c = tau[zero_orig_c]

    r.sendline(f'{zero_new_r} {zero_new_c}'.encode())
    response = r.recvuntil([b'Yay you won!', b'Try again'])
    return b'Yay you won!' in response

def main():
    if len(sys.argv) > 1:
        r = remote(sys.argv[1], int(sys.argv[2]))
    else:
        r = process(['python3', 'battleship.py'])

    r.recvuntil(b'5. Exit')
    r.sendline(b'4')  # Ultimate Challenge

    for diff_name, size, attempts, basis in configs:
        for round_num in range(10):
            if not play_round(r, size, attempts, basis, diff_name, round_num + 1):
                log.error(f'Failed at {diff_name} round {round_num + 1}!')
                return

    r.recvuntil(b'greatest admiral')
    remaining = r.recvall(timeout=5).decode()
    log.success(f'Flag: {remaining.strip()}')
    r.close()

if __name__ == '__main__':
    main()
```

Running against the remote server:
```bash
python3 solve.py chal.bearcatctf.io 45457
```

All 30 rounds were won successfully, and the server printed the flag.

## Flag
`BCCTF{S0r7_0f_L1k3_SuD0ku}`
