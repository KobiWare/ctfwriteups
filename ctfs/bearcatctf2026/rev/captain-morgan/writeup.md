---
author: Claude
credit: Claude, Fenix
---
## Solution

### Analysis

The challenge provides a single file `chall.py` -- a heavily obfuscated Python script that reads user input and prints either "correct" or "incorrect". The obfuscation involves:

1. **Input parsing**: The script checks that input starts with `BCCTF{` and ends with `}`, then converts the inner content to a big integer via `int.from_bytes(agu[6:-1].encode())`.

2. **Walrus operator chains**: The integer is right-shifted 232 times through deeply nested walrus operator (`:=`) assignments, creating approximately 232 bit-position variables:
   ```python
   iv=(dr:=(bva:=(btt:=(...(yu:=(ari)>>bhy)>>bhy)>>bhy)...
   ```
   Since `bhy = 1` (from `agu.startswith("BCCTF{")`), each shift extracts the next bit position.

3. **Boolean circuit**: The extracted bits are combined through hundreds of AND (`&`), OR (`|`), XOR (`^`) operations, ultimately computing a final variable `bfu`.

4. **Verification**: The script prints `"in" * bfu + "correct"` -- meaning it prints "correct" when `bfu == 0` and "incorrect" otherwise.

### Approach

Rather than trying to reverse the boolean circuit by hand, the entire script was translated into a **Z3 SMT constraint satisfaction problem**:

1. Parse each semicolon-separated statement in `chall.py`
2. Replace the input integer `ari` with a symbolic Z3 bitvector
3. Set `bhy = 1` and `aja = 1` (assuming valid flag format)
4. Simulate each walrus chain as logical right-shifts
5. Translate all `&`, `|`, `^`, `>>` operations into Z3 symbolic operations
6. Add the constraint `bfu == 0` (the "correct" condition)
7. Add printable ASCII constraints for each byte of the flag content
8. Let Z3 find the satisfying assignment

### Solve Script

```python
from z3 import *
import re

with open('/home/kali/work/chal16/chall.py') as f:
    code = f.read()

stmts = [s.strip() for s in code.split(';')]

N = 256  # Bit width for Z3 bitvectors
ari_z3 = BitVec('ari', N)

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
    if not stmt or stmt.startswith('agu=') or stmt.startswith('bhy=') \
       or stmt.startswith('aja=') or stmt.startswith('ari=') \
       or stmt.startswith('print('):
        continue
    if '=' not in stmt:
        continue

    if ':=' in stmt:
        # Walrus operator chain (shift chain)
        outer = stmt.split('=', 1)[0].strip()
        names = re.findall(r'(\w+):=', stmt)
        names.reverse()
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
        lhs, rhs = lhs.strip(), rhs.strip()
        done = False
        for op, z3op in [
            ('>>', lambda a, b: LShR(a, b)),
            ('^', lambda a, b: a ^ b),
            ('&', lambda a, b: a & b),
            ('|', lambda a, b: a | b),
        ]:
            if not done and op in rhs:
                parts = rhs.split(op, 1)
                env[lhs] = z3op(val(parts[0]), val(parts[1]))
                done = True
        if not done:
            env[lhs] = val(rhs)

s = Solver()
s.add(env['bfu'] == BitVecVal(0, N))
s.add(LShR(ari_z3, 233) == BitVecVal(0, N))

for i in range(29):
    byte_i = Extract(i*8+7, i*8, ari_z3)
    s.add(Or(byte_i == 0, And(byte_i >= 0x20, byte_i <= 0x7e)))

result = s.check()
if result == sat:
    model = s.model()
    ari_val = model[ari_z3].as_long()
    byte_len = max(1, (ari_val.bit_length() + 7) // 8)
    content = ari_val.to_bytes(byte_len, 'big')
    flag = "BCCTF{" + content.decode() + "}"
    print(f"Flag: {flag}")
```

The solver ran quickly and produced the flag, which was then verified against the original challenge script:

```bash
$ echo 'BCCTF{Y00_hO_Ho_anD_4_B07Tl3_oF_rUm}' | python3 chall.py
correct
```

## Flag
`BCCTF{Y00_hO_Ho_anD_4_B07Tl3_oF_rUm}`
