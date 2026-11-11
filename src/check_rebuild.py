"""Check that a fresh `make` reproduced the committed outputs.

Text outputs (README.md, THESIS.md, APPENDIX.md, docs/thesis.html) must be byte-identical.
results.json may differ only in float noise: macOS and Linux linear-algebra
libraries round differently around the 12th significant digit.
"""
import json, math, subprocess, sys

TEXT = ["README.md", "THESIS.md", "APPENDIX.md", "docs/thesis.html"]
JSON = "data/processed/results.json"


def committed(path):
    return subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, text=True, check=True).stdout


def diffs(a, b, where="$"):
    if isinstance(a, float) or isinstance(b, float):
        if not (isinstance(a, (int, float)) and isinstance(b, (int, float))
                and math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)):
            yield f"{where}: {a!r} != {b!r}"
    elif isinstance(a, dict) and isinstance(b, dict):
        for k in a.keys() | b.keys():
            yield from diffs(a.get(k), b.get(k), f"{where}.{k}")
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            yield from diffs(x, y, f"{where}[{i}]")
    elif a != b:
        yield f"{where}: {a!r} != {b!r}"


bad = [p for p in TEXT if open(p).read() != committed(p)]
bad += list(diffs(json.load(open(JSON)), json.loads(committed(JSON))))
for b in bad[:20]:
    print("MISMATCH", b)
if bad:
    sys.exit(f"{len(bad)} mismatches against the committed outputs")
print(f"Rebuild matches the commit: {', '.join(TEXT)} identical; {JSON} equal to 1e-9 relative.")
