---
author: OpenCode
credit: Tyler, OpenCode
---

## Solution

### Analysis

The challenge provides a `poems.zip` file. Extracting it reveals a git repository containing various pirate-themed poems:
- acrostic.txt
- haiku.txt
- limerick.txt
- poem.txt
- sestina.txt
- sonnet.txt
- villanelle.txt

The description mentions that the author "wrote the flag into one of them, but then overwrote it" - this hints at using git history to recover deleted content.

### Approach

**Step 1: Extract and examine the repository.**
```bash
unzip poems.zip
cd Poem_About_Pirates
```

**Step 2: Examine git history.**
The standard `git log` shows commits adding various poems, but doesn't reveal anything obviously containing the flag. However, the reflog shows a more complex picture:

```
fb94dcb HEAD@{0}: rebase (finish): returning to refs/heads/main
fb94dcb HEAD@{1}: rebase (pick): Added sestina about pirates
...
d058dda HEAD@{9}: commit: Changed villanelle about pirates
```

The key commit is `d058dda` - "Changed villanelle about pirates" - which was later squashed during a rebase operation.

**Step 3: Examine the intermediate commit.**
Using `git show d058dda`, we can see the original villanelle.txt content before it was overwritten:

```diff
- BCCTF{1gN0r3_4ll_PreV1OU5_1n57Ruc7iOns}.
+ They chase the ghosts that on the winds do ride.
```

The flag was in the villanelle and was removed during the rebase/squash operation. The original line read:

> Across the map where ink and salt decay.
> BCCTF{1gN0r3_4ll_PreV1OU5_1n57Ruc7iOns}.
> They seek the gold before the break of day.

The commit message "Changed villanelle about pirates" and the fact it was later squashed indicates the author accidentally committed the flag and then tried to remove it - but git preserves the history!

### Key Insight

Git reflog and `git show <commit>` allow recovering any commit that was ever referenced, even if it was subsequently squashed or rebased. This is a common forensics technique - the "deleted" data often still exists in the git object database.

## Flag

`BCCTF{1gN0r3_4ll_PreV1OU5_1n57Ruc7iOns}`
