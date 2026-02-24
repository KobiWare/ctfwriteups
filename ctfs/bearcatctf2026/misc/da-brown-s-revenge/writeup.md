---
author: OpenCode
credit: OpenCode, Tyler
---

## Solution

### Analysis

The challenge provides a Python script (`CodeRoller.py`) that simulates a rolling code security system - similar to garage door openers that use rolling codes for security.

The server:
1. Generates a random 12-bit code (4096 possible values)
2. Accepts binary input (only 0s and 1s)
3. Checks if the generated code appears anywhere in the user's input
4. Requires 20 consecutive correct guesses to get the flag

The key constraint is a 4107 character limit on input.

### Approach

**Step 1: Understand the problem.**
With 4096 possible 12-bit codes and only 4107 characters of input, we can't simply send all codes separately (4096 * 12 = 49152 characters).

**Step 2: Use a De Bruijn sequence.**
A De Bruijn sequence B(2, 12) is a cyclic sequence that contains every possible 12-bit binary string as a substring exactly once. The length is:
- 2^12 = 4096 (the sequence itself)
- + 11 (to wrap around and include all codes as substrings)
- = 4107 characters

This exactly fits our character limit!

The sequence can be generated using the classic algorithm:

```python
def de_bruijn(k, n):
    a = [0] * (k * n)
    sequence = []
    
    def db(t, p):
        if t > n:
            if n % p == 0:
                sequence.extend(a[1:p+1])
        else:
            a[t] = a[t - p]
            db(t + 1, p)
            for j in range(a[t - p] + 1, k):
                a[t] = j
                db(t + 1, t)
    
    db(1, 1)
    return ''.join(str(d) for d in sequence)
```

**Step 3: Connect and solve.**
Since a De Bruijn sequence contains ANY 12-bit code as a substring, sending this sequence guarantees a correct guess every round. We simply reconnect and send the same sequence 20 times.

### Key Insight

The flag `i_5pe11ed_de_brujin_wr0ng` confirms the intended solution - a De Bruijn sequence! Rolling code systems that only accept binary input can be defeated by sending a De Bruijn sequence that covers the entire code space.

## Flag

`BCCTF{i_5pe11ed_de_brujin_wr0ng_7689472}`
