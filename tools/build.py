#!/usr/bin/env python3
"""Render src/ into site/ and clearsign the plaintext pages.

    tools/build.py <key-id>

Needs gpg with the secret key available. Each page exists twice: a
plaintext document that gets clearsigned, and the HTML version, which
carries that same signature in its footer.
"""
import re
import subprocess
import sys
from pathlib import Path

from randomart import randomart

ROOT = Path(__file__).resolve().parent.parent
SRC, SITE = ROOT / "src", ROOT / "site"
PAGES = [("esthetis.txt", "index.html"), ("privacy.txt", "privacy.html")]


def gpg(*args, data=None):
    return subprocess.run(["gpg", "--batch", *args], input=data,
                          capture_output=True, text=True, check=True).stdout


def fingerprint(key):
    for line in gpg("--with-colons", "--fingerprint", key).splitlines():
        if line.startswith("fpr:"):
            return line.split(":")[9]
    sys.exit(f"no fingerprint for {key}")


def fill(text, values):
    out = re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: values[m.group(1)], text)
    assert "{{" not in out, "unfilled placeholder"
    return out


def main(key):
    fp = fingerprint(key)
    groups = [fp[i:i + 4] for i in range(0, 40, 4)]
    values = {
        "FP_HEX": fp,
        "FP_SPACED": " ".join(groups),
        "FP_SPLIT": " ".join(groups[:5]) + "<br>" + " ".join(groups[5:]),
        "FP_SHORT": " ".join(groups[:2]) + " ... " + " ".join(groups[-2:]),
        "ART": randomart(bytes.fromhex(fp)),
    }

    (SITE / "esthetis.asc").write_text(gpg("--armor", "--export", fp))

    for txt, html in PAGES:
        plain = fill((SRC / txt).read_text(), values)
        (SITE / txt).write_text(plain)
        signed = gpg("--local-user", fp, "--digest-algo", "SHA512",
                     "--clearsign", data=plain)
        (SITE / f"{txt}.asc").write_text(signed)

        page = dict(values,
                    HASH=re.search(r"^Hash: (\S+)", signed, re.M).group(1),
                    SIG=re.search(r"-----BEGIN PGP SIGNATURE-----\n\n(.*?)\n"
                                  r"-----END PGP SIGNATURE-----",
                                  signed, re.S).group(1))
        (SITE / html).write_text(fill((SRC / html).read_text(), page))

        gpg("--verify", str(SITE / f"{txt}.asc"))
        print(f"{html}: signed by {values['FP_SPACED']}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
