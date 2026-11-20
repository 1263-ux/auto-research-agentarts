"""Show whether the G5 transfer pin can pass on THIS checkout, byte by byte.

Round 11 concluded that fixing B1 would "necessarily break the G5 archived
evidence", because `run_scheduling_policy_transfer.py` hashes the live working
tree and compares it against stored fingerprints. That conclusion is about
*content*. It leaves out state: this repository sets `core.autocrlf=true` and
`.gitattributes` pins `eol=lf` for exactly one file, so the other pinned sources
are checked out with CRLF on Windows. Their live bytes therefore differ from the
recorded (LF) bytes **before anybody edits anything**.

That distinction decides whether the B1 trade-off is real here:

  if every pin differs only by line endings -> the G5 environment gate is already
  red on this machine, so fixing B1 costs nothing that is not already lost;
  if the pins match the live bytes -> editing them really would destroy evidence.

This script answers it with a proof instead of an inference. For each pinned file
it computes the disk hash, the committed-blob hash, and the hash of the disk bytes
after normalising CRLF to LF. `eol_only` means the third equals the second: the
only difference is line endings.

Exit codes
  0  every pin matches the live bytes (a content edit would break them)
  1  at least one pin differs by content (the evidence is stale for another reason)
  2  at least one pin differs by line endings only (gate already red here)
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

# Mirrors SOURCE_FILES in scripts/run_scheduling_policy_transfer.py. Duplicated on
# purpose: importing that module would pull in the POSIX-only ledger and fail on
# Windows, which is the very blocker under discussion.
PINNED = (
    "src/autoresearch/contracts.py",
    "src/autoresearch/bounded_study_ledger.py",
    "src/autoresearch/scheduling_threshold_policy.py",
    "src/autoresearch/scheduling_kernel.py",
    "scripts/run_scheduling_policy_transfer.py",
    "scripts/verify_scheduling_policy_transfer.py",
)

# Values the script itself hardcodes or records; used to say which side is stale.
RECORDED = {
    "src/autoresearch/bounded_study_ledger.py":
        "1d39b54dd4dcc6eb1c477cc7c1d8c5f78d8a8e8fc362390189fe8a8d9ba535a4",
    "src/autoresearch/scheduling_kernel.py":
        "3a335e102279ce9e6a7a8861a3f203670fccfbfb3ea3d2941f8b9406ea92e401",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def blob_bytes(root, relative, commit="HEAD"):
    out = subprocess.run(["git", "-C", str(root), "cat-file", "blob", "%s:%s" % (commit, relative)],
                         capture_output=True)
    return None if out.returncode else out.stdout


def classify(root, relative):
    path = root / relative
    if not path.is_file():
        return {"file": relative, "verdict": "missing", "detail": "not on disk"}
    disk = path.read_bytes()
    blob = blob_bytes(root, relative)
    if blob is None:
        return {"file": relative, "verdict": "missing_blob", "detail": "not in HEAD"}
    normalised = disk.replace(b"\r\n", b"\n")
    record = {
        "file": relative,
        "disk_sha256": sha(disk),
        "disk_bytes": len(disk),
        "blob_sha256": sha(blob),
        "blob_bytes": len(blob),
        "crlf_count": disk.count(b"\r\n"),
    }
    recorded = RECORDED.get(relative)
    if recorded:
        record["recorded_sha256"] = recorded
        record["recorded_matches"] = "blob" if recorded == sha(blob) else (
            "disk" if recorded == sha(disk) else "neither")
    if sha(disk) == sha(blob):
        record["verdict"] = "match"
        record["detail"] = "live bytes equal the committed blob"
    elif sha(normalised) == sha(blob):
        record["verdict"] = "eol_only"
        record["detail"] = "%d CRLF conversions account for all %d extra bytes" % (
            record["crlf_count"], len(disk) - len(blob))
    else:
        record["verdict"] = "content_differs"
        record["detail"] = "%d bytes differ beyond line endings" % abs(len(disk) - len(blob))
    return record


def exit_code(records):
    verdicts = {r["verdict"] for r in records}
    if "content_differs" in verdicts or "missing" in verdicts or "missing_blob" in verdicts:
        return 1
    if "eol_only" in verdicts:
        return 2
    return 0


def render(code, records):
    lines = ["%-52s %-14s %-10s %s" % ("file", "verdict", "disk/blob", "detail")]
    for r in records:
        if r["verdict"] in ("missing", "missing_blob"):
            lines.append("%-52s %-14s %-10s %s" % (r["file"], r["verdict"], "-", r["detail"]))
            continue
        lines.append("%-52s %-14s %-10s %s %s"
                     % (r["file"], r["verdict"],
                        "%d/%d" % (r["disk_bytes"], r["blob_bytes"]), r["detail"],
                        ("recorded=%s" % r["recorded_matches"]) if "recorded_matches" in r else ""))
    counts = {}
    for r in records:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    lines.append("")
    lines.append("%d pinned files: %s" % (len(records), ", ".join(
        "%d %s" % (n, k) for k, n in sorted(counts.items()))))
    labels = {0: "PINS_MATCH_LIVE_BYTES",
              1: "CONTENT_DIFFERS",
              2: "EOL_ONLY_GATE_ALREADY_RED"}
    lines.append("EXIT %d (%s)" % (code, labels[code]))
    if code == 2:
        lines.append("NOTE: the only difference is line endings, so the G5 environment gate "
                     "cannot pass on this checkout whether or not B1 is fixed.")
    return "\n".join(lines)


def selftest():
    import tempfile
    results = []

    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "a@b"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "a"], check=True)
        document = {"same.py": b"one\ntwo\nthree\n",
                    "crlf.py": b"alpha\nbeta\n"}
        for name, raw in document.items():
            (root / name).write_bytes(raw)
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "x"], check=True)

        # S1: unchanged file matches the blob
        record = classify(root, "same.py")
        check("S1 identical bytes are a match", record["verdict"] == "match", str(record))

        # S2: a CRLF working copy is eol_only, and the byte delta is the CRLF count
        (root / "crlf.py").write_bytes(b"alpha\r\nbeta\r\n")
        record = classify(root, "crlf.py")
        check("S2 CRLF is eol_only, not content drift", record["verdict"] == "eol_only", str(record.get("verdict")))
        check("S2b the byte delta equals the CRLF count",
              record["disk_bytes"] - record["blob_bytes"] == record["crlf_count"], str(record))

        # S3: one real character change must not be excused as a line ending
        (root / "same.py").write_bytes(b"one\ntwo\nthreeX\n")
        record = classify(root, "same.py")
        check("S3 a real edit is content_differs", record["verdict"] == "content_differs",
              str(record.get("verdict")))

        # S4: exit code separates the three states
        check("S4 eol_only exits 2", exit_code([{"verdict": "eol_only"}]) == 2)
        check("S4b content_differs exits 1", exit_code([{"verdict": "content_differs"}]) == 1)
        check("S4c all matching exits 0", exit_code([{"verdict": "match"}]) == 0)

        # S5: a file absent from disk is its own verdict, never a silent match
        (root / "gone.py").write_bytes(b"")
        subprocess.run(["git", "-C", str(root), "add", "gone.py"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "y"], check=True)
        (root / "gone.py").unlink()
        check("S5 missing file is reported, not skipped",
              classify(root, "gone.py")["verdict"] == "missing")

    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        print("%-58s %s %s" % (name, "PASS" if ok else "FAIL", "" if ok else "| " + detail))
    print("")
    print("%d/%d checks passed" % (passed, len(results)))
    return 0 if passed == len(results) else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    root = Path(args.root).resolve()
    records = [classify(root, relative) for relative in PINNED]
    code = exit_code(records)
    if args.json:
        print(json.dumps({"exit_code": code, "files": records}, indent=2, ensure_ascii=False))
    else:
        print(render(code, records))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
