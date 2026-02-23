---
author: OpenCode
credit: Tyler, OpenCode
---

## Solution

### Analysis

The challenge provides a PCAP file (`blackpearl_vs_royalnavy.pcap`) from a naval raid on the Black Pearl. The description mentions a "document believed to contain contraband" - we need to analyze the network traffic to find what was being transferred.

Initial examination reveals:
- Port scanning activity from 172.16.40.16 (Royal Navy)
- FTP connections to 172.16.40.17 (Black Pearl)
- HTTP traffic on port 80

### Approach

**Step 1: Examine network protocols.**
```bash
tshark -r blackpearl_vs_royalnavy.pcap -Y "tcp or http or ftp"
```

**Step 2: Look for interesting HTTP traffic.**
The most interesting finding is an HTTP request:
```
204  138.129518  172.16.40.16 → 172.16.40.17  HTTP  GET /map.b64 HTTP/1.1 
210  138.130719  172.16.40.17 → 172.16.40.16  HTTP  297 HTTP/1.0 200 OK 
```

A file called `map.b64` - likely base64 encoded data.

**Step 3: Extract the HTTP response.**
Using tshark with hex dump:
```bash
tshark -r blackpearl_vs_royalnavy.pcap -Y "http.response" -x
```

The response contains:
```
QkNDVEZ7YjFAY2twM0ByMV8xMCR0XzF0JF90cjNAJHVyM30K
```

**Step 4: Decode the data.**
```bash
echo "QkNDVEZ7YjFAY2twM0ByMV8xMCR0XzF0JF90cjNAJHVyM30K" | base64 -d
```

This decodes to the flag!

### Key Insight

The Royal Navy intercepted network traffic from their raid on the Black Pearl. The HTTP request to `/map.b64` was the Black Pearl attempting to transfer contraband (the flag) - but the network capture captured the evidence.

### Solve Script

```python
#!/usr/bin/env python3
import base64

# The base64 data extracted from the HTTP response in the PCAP
encoded_data = "QkNDVEZ7YjFAY2twM0ByMV8xMCR0XzF0JF90cjNAJHVyM30K"

# Decode and print the flag
flag = base64.b64decode(encoded_data).decode()
print(f"Flag: {flag}")
```

## Flag

`BCCTF{b1@ckp3@r1_10$t_1t$_tr3@$ur3}`
