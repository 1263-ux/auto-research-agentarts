"""A build-time key contract for frozen retrieval packets.

Why this exists
---------------
Two things are now established facts about the M1b packet, both measured from bytes:

1. `id` alone is not a key. Ten ids appear in `documents` and in `excluded_sections`
   at once, because the id scheme is `id == "d-16-" + sectno` and ten clause numbers
   repeat inside the source volume.
2. The remedy proposed in the M1b errata -- move the key to `(id, kept_as)` -- does not
   work. On those ten ids the kept document and the dropped duplicate are both
   `kept_as == "distractor"`, so `(id, kept_as)` still collides ten times.

This module turns that into an executable contract so a *new* packet fails at build time
instead of at consumption time. It is deliberately independent of `src.autoresearch`:
an error in the packet builder must not be able to hide itself here.

Contract v1
-----------
  * every row in both partitions carries a non-empty `partition` field;
  * `(id, partition)` is unique inside each table and across the two tables;
  * `id` alone is never treated as a key, and neither is `(id, kept_as)`.

The frozen M1 packets predate the contract and violate it by construction. This script
does not repair them and does not call them broken: it reports the real packet as
`LEGACY_VIOLATION_EXPECTED`, then shows -- on the real rows -- that both admissible fixes
collapse the collision count to zero.

Usage
-----
    .venv/Scripts/python.exe -B scripts/packet_key_contract.py --self-test
    .venv/Scripts/python.exe -B scripts/packet_key_contract.py --packet runs/m1b-packet-20261119
    .venv/Scripts/python.exe -B scripts/packet_key_contract.py --packet runs/m1b-packet-20261119 \
        --json runs/key-contract-20261119/contract.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

SCHEMA = "packet-key-contract-v1"
REQUIRED_FIELDS = ("id", "partition")
PARTITIONS = {"kept", "excluded"}

# Findings that make a packet unfit to freeze. Everything else is evidence, not a failure.
BLOCKING = {"C1_MISSING_FIELD", "C2_DUPLICATE_WITHIN_TABLE", "C3_DUPLICATE_ACROSS_TABLES"}


class KeyContractError(AssertionError):
    """Raised by assert_contract() when a packet may not be frozen."""


def key_of(row, fields=REQUIRED_FIELDS):
    return tuple(str(row.get(field, "")) for field in fields)


def collisions(rows, fields=REQUIRED_FIELDS):
    """Keys that occur more than once, with their multiplicity."""
    counts = Counter(key_of(row, fields) for row in rows)
    return {key: n for key, n in counts.items() if n > 1}


def check(tables):
    """Run contract v1 over named tables. `tables` maps table name -> list of rows."""
    findings = []

    # C1 -- every row must carry a non-empty partition inside the closed vocabulary.
    missing, unknown = [], []
    for name, rows in tables.items():
        for index, row in enumerate(rows):
            value = row.get("partition")
            if not isinstance(value, str) or not value.strip():
                missing.append({"table": name, "index": index, "id": row.get("id")})
            elif value not in PARTITIONS:
                unknown.append({"table": name, "index": index, "id": row.get("id"), "value": value})
    findings.append({
        "code": "C1_MISSING_FIELD",
        "state": "FAIL" if missing or unknown else "PASS",
        "detail": {"missing_or_blank": len(missing), "outside_vocabulary": len(unknown),
                   "examples": (missing + unknown)[:5]},
    })

    # C2 -- (id, partition) unique inside each table.
    per_table = {}
    for name, rows in tables.items():
        found = collisions(rows)
        per_table[name] = len(found)
    findings.append({
        "code": "C2_DUPLICATE_WITHIN_TABLE",
        "state": "FAIL" if any(per_table.values()) else "PASS",
        "detail": per_table,
    })

    # C3 -- (id, partition) unique across the union of tables.
    union = [row for rows in tables.values() for row in rows]
    across = collisions(union)
    findings.append({
        "code": "C3_DUPLICATE_ACROSS_TABLES",
        "state": "FAIL" if across else "PASS",
        "detail": {"colliding_keys": len(across), "rows": len(union)},
    })

    # C4 -- evidence that bare `id` cannot be a key. Informational by design: a clean
    # packet may legitimately repeat an id across partitions, so this never blocks.
    bare = collisions(union, fields=("id",))
    findings.append({
        "code": "C4_ID_ALONE_COLLIDES",
        "state": "EVIDENCE",
        "detail": {"colliding_ids": len(bare), "sample": sorted(k[0] for k in bare)[:10]},
    })

    # C5 -- evidence that (id, kept_as) cannot be a key either.
    compound = collisions(union, fields=("id", "kept_as"))
    findings.append({
        "code": "C5_ID_KEPT_AS_COLLIDES",
        "state": "EVIDENCE",
        "detail": {"colliding_keys": len(compound),
                   "sample": sorted(k[0] for k in compound)[:10]},
    })

    blocking = [f for f in findings if f["code"] in BLOCKING and f["state"] == "FAIL"]
    return {
        "schema": SCHEMA,
        "verdict": "FAIL" if blocking else "PASS",
        "blocking_findings": [f["code"] for f in blocking],
        "findings": findings,
    }


def assert_contract(documents, exclusions):
    """Call this from a packet builder before freezing. Raises on any blocking finding."""
    report = check({"documents": documents, "excluded_sections": exclusions})
    if report["verdict"] != "PASS":
        raise KeyContractError(
            "packet-key-contract-v1 rejected the packet: "
            + ", ".join(report["blocking_findings"])
            + " -- see findings for row indices"
        )
    return report


def restamp_duplicate_ids(documents, exclusions, suffix="#dup"):
    """Fix route A: give the later occurrence of a repeated id a distinct suffix.

    Deterministic: rows are walked documents-first, then exclusions, in file order.
    """
    seen = set()
    out = {"documents": [], "excluded_sections": []}
    for name, rows in (("documents", documents), ("excluded_sections", exclusions)):
        for row in rows:
            new = dict(row)
            base = str(row.get("id", ""))
            if base in seen:
                new["id"] = base + suffix
                new["id_restamped_from"] = base
            seen.add(new["id"])
            out[name].append(new)
    return out["documents"], out["excluded_sections"]


def stamp_partition(documents, exclusions):
    """Fix route B: add an explicit partition field; ids stay untouched."""
    kept = []
    for row in documents:
        new = dict(row)
        new["partition"] = "kept"
        kept.append(new)
    dropped = []
    for row in exclusions:
        new = dict(row)
        new["partition"] = "excluded"
        dropped.append(new)
    return kept, dropped


def load_packet(packet_dir):
    manifest = json.loads((Path(packet_dir) / "assets" / "manifest.json").read_text(encoding="utf-8"))
    return manifest, manifest["documents"], manifest["excluded_sections"]


def evaluate_real_packet(packet_dir):
    manifest, documents, exclusions = load_packet(packet_dir)

    as_is = check({"documents": documents, "excluded_sections": exclusions})
    # The frozen packet has no partition field, so the as-is verdict is a fail by design.
    # Report it as legacy rather than as a regression of this round.
    as_is["label"] = "as_frozen"
    as_is["verdict"] = "LEGACY_VIOLATION_EXPECTED"

    a_docs, a_exc = restamp_duplicate_ids(documents, exclusions)
    route_a = check({"documents": a_docs, "excluded_sections": a_exc})
    route_a["label"] = "route_a_restamp_ids"

    b_docs, b_exc = stamp_partition(documents, exclusions)
    route_b = check({"documents": b_docs, "excluded_sections": b_exc})
    route_b["label"] = "route_b_partition_field"

    # Route A re-stamps ids but leaves the partitions undeclared. Does it become usable once
    # partitions are declared as well? Measured on the real rows, not assumed.
    ab_docs, ab_exc = restamp_duplicate_ids(b_docs, b_exc)
    route_ab = check({"documents": ab_docs, "excluded_sections": ab_exc})
    route_ab["label"] = "route_a_plus_b"

    return {
        "schema": SCHEMA,
        "packet": manifest.get("packet"),
        "packet_dir": str(Path(packet_dir)).replace("\\", "/"),
        "rows": {"documents": len(documents), "excluded_sections": len(exclusions)},
        "views": [as_is, route_a, route_b, route_ab],
        "summary": {
            "as_frozen_id_collisions": _value(as_is, "C4_ID_ALONE_COLLIDES", "colliding_ids"),
            "as_frozen_id_kept_as_collisions": _value(as_is, "C5_ID_KEPT_AS_COLLIDES", "colliding_keys"),
            "route_a_collisions": _value(route_a, "C3_DUPLICATE_ACROSS_TABLES", "colliding_keys"),
            "route_b_collisions": _value(route_b, "C3_DUPLICATE_ACROSS_TABLES", "colliding_keys"),
            "route_a_plus_b_collisions": _value(route_ab, "C3_DUPLICATE_ACROSS_TABLES", "colliding_keys"),
            "route_a_blocking": route_a["blocking_findings"],
            "route_b_blocking": route_b["blocking_findings"],
        },
    }


def _value(view, code, field):
    for finding in view["findings"]:
        if finding["code"] == code:
            return finding["detail"].get(field)
    return None


def self_test():
    """Fault injection on the checker itself: each case must land on the stated code."""
    cases = []

    def case(name, tables, expect_verdict, expect_code=None):
        report = check(tables)
        hit = any(f["code"] == expect_code and f["state"] == "FAIL" for f in report["findings"]) \
            if expect_code else True
        cases.append({
            "case": name,
            "expected_verdict": expect_verdict,
            "actual_verdict": report["verdict"],
            "expected_failure_code": expect_code,
            "ok": report["verdict"] == expect_verdict and hit,
        })

    good = {"documents": [{"id": "a", "partition": "kept"}, {"id": "b", "partition": "kept"}],
            "excluded_sections": [{"id": "c", "partition": "excluded"}]}
    case("clean packet passes", good, "PASS")

    case("same id in both partitions passes",
         {"documents": [{"id": "a", "partition": "kept"}],
          "excluded_sections": [{"id": "a", "partition": "excluded"}]},
         "PASS")

    case("duplicate inside one table fails",
         {"documents": [{"id": "a", "partition": "kept"}, {"id": "a", "partition": "kept"}],
          "excluded_sections": []},
         "FAIL", "C2_DUPLICATE_WITHIN_TABLE")

    case("cross-table duplicate on the same partition fails",
         {"documents": [{"id": "a", "partition": "kept"}],
          "excluded_sections": [{"id": "a", "partition": "kept"}]},
         "FAIL", "C3_DUPLICATE_ACROSS_TABLES")

    case("missing partition fails",
         {"documents": [{"id": "a"}], "excluded_sections": []},
         "FAIL", "C1_MISSING_FIELD")

    case("blank partition fails",
         {"documents": [{"id": "a", "partition": "  "}], "excluded_sections": []},
         "FAIL", "C1_MISSING_FIELD")

    case("partition outside vocabulary fails",
         {"documents": [{"id": "a", "partition": "other"}], "excluded_sections": []},
         "FAIL", "C1_MISSING_FIELD")

    # The counter-example the errata pointed at: identical kept_as on both copies.
    legacy = check({"documents": [{"id": "a", "kept_as": "distractor"}],
                    "excluded_sections": [{"id": "a", "kept_as": "distractor"}]})
    c5 = next(f for f in legacy["findings"] if f["code"] == "C5_ID_KEPT_AS_COLLIDES")
    cases.append({
        "case": "legacy (id, kept_as) collision is visible as evidence",
        "expected_verdict": "FAIL",  # no partition field either
        "actual_verdict": legacy["verdict"],
        "expected_failure_code": "C5_ID_KEPT_AS_COLLIDES",
        "ok": legacy["verdict"] == "FAIL" and c5["detail"]["colliding_keys"] == 1,
    })

    # assert_contract must refuse the same packet that check() refuses.
    raised = False
    try:
        assert_contract([{"id": "a"}], [])
    except KeyContractError:
        raised = True
    cases.append({
        "case": "assert_contract raises on a non-compliant packet",
        "expected_verdict": "RAISES",
        "actual_verdict": "RAISES" if raised else "RETURNED",
        "expected_failure_code": None,
        "ok": raised,
    })

    passed = sum(1 for c in cases if c["ok"])
    return {"schema": SCHEMA + "-selftest", "passed": passed, "total": len(cases), "cases": cases}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--packet", help="packet directory containing assets/manifest.json")
    parser.add_argument("--json", help="write the full report here")
    parser.add_argument("--self-test", action="store_true", help="fault-inject the checker")
    args = parser.parse_args(argv)

    if not args.packet and not args.self_test:
        parser.error("give --packet and/or --self-test")

    payload = {}
    exit_code = 0

    if args.self_test:
        result = self_test()
        payload["self_test"] = result
        print(f"self-test: {result['passed']}/{result['total']}")
        for item in result["cases"]:
            mark = "ok  " if item["ok"] else "FAIL"
            print(f"  [{mark}] {item['case']} -> {item['actual_verdict']}")
        if result["passed"] != result["total"]:
            exit_code = 1

    if args.packet:
        report = evaluate_real_packet(args.packet)
        payload["packet_report"] = report
        print(f"packet: {report['packet']} rows={report['rows']}")
        for view in report["views"]:
            print(f"  {view['label']:<24} {view['verdict']:<26} "
                  f"blocking={view['blocking_findings']}")
        print("  summary: " + json.dumps(report["summary"], ensure_ascii=False))
        # A single route that fails is a finding, not a crash: only "no route reaches PASS"
        # means the contract cannot be satisfied by the packet's own rows.
        if not any(view["verdict"] == "PASS" for view in report["views"][1:]):
            print("  no fix route reaches PASS on the real rows", file=sys.stderr)
            exit_code = 1

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes((json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
        print(f"wrote {out}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
