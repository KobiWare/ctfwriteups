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

print(f"E[0..15] = {E[:16]}")
print(f"E[316..320] = {E[316:321]}")
print(f"N_windows={N_windows}, W={W}, N={N} bits = {N//8} bytes")

# Compute differences: d[i] = E[i+1] - E[i] for i in 0..335
d = [E[i+1] - E[i] for i in range(N_windows - 1)]

# For each residue r mod W:
# Positions: r, r+W, r+2W, ...
# x[r + W*k] = x[r] + cumsum[k] where cumsum[0]=0, cumsum[k] = cumsum[k-1] + d[r + W*(k-1)]
# Constraint: x[r + W*k] in {0, 1} for all k
# => x[r] + cumsum[k] in {0, 1}
# => if x[r]=0: cumsum[k] in {0,1} for all k
# => if x[r]=1: cumsum[k] in {-1,0} for all k

solutions_per_residue = {}
print("\n--- Residue analysis ---")
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
    print(f"  r={r:2d}: b=0 valid={valid0}, b=1 valid={valid1}, K={K}, "
          f"cumsum range=[{min(cumsum)},{max(cumsum)}]")

# Check for problematic residues
problems = [r for r in range(W) if not solutions_per_residue[r][0] and not solutions_per_residue[r][1]]
if problems:
    print(f"\nProblematic residues: {problems}")
    for r in problems:
        _, _, cumsum, _, _ = solutions_per_residue[r]
        print(f"  r={r}: cumsum={cumsum}")

# Collect valid choices
valid_choices = []
for r in range(W):
    valid0, valid1, _, _, _ = solutions_per_residue[r]
    choices = []
    if valid0: choices.append(0)
    if valid1: choices.append(1)
    valid_choices.append(choices)

print(f"\nValid choices: {valid_choices}")

# Check if all residues have at least one choice
all_ok = all(len(c) > 0 for c in valid_choices)
print(f"All residues solvable: {all_ok}")

if all_ok:
    # Enumerate combinations with sum = E[0]
    target_sum = E[0]
    print(f"\nTarget window-0 sum: {target_sum}")
    
    found_solutions = []
    
    def backtrack(r, current_sum, chosen):
        if r == W:
            if current_sum == target_sum:
                found_solutions.append(chosen[:])
            return
        remaining = W - r
        for b in valid_choices[r]:
            new_sum = current_sum + b
            # Pruning
            if new_sum > target_sum:
                continue
            if new_sum + (remaining - 1) < target_sum:
                continue
            chosen.append(b)
            backtrack(r+1, new_sum, chosen)
            chosen.pop()
    
    backtrack(0, 0, [])
    print(f"Found {len(found_solutions)} solutions")
    
    def reconstruct_bits(initial_bits):
        bits = [0] * N
        for r in range(W):
            _, _, cumsum, positions, K = solutions_per_residue[r]
            b = initial_bits[r]
            for k, pos in enumerate(positions):
                bits[pos] = b + cumsum[k]
        return bits
    
    def verify(bits):
        for i in range(N_windows):
            s = sum(bits[i:i+W])
            if s != E[i]:
                return False, i
        return True, -1
    
    def bits_to_bytes(bits):
        result = []
        for bi in range(len(bits) // 8):
            val = 0
            for j in range(8):
                val |= bits[bi*8 + j] << (7-j)
            result.append(val)
        return bytes(result)
    
    print("\n--- Solutions ---")
    for idx, sol in enumerate(found_solutions):
        bits = reconstruct_bits(sol)
        ok, fail_i = verify(bits)
        if ok:
            data = bits_to_bytes(bits)
            text = data.decode('ascii', errors='replace')
            print(f"Solution {idx}: initial_bits={sol}")
            print(f"  Hex: {data.hex()}")
            print(f"  Text: {repr(text)}")
            
            # Check all 337 windows
            all_windows_ok = all(sum(bits[i:i+W]) == E[i] for i in range(N_windows))
            print(f"  All 337 windows verified: {all_windows_ok}")
        else:
            print(f"Solution {idx}: FAILED at window {fail_i}")

else:
    print("\nUsing ILP to solve...")
    import pulp
    
    prob = pulp.LpProblem("BitSolver", pulp.LpMinimize)
    x = [pulp.LpVariable(f"x{i}", cat='Binary') for i in range(N)]
    prob += 0
    for i in range(N_windows):
        prob += pulp.lpSum(x[i+j] for j in range(W)) == E[i]
    
    status = prob.solve(pulp.PULP_CBC_CMD(msg=0))
    print(f"ILP Status: {pulp.LpStatus[prob.status]}")
    
    if prob.status == 1:
        bits = [int(pulp.value(x[i])) for i in range(N)]
        data_bytes = bytes([sum(bits[bi*8+j] << (7-j) for j in range(8)) for bi in range(N//8)])
        print(f"Hex: {data_bytes.hex()}")
        print(f"Text: {repr(data_bytes.decode('ascii', errors='replace'))}")

