#!/usr/bin/env python3
import socket

def de_bruijn(k, n):
    """Generate de Bruijn sequence for alphabet size k and subsequences of length n."""
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

# Generate de Bruijn sequence for k=2, n=12
seq = de_bruijn(2, 12)
# Add first 11 chars to make it cyclic (wrapping)
seq_full = seq + seq[:11]  # 4107 chars - exactly the limit

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('chal.bearcatctf.io', 19679))

# Read initial prompt
s.recv(1024)

# Send the De Bruijn sequence 20 times
for i in range(20):
    s.sendall((seq_full + '\n').encode())
    data = s.recv(4096).decode()
    print(f'Round {i+1}: {data.strip()}')
    if 'BCCTF{' in data:
        break

s.close()
