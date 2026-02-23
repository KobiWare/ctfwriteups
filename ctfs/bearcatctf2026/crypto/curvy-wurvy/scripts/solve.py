#!/usr/bin/env python3
from pwn import *
import gmpy2
from gmpy2 import mpz, invert
import sys
import time

# Ed25519 parameters
q = mpz(57896044618658097711785492504343953926634992332820282019728792003956564819949)
p = mpz(7237005577332262213973186563042994240857116359379907606001950938285454250989)
d = mpz(37095705934669439343138083508754565189542113879843219016388785533085940283555)
Gx = mpz(15112221349535400772501151409588531511454012693041857206046113283949847762202)
Gy = mpz(46316835694926478169428394003475163141307993866256225615783033603165251855960)

# Extended twisted Edwards coordinates
INF = (mpz(0), mpz(1), mpz(1), mpz(0))

def ext_add(P1, P2):
    X1, Y1, Z1, T1 = P1
    X2, Y2, Z2, T2 = P2
    A = X1 * X2 % q; B = Y1 * Y2 % q
    C = d * T1 % q * T2 % q; D = Z1 * Z2 % q
    E = ((X1 + Y1) * (X2 + Y2) - A - B) % q
    F = (D - C) % q; G = (D + C) % q; H = (B + A) % q
    return (E * F % q, G * H % q, F * G % q, E * H % q)

def ext_dbl(P):
    X1, Y1, Z1, T1 = P
    A = X1 * X1 % q; B = Y1 * Y1 % q
    C = 2 * Z1 * Z1 % q; D = (q - A) % q
    E = ((X1 + Y1) * (X1 + Y1) - A - B) % q
    G = (D + B) % q; F = (G - C) % q; H = (D - B) % q
    return (E * F % q, G * H % q, F * G % q, E * H % q)

def ext_neg(P):
    X, Y, Z, T = P
    return ((q - X) % q, Y, Z, (q - T) % q)

def to_affine(P):
    X, Y, Z, T = P
    Zinv = invert(Z, q)
    return (int(X * Zinv % q), int(Y * Zinv % q))

def to_ext(x, y):
    x, y = mpz(x), mpz(y)
    return (x, y, mpz(1), x * y % q)

def ext_mul(k, P):
    result = INF; Q = P; k = int(k)
    while k > 0:
        if k & 1: result = ext_add(result, Q)
        Q = ext_dbl(Q); k >>= 1
    return result

def x_recover(y):
    """Recover x from y on Ed25519 (sign=0, even x)"""
    y = int(y) % int(q)
    yy = y * y % int(q)
    u = (1 - yy) % int(q)
    v = int(invert(mpz((-1 - int(d) * yy) % int(q)), q))
    xx = u * v % int(q)
    x = int(pow(mpz(xx), int((q + 3) // 8), int(q)))
    if (x * x - xx) % int(q) != 0:
        I = int(pow(mpz(2), int((q - 1) // 4), int(q)))
        x = x * I % int(q)
    if (x * x) % int(q) != xx % int(q):
        return None
    if x & 1:
        x = int(q) - x
    return x

def compute_torsion_points():
    """Compute the 8 torsion points of Ed25519"""
    # Find a point not in the prime-order subgroup
    for test_y in range(3, 1000):
        test_x = x_recover(test_y)
        if test_x is not None:
            P_test = to_ext(test_x, test_y)
            T = ext_mul(int(p), P_test)
            T_aff = to_affine(T)
            if T_aff != (0, 1):
                # T is a non-trivial torsion point; generate all 8
                torsion = []
                for i in range(8):
                    iT = ext_mul(i, T)
                    torsion.append(iT)
                return torsion
    raise Exception("Could not find torsion generator")

# Precompute torsion points
TORSION = compute_torsion_points()
log.info(f"Computed {len(TORSION)} torsion points")

def bsgs(P_ext, Q_ext, bound):
    """Baby-step Giant-step: find k in [1, bound] s.t. k*P = Q"""
    m = int(gmpy2.isqrt(bound)) + 1
    log.info(f"BSGS: bound={bound}, m={m}")

    # Baby steps
    table = {}
    jP = INF
    t0 = time.time()
    for j in range(m):
        aff_y = int(jP[1] * invert(jP[2], q) % q)
        table[aff_y] = j
        jP = ext_add(jP, P_ext)
        if j > 0 and j % 500000 == 0:
            elapsed = time.time() - t0
            log.info(f"  Baby step {j}/{m} ({j/elapsed:.0f}/s)")

    log.info(f"Baby steps done in {time.time()-t0:.1f}s")

    # Giant steps
    mP = ext_mul(m, P_ext)
    neg_mP = ext_neg(mP)
    Q_aff = to_affine(Q_ext)

    gamma = Q_ext
    t1 = time.time()
    for i in range(m + 1):
        gamma_y = int(gamma[1] * invert(gamma[2], q) % q)
        if gamma_y in table:
            j = table[gamma_y]
            for candidate_k in [i * m + j, i * m - j]:
                if 0 < candidate_k <= bound:
                    check = to_affine(ext_mul(candidate_k, P_ext))
                    if check == Q_aff:
                        log.success(f"Found k = {candidate_k}")
                        return candidate_k
                # Also try p - k (negation)
                pk = int(p) - candidate_k
                if 0 < pk <= bound:
                    check = to_affine(ext_mul(pk, P_ext))
                    if check == Q_aff:
                        log.success(f"Found k = {pk} (via negation)")
                        return pk
        gamma = ext_add(gamma, neg_mP)
        if i > 0 and i % 500000 == 0:
            elapsed = time.time() - t1
            log.info(f"  Giant step {i}/{m} ({i/elapsed:.0f}/s)")

    return None

def recover_flag(master_key, FLAG_UID, flag_sig):
    """Recover FLAG given MASTER_KEY, FLAG_UID, and flag_sig"""
    flag_key = master_key * FLAG_UID % int(p)
    inv_flag_key = int(invert(mpz(flag_key), p))

    # Extract y-coordinate from flag_sig (padding should be 0)
    flag_signed_y = flag_sig & ((1 << 256) - 1)

    q_int = int(q)

    # Try both x-signs for the signed point
    for sign_idx in range(2):
        SP_x = x_recover(flag_signed_y)
        if SP_x is None:
            log.error("flag_signed_y is not a valid y-coordinate!")
            return None
        if sign_idx == 1:
            SP_x = int(q) - SP_x

        SP_ext = to_ext(SP_x, flag_signed_y)
        R = ext_mul(inv_flag_key, SP_ext)

        # Try all 8 torsion corrections
        for ti, T_ext in enumerate(TORSION):
            candidate = ext_add(R, T_ext)
            cand_aff = to_affine(candidate)
            y_rec = cand_aff[1]  # This is FLAG_int mod q
            if y_rec == 0:
                continue

            # FLAG_int = y_rec + k*q for some k >= 0
            # Use known prefix "BCCTF{" to narrow k efficiently
            # Try different flag lengths (20-80 bytes)
            for flag_len in range(15, 80):
                prefix = b'BCCTF{'
                lo = int.from_bytes(prefix + b'\x00' * (flag_len - len(prefix)), 'big')
                hi = int.from_bytes(prefix + b'\xff' * (flag_len - len(prefix)), 'big')

                # k must satisfy: lo <= y_rec + k*q <= hi
                if y_rec > hi:
                    k_lo = max(0, (lo - y_rec + q_int - 1) // q_int)
                else:
                    k_lo = max(0, (lo - y_rec + q_int - 1) // q_int)
                k_hi = (hi - y_rec) // q_int

                for k in range(max(0, k_lo), k_hi + 1):
                    flag_int = y_rec + k * q_int
                    if flag_int < lo or flag_int > hi:
                        continue
                    try:
                        flag_bytes = flag_int.to_bytes(flag_len, 'big')
                        if flag_bytes.startswith(b'BCCTF{') and flag_bytes.endswith(b'}'):
                            log.info(f"Found with sign={sign_idx}, torsion={ti}, k={k}, len={flag_len}")
                            return flag_bytes
                    except:
                        pass

    return None

def interact(r):
    """Parse server output"""
    r.recvuntil(b"Verify the true flag with\n")
    uid_line = r.recvline().decode().strip()
    sig_line = r.recvline().decode().strip()
    FLAG_UID = int(uid_line.split(": ")[1])
    flag_sig = int(sig_line.split(": ")[1])
    return FLAG_UID, flag_sig

def sign_data(r, data, uid):
    """Use server to sign data with given uid"""
    r.recvuntil(b"What would you like to do?")
    r.recvuntil(b"3. Verify signature\n")
    r.sendline(b"2")
    r.recvuntil(b"Enter your data: ")
    r.sendline(str(data).encode())
    r.recvuntil(b"Enter your UID: ")
    r.sendline(str(uid).encode())
    r.recvuntil(b"Your signature is: ")
    sig = int(r.recvline().decode().strip())
    return sig

def solve(host, port):
    r = remote(host, port)

    FLAG_UID, flag_sig = interact(r)
    log.info(f"FLAG_UID = {FLAG_UID}")
    log.info(f"flag_sig = {flag_sig}")

    # Sign generator's y with uid=1 to get Q = MASTER_KEY * P
    data_y = int(Gy)
    Q_sig = sign_data(r, data_y, 1)
    Q_y = Q_sig & ((1 << 256) - 1)
    log.info(f"Q.y = {Q_y}")

    # Recover P (the base point used by server)
    P_x = x_recover(data_y)
    P_ext = to_ext(P_x, data_y)

    # BSGS to find MASTER_KEY (try both x-signs for Q)
    master_key = None
    for exp in [20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 63]:
        bound = 2 ** exp
        log.info(f"\n--- Trying bound 2^{exp} ---")

        for sign_idx in range(2):
            Q_x = x_recover(Q_y)
            if sign_idx == 1:
                Q_x = int(q) - Q_x
            Q_ext = to_ext(Q_x, Q_y)

            result = bsgs(P_ext, Q_ext, bound)
            if result is not None:
                master_key = result
                break

        if master_key is not None:
            break

    if master_key is None:
        log.error("Could not find MASTER_KEY!")
        r.close()
        return None

    log.success(f"MASTER_KEY = {master_key}")

    # Recover FLAG
    flag_bytes = recover_flag(master_key, FLAG_UID, flag_sig)

    if flag_bytes:
        log.success(f"FLAG: {flag_bytes.decode()}")
    else:
        log.error("Could not recover FLAG!")

    r.close()
    return flag_bytes

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        host = sys.argv[1]
        port = int(sys.argv[2])
    else:
        print(f"Usage: {sys.argv[0]} <host> <port>")
        sys.exit(1)

    solve(host, port)
