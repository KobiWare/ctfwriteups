#!/usr/bin/env python3
"""
Solver for pollys_key CTF challenge (Ruby/Perl polyglot).

The file is a polyglot that runs in both Ruby and Perl, with different code
paths due to =begin/=end (Ruby block comments) and =cut (Perl POD).

Key constraints from both paths:
- Ruby: 50-char key, ASCII 33-126, each (char-16)%257 must be a primitive root mod 257
- Perl: 52-element array (50 chars + newline + '0'), no caret, specific insertion sort pattern
- Perl transform: (($_ - $c) . hex($_)) % 257 where $c="0x10" (=0 numerically)
  Evaluates as: int(str(val) + str(hex(str(val)))) % 257
- Both paths have ordering constraints that resolve ambiguities
"""
import hashlib


def perl_transform(val):
    """Simulate Perl expression: (($_ - $c) . hex($_)) % 257
    In Perl, - and . have same precedence (left-to-right), so:
    ($_ - $c) . hex  =  str(val - 0) + str(hex(str(val)))
    Then % 257 forces numeric context.
    """
    hex_val = int(str(val), 16)
    concat = str(val) + str(hex_val)
    return int(concat) % 257


def is_primitive_root(g, p=257):
    """Check if g is a primitive root mod 257. Since 257 is prime and
    257-1 = 256 = 2^8, g is a primitive root iff g^128 != 1 (mod 257)."""
    return pow(g, 128, p) != 1


def reverse_insertion_sort(sorted_arr, swap_counts):
    """Given sorted array and per-step swap counts, reconstruct original."""
    arr = list(sorted_arr)
    for k in range(len(swap_counts) - 1, -1, -1):
        i = k + 1
        s = swap_counts[k]
        pos = i - s
        val = arr[pos]
        for j in range(pos, i):
            arr[j] = arr[j + 1]
        arr[i] = val
    return arr


def solve():
    # Step 1: Find all valid key characters (primitive roots mod 257 in transform range)
    valid_chars = []
    for c in range(33, 127):
        if c == 94:  # no caret
            continue
        if is_primitive_root((c - 16) % 257):
            valid_chars.append(c)

    assert len(valid_chars) == 50, f"Expected 50 valid chars, got {len(valid_chars)}"

    # Step 2: Build 52-element Perl array values and apply Perl transform
    # Array: 50 key ASCII values + 10 (newline) + 47 (48 decremented)
    all_raw = valid_chars + [10, 47]
    all_perl = [perl_transform(v) for v in all_raw]

    # Build mapping from Perl-transformed value to possible original chars
    pt_to_chars = {}
    for c in valid_chars:
        pt = perl_transform(c)
        pt_to_chars.setdefault(pt, []).append(c)

    # Step 3: Reverse insertion sort to find original arrangement
    sArray = [0, 2, 3, 4, 0, 2, 6, 2, 2, 2, 2, 3, 9, 8, 0, 11, 17, 13,
              11, 16, 14, 20, 6, 19, 6, 13, 26, 1, 1, 28, 15, 1, 14, 9,
              14, 29, 3, 7, 23, 26, 9, 0, 41, 3, 30, 11, 1, 20, 10, 2, 27]

    sorted_perl = sorted(all_perl)
    original_perl = reverse_insertion_sort(sorted_perl, sArray)

    # Verify positions 50,51 hold newline and decremented-0 transforms
    pt_10 = perl_transform(10)
    pt_47 = perl_transform(47)
    assert original_perl[50] == pt_10, f"Position 50 mismatch: {original_perl[50]} != {pt_10}"
    assert original_perl[51] == pt_47, f"Position 51 mismatch: {original_perl[51]} != {pt_47}"

    # Step 4: Map Perl-transformed positions back to original characters
    key_chars = [None] * 50
    ambiguous = []

    for i in range(50):
        pt = original_perl[i]
        possible = pt_to_chars[pt]
        if len(possible) == 1:
            key_chars[i] = possible[0]
        else:
            ambiguous.append((i, pt, possible))

    used = set(c for c in key_chars if c is not None)

    # Step 5: Resolve ambiguities using ordering constraints
    # Ruby: index(99) <= index(70), index(79) <= index(112), index(69) <= index(102)
    # Perl: index(96) <= index(56), index(54) <= index(117), index(123) <= index(55)

    # Group (positions, chars) -> resolved assignment
    # O(79)/p(112) at [1,5]: Ruby says O before p -> pos1=79, pos5=112
    key_chars[1] = 79;   key_chars[5] = 112;  used.update([79, 112])
    # E(69)/f(102) at [28,37]: Ruby says E before f -> pos28=69, pos37=102
    key_chars[28] = 69;  key_chars[37] = 102;  used.update([69, 102])
    # c(99)/F(70) at [41,46]: Ruby says c before F -> pos41=99, pos46=70
    key_chars[41] = 99;  key_chars[46] = 70;   used.update([99, 70])
    # `(96)/8(56) at [4,22]: Perl says ` before 8 -> pos4=96, pos22=56
    key_chars[4] = 96;   key_chars[22] = 56;   used.update([96, 56])
    # 6(54)/u(117) at [18,21]: Perl says 6 before u -> pos18=54, pos21=117
    key_chars[18] = 54;  key_chars[21] = 117;  used.update([54, 117])
    # {(123)/7(55) at [23,25]: Perl says { before 7 -> pos23=123, pos25=55
    key_chars[23] = 123; key_chars[25] = 55;   used.update([123, 55])

    # @(64)/~(126) at [16,19]: both options pass constraints, try both
    for opt_a, opt_b in [(64, 126), (126, 64)]:
        key_chars[16] = opt_a
        key_chars[19] = opt_b

        key_str = ''.join(chr(c) for c in key_chars)
        md5_hash = hashlib.md5(key_str.encode()).hexdigest()

        encTreasure = [76, 77, 65, 83, 67, 121, 85, 100, 48, 94, 91, 48,
                       53, 102, 82, 55, 97, 73, 111, 123, 61, 52, 76, 116,
                       95, 116, 58, 123, 119, 54, 120, 127]

        flag = ''.join(chr(int(md5_hash[i], 16) ^ encTreasure[i]) for i in range(32))

        if flag.startswith("BCCTF{"):
            print(f"Key: {key_str}")
            print(f"Flag: {flag}")
            return flag

    print("No valid flag found!")
    return None


if __name__ == "__main__":
    solve()
