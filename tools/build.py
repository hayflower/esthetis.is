#!/usr/bin/env python3
"""Render src/ into site/ and clearsign each page.

    tools/build.py <key-id>          build and sign (gpg asks for the passphrase)
    tools/build.py <key-id> --draft  preview build, unsigned, pending text allowed

Each page exists twice: the HTML, and a plaintext rendering of it that gets
clearsigned. The HTML footer carries that same signature.
"""
import re
import subprocess
import sys
from pathlib import Path

from plaintext import render

ROOT = Path(__file__).resolve().parent.parent
SRC, SITE = ROOT / "src", ROOT / "site"
PAGES = [("index.html", "esthetis.txt", "https://esthetis.is"),
         ("privacy.html", "privacy.txt", "https://esthetis.is/privacy")]


def gpg(*args, data=None):
    return subprocess.run(["gpg", *args], input=data,
                          capture_output=True, text=True, check=True).stdout


def fingerprint(key):
    for line in gpg("--with-colons", "--fingerprint", key).splitlines():
        if line.startswith("fpr:"):
            return line.split(":")[9]
    sys.exit(f"no fingerprint for {key}")


def fill(text, values):
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: values[m.group(1)], text)


def main(key, draft):
    fp = fingerprint(key)
    groups = [fp[i:i + 4] for i in range(0, 40, 4)]
    values = {
        "FP_HEX": fp,
        "FP_SPACED": " ".join(groups),
        "FP_SHORT": " ".join(groups[:2]) + " ... " + " ".join(groups[-2:]),
    }

    (SITE / "esthetis.asc").write_text(gpg("--armor", "--export", fp))

    for html, txt, url in PAGES:
        source = (SRC / html).read_text()
        if 'class="pending"' in source and not draft:
            sys.exit(f"{html} still has pending text; fill it in or build with --draft")

        page = fill(source, dict(values, SIG="{{SIG}}"))
        plain = render(page, f"{url}  ·  Signed with {values['FP_SHORT']}")
        (SITE / txt).write_text(plain)

        if draft:
            sig = "(draft: not signed)"
        else:
            signed = gpg("--local-user", fp, "--digest-algo", "SHA512",
                         "--clearsign", data=plain)
            (SITE / f"{txt}.asc").write_text(signed)
            gpg("--verify", str(SITE / f"{txt}.asc"))
            sig = re.search(r"-----BEGIN PGP SIGNATURE-----\n\n(.*?)\n"
                            r"-----END PGP SIGNATURE-----", signed, re.S).group(1)

        out = page.replace("{{SIG}}", sig)
        assert "{{" not in out, f"unfilled placeholder in {html}"
        (SITE / html).write_text(out)
        print(f"{html}: {'draft' if draft else 'signed by ' + values['FP_SPACED']}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--draft"]
    if len(args) != 1:
        sys.exit(__doc__)
    main(args[0], "--draft" in sys.argv)
