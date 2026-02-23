from hashlib import sha1
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from sympy.ntheory import factorint
import math, random

curves = {"Daquavious Pork": (92477645447719597722241924944220804509189685020218853319582456492812008432951, 12077440433756325151450430637702142241115682027769009672424134533824264621982, 5820075301718484807190615376227445775094236611137942662646164904513344955506, 79756563336507309847840508616642202952716246885851710551602577895600001192101, (23535374861808337349161906509731226338003476556014177115380062081237358087693, 40704090379575014906510835547748879494479225636219808088614211329238685473492))}

Apub = (19999980900332548666647825711719038277575827040455645145254638510596245466124, 74074723990829271510242905157744389162286139267930898572127411005358889867706)
Bpub = (9933922657317675684240599494550017485660256920888896442872535198890063987564, 6391239582083802949950091900262307697706602880557844650164383022670939711034)
ct_data = {'iv': '2b7ac2eef33b5ad9c033dd17e0f79917', 'ciphertext': 'c961c235f307d03c95fb3716a85a3a7ba54f79f762f47b57c448a160d7f2d7b5'}

p, a, b, c, G = curves["Daquavious Pork"]

def modinv(x, m):
    return pow(x, m - 2, m)

c_inv = modinv(c, p)

def point_to_w(px, py):
    real = ((px - a) * c_inv) % p
    imag = ((py - b) * c_inv) % p
    return (real % p, imag % p)

def fp2_mul(a_pair, b_pair):
    a0, a1 = a_pair
    b0, b1 = b_pair
    return ((a0*b0 - a1*b1) % p, (a0*b1 + a1*b0) % p)

def fp2_pow(base, exp):
    result = (1, 0)
    b = base
    exp = exp % (p*p - 1) if exp < 0 else exp
    while exp > 0:
        if exp & 1:
            result = fp2_mul(result, b)
        b = fp2_mul(b, b)
        exp >>= 1
    return result

def fp2_inv(a_pair):
    a0, a1 = a_pair
    norm = (a0*a0 + a1*a1) % p
    norm_inv = modinv(norm, p)
    return (a0 * norm_inv % p, (-a1) * norm_inv % p)

def fp2_eq(a_pair, b_pair):
    return a_pair[0] % p == b_pair[0] % p and a_pair[1] % p == b_pair[1] % p

wG = point_to_w(*G)
wA = point_to_w(*Apub)
wB = point_to_w(*Bpub)

print(f"wG = {wG}")
print(f"wA = {wA}")
print(f"wB = {wB}")

order = p + 1
print(f"\nGroup order = p + 1 = {order}")
facs = {2: 3, 3: 1, 7: 1, 17: 1, 149: 1, 457: 1, 4517: 1, 5749: 1, 717427: 1, 1966366126889: 1, 25391461992785507: 1, 511215348081772579342664383: 1}
print(f"Factors: {facs}")

# Check which factors we need: private key is < 2^128
# Product of small factors must exceed 2^128
prod = 1
needed_factors = []
for prime in sorted(facs.keys()):
    exp = facs[prime]
    pe = prime ** exp
    needed_factors.append((prime, exp, pe))
    prod *= pe
    print(f"  Including {prime}^{exp} = {pe}, cumulative product bits: {prod.bit_length()}")
    if prod.bit_length() > 130:  # Some margin over 128
        break

print(f"\nNeed to solve DLP for {len(needed_factors)} factor groups")

def bsgs_fp2(g, h, n):
    """Baby-step giant-step for DLP g^x = h, order n, in GF(p^2)"""
    m = int(math.isqrt(n)) + 1
    # Baby steps
    table = {}
    baby = (1, 0)
    for j in range(m):
        table[baby] = j
        baby = fp2_mul(baby, g)
    # Giant step: g^{-m}
    g_inv_m = fp2_pow(fp2_inv(g), m)
    gamma = h
    for i in range(m):
        if gamma in table:
            ans = (i * m + table[gamma]) % n
            return ans
        gamma = fp2_mul(gamma, g_inv_m)
    return None

def pollard_rho_dlp_fp2(g, h, n):
    """Pollard's rho for DLP g^x = h in group of order n in GF(p^2)"""
    # Partition function based on x-coordinate mod 3
    def partition(pt):
        return pt[0] % 3

    def step(x, a_coeff, b_coeff):
        s = partition(x)
        if s == 0:
            return fp2_mul(x, x), (2 * a_coeff) % n, (2 * b_coeff) % n
        elif s == 1:
            return fp2_mul(x, g), (a_coeff + 1) % n, b_coeff
        else:
            return fp2_mul(x, h), a_coeff, (b_coeff + 1) % n

    # Random starting point
    a0 = random.randint(1, n - 1)
    b0 = random.randint(1, n - 1)
    x = fp2_mul(fp2_pow(g, a0), fp2_pow(h, b0))

    # Tortoise and hare
    xi, ai, bi = x, a0, b0
    xj, aj, bj = step(x, a0, b0)
    xj, aj, bj = step(*step(xj, aj, bj))  # 2 steps for hare... wait let me redo

    # Actually let me be more careful
    xi, ai, bi = x, a0, b0
    xj, aj, bj = x, a0, b0

    for _ in range(4 * int(math.isqrt(n)) + 1000):
        xi, ai, bi = step(xi, ai, bi)
        xj, aj, bj = step(*step(xj, aj, bj))

        if fp2_eq(xi, xj):
            # Found collision: g^ai * h^bi = g^aj * h^bj
            # g^(ai - aj) = h^(bj - bi)
            # If h = g^x, then g^(ai - aj) = g^(x*(bj - bi))
            # ai - aj = x * (bj - bi) mod n
            r = (bj - bi) % n
            if r == 0:
                # Retry with different start
                break
            # x = (ai - aj) * r^{-1} mod n
            from math import gcd
            d = gcd(r, n)
            if d == 1:
                return ((ai - aj) * pow(r, -1, n)) % n
            else:
                # Multiple solutions: x = ((ai-aj)/d) * (r/d)^{-1} mod (n/d) + k*(n/d)
                r2 = r // d
                lhs = ((ai - aj) // d) % (n // d)
                base = (lhs * pow(r2, -1, n // d)) % (n // d)
                for k in range(d):
                    candidate = base + k * (n // d)
                    if fp2_eq(fp2_pow(g, candidate), h):
                        return candidate
                break  # retry
    return None  # retry

def solve_dlp_fp2(g, h, n):
    """Solve g^x = h in group of order n"""
    if n < 10**8:
        result = bsgs_fp2(g, h, n)
        if result is not None:
            return result

    # Try BSGS for moderate sizes (up to ~10^13, sqrt ~3.2M)
    if n < 10**13:
        result = bsgs_fp2(g, h, n)
        if result is not None:
            return result

    # For larger, use Pollard's rho
    print(f"    Using Pollard's rho for n={n} (~{n.bit_length()} bits)...")
    for attempt in range(20):
        result = pollard_rho_dlp_fp2(g, h, n)
        if result is not None:
            return result
        print(f"    Rho attempt {attempt+1} failed, retrying...")
    return None

# Pohlig-Hellman
remainders = []
moduli = []

for prime, exp, pe in needed_factors:
    cofactor = order // pe
    gi = fp2_pow(wG, cofactor)
    hi = fp2_pow(wA, cofactor)

    if fp2_eq(hi, (1, 0)):
        xi = 0
        print(f"  x mod {prime}^{exp} ({pe}) = 0 (trivial)")
    elif exp == 1:
        print(f"  Solving DLP mod {prime} ({prime.bit_length()} bits)...")
        xi = solve_dlp_fp2(gi, hi, pe)
        print(f"  x mod {prime}^{exp} ({pe}) = {xi}")
    else:
        # For prime powers, use the standard Pohlig-Hellman lifting
        # x = x0 + x1*prime + x2*prime^2 + ...
        xi = 0
        gamma = fp2_pow(gi, pe // prime)  # generator of order prime
        h_curr = hi
        for k in range(exp):
            # h_k = h_curr^{prime^{exp-1-k}}
            h_k = fp2_pow(h_curr, pe // prime**(k+1))
            dk = solve_dlp_fp2(gamma, h_k, prime)
            if dk is None:
                print(f"  Failed at prime power decomposition for {prime}^{exp}")
                break
            xi += dk * (prime ** k)
            # Update: h_curr = h_curr * gi^{-dk * prime^k}
            h_curr = fp2_mul(h_curr, fp2_pow(fp2_inv(gi), dk * (prime ** k)))
        print(f"  x mod {prime}^{exp} ({pe}) = {xi}")

    if xi is not None:
        # Verify
        check = fp2_pow(wG, xi * cofactor)
        expected = fp2_pow(wA, cofactor)
        if not fp2_eq(check, expected):
            print(f"  WARNING: Verification failed for {prime}^{exp}!")
        remainders.append(int(xi))
        moduli.append(int(pe))

# CRT
def extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    g, x, y = extended_gcd(b % a, a)
    return g, y - (b // a) * x, x

def crt(rems, mods):
    r, m = rems[0], mods[0]
    for i in range(1, len(rems)):
        r2, m2 = rems[i], mods[i]
        g, x, y = extended_gcd(m, m2)
        if (r2 - r) % g != 0:
            return None, None
        lcm = m * m2 // g
        r = (r + m * ((r2 - r) // g) * x) % lcm
        m = lcm
    return r % m, m

n_alice, M = crt(remainders, moduli)
print(f"\nAlice private key candidate: {n_alice}")
print(f"Modulus: {M} ({M.bit_length()} bits)")

# Verify
check = fp2_pow(wG, n_alice)
if fp2_eq(check, wA):
    print("DLP VERIFIED!")
else:
    print("Direct verification failed, but key is mod M")

# Compute shared secret: ss = Bpub * n_alice
# In w-space: w_ss = wB ^ n_alice
w_ss = fp2_pow(wB, n_alice)
print(f"w_ss = {w_ss}")

# Convert back to point coordinates
# w = ((x-a) + i*(y-b)) / c
# so x-a = Re(w * c), y-b = Im(w * c)
# x = w[0] * c + a mod p
x_ss = (w_ss[0] * c + a) % p
ss = int(x_ss)

print(f"\n=== Step 3: Decrypt ===")
print(f"Trying shared secret x = {ss}")

# Try decryption with this and various alternatives
iv_bytes = bytes.fromhex(ct_data['iv'])
ct_bytes = bytes.fromhex(ct_data['ciphertext'])

candidates = [ss]
# Also try y coordinate and other representations
y_ss = (w_ss[1] * c + b) % p
candidates.append(int(y_ss))

for candidate_ss in candidates:
    key = sha1(str(candidate_ss).encode()).digest()[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv_bytes)
    try:
        pt = unpad(cipher.decrypt(ct_bytes), 16)
        print(f"FLAG: {pt.decode()}")
        exit(0)
    except Exception as e:
        print(f"  ss={candidate_ss} failed: {e}")

# If that didn't work, try with the original CrazyCurve point arithmetic
# to compute the shared secret directly
print("\nTrying direct point computation...")

# Reconstruct the CrazyCurve point arithmetic
def circle_add(P, Q, a, b, c, p):
    """Add two points on circle (x-a)^2 + (y-b)^2 = c^2 mod p"""
    ptx = (P[0] - a) % p
    pty = (P[1] - b) % p
    qtx = (Q[0] - a) % p
    qty = (Q[1] - b) % p
    c_inv_loc = modinv(c, p)
    xval = (ptx*qtx - qty*pty) * c_inv_loc % p + a
    yval = (ptx*qty + qtx*pty) * c_inv_loc % p + b
    return (xval % p, yval % p)

def circle_mul(n, P, a, b, c, p):
    """Scalar multiply on circle"""
    O = ((a + c) % p, b % p)  # identity
    R = O
    Q = P
    while n:
        if n & 1:
            R = circle_add(R, Q, a, b, c, p)
        Q = circle_add(Q, Q, a, b, c, p)
        n >>= 1
    return R

# Compute Alice_pub * Bob_priv = Bob_pub * Alice_priv
# We found n_alice, so compute Bob_pub * n_alice
ss_point = circle_mul(n_alice, Bpub, a, b, c, p)
print(f"Shared secret point: {ss_point}")
ss_x = int(ss_point[0])
print(f"Shared secret x = {ss_x}")

key = sha1(str(ss_x).encode()).digest()[:16]
cipher = AES.new(key, AES.MODE_CBC, iv_bytes)
try:
    pt = unpad(cipher.decrypt(ct_bytes), 16)
    print(f"FLAG: {pt.decode()}")
except Exception as e:
    print(f"Decryption failed: {e}")

    # The x-coordinate goes through self.curve.f(x) which is GF(p)(x)
    # so it's just x mod p, which we already have. But the code does int(ss.x)
    # Let's try some more alternatives
    for alt in [p - ss_x, ss_point[1], p - ss_point[1]]:
        key2 = sha1(str(int(alt)).encode()).digest()[:16]
        cipher2 = AES.new(key2, AES.MODE_CBC, iv_bytes)
        try:
            pt2 = unpad(cipher2.decrypt(ct_bytes), 16)
            print(f"FLAG (alt): {pt2.decode()}")
            exit(0)
        except:
            pass
    print("All attempts failed!")
