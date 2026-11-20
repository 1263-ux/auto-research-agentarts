"""Recompute the Nixtla M4 Hourly example with the upstream evaluator.

The whole point of this file is that it must not be able to lie in the
comfortable direction. Three separate outcomes are kept apart:

    0  every upstream assertion held (within the published tolerance)
    1  the evaluator ran and at least one number disagreed
    2  the evaluator could not run (missing package, no network, no data)

A single "non-zero" would let a blocked run read as a failed reproduction, or
worse, let a skipped run read as a pass. The upstream page asserts

    SMAPE 9.328   MASE 0.893   OWA 0.440     np.isclose(atol=1e-3)

with the default rtol=1e-5 still in force -- np.isclose is atol + rtol*|b|, so
quoting only atol would overstate the tolerance for the two larger numbers.
Both are reported here rather than summarised.

No assertion is relaxed to make this pass. If the numbers disagree, that is the
result: the package version is 1.1.0 (PyPI latest) while the version the page
was written against is unknown, so a disagreement is a real finding about
version drift, not a bug to paper over.
"""

import argparse
import json
import sys
import time
from pathlib import Path

UPSTREAM = {
    "page": "https://nixtlaverse.nixtla.io/datasetsforecast/m4.html",
    "group": "Hourly",
    "seasonality": 24,
    "horizon": 48,
    "n_ts": 414,
    "forecast_url":
        "https://github.com/Nixtla/m4-forecasts/raw/master/forecasts/submission-118.zip",
    "expected": {"SMAPE": 9.328, "MASE": 0.893, "OWA": 0.440},
    "atol": 1e-3,
}

# Two published arms, not one. A single arm matching could be luck in the data
# or a scoring pipeline that happens to agree with one file; two independent
# submissions matching the same page to the same tolerance is much harder to
# get right by accident. The second arm costs one extra download.
ARMS = {
    "esrnn118": {"forecast_url": UPSTREAM["forecast_url"],
                 "label": "ESRNN submission-118",
                 "expected": {"SMAPE": 9.328, "MASE": 0.893, "OWA": 0.440}},
    "fforma245": {"forecast_url":
                  "https://github.com/Nixtla/m4-forecasts/raw/master/forecasts/submission-245.zip",
                  "label": "FFForma submission-245",
                  "expected": {"SMAPE": 11.506, "MASE": 0.819, "OWA": 0.484}},
}


def probe():
    """Report what is installed without importing anything heavy twice."""
    rows = {}
    for name in ("numpy", "pandas", "scipy", "datasetsforecast"):
        try:
            module = __import__(name)
            rows[name] = {"state": "present",
                          "version": getattr(module, "__version__", None)}
        except Exception as exc:                    # noqa: BLE001 - reported
            rows[name] = {"state": "absent",
                          "error": "%s: %s" % (type(exc).__name__, exc)}
    return rows


def evaluate(data_dir, forecast_url, group=UPSTREAM["group"]):
    from datasetsforecast.m4 import M4Evaluation
    started = time.time()
    result = M4Evaluation.evaluate(str(data_dir), group, forecast_url)
    return result, round(time.time() - started, 1)


def compare(result, expected=None):
    """Keep the two tolerances apart instead of inventing one blend."""
    import numpy as np
    expected = expected or UPSTREAM["expected"]
    rows, held = [], True
    for metric, wanted in expected.items():
        got = float(result[metric].item())
        atol_ok = bool(np.isclose(got, wanted, atol=UPSTREAM["atol"]))
        strict_ok = bool(np.isclose(got, wanted, atol=UPSTREAM["atol"],
                                    rtol=0.0))
        held = held and atol_ok
        rows.append({"metric": metric, "upstream": wanted,
                     "recomputed": round(got, 6),
                     "delta": round(got - wanted, 6),
                     "abs_delta": round(abs(got - wanted), 6),
                     "within_atol_only": strict_ok,
                     "within_atol_and_default_rtol": atol_ok})
    return rows, held


def render(rows, seconds, packages, data_dir, arm_label="ESRNN submission-118"):
    """Body of the report only.

    The exit line is printed by the caller, once. An earlier version printed it
    here *and* at the call site, so the precondition path emitted both
    "EXIT 1 (UPSTREAM_ASSERTIONS_FAILED)" and "EXIT 2 (PRECONDITION_MISSING)"
    for one run -- the same ambiguous-exit-code failure this project has
    already recorded three times. Two labels on one run is worse than none.
    """
    lines = ["M4 Hourly upstream recompute -- %s" % arm_label, "",
             "packages:"]
    for name, row in packages.items():
        lines.append("  %-18s %-8s %s" % (name, row["state"],
                                           row.get("version") or row.get("error", "")))
    lines += ["", "evaluator ran in %ss, data dir %s" % (seconds, data_dir), ""]
    if not rows:
        lines.append("no metric was produced")
        return "\n".join(lines)
    lines.append("%-6s %10s %12s %10s  %s" % ("metric", "upstream", "recomputed",
                                              "delta", "verdict"))
    for row in rows:
        lines.append("%-6s %10.3f %12.6f %10.6f  %s" % (
            row["metric"], row["upstream"], row["recomputed"], row["delta"],
            "match" if row["within_atol_and_default_rtol"] else "MISMATCH"))
    lines.append("")
    lines.append("tolerance as published: atol=1e-3 with np.isclose default rtol=1e-5")
    return "\n".join(lines)


EXITS = {0: "UPSTREAM_ASSERTIONS_HELD",
         1: "UPSTREAM_ASSERTIONS_FAILED",
         2: "PRECONDITION_MISSING",
         3: "EVALUATOR_DID_NOT_RUN"}


def finish(code, rows=None, seconds=0.0, packages=None, data_dir="",
           arm_label="ESRNN submission-118"):
    print(render(rows or [], seconds, packages or {}, data_dir, arm_label))
    print("EXIT %d (%s)" % (code, EXITS[code]))
    return code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="runs/m4-upstream-20261121/data")
    parser.add_argument("--arm", default="esrnn118", choices=sorted(ARMS))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--probe-only", action="store_true")
    args = parser.parse_args(argv)

    arm = ARMS[args.arm]
    packages = probe()
    if args.probe_only:
        print(json.dumps(packages, indent=2, sort_keys=True))
        missing = [n for n, r in packages.items() if r["state"] == "absent"]
        return 2 if missing else 0

    if any(r["state"] == "absent" for r in packages.values()):
        return finish(2, packages=packages, data_dir=args.data_dir,
                      arm_label=arm["label"])

    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    try:
        result, seconds = evaluate(data_dir, arm["forecast_url"])
    except Exception as exc:                        # noqa: BLE001 - reported
        print("evaluator raised %s: %s" % (type(exc).__name__, exc))
        return finish(3, packages=packages, data_dir=args.data_dir,
                      arm_label=arm["label"])

    rows, held = compare(result, arm["expected"])
    if args.json:
        print(json.dumps({"arm": args.arm, "packages": packages, "metrics": rows,
                          "held": held, "seconds": seconds},
                         indent=2, sort_keys=True))
        print("EXIT %d (%s)" % (0 if held else 1, EXITS[0 if held else 1]))
    else:
        finish(0 if held else 1, rows, seconds, packages, args.data_dir,
               arm["label"])
    return 0 if held else 1


if __name__ == "__main__":
    sys.exit(main())
