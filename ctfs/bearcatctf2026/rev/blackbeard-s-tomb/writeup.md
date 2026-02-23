---
author: Claude
credit: GoodDays13, Claude, Fenix
---
## Solution

### Analysis
The `tomb` binary is a 5MB statically linked ELF 64-bit executable (not stripped) with executable stack and RWX segments. It statically links OpenSSL for SHA256 operations. Running it requires `OPENSSL_CONF=/dev/null` to avoid a crash from dynamic provider loading.

```
$ file tomb
tomb: ELF 64-bit LSB executable, x86-64, version 1 (GNU/Linux), statically linked, not stripped

$ pwn checksec tomb
    Arch:       amd64-64-little
    RELRO:      Partial RELRO
    Stack:      Canary found
    NX:         NX unknown - GNU_STACK missing
    PIE:        No PIE (0x400000)
    Stack:      Executable
    RWX:        Has RWX segments
```

Key symbols identified via `nm`:

| Address    | Symbol     | Purpose |
|------------|------------|---------|
| 0x403385   | `proc`     | Real entry point, anti-debug #1 |
| 0x402f75   | `main`     | Main verification logic |
| 0x402d60   | `puts`     | Custom puts with anti-debug #2 |
| 0x402c95   | `hash`     | SHA256 wrapper |
| 0x402ccf   | `xor`      | SHA256-based XOR function |
| 0x8413e0   | `tomb_key` | 32-byte global key (modified at runtime) |
| 0x841140   | `lock`     | 20 x 32-byte comparison table |

The binary has a layered architecture:

```
Program Entry
  -> proc()              [anti-debug #1: /proc/self/status TracerPid]
       -> main()
             |-> custom puts()   [anti-debug #2: ptrace(TRACEME) + XOR]
             |-> SHA256 check    [verifies "BCCTF{" prefix]
             |-> Lock table      [verifies flag[6..25] via SHA256 pairs]
             -> Shellcode        [anti-debug #3: self-decrypting final check]
```

### Approach

**Step 1: Identify the real entry point.**
Disassembly revealed that `__libc_start_call_main` calls `proc` (at 0x403385), not `main` (at 0x402f75). The `proc` function is the real entry point and contains the first anti-debugging layer.

**Step 2: Reverse anti-debug #1 -- `proc()` (TracerPid check).**
The `proc` function:
1. Computes `sum = 0 + 1 + 2 + ... + 99 = 4950 (0x1356)`
2. Decodes strings via XOR with 0xFD to reveal `/proc/self/status` and `TracerPid:`
3. Opens `/proc/self/status`, parses the TracerPid value
4. Computes `xor_value = TracerPid + 4950`
5. Computes `ptr = 0x84008A + 4950 = 0x8413E0` (the `tomb_key` address)
6. XORs 8 x 32-bit words at `tomb_key` with `xor_value`
7. Calls `main(argc, argv)`

Under normal execution, TracerPid is 0, so the XOR value is 0x1356. Under a debugger, the TracerPid is the debugger's PID, producing a wrong XOR value and corrupting `tomb_key`.

**Step 3: Reverse anti-debug #2 -- Custom `puts()`.**
The `puts` function at 0x402d60 is not the standard C library `puts`. After printing the banner string "You have entered my tomb! None will escape...", it verifies the string's SHA256 hash matches a hardcoded value. If it matches, it constructs 72 bytes of shellcode on the stack and calls it twice with arguments `(0x68E280, 0x8403E0)`.

The decoded shellcode performs:
```asm
push rdi                    ; save 0x68E280
pop rax                     ; rax = 0x68E280
add rax, 0x1000             ; rax = 0x68F280 = ptrace()
push rsi                    ; save 0x8403E0
xor rdi, rdi                ; PTRACE_TRACEME = 0
xor rsi, rsi                ; pid = 0
call rax                    ; ptrace(PTRACE_TRACEME, 0)
pop rsi                     ; restore 0x8403E0
test rax, rax
js skip                     ; if ptrace failed, skip XOR
add rsi, 0x1000             ; rsi = 0x8413E0 = tomb_key
mov rdi, rsi
add rdi, 0x28               ; rdi = tomb_key + 40
mov rax, 0x04030201         ; XOR pattern
loop:
  mov rbx, [rsi]
  xor rbx, rax
  mov [rsi], rbx
  add rsi, 8
  cmp rdi, rsi
  jne loop
skip:
  ret
```

- **First call**: `ptrace(TRACEME)` succeeds -> XOR applied to `tomb_key` with pattern `01 02 03 04 00 00 00 00`
- **Second call**: `ptrace(TRACEME)` fails (already traced) -> XOR skipped
- **Net effect (normal run)**: `tomb_key` XOR'd once with the pattern
- **Under GDB**: Both calls fail -> no XOR applied -> corrupted `tomb_key`

**Step 4: Reverse the main verification logic.**
Main performs four checks:

1. **SHA256 prefix check (positions 0-5)**: Computes SHA256 of the first 6 bytes of input and compares against a hardcoded hash (the hash of "BCCTF{"). If matched, XORs `tomb_key` with SHA256("BCCTF{").

2. **Length check**: Verifies `argv[1][0x2D] == 0` (flag is exactly 45 bytes). If so, XORs all 32 bytes of `tomb_key` with `argv[1][0x2C]` which is `}` (0x7D).

3. **Lock table check (positions 6-25)**: For each position i from 6 to 25, calls the `xor()` function which computes `SHA256(flag[i+1])` and XORs byte 0 with `SHA256(flag[i])[0]`, then compares the result against the corresponding 32-byte entry in the `lock` table. Each successful comparison further XORs `tomb_key`.

4. **Self-decrypting shellcode (positions 26-43)**: Constructs a 39-byte XOR decoder function on the stack (each byte XOR'd with 0xCC), which decrypts a 52-byte shellcode payload using the current `tomb_key` state and then jumps to it.

**Step 5: Recover the flag from the lock table.**
The lock table recovery was straightforward:
- Bytes 1-31 of each lock entry equal `SHA256(flag[i+1])[1:31]`
- Pre-computed SHA256 of all 256 byte values, then reverse-looked up by bytes 1-31
- This recovered `flag[7]` through `flag[26]`
- `flag[6]` was recovered from byte 0 via: `SHA256(flag[6])[0] = lock[0][0] ^ SHA256(flag[7])[0]`
- **Result**: positions 6-26 = `Buri3d_at_sea_Ent0m3d`

**Step 6: Recover the flag from the shellcode.**
After XOR-decrypting with the correct `tomb_key`, the shellcode performs:
```asm
add rsi, 0x1a         ; rsi = &flag[26]
mov rdx, 0x539        ; rdx = 1337 (success)
xor rcx, rcx          ; counter = 0
loop:
  mov al, 5
  mul cl              ; ax = 5 * counter
  add al, 0x40        ; al = 5*counter + 64
  xor al, [rsi]       ; al ^= flag[26+counter]
  mov bl, [rdi]       ; bl = tomb_key[counter]
  cmp bl, al
  jne fail
  inc rsi / inc rdi / inc rcx
  cmp rcx, 0x12       ; 18 iterations
  jne loop
  jmp done
fail:
  inc rdx             ; rdx = 1338 (failure)
done:
  mov rax, rdx        ; return 1337 or 1338
  ret
```

The recovery formula is: `flag[26+i] = tomb_key[i] ^ (5*i + 0x40)` for i=0..17.
- **Result**: positions 26-43 = `d_amm0nG_th3_w4v3S` (position 26='d' confirms overlap with lock table recovery)

**Step 7: Compute the correct `tomb_key`.**
The 32-byte `tomb_key` global undergoes this XOR chain:
```
Initial value (from .data):
  f9 00 16 37 04 14 b8 22 ed 3b b7 cf 21 58 77 3a
  d2 8c 72 6a ea df f1 33 e8 24 10 92 ad 08 dd 0d

1. proc():     XOR each 32-bit word with 0x1356
2. puts():     XOR with 01 02 03 04 00 00 00 00 pattern (5x8 bytes)
3. main():     XOR with SHA256("BCCTF{")
4. main():     XOR each byte with 0x7D ('}')
5. main():     XOR with each of 20 lock entries (32 bytes each)
```

The final `tomb_key` used by the shellcode was computed in Python by replaying all five XOR layers.

### Solve Script
```python
#!/usr/bin/env python3
import hashlib, struct

# Initial tomb_key from .data section at 0x8413E0
tomb_key = bytearray.fromhex(
    "f90016370414b822ed3bb7cf2158773a"
    "d28c726aeadff133e8241092ad08dd0d"
)

# Step 1: proc() XOR - sum(0..99) = 4950 = 0x1356
xor_val = 0x1356
for i in range(0, 32, 4):
    word = struct.unpack_from('<I', tomb_key, i)[0]
    word ^= xor_val
    struct.pack_into('<I', tomb_key, i, word)

# Step 2: puts() shellcode XOR - pattern 01 02 03 04 00 00 00 00
pattern = bytes([0x01, 0x02, 0x03, 0x04, 0x00, 0x00, 0x00, 0x00])
for i in range(32):
    tomb_key[i] ^= pattern[i % 8]

# Step 3: SHA256("BCCTF{") XOR
sha_prefix = hashlib.sha256(b"BCCTF{").digest()
for i in range(32):
    tomb_key[i] ^= sha_prefix[i]

# Step 4: XOR with 0x7D ('}')
for i in range(32):
    tomb_key[i] ^= 0x7D

# Step 5: Lock table - recover characters from SHA256 reverse lookup
# Pre-compute SHA256 of all byte values
sha_table = {}
for b in range(256):
    h = hashlib.sha256(bytes([b])).digest()
    sha_table[h[1:]] = b  # bytes 1-31 as key

# Lock table entries (20 x 32 bytes) extracted from the binary
lock_entries = [...]  # 20 entries extracted via GDB/objdump

# Recover flag[7..26] from lock entries bytes 1-31
flag_chars = [0] * 46
flag_chars[0:6] = list(b"BCCTF{")
flag_chars[45] = 0  # null terminator
flag_chars[44] = ord('}')

for i in range(20):
    entry = lock_entries[i]
    flag_chars[7 + i] = sha_table[bytes(entry[1:])]

# Recover flag[6] from byte 0 of first lock entry
for c in range(256):
    h = hashlib.sha256(bytes([c])).digest()
    if h[0] ^ hashlib.sha256(bytes([flag_chars[7]])).digest()[0] == lock_entries[0][0]:
        flag_chars[6] = c
        break

# Apply lock table XOR to tomb_key
for i in range(20):
    entry = lock_entries[i]
    for j in range(32):
        tomb_key[j] ^= entry[j]

# Step 6: Shellcode recovery - flag[26+i] = tomb_key[i] ^ (5*i + 0x40)
for i in range(18):
    flag_chars[26 + i] = tomb_key[i] ^ (5 * i + 0x40)

flag = ''.join(chr(c) for c in flag_chars[:45])
print(f"Flag: {flag}")
```

### Verification
```
$ OPENSSL_CONF=/dev/null ./tomb 'BCCTF{Buri3d_at_sea_Ent0m3d_amm0nG_th3_w4v3S}'
You have entered my tomb! None will escape...

You have defied the odds and made it back to shore. Great job
```

## Flag
`BCCTF{Buri3d_at_sea_Ent0m3d_amm0nG_th3_w4v3S}`
