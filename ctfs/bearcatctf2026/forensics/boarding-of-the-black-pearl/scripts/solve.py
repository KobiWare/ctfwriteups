#!/usr/bin/env python3
import base64

# The base64 data extracted from the HTTP response in the PCAP
encoded_data = "QkNDVEZ7YjFAY2twM0ByMV8xMCR0XzF0JF90cjNAJHVyM30K"

# Decode and print the flag
flag = base64.b64decode(encoded_data).decode()
print(f"Flag: {flag}")
