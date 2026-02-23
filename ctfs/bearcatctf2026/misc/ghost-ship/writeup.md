---
author: Claude
credit: Claude, Fenix
---
## Solution

### Analysis
The challenge provides a single file called `ghost_ship`. Running `file` on it reveals it is ASCII text with very long lines (10720 characters). Examining the hex dump shows characters like `>`, `+`, `[`, `<`, `-`, `]`, `.`, and `,` -- this is **Brainfuck** source code.

The Brainfuck program is a flag checker that:
1. Prints a ghost pirate prompt: "WoOOOoOo we are ghOooOoOost pirates and want to haunt yOOoOOoooOu! The oOoOoOoOOnly thing that woOOOoOoOould make us recOoOonsider is the flag! Tell it tooOoOoO us: "
2. Reads exactly 40 characters of input (each stored 13 tape cells apart)
3. Sets up expected values at an offset from each input position
4. Compares each character against its expected value using a chained bit-level comparison algorithm (divmod by 64, 32, 16, 8, 4, 2, 1)
5. Prints a success or failure message

### Approach

**Step 1: Identify the language.**
The file was identified as Brainfuck code based on the character set. There are exactly 40 `,` (input read) instructions, confirming it reads a 40-character flag.

**Step 2: Attempt direct execution.**
No Brainfuck interpreter was installed, and a Python-based interpreter was too slow for the 10KB program. A compiled C interpreter was also tried but crashed due to memory issues with the tape pointer going negative.

**Step 3: Compile Brainfuck to optimized C.**
A Python script was written to transpile the Brainfuck to C code with run-length encoding optimizations (collapsing consecutive `+`/`-`/`>`/`<` into single operations and pre-computing bracket matches). This compiled successfully with `gcc -O3`.

**Step 4: Analyze the program structure.**
The Brainfuck code was segmented:
- Characters 0-2748: Prompt printing
- Characters 2749-3295: Input reading (40 commas, spaced 14 characters apart)
- Characters 3296-3179: Expected value setup (arithmetic operations placing target values at offset +5 from each input position)
- Characters 3180-5696: Main comparison loop (chained right-to-left comparison with mismatch detection)
- Characters 5697+: Success/failure output

**Step 5: Brute-force characters right-to-left.**
The key insight was identifying the **mismatch flag cell** at offset +10 from each input position. The comparison loop processes characters from position 39 down to 0, and each character's comparison result propagates adjustments to the next character's cells (a chained comparison).

A Python script was written that:
1. Runs the pre-input code and value setup code to initialize the tape
2. For each character position (39 down to 0), tries all 128 ASCII values
3. Runs one iteration of the comparison loop body
4. Checks if the mismatch flag cell (offset +10) is 0 (correct) or non-zero (wrong)
5. Selects the character value that produces a 0 mismatch flag

This produced the flag character by character in about 30 seconds.

**Step 6: Verify.**
The decoded flag was fed back into the compiled program, which printed the success message: "YoOOOOooOu actually did it? NoOooOOOoOOOOOOooOOoooOOOO!"

### Solve Script
```python
# Core approach: brute-force each character right-to-left
# by checking the mismatch flag cell after one iteration
# of the comparison loop body

with open('ghost_ship', 'r') as f:
    code = f.read().strip()
bf = ''.join(ch for ch in code if ch in '><+-.,[]')

# Run pre-input code to set up the tape
# Skip input (set all input cells to 0)
# Run value setup code
# For each character position (39 to 0):
#   Try all 128 ASCII values
#   Run one comparison loop iteration
#   Check mismatch flag at offset +10
#   Select value where mismatch = 0

# Results:
# char[39] = 125 = '}'
# char[38] =  33 = '!'
# char[37] =  53 = '5'
# ...
# char[0]  =  66 = 'B'
# -> BCCTF{N0_moR3_H4un71n6!_N0_M0rE_Gh0575!}
```

The flag in leetspeak translates to: "No more Haunting! No More Ghosts!"

## Flag
`BCCTF{N0_moR3_H4un71n6!_N0_M0rE_Gh0575!}`
