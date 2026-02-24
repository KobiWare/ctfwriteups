---
author: OpenCode
credit: OpenCode, Tyler
---

## Analysis

The challenge is a Reverse Engineering problem with an interesting hint in the description: "Surely it's A. Or B. Or D. Or E. Or F. Or J. Or K. Or L. Or M. Or P. Or Q. Or S. Or T. Or V. Or Y. But certainly not C."

This is R code! Looking at the syntax (`nchar()`, `utf8ToInt()`, `intToUtf8()`, `bitwAnd()`, `bitwOr()`, `bitwNot()`), this is the R programming language - the single character name that the hint references.

The code takes user input, applies bitwise transformations, and compares against an encrypted string.

## Approach

### Step 1: Analyze the R Code

The code performs the following transformation on the input:

```r
for (i in 1:14) { 
    inputVector[i] = bitwAnd(bitwOr(inputVector[i], i), bitwNot(bitwAnd(inputVector[i], i)))
}

for (i in 15:28) {
    inputVector[i] = bitwAnd(bitwOr(inputVector[i], (29 - i)), bitwNot(bitwAnd(inputVector[i], (29 - i))))
}
```

Let's simplify the bitwise operation:
- `bitwOr(x, i)` = x | i
- `bitwAnd(x, i)` = x & i  
- `bitwNot(x)` = ~x

So: `(x | i) & ~(x & i)` = `x ^ i` (XOR)

The algorithm applies:
- XOR with indices 1-14 for characters 1-14
- XOR with indices 14-1 (29-i) for characters 15-28

### Step 2: Reverse the Transformation

The ciphertext is: `"CA@PC}Wz:~<uR;[_?T;}[XE$%2#|"`

To decrypt, we XOR again with the same values:

```python
ct = "CA@PC}Wz:~<uR;[_?T;}[XE$%2#|"
ct_bytes = [ord(c) for c in ct]

# Reverse first loop (i = 1 to 14)
for i in range(1, 15):
    ct_bytes[i-1] ^= i

# Reverse second loop (i = 15 to 28)
for i in range(15, 29):
    ct_bytes[i-1] ^= (29 - i)

flag = ''.join(chr(b) for b in ct_bytes)
# Output: BCCTF{Pr3t7y_5UR3_1tS_C!!1!}
```

## Solve Script

```python
#!/usr/bin/env python3
# Reverse the XOR transformation in the R program

ct = "CA@PC}Wz:~<uR;[_?T;}[XE$%2#|"
ct_bytes = [ord(c) for c in ct]

# Reverse first loop: input[i] = input[i] XOR i (for i=1 to 14)
for i in range(1, 15):
    ct_bytes[i-1] ^= i

# Reverse second loop: input[i] = input[i] XOR (29-i) (for i=15 to 28)
for i in range(15, 29):
    ct_bytes[i-1] ^= (29 - i)

flag = ''.join(chr(b) for b in ct_bytes)
print(f"Flag: {flag}")
```

## Flag

`BCCTF{Pr3t7y_5UR3_1tS_C!!1!}`
