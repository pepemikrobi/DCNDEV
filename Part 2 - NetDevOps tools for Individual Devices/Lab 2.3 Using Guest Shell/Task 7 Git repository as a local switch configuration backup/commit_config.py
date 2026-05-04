#!/usr/bin/env python3
import os
import sys
import subprocess
import hashlib
from datetime import datetime

try:
    from cli import execute
except ImportError:
    sys.stderr.write("Cisco cli module not available\n")
    sys.exit(1)

REPO_DIR = "/bootflash/guest-share/cfggit"
CFG_FILE = os.path.join(REPO_DIR, "running-config.cfg")
HOSTNAME_FILE = os.path.join(REPO_DIR, ".hostname")

def run(cmd, cwd=REPO_DIR, check=False):
    p = subprocess.run(
        cmd, cwd=cwd, shell=False,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True
    )
    if p.stdout:
        print(f"[CMD {' '.join(cmd)}] STDOUT:\n{p.stdout}")
    if p.stderr:
        print(f"[CMD {' '.join(cmd)}] STDERR:\n{p.stderr}", file=sys.stderr)
    if check and p.returncode != 0:
        raise RuntimeError(f"Command {cmd} failed with {p.returncode}")
    return p

def ensure_repo():
    if not os.path.isdir(REPO_DIR):
        os.makedirs(REPO_DIR, exist_ok=True)
    if not os.path.isdir(os.path.join(REPO_DIR, ".git")):
        run(["git", "init"])
        run(["git", "config", "user.name", "c9300-guestshell"])
        run(["git", "config", "user.email", "c9300@sdn.lab"])
        run(["git", "config", "commit.gpgsign", "false"])

def get_hostname():
    out = execute("show running-config | include ^hostname")
    line = out.strip()
    if line.startswith("hostname "):
        return line.split(None, 1)[1]
    return "switch"

def get_running_config():
    return execute("show running-config")

def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def main():
    ensure_repo()

    hostname = get_hostname()
    with open(HOSTNAME_FILE, "w") as f:
        f.write(hostname + "\n")

    cfg = get_running_config()
    new_hash = sha256_text(cfg)

    old_hash = None
    if os.path.exists(CFG_FILE):
        with open(CFG_FILE, "r") as f:
            old_hash = sha256_text(f.read())

    if new_hash == old_hash:
        sys.exit(0)

    with open(CFG_FILE, "w") as f:
        f.write(cfg)

    run(["git", "add", "running-config.cfg", ".hostname"])

    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    msg = f"{hostname}: auto-commit after write memory at {ts}"
    result = run(["git", "commit", "-m", msg])

    if result.returncode not in (0,):
        sys.stderr.write(result.stderr)

if __name__ == "__main__":
    main()
