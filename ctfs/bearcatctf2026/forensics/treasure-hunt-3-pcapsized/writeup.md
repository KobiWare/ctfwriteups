---
author: Claude
credit: Claude, Fenix
---
## Solution

### Analysis
The PCAP file contains a mix of normal network traffic (TLS sessions, NTP, UDP broadcasts) and a suspicious sequence of 48 TCP packets from `237.84.138.236:1337` to `192.168.4.3:5748`.

```
$ tshark -r pcapsized.pcap -Y "tcp.port == 1337" | head -10
 18   4.167562 237.84.138.236 -> 192.168.4.3  TCP [TCP Window Update] 1337 -> 5748 [ACK]
 19   4.168462 237.84.138.236 -> 192.168.4.3  TCP 1337 -> 5748 [RST, URG]
 20   4.169162 237.84.138.236 -> 192.168.4.3  TCP 1337 -> 5748 [FIN, RST, PSH]
 21   4.170062 237.84.138.236 -> 192.168.4.3  TCP 1337 -> 5748 [FIN, SYN]
 22   4.170862 237.84.138.236 -> 192.168.4.3  TCP 1337 -> 5748 [FIN, RST, ACK]
```

These packets have unusual TCP flag combinations that make no sense in normal TCP communication (e.g., `[RST, URG]`, `[FIN, RST, PSH]`, `[FIN, SYN]`). The source port 1337 ("leet") is another indicator of intentional placement.

### Approach

**Step 1: Identify the covert channel.**
The challenge hints ("dive to the bottom", "My Vessel", "flag transfers") all point to data encoded in the TCP flags field:
- "dive to the bottom" = look at the lowest protocol layer (TCP flags)
- "My Vessel" = the packet itself carries hidden cargo
- "flag transfers" = TCP *flags* are used to *transfer* the *flag*

**Step 2: Extract TCP flag values.**
Each packet's TCP flags field was extracted using tshark:

```
$ tshark -r pcapsized.pcap -Y "tcp.port == 1337" -T fields -e tcp.flags
0x0010
0x0024
0x000d
0x0003
0x0015
0x0004
...
0x003d
0x003d
```

All 48 values fall in the range 0x00-0x3D (0-61 decimal), fitting within 6 bits -- the six standard TCP flags: URG (bit 5), ACK (bit 4), PSH (bit 3), RST (bit 2), SYN (bit 1), FIN (bit 0).

**Step 3: Decode the bitstream.**
With 48 packets at 6 bits each: 48 * 6 = 288 bits = 36 bytes. Each flag value was converted to a 6-bit binary string, concatenated into a single bitstream, then grouped into 8-bit bytes:

```python
flags = [
    0x10, 0x24, 0x0d, 0x03, 0x15, 0x04, 0x19, 0x3b,
    0x10, 0x33, 0x01, 0x2e, 0x14, 0x33, 0x24, 0x31,
    0x18, 0x37, 0x15, 0x2f, 0x15, 0x13, 0x15, 0x1f,
    0x18, 0x34, 0x20, 0x34, 0x13, 0x26, 0x38, 0x33,
    0x0c, 0x17, 0x0d, 0x1f, 0x0d, 0x04, 0x34, 0x31,
    0x1c, 0x23, 0x05, 0x14, 0x0c, 0x33, 0x3d, 0x3d
]

bits = ''.join(format(f, '06b') for f in flags)
result = bytearray(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))
print(result.decode())  # BCCTF{C0nS91cuoU5_cH4Nn31s_4M1r1T3?}
```

The decoded 36 bytes are also valid base64 (`QkNDVEZ7QzBuUzkxY3VvVTVfY0g0Tm4zMXNfNE0xcjFUMz99`) which decodes to the same flag, confirming the last two `0x3d` values correspond to `=` padding characters.

The leetspeak in the flag decodes to: "Conspicuous channels, amirite?" -- a reference to how TCP flag covert channels are easily detectable by network monitoring tools.

## Flag
`BCCTF{C0nS91cuoU5_cH4Nn31s_4M1r1T3?}`
