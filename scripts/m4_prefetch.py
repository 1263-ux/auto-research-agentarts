"""Place the four M4 inputs the evaluator wants, without touching GitHub directly.

Why this exists: `M4.load` and `M4Evaluation.load_benchmark` fetch from
`raw.githubusercontent.com`, which is unreachable from this machine (SSL EOF
mid-handshake, three retries, then a hard fail). That is a network fact about
this host, not a defect in the upstream code, so the fix belongs here and not in
a patched copy of the package.

The evaluator only downloads when a file is *absent* (`M4._missing_files`), so
fetching the same bytes through a mirror and dropping them at the exact paths it
looks for makes the unmodified upstream path run. Nothing is monkeypatched; if
this script is wrong the evaluator will simply go back to failing.

Paths are hard-coded from the package source rather than guessed:
    {data}/m4/datasets/{Hourly-train.csv, Hourly-test.csv, M4-info.csv}
    {data}/m4/datasets/submission-Naive2.csv   <- read for the OWA denominator
    {data}/m4/benchmarks/submission-118.zip    <- read by load_benchmark

Every byte is hashed so the report can say which files it actually scored.
"""

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

DATASET = "https://raw.githubusercontent.com/Mcompetitions/M4-methods/master/Dataset"
FORECASTS = "https://github.com/Nixtla/m4-forecasts/raw/master/forecasts"

FILES = [
    (f"{DATASET}/Train/Hourly-train.csv", "datasets/Hourly-train.csv"),
    (f"{DATASET}/Test/Hourly-test.csv", "datasets/Hourly-test.csv"),
    (f"{DATASET}/M4-info.csv", "datasets/M4-info.csv"),
    (f"{FORECASTS}/submission-Naive2.zip", "datasets/submission-Naive2.zip"),
    (f"{FORECASTS}/submission-118.zip", "benchmarks/submission-118.zip"),
    (f"{FORECASTS}/submission-245.zip", "benchmarks/submission-245.zip"),
]


def fetch(url, destination, mirror, retries=3):
    if destination.exists() and destination.stat().st_size > 0:
        return "cached"
    destination.parent.mkdir(parents=True, exist_ok=True)
    errors = []
    for attempt in range(1, retries + 1):
        try:
            request = Request(mirror + url if mirror else url,
                              headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=90) as response:
                payload = response.read()
            if not payload:
                raise IOError("empty response")
            destination.write_bytes(payload)
            return "downloaded"
        except Exception as exc:                    # noqa: BLE001 - reported
            errors.append("%s: %s" % (type(exc).__name__, exc))
    raise IOError("%s failed after %d attempts: %s"
                  % (url, retries, "; ".join(errors)))


def unzip(archive, target):
    """Extract next to the archive, keeping only what the evaluator reads."""
    written = []
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.namelist():
            if member.endswith("/"):
                continue
            out = target / Path(member).name
            out.write_bytes(bundle.read(member))
            written.append(out)
    return written


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="runs/m4-upstream-20261121/data")
    parser.add_argument("--mirror", default="https://gh-proxy.com/",
                        help="prefix prepended to the original URL; empty for direct")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.data_dir) / "m4"
    rows = []
    for url, relative in FILES:
        target = root / relative
        try:
            how = fetch(url, target, args.mirror)
        except Exception as exc:                    # noqa: BLE001 - reported
            print("FAILED %-28s %s" % (relative, exc))
            return 2
        rows.append({"file": relative, "how": how,
                     "bytes": target.stat().st_size,
                     "sha256": sha256(target)})
        print("%-9s %-34s %10d bytes  %s"
              % (how, relative, target.stat().st_size, rows[-1]["sha256"][:16]))

    for archive, where in (("datasets/submission-Naive2.zip", "datasets"),
                           ("benchmarks/submission-118.zip", "benchmarks"),
                           ("benchmarks/submission-245.zip", "benchmarks")):
        path = root / archive
        if path.exists():
            for out in unzip(path, root / where):
                print("unzipped %-32s %10d bytes  %s"
                      % (out.name, out.stat().st_size, sha256(out)[:16]))

    if args.json:
        import json
        print(json.dumps(rows, indent=2))
    missing = [r["file"] for r in rows
               if not (root / r["file"]).exists()]
    print("EXIT %d (%s)" % (0 if not missing else 2,
                            "INPUTS_PRESENT" if not missing else "INPUTS_MISSING"))
    return 0 if not missing else 2


if __name__ == "__main__":
    sys.exit(main())
