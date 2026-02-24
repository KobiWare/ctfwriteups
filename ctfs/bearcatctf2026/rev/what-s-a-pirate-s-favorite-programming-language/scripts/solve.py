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
