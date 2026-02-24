---
author: Claude
credit: Claude, Fenix
---
## Solution

### Analysis

The challenge source `brig.py` implements a Python jail:

```python
from Crypto.Util.number import long_to_bytes

def main():
    print("Welcome to the brig. There is no escape...")
    inp = input('> ')
    if len(inp) != 2:
        print("I see you smuggleing contraband in!")
        return 1
    ok_chars = set(inp)
    inp = input('> ')
    if not set(inp) <= ok_chars:
        print("You don't have that tool")
        return 1
    if len(inp) >= 2**12:
        print("You took too long! We have already arrived")
        return 1
    try:
        print(eval(long_to_bytes(eval(inp))))
    except:
        print("What are you trying to do there?")
```

The flow is:
1. Choose exactly 2 characters (your "tools")
2. Write an expression using only those 2 characters (max 4096 chars)
3. The expression is `eval()`'d to produce an integer
4. That integer is converted to bytes via `long_to_bytes()`
5. The resulting bytes are `eval()`'d as Python code
6. The result is printed

The goal is to craft an expression that, when double-evaluated through this pipeline, reads `/flag.txt`.

### Approach

#### Key Insight: Repunit Decomposition

Choose the characters `1` and `+`. Using only these two characters, we can write sums of **repunits** (numbers consisting entirely of 1s, like 1, 11, 111, 1111, ...). Any positive integer can be decomposed as a sum of repunits using a greedy algorithm.

#### Two-Stage Exploit via eval(input())

The target code `eval(input())` converts to the integer `bytes_to_long(b"eval(input())") = 8038681421665166480228657670441`. This integer can be decomposed into a repunit sum of only 2561 characters -- well within the 4096 limit.

The exploit chain:
1. **Line 1**: Send `1+` (the two chosen characters)
2. **Line 2**: Send the repunit sum `1111...+111...+11...+1` (2561 chars)
3. **Line 3**: Send arbitrary Python code (read by the `input()` that runs inside `eval()`)

When the jail evaluates the repunit sum, it gets the integer `8038681421665166480228657670441`. Then `long_to_bytes()` converts it back to `b"eval(input())"`. The outer `eval()` runs `eval(input())`, which reads a third line from stdin -- our unrestricted Python payload.

#### Remote Exploitation Challenges

Initially, the exploit was tested locally and worked perfectly. However, when connecting to the remote server:

- **First attempt**: Sending lines with delays between them caused `input()` to hit EOF, because the server closed the pipe before the third line arrived.
- **Alternative attempts**: Tried encoding various direct file-read expressions like `[*open('flag')]`, `open('flag.txt').read()`, etc. directly as repunit sums, but most exceeded the 4096 character limit or targeted the wrong filename.
- **Successful approach**: Sending all three lines **at once** (concatenated with newlines) so the data was buffered in the socket. This way, when `eval(input())` ran inside the jail, it could read the third line from the buffered input:

```python
payload = b"1+\n" + expr.encode() + b"\nopen('/flag.txt').read()\n"
s.sendall(payload)
```

## Flag
`BCCTF{1--1--1--1--111--111--1111_e1893d6cdf}`
