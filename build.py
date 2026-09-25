#!/usr/bin/env python3
"""
fpsales build script.

Reads the plain-text email templates in private/templates/, bundles them
into one JSON payload, and encrypts it with Nati's user name and password
(from private/credentials.json). Writes the result to data.enc.json,
which is the only template file that gets published.

Run from this folder after editing any template:

    python3 build.py

Uses the Python standard library only. No installs needed.

Crypto: PBKDF2-HMAC-SHA256 (310,000 rounds) derives two 32-byte keys from
"username\\npassword". The payload is encrypted with HMAC-SHA256 in counter
mode and authenticated with HMAC-SHA256 (encrypt-then-MAC). index.html
reverses this with the browser's built-in Web Crypto API.
"""
import base64, hashlib, hmac, json, os, re, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
PRIVATE = os.path.join(HERE, "private")
TEMPLATES = os.path.join(PRIVATE, "templates")
CREDS = os.path.join(PRIVATE, "credentials.json")
OUT = os.path.join(HERE, "data.enc.json")
ITERATIONS = 310_000

STATUSES = {"none", "cozzini", "unknown"}
FOCUSES = {"all", "procurement", "purchasing", "culinary", "executive"}


def fail(msg):
    print("ERROR: " + msg)
    sys.exit(1)


def parse_template(path):
    text = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        fail(f"{os.path.basename(path)} is missing its --- header block.")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    for key in ("profile", "status", "focus", "subject"):
        if not meta.get(key):
            fail(f"{os.path.basename(path)} is missing '{key}' in its header.")
    if meta["status"] not in STATUSES:
        fail(f"{os.path.basename(path)}: status must be one of {sorted(STATUSES)}.")
    if meta["focus"] not in FOCUSES:
        fail(f"{os.path.basename(path)}: focus must be one of {sorted(FOCUSES)}.")
    meta["body"] = m.group(2).strip("\n")
    meta["file"] = os.path.basename(path)
    return meta


def keystream_xor(key, nonce, data):
    out = bytearray(len(data))
    for block in range((len(data) + 31) // 32):
        ks = hmac.new(key, nonce + block.to_bytes(4, "big"), hashlib.sha256).digest()
        start = block * 32
        chunk = data[start:start + 32]
        for i, b in enumerate(chunk):
            out[start + i] = b ^ ks[i]
    return bytes(out)


def main():
    if not os.path.exists(CREDS):
        fail("private/credentials.json not found.")
    creds = json.load(open(CREDS, encoding="utf-8"))
    user, pw = creds.get("username", ""), creds.get("password", "")
    if not user or not pw:
        fail("credentials.json needs both username and password.")

    sig_path = os.path.join(TEMPLATES, "_signature.md")
    if not os.path.exists(sig_path):
        fail("private/templates/_signature.md not found.")
    signature = open(sig_path, encoding="utf-8").read().strip("\n")

    templates = {}
    for name in sorted(os.listdir(TEMPLATES)):
        if not name.endswith(".md") or name.startswith("_"):
            continue
        t = parse_template(os.path.join(TEMPLATES, name))
        key = t["status"] if t["focus"] == "all" else f'{t["status"]}-{t["focus"]}'
        if key in templates:
            fail(f"Two templates share status/focus '{key}': {templates[key]['file']} and {name}.")
        templates[key] = t

    for status in STATUSES:
        if status not in templates and not any(k.startswith(status + "-") for k in templates):
            print(f"WARNING: no template covers status '{status}'.")

    payload = json.dumps({
        "built": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "signature": signature,
        "templates": templates,
    }, ensure_ascii=False).encode("utf-8")

    salt, nonce = os.urandom(16), os.urandom(16)
    keys = hashlib.pbkdf2_hmac("sha256", f"{user}\n{pw}".encode("utf-8"), salt, ITERATIONS, 64)
    enc_key, mac_key = keys[:32], keys[32:]
    ct = keystream_xor(enc_key, nonce, payload)
    tag = hmac.new(mac_key, salt + nonce + ct, hashlib.sha256).digest()

    b64 = lambda b: base64.b64encode(b).decode("ascii")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"v": 1, "iter": ITERATIONS, "salt": b64(salt), "nonce": b64(nonce),
                   "ct": b64(ct), "tag": b64(tag)}, f)
        f.write("\n")

    print(f"Built data.enc.json with {len(templates)} templates:")
    for k, t in sorted(templates.items()):
        print(f"  {k:<22} {t['file']:<24} {t['profile']}")


if __name__ == "__main__":
    main()
