from Crypto.Util.number import long_to_bytes
from itertools import product as iterproduct
from sympy.ntheory.modular import crt
from sympy import factorint

n = 147411106158287041622784593501613775873740698182074300197321802109276152016347880921444863007
e = 3
c = 114267757154492856513993877195962986022489770009120200367811440852965239059854157313462399351

# Factor n (13 small primes)
factors_dict = factorint(n)
factors = list(factors_dict.keys())

# Find all cube roots mod each prime factor
roots_per_prime = []
for p in factors:
    cp = c % p
    roots = [x for x in range(p) if pow(x, 3, p) == cp]
    roots_per_prime.append(roots)

# CRT to combine all combinations, filter for printable ASCII
best_score = 0
best_result = None

for combo in iterproduct(*roots_per_prime):
    remainders = list(combo)
    m, mod = crt(factors, remainders)
    m = int(m)
    if pow(m, 3, n) != c:
        continue
    flag = long_to_bytes(m)

    # Count printable ASCII bytes
    printable = sum(1 for b in flag if 32 <= b < 127)
    score = printable / len(flag) if flag else 0

    if score > best_score:
        best_score = score
        best_result = flag
        if score > 0.8:
            print(f"Score {score:.2f}: {flag}")

print(f"\nBest result: {best_result}")
