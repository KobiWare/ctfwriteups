#!/usr/bin/env python3
"""
Bit-slicing solver with corrected GF(2) Gaussian elimination.
Handles free variables by enumerating all 2^(num_free) possibilities.
"""
import itertools

target = b'c\xc9\xa2+\xcf\xef\xd4+\xeb\x83w&\xe7\xfd\t\xde\xf3\xe5\xdeO\x13\x0bl\xb7\x1b\xab\x0f\x8a\x13\xc5\xfd\x92'
n = 32

def forward(flag_bytes):
    state = list(flag_bytes)
    for j in range(100):
        y = 140*j + 133
        op = (2*j) % 5
        if op == 0: state = [state[i] ^ state[(i+y)%n] for i in range(n)]
        elif op == 1: state = [state[(i+y)%n] for i in range(n)]
        elif op == 2: state = [state[i] ^ y for i in range(n)]
        elif op == 3: state = [state[i] * y % 256 for i in range(n)]
        elif op == 4: state = [(state[i] + y) % 256 for i in range(n)]
    return bytes(state)

def mat_mul(A, B):
    BT = [0]*n
    for i in range(n):
        for j in range(n):
            if B[i] & (1<<j): BT[j] |= (1<<i)
    R = [0]*n
    for i in range(n):
        for j in range(n):
            if bin(A[i] & BT[j]).count('1') & 1: R[i] |= (1<<j)
    return R

def mat_vec(A, v):
    r = 0
    for i in range(n):
        if bin(A[i] & v).count('1') & 1: r |= (1<<i)
    return r

def identity():
    return [(1<<i) for i in range(n)]

def forward_partial_all(flag_vals, mask):
    state = [f & mask for f in flag_vals]
    history = [list(state)]
    for j in range(100):
        y = 140*j + 133
        op = (2*j) % 5
        if op == 0: state = [(state[i] ^ state[(i+y)%n]) & mask for i in range(n)]
        elif op == 1: state = [state[(i+y)%n] for i in range(n)]
        elif op == 2: state = [(state[i] ^ (y & 0xFF)) & mask for i in range(n)]
        elif op == 3: state = [(state[i] * (y%256)) & mask for i in range(n)]
        elif op == 4: state = [(state[i] + (y%256)) & mask for i in range(n)]
        history.append(list(state))
    return history

def solve_gf2_all(A_full, rhs_full, unknowns, knowns):
    """Solve A*x = rhs over GF(2). Returns (particular_solution, null_space_vectors)."""
    num_unk = len(unknowns)

    # Adjust RHS for known values
    rhs = rhs_full
    for pos, val in knowns.items():
        if val:
            col = 0
            for row in range(n):
                if A_full[row] & (1 << pos):
                    col |= (1 << row)
            rhs ^= col

    # Extract submatrix: n rows x num_unk cols
    mat = [0] * n
    rhs_bits = [0] * n
    for row in range(n):
        r = 0
        for idx, u in enumerate(unknowns):
            if A_full[row] & (1 << u):
                r |= (1 << idx)
        mat[row] = r
        rhs_bits[row] = (rhs >> row) & 1

    # Gaussian elimination
    pivot_row = {}  # col -> row index after elimination
    cur_row = 0
    for col in range(num_unk):
        # Find pivot
        piv = -1
        for row in range(cur_row, n):
            if mat[row] & (1 << col):
                piv = row
                break
        if piv == -1:
            continue

        # Swap to cur_row
        mat[piv], mat[cur_row] = mat[cur_row], mat[piv]
        rhs_bits[piv], rhs_bits[cur_row] = rhs_bits[cur_row], rhs_bits[piv]

        pivot_row[col] = cur_row

        # Eliminate
        for row in range(n):
            if row != cur_row and mat[row] & (1 << col):
                mat[row] ^= mat[cur_row]
                rhs_bits[row] ^= rhs_bits[cur_row]

        cur_row += 1

    # Check consistency
    for row in range(n):
        if mat[row] == 0 and rhs_bits[row] == 1:
            return None, None  # Inconsistent

    # Identify free variables
    free_cols = [col for col in range(num_unk) if col not in pivot_row]

    # Particular solution (free vars = 0)
    particular = [0] * num_unk
    for col, row in pivot_row.items():
        particular[col] = rhs_bits[row]

    # Null space basis vectors
    null_vecs = []
    for fc in free_cols:
        vec = [0] * num_unk
        vec[fc] = 1
        # For each pivot column, check if it depends on this free column
        for col, row in pivot_row.items():
            if mat[row] & (1 << fc):
                vec[col] = 1
        null_vecs.append(vec)

    return particular, null_vecs

def build_affine_transform(k, history):
    """Build the composed affine transformation (A, b) for bit plane k."""
    A = identity()
    b = 0
    mask = (1 << k) - 1

    for j in range(100):
        y = 140*j + 133
        op = (2*j) % 5

        if op == 0:  # XOR shift
            s = y % n
            A_j = [0]*n
            for i in range(n):
                A_j[i] = (1<<i) | (1<<((i+s)%n))
            b = mat_vec(A_j, b)
            A = mat_mul(A_j, A)

        elif op == 1:  # Rotation
            r = y
            A_j = [0]*n
            for i in range(n):
                A_j[i] = 1 << ((i+r)%n)
            b = mat_vec(A_j, b)
            A = mat_mul(A_j, A)

        elif op == 2:  # XOR const
            y_low = y & 0xFF
            if (y_low >> k) & 1:
                b ^= (1<<n) - 1

        elif op == 3:  # Multiply
            y_mul = y % 256
            b_j = 0
            for i in range(n):
                val = (history[j][i] * y_mul) if k > 0 else 0
                b_j |= (((val >> k) & 1) << i)
            b ^= b_j

        elif op == 4:  # Add
            y_add = y % 256
            add_k = (y_add >> k) & 1
            b_j = 0
            if k > 0:
                y_add_low = y_add & mask
                for i in range(n):
                    carry = ((history[j][i] + y_add_low) >> k) & 1
                    b_j |= ((add_k ^ carry) << i)
            else:
                if add_k:
                    b_j = (1<<n) - 1
            b ^= b_j

    return A, b

# Known flag bytes
flag_known = {0: ord('B'), 1: ord('C'), 2: ord('C'), 3: ord('T'),
              4: ord('F'), 5: ord('{'), 31: ord('}')}
known_positions = set(flag_known.keys())
unknown_positions = sorted(set(range(n)) - known_positions)

# Solve all 8 bit planes, collecting free variable choices
flag_vals = [0] * n
for pos, val in flag_known.items():
    flag_vals[pos] = val

all_free_choices = []  # List of (bit_plane, null_vecs, particular, unknowns)

print("Solving bit planes...")
for k in range(8):
    mask = (1 << k) - 1
    history = forward_partial_all(flag_vals, mask) if k > 0 else [[0]*n]*101

    A, b = build_affine_transform(k, history)

    target_bits = 0
    for i in range(n):
        target_bits |= (((target[i] >> k) & 1) << i)
    rhs = target_bits ^ b

    knowns_k = {pos: (val >> k) & 1 for pos, val in flag_known.items()}

    particular, null_vecs = solve_gf2_all(A, rhs, unknown_positions, knowns_k)
    if particular is None:
        print(f"  Bit {k}: INCONSISTENT - trying with current flag state")
        break

    num_free = len(null_vecs)
    print(f"  Bit {k}: rank deficit = {num_free} free variable(s)")

    if num_free == 0:
        # Unique solution
        for idx, pos in enumerate(unknown_positions):
            flag_vals[pos] |= (particular[idx] << k)
    else:
        # Try all combinations of free variables
        all_free_choices.append((k, particular, null_vecs))
        # For now, use particular solution (free vars = 0)
        for idx, pos in enumerate(unknown_positions):
            flag_vals[pos] |= (particular[idx] << k)

# Enumerate free variable combinations
total_free = sum(len(nv) for _, _, nv in all_free_choices)
print(f"\nTotal free variables: {total_free}")
print(f"Enumerating {2**total_free} combinations...")

# Build list of all free variable flips
free_bits = []  # (bit_plane, null_vec_index, null_vec)
for k, particular, null_vecs in all_free_choices:
    for nvi, nv in enumerate(null_vecs):
        free_bits.append((k, nv))

best_flag = None
for combo in itertools.product([0, 1], repeat=total_free):
    # Start from particular solution
    test_flag = list(flag_vals)  # Already has particular solutions set

    # First, reset the bits for planes with free variables
    for k, particular, null_vecs in all_free_choices:
        for idx, pos in enumerate(unknown_positions):
            test_flag[pos] &= ~(1 << k)  # Clear bit k
            test_flag[pos] |= (particular[idx] << k)  # Set particular

    # Apply free variable flips
    for fi, (k, nv) in enumerate(free_bits):
        if combo[fi]:
            for idx, pos in enumerate(unknown_positions):
                if nv[idx]:
                    test_flag[pos] ^= (1 << k)

    # Check constraints
    ok = True
    for pos, val in flag_known.items():
        if test_flag[pos] != val:
            ok = False
            break
    if not ok:
        continue

    # Check printable ASCII
    all_print = True
    for i in range(6, 31):
        if test_flag[i] < 0x20 or test_flag[i] > 0x7E:
            all_print = False
            break
    if not all_print:
        continue

    # Verify forward
    result = forward(bytes(test_flag))
    if result == target:
        best_flag = bytes(test_flag)
        print(f"\nFLAG FOUND: {best_flag.decode()}")
        break

if best_flag is None:
    # Also try without printability constraint
    print("\nTrying without printability constraint...")
    for combo in itertools.product([0, 1], repeat=total_free):
        test_flag = list(flag_vals)
        for k, particular, null_vecs in all_free_choices:
            for idx, pos in enumerate(unknown_positions):
                test_flag[pos] &= ~(1 << k)
                test_flag[pos] |= (particular[idx] << k)
        for fi, (k, nv) in enumerate(free_bits):
            if combo[fi]:
                for idx, pos in enumerate(unknown_positions):
                    if nv[idx]:
                        test_flag[pos] ^= (1 << k)
        result = forward(bytes(test_flag))
        if result == target:
            best_flag = bytes(test_flag)
            print(f"FLAG FOUND: {best_flag}")
            try:
                print(f"Decoded: {best_flag.decode()}")
            except:
                print("(not decodable as UTF-8)")
            break

if best_flag is None:
    print("No solution found!")
