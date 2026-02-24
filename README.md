# KobiWare CTF Team Writeups

This is the repo for the KobiWare CTF Team's challenge solution writeups.

The deployed website can be accessed here: https://ctfwriteups.kobiware.com

This repo also contains all of the challenge files of each ctf we participate in, so, for the ones that don't rely on a remote server, you can use this as example ctf training. Below is an AI-generated guide on how to setup your own ctfd instance with our saved challenges:

## Importing Challenges into CTFd

Each CTF directory (e.g. `ctfs/bearcatctf2026/`) contains [ctfcli](https://github.com/CTFd/ctfcli)-compatible challenge files that can be imported directly into a [CTFd](https://github.com/CTFd/CTFd) instance. The `.ctf/config` file in each directory lists all available challenges.

### Quick Start

1. **Start a CTFd instance**

   ```bash
   docker run -p 8080:8000 ctfd/ctfd
   ```

2. **Complete CTFd setup** — Open `http://127.0.0.1:8080/setup` and create an admin account.

3. **Generate an API token** — Click your username in the top-right corner, then Settings, then the Access Tokens tab. Copy the token immediately — it is only shown once.

4. **Install and configure ctfcli**

   ```bash
   pip install ctfcli
   ```

   Edit the `.ctf/config` in the CTF directory (e.g. `ctfs/bearcatctf2026/.ctf/config`) and set `url` and `access_token`:

   ```ini
   [config]
   url = http://127.0.0.1:8080
   access_token = ctfd_your_token_here
   ```

5. **Import all challenges** — Run `ctf challenge install` from the CTF's root directory (the one that contains the `.ctf/` folder):

   ```bash
   cd ctfs/<ctf name here>
   ctf challenge install
   ```

6. **Verify** — Open `http://127.0.0.1:8080/challenges` and confirm the challenges appear with correct categories, descriptions, and point values.
