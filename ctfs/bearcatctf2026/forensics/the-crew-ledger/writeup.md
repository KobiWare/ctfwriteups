---
author: Claude
credit: Claude, Fenix
---
## Solution

### Analysis

The challenge provides a single file `emails.tar.gz` which, when extracted, yields a directory `email_log/` containing 102 pirate-themed `.eml` files. The emails simulate communications among a pirate crew, with subjects like ship operations, treasure maps, supply assessments, and various crew activities.

### Approach

#### Step 1: Extract and Survey Emails

Extracting `emails.tar.gz` revealed 101+ `.eml` files. A broad search for "BCCTF", "flag", "secret", "hidden", and "password" across all emails identified several interesting leads:

- **Email 11** ("Secret: The X on the Map"): From the Captain to Anne Bonny, containing a password-protected `secret_location.zip` with `treasure_map.png` inside.
- **Email 68**: Contained a `recovered.zip` attachment with JPEG images (pirate-themed photos).
- **Email 81**: The Captain mentions he forgot his encryption password.
- **Email 82**: An admin replies with the hint: "Consider the name of your very first ship."
- **Email 42**: Contained `key_photo.png`.
- **Email 49**: Contained `schematic.pdf` showing a ship with a hidden compartment.
- **Email 59**: Contained `escape.png`.
- **Email 92**: "Post-Battle Supply Assessment" with `lost_supplies.xlsx` attachment.

#### Step 2: Attempt to Crack the ZIP Password

The password-protected `secret_location.zip` from email 11 was the clear target. Several approaches were tried:

- **Manual password guessing**: Tried ship names ("Scallywag", "Runa"), character names, and common pirate-related words -- all failed.
- **Dictionary attack with john**: Used `zip2john` to extract the hash, then ran John the Ripper with the `rockyou.txt` wordlist -- no match found.
- **fcrackzip**: Also attempted with rockyou -- unsuccessful.

This confirmed the password was not a common dictionary word.

#### Step 3: Investigate Images and Attachments

Multiple steganography tools were tried on the extracted images:
- **binwalk** on `Runa.jpg` and `wanted_poster.jpg` -- no hidden data.
- **exiftool** -- standard metadata only.
- **LSB steganography** with `stegano` Python library on `key_photo.png` -- nothing found.
- **stego-lsb** tool -- no hidden messages.

The `schematic.pdf` showed a ship blueprint with a mysterious hidden compartment labeled "????", hinting that something was concealed within one of the files.

#### Step 4: The Critical Discovery -- Hidden File in XLSX

The breakthrough came from examining **email 92**'s attachment `lost_supplies.xlsx`. Since `.xlsx` files are actually ZIP archives containing XML files, the internal structure was examined. Hidden within the xlsx ZIP structure were two injected files that do not belong in a normal xlsx:

- **`xl/theme/pass.xml`**: Contained the plaintext password: `Ah0y_m4t3y_801ecc51`
- **`xl/theme/secret.xml`**: Contained a copy of the `secret_location.zip` itself

#### Step 5: Extract the Flag

Using the discovered password to extract `secret_location.zip`:

```bash
unzip -P "Ah0y_m4t3y_801ecc51" -o secret_location.zip -d /tmp/treasure_verify
```

This successfully extracted `treasure_map.png`, which contained the flag written on the image.

#### Additional Investigated Leads (Dead Ends)

The solving process also explored several paths that turned out to be unrelated:
- **Acrostic from email subjects**: First letters of all 101 subjects were extracted but spelled no readable message.
- **Zero-width characters**: No invisible Unicode characters were found in email bodies.
- **Content after MIME boundaries**: No data appended after final boundary markers.
- **Base64 in plain text bodies**: No encoded strings hidden in regular email text.
- **Email 77** revealed a Wi-Fi password "DeadMenTellNoTales" in its subject, but this was not the ZIP password.

## Flag
`BCCTF{X_M4rk3Sss_th3_Sp0T}`
