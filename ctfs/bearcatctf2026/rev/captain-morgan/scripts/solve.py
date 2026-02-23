from z3 import *
import re

with open('/home/kali/work/chal16/chall.py') as f:
    code = f.read()

# Split into statements by semicolons
stmts = [s.strip() for s in code.split(';')]

N = 256  # Bit width for Z3 bitvectors

# Z3 variable for the flag content integer
ari_z3 = BitVec('ari', N)

# Environment mapping variable names to Z3 expressions
env = {
    'ari': ari_z3,
    'bhy': BitVecVal(1, N),  # True - starts with BCCTF{
    'aja': BitVecVal(1, N),  # True - ends with }
}

def val(name):
    name = name.strip()
    if name in env:
        return env[name]
    return BitVecVal(int(name), N)

for stmt in stmts:
    stmt = stmt.strip()
    if not stmt:
        continue

    # Skip special statements
    if stmt.startswith('agu=') or stmt.startswith('bhy=') or stmt.startswith('aja=') or stmt.startswith('ari=') or stmt.startswith('print('):
        continue

    if '=' not in stmt:
        continue

    if ':=' in stmt:
        # Walrus operator chain (shift chain)
        outer = stmt.split('=', 1)[0].strip()
        names = re.findall(r'(\w+):=', stmt)
        names.reverse()  # innermost first
        names.append(outer)

        m = re.search(r'\((\w+)\)>>(\w+)\)', stmt)
        base = val(m.group(1))
        shift = val(m.group(2))

        prev = base
        for n in names:
            prev = LShR(prev, shift)
            env[n] = prev
    else:
        lhs, rhs = stmt.split('=', 1)
        lhs = lhs.strip()
        rhs = rhs.strip()

        done = False
        if '>>' in rhs:
            parts = rhs.split('>>', 1)
            env[lhs] = LShR(val(parts[0]), val(parts[1]))
            done = True

        if not done and '^' in rhs:
            parts = rhs.split('^', 1)
            env[lhs] = val(parts[0]) ^ val(parts[1])
            done = True

        if not done and '&' in rhs:
            parts = rhs.split('&', 1)
            env[lhs] = val(parts[0]) & val(parts[1])
            done = True

        if not done and '|' in rhs:
            parts = rhs.split('|', 1)
            env[lhs] = val(parts[0]) | val(parts[1])
            done = True

        if not done:
            env[lhs] = val(rhs)

# Solve
s = Solver()
s.add(env['bfu'] == BitVecVal(0, N))
# Flag content fits in ~232 bits (29 bytes)
s.add(LShR(ari_z3, 233) == BitVecVal(0, N))

# Add printable ASCII constraints for each byte
for i in range(29):
    byte_i = Extract(i*8+7, i*8, ari_z3)
    # Either the byte is 0 (padding) or printable ASCII (0x20-0x7e)
    s.add(Or(byte_i == 0, And(byte_i >= 0x20, byte_i <= 0x7e)))

print("Solving...", flush=True)
result = s.check()
print(f"Result: {result}", flush=True)

if result == sat:
    model = s.model()
    ari_val = model[ari_z3].as_long()
    byte_len = max(1, (ari_val.bit_length() + 7) // 8)
    content = ari_val.to_bytes(byte_len, 'big')
    print(f"Content bytes: {content}")
    try:
        flag = "BCCTF{" + content.decode() + "}"
        print(f"Flag: {flag}")
    except:
        print(f"Hex: {content.hex()}")
elif result == unsat:
    print("UNSAT - no solution exists")
else:
    print("Unknown")
