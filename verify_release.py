#!/usr/bin/env python3
"""verify_release: check a Hamilton engine release without trusting us.

Public tool. Standard library only (plus the OpenTimestamps client for step 3).

    python verify_release.py registry.jsonl               # chain + manifest hashes
    python verify_release.py registry.jsonl --ots         # also verify Bitcoin timestamps
    python verify_release.py registry.jsonl --engine DIR  # also recompute an engine fingerprint (auditors)
    python verify_release.py registry.jsonl --dossier DIR --version V  # check a dossier you were given

What each check proves:

1. Chain. Every registry line's manifest hashes to the recorded manifest_sha256,
   and names the previous line's hash. Rewriting or deleting any past release
   breaks every link after it.
2. Manifest. The manifest states the engine fingerprint, the test suite
   fingerprint, pass/fail counts per validation study, and the SHA-256 of the
   private validation dossier.
3. Time (--ots). The manifest's hash was committed to the Bitcoin blockchain via
   OpenTimestamps. Proves the manifest existed no later than that block.
4. Engine (--engine, auditors). Recomputes the engine fingerprint from source
   code you were given and compares it to the manifest: same code or not.
5. Dossier (--dossier, auditors). Recomputes the dossier hash from the files you
   were given and compares it to the manifest: same dossier or not.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()


def tree_sha(directory, names):
    rows = sorted((n.replace(os.sep, "/"), sha(os.path.join(directory, n))) for n in names)
    return hashlib.sha256("".join(f"{h}  {n}\n" for n, h in rows).encode()).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("registry")
    ap.add_argument("--ots", action="store_true")
    ap.add_argument("--engine", help="folder holding the engine source (auditors)")
    ap.add_argument("--dossier", help="folder holding a release dossier (auditors)")
    ap.add_argument("--version", help="release version for --dossier")
    args = ap.parse_args(argv)

    base = os.path.dirname(os.path.abspath(args.registry))
    entries = [json.loads(l) for l in open(args.registry, encoding="utf-8") if l.strip()]
    ok = True
    prev = None
    manifests = {}
    for e in entries:
        mpath = os.path.join(base, e["version"], "manifest.json")
        m_sha = sha(mpath)
        man = json.load(open(mpath, encoding="utf-8"))
        manifests[e["version"]] = man
        good = (m_sha == e["manifest_sha256"] and e["previous_manifest_sha256"] == prev
                and man.get("previous_manifest_sha256") == prev)
        ok &= good
        print(f"{'OK  ' if good else 'FAIL'} {e['version']} {e['date']} engine {e['engine_id']} manifest {m_sha[:16]}")
        if args.ots:
            r = subprocess.run(["ots", "verify", mpath + ".ots"], capture_output=True, text=True)
            text = (r.stdout + r.stderr).strip().splitlines()
            print("     ots:", text[-1] if text else "no output")
        prev = e["manifest_sha256"]
    print("chain:", "intact" if ok else "BROKEN")

    if args.engine:
        man = manifests[entries[-1]["version"]] if not args.version else manifests[args.version]
        names = ["cli.py", "money.py", "ledger.py", "mathkit.py", "pricing.py",
                 "corpfin.py", "fsa.py", "fpa.py", "fingerprint.py"]
        got = tree_sha(args.engine, names)
        same = got == man["engine_sha256"]
        ok &= same
        print(f"engine: {'MATCH' if same else 'DIFFERENT'} {got}")

    if args.dossier:
        man = manifests[args.version or entries[-1]["version"]]
        got = tree_sha(args.dossier, os.listdir(args.dossier))
        same = got == man["dossier_sha256"]
        ok &= same
        print(f"dossier: {'MATCH' if same else 'DIFFERENT'} {got}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
