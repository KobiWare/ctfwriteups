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

## Flag
`BCCTF{Y00_hO_Ho_anD_4_B07Tl3_oF_rUm}`
