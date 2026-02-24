---
author: OpenCode
credit: OpenCode, Tyler
---

## Analysis

This is a Reverse Engineering challenge that requires analyzing an ELF binary. The description hints at finding "One Piece" - a reference to the popular anime One Piece where the legendary treasure exists.

The challenge mentions: "I did a puzzle but was missing One Piece... I think the One Piece is actually a flag."

## Approach

### Step 1: Initial Analysis

Running the binary without arguments gives:
```
It seems the One Piece is nowhere to be found...
```

### Step 2: Examine Binary Strings

Using `strings` on the binary reveals important clues:
```
./devilishFruit
PWD=/tmp/gogear5
ONE_PIECE=IS_REAL
The legends have been proven true! %s
It seems the One Piece is nowhere to be found...
you_dont_need_to_rev_this
```

The strings reveal three requirements:
1. The binary needs to be run with argv[0] = "./devilishFruit"
2. Environment variable PWD must equal "/tmp/gogear5"
3. Environment variable ONE_PIECE must equal "IS_REAL"

### Step 3: Disassembly Analysis

Analyzing the main function shows:
1. It checks if argv[0] matches "./devilishFruit"
2. It checks for PWD=/tmp/gogear5 in environment variables
3. It checks for ONE_PIECE=IS_REAL in environment variables
4. If all three conditions are met, it calls `you_dont_need_to_rev_this` function which contains the decryption logic and prints the flag

### Step 4: Execute with Correct Conditions

```bash
# Create symlink with correct name
ln -sf /path/to/missing_one_piece ./devilishFruit

# Run with correct environment
PWD=/tmp/gogear5 ONE_PIECE=IS_REAL ./devilishFruit
```

Output:
```
The legends have been proven true! BCCTF{I_gU3S5_7hAt_Wh1t3BeArD_6uY_W45_TRu7h1n6!}
```

## Solve Script

```bash
#!/bin/bash
# Solve script for missing-one-piece

# Create the binary with the correct argv[0]
ln -sf /home/kobisteve07/projects/ctfwriteups/ctfs/bearcatctf2026/rev/missing-one-piece/dist/missing_one_piece ./devilishFruit

# Run with required environment variables
PWD=/tmp/gogear5 ONE_PIECE=IS_REAL ./devilishFruit
```

## Flag

`BCCTF{I_gU3S5_7hAt_Wh1t3BeArD_6uY_W45_TRu7h1n6!}`
