import json

# Load data
with open("output.txt") as f:
    lines = f.readlines()

data_M = json.loads(lines[0])
M = data_M["M"]
n = len(M)

flag = ""

for line in lines[1:]:
    d = json.loads(line)
    aM = d["aM"][0]       # 1x64 row vector -> list of 64
    Mb = [row[0] for row in d["Mb"]]  # 64x1 col vector -> list of 64
    enc_char = d["enc_char"]

    # Recover b' using tropical residuation:
    # b'[j] = max_i(Mb[i] - M[i][j])
    # This is the greatest subsolution of M ⊗ x = Mb,
    # and since Mb is in the image (true b is a solution),
    # b' is an exact solution: M ⊗ b' = Mb.
    b_prime = []
    for j in range(n):
        b_prime.append(max(Mb[i] - M[i][j] for i in range(n)))

    # Compute aMb = aM ⊗ b' = min_j(aM[j] + b'[j])
    aMb = min(aM[j] + b_prime[j] for j in range(n))

    # Decrypt
    key = aMb % 32
    pt_char = chr(key ^ ord(enc_char))
    flag += pt_char

print(flag)
