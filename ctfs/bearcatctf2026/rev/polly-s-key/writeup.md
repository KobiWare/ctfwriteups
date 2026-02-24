---
author: Claude
credit: Claude, Fenix
---
## Solution

### Analysis
The file `pollys_key` is identified by `file` as a "Ruby script, ASCII text, with CRLF line terminators." However, closer inspection reveals it is a **polyglot** -- a program valid in both Ruby and Perl simultaneously. It uses language-specific comment/documentation blocks to selectively show and hide code for each interpreter:

- `=begin` / `=end` are Ruby multi-line block comments
- `=begin` / `=cut` are Perl POD (Plain Old Documentation) blocks
- Heredoc tricks (`q = <<'$q;'`) are used to hide code from one language while exposing it to the other

The program prompts for a 50-character key and validates it through constraints from both language paths. If valid, it decrypts a treasure (the flag) by XORing MD5 hash nibbles of the key with a hardcoded `encTreasure` array.

### Key Constraints

**Ruby path:**
- Key must be exactly 50 characters, all unique, ASCII 33-126 (no caret, ASCII 94)
- Each character is transformed via `(char_code - 16) % 257`
- Each transformed value must be a **primitive root modulo 257** (since 257 is prime and 257-1 = 2^8, this means `g^128 mod 257 != 1`)
- Ordering constraints: `index(99) <= index(70)`, `index(79) <= index(112)`, `index(69) <= index(102)`, etc.

**Perl path:**
- 52-element array (50 key chars + newline char 10 + '0' decremented to 47)
- No caret character (ASCII 94)
- Perl transform: `(($_ - $c) . hex($_)) % 257` where `$c="0x10"` -- this concatenates the value with its hex interpretation and takes mod 257
- **Insertion sort swap counts** must match a hardcoded `sArray` -- this is effectively an inversion table that uniquely determines the ordering
- Ordering constraints: `index(96) <= index(56)`, `index(54) <= index(117)`, `index(123) <= index(55)`, etc.

### Approach

**Step 1: Find valid characters.**
There are exactly 50 ASCII characters in range 33-126 (excluding 94/caret) whose `(c - 16) % 257` value is a primitive root mod 257. Since there are exactly 50 valid characters and the key must contain all unique characters, every valid character must appear exactly once.

**Step 2: Apply Perl transform and reverse insertion sort.**
Each valid character's Perl-transformed value was computed. The `sArray` (swap counts from insertion sort) was used to reverse the insertion sort -- given the sorted array and the per-step swap counts, the original arrangement was reconstructed using a reverse insertion sort algorithm.

**Step 3: Map back to original characters.**
Each position's Perl-transformed value was mapped back to the original ASCII character. Most positions had a unique mapping, but six pairs of characters produced the same Perl transform value, creating ambiguities.

**Step 4: Resolve ambiguities using ordering constraints.**
The ordering constraints from both Ruby and Perl paths resolved all six ambiguous pairs:
- `O(79)/p(112)`: Ruby says O before p
- `E(69)/f(102)`: Ruby says E before f
- `c(99)/F(70)`: Ruby says c before F (Ruby reverses the constraint direction)
- backtick(96)/8(56): Perl says backtick before 8
- `6(54)/u(117)`: Perl says 6 before u
- `{(123)/7(55)`: Perl says { before 7

**Step 5: Handle remaining ambiguity and decrypt.**
One pair `@(64)/~(126)` had no distinguishing constraint. Both orderings were tried, and the MD5 hash of the key was XORed with `encTreasure` to check which produced a flag starting with `BCCTF{`.

## Flag
`BCCTF{Th3_P05h_9oLly61Ot_p4rr0t}`
