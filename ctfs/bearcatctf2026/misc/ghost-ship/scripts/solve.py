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
