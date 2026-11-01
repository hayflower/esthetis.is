"""OpenSSH drunken-bishop randomart (sshkey.c fingerprint_randomart)."""
import sys

def randomart(data: bytes, title="ED25519 256") -> str:
    W, H = 17, 9
    syms = " .o+=*BOX@%&#/^SE"
    grid = [[0] * W for _ in range(H)]
    x, y = W // 2, H // 2
    for byte in data:
        for _ in range(4):
            x += 1 if byte & 1 else -1
            y += 1 if byte & 2 else -1
            x = max(0, min(W - 1, x)); y = max(0, min(H - 1, y))
            if grid[y][x] < len(syms) - 3:
                grid[y][x] += 1
            byte >>= 2
    grid[H // 2][W // 2] = len(syms) - 2
    grid[y][x] = len(syms) - 1
    head = f"[{title}]"
    top = "+" + ("--" + head).ljust(W, "-")[:W] + "+"
    rows = ["|" + "".join(syms[c] for c in r) + "|" for r in grid]
    return "\n".join([top, *rows, "+" + "-" * W + "+"])

if __name__ == "__main__":
    print(randomart(bytes.fromhex(sys.argv[1])))
