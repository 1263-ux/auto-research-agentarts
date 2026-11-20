"""Does "run one card once" actually move the P2 gate? Test the published promise.

Two places in this repository state the same operational promise:

  continuous-status.md  "任一张卡跑通一次最小例 -> 改两个字段 + 给日志路径 ->
                         门禁自动少一条失败项。P2 的进度因此可量化"
  current.md            "P2 的缺口现在只剩「卡真跑过一次」这一件事"

Both are load-bearing: they are what makes P2 look like a sequence of small
increments rather than a batch job. Neither has been executed. This script
executes it against synthetic manifests and reports which reading is true.

Why it can be false
-------------------
R6 and R7 are *all-recipes* rules: they iterate over every recipe and fail if
any single one is missing a call record or a verified minimal example. Filling
one card therefore cannot clear them -- it can only shorten their detail string.
R5 is a different axis again: it fails on `anchor_strength == "weak"` for two
named cards, which running a minimal example does not touch.

So the four scenarios below separate the run axis from the version axis, and
the "one card" claim is the one that gets falsified or confirmed.

   A  baseline, manifest untouched
   B  exactly one card filled in (call record + verified example + real files)
   C  all ten cards filled in
   D  C plus the two weak anchors versioned  -- COUNTERFACTUAL, see below

D is not a claim that P2 is achievable. It only answers "is the gate
simultaneously satisfiable at all, and if so what is the minimal set", by
pretending the two version pins exist. Nothing here asserts they do.

What this does not do
---------------------
No writes outside `runs/`, no installs, no network, no model calls, no research
actions. The real manifest is never modified: every scenario is a deep copy
written under `runs/p2-unlock-20261120/`. Evidence files created for the filled
cards are synthetic placeholders that exist only so the rule's `is_file()` check
has something to open -- they are not call records and must never be cited as
such.

Exit codes
  0  every scenario produced its expected failing-rule set
  1  a scenario disagreed with the expectation above (the probe is wrong, or the
     gate changed)
  2  usage error
"""

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

MANIFEST = "docs/project/workbuddy/recipe-manifest-20261120.json"
OUT = "runs/p2-unlock-20261120"


def _load_gate():
    """Load the gate by path. Imported, not re-implemented: a second copy of the
    rules would be a second thing to drift."""
    path = Path(__file__).resolve().parent / "p2_recipe_check.py"
    spec = importlib.util.spec_from_file_location("_p2_recipe_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def failing(results):
    """The failing rule names, sorted. This is the only thing the promise moves."""
    return sorted({item["rule"] for item in results if not item["ok"]})


def _slug(title):
    return "".join(ch if ch.isalnum() else "-" for ch in title).strip("-").lower()


def fill_card(root, item, evidence_dir):
    """Give one recipe the two things a real run would produce."""
    slug = _slug(item.get("title") or "card")
    record_path = evidence_dir / ("%s-call.md" % slug)
    example_path = evidence_dir / ("%s-example.log" % slug)
    record_path.write_bytes(
        ("synthetic placeholder for %s -- not a real call record\n" % item.get("title")).encode("utf-8"))
    example_path.write_bytes(
        ("synthetic placeholder log for %s -- not a real run\n" % item.get("title")).encode("utf-8"))
    item["call_record"] = {"declared": "present",
                           "evidence": [str(record_path.relative_to(root)).replace("\\", "/")]}
    item["min_example"] = "verified"
    item["min_example_evidence"] = [str(example_path.relative_to(root)).replace("\\", "/")]


def build(manifest, root, titles, evidence_dir, version_anchors=False):
    """A scenario manifest. Deep copy every time; never touch the caller's."""
    scenario = copy.deepcopy(manifest)
    for item in scenario["recipes"]:
        if item.get("title") in titles:
            fill_card(root, item, evidence_dir)
    if version_anchors:
        for item in scenario["recipes"]:
            if item.get("anchor_strength") == "weak":
                item["anchor_strength"] = "medium"
    return scenario


def facts(manifest):
    """Input-side counts, derived from the manifest alone (not from the gate)."""
    recipes = manifest["recipes"]
    return {
        "recipes": len(recipes),
        "no_call_record": sum(1 for item in recipes
                              if (item.get("call_record") or {}).get("declared") == "none"),
        "example_draft_only": sum(1 for item in recipes if item.get("min_example") == "draft_only"),
        "weak_anchors": [item.get("title") for item in recipes
                         if item.get("anchor_strength") == "weak"],
        "blockers_total": sum(len(item.get("blockers") or []) for item in recipes),
        "cards_with_zero_blockers": sum(1 for item in recipes if not (item.get("blockers") or [])),
        "min_blockers_on_one_card": min(len(item.get("blockers") or []) for item in recipes),
        "max_blockers_on_one_card": max(len(item.get("blockers") or []) for item in recipes),
    }


EXPECTED = {
    "A_baseline": ["R5_anchor", "R6_call_record", "R7_min_example"],
    # The promise says this should lose one rule. R6/R7 are all-recipes rules,
    # so the prediction is that it loses none.
    "B_one_card_filled": ["R5_anchor", "R6_call_record", "R7_min_example"],
    "C_all_ten_filled": ["R5_anchor"],
    "D_all_filled_anchors_versioned": [],
}


def run(root, manifest_path, out_dir):
    gate = _load_gate()
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    titles = [item.get("title") for item in manifest["recipes"]]
    # Resolved against root: evidence paths are stored repo-relative, and
    # Path.relative_to() refuses to bridge a relative dir and an absolute root.
    evidence_dir = (root / out_dir / "evidence").resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)

    scenarios = {
        "A_baseline": copy.deepcopy(manifest),
        "B_one_card_filled": build(manifest, root, titles[:1], evidence_dir),
        "C_all_ten_filled": build(manifest, root, titles, evidence_dir),
        "D_all_filled_anchors_versioned": build(manifest, root, titles, evidence_dir,
                                                version_anchors=True),
    }

    rows = []
    for name, scenario in scenarios.items():
        code, results = gate.check(scenario, root)
        payload = {"scenario": name,
                   "exit_code": code,
                   "failing": failing(results),
                   "expected": EXPECTED[name],
                   "matched": failing(results) == EXPECTED[name],
                   "details": {item["rule"]: item["detail"]
                               for item in results if not item["ok"]}}
        (out_dir / ("%s.json" % name)).write_bytes(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8"))
        rows.append(payload)

    return {"manifest": str(manifest_path), "facts": facts(manifest), "scenarios": rows}


def render(report):
    lines = ["P2 UNLOCK PROBE  (does filling one card move the gate?)", ""]
    facts = report["facts"]
    lines.append("INPUT (derived from the manifest, not from the gate)")
    lines.append("  recipes %d / call records missing %d / examples still draft_only %d"
                 % (facts["recipes"], facts["no_call_record"], facts["example_draft_only"]))
    lines.append("  weak anchors %d: %s" % (len(facts["weak_anchors"]), ", ".join(facts["weak_anchors"])))
    lines.append("  blockers %d across %d cards; cards with zero blockers %d; per-card range %d-%d"
                 % (facts["blockers_total"], facts["recipes"], facts["cards_with_zero_blockers"],
                    facts["min_blockers_on_one_card"], facts["max_blockers_on_one_card"]))
    lines.append("")
    lines.append("SCENARIOS")
    for row in report["scenarios"]:
        lines.append("  %-32s rc=%s failing=%s"
                     % (row["scenario"], row["exit_code"],
                        ",".join(row["failing"]) if row["failing"] else "(none)"))
    lines.append("")
    lines.append("READING")
    b = next(row for row in report["scenarios"] if row["scenario"] == "B_one_card_filled")
    c = next(row for row in report["scenarios"] if row["scenario"] == "C_all_ten_filled")
    lines.append("  one card filled: %d failing rule(s), unchanged from baseline -> promise %s"
                 % (len(b["failing"]), "REFUTED" if len(b["failing"]) == 3 else "holds"))
    lines.append("  all ten filled:  %d failing rule(s) %s"
                 % (len(c["failing"]), ",".join(c["failing"]) if c["failing"] else ""))
    lines.append("  -> the run axis needs %d real runs, not 1; the version axis needs %d anchor(s)"
                 % (facts["recipes"], len(facts["weak_anchors"])))
    lines.append("  -> D is counterfactual: it pretends the two anchors exist. Nothing here claims they do.")
    ok = all(row["matched"] for row in report["scenarios"])
    lines.append("")
    lines.append("EXIT %d (%s)" % (0 if ok else 1, "EXPECTATIONS_MET" if ok else "EXPECTATION_MISMATCH"))
    return "\n".join(lines)


def selftest():
    import tempfile
    results = []

    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    check("T1 failing() reads only the failing rules",
          failing([{"rule": "R1", "ok": True}, {"rule": "R2", "ok": False}]) == ["R2"])
    check("T1b failing() is deduplicated and sorted",
          failing([{"rule": "b", "ok": False}, {"rule": "a", "ok": False},
                   {"rule": "a", "ok": False}]) == ["a", "b"])
    check("T2 all-passing yields an empty set", failing([{"rule": "R1", "ok": True}]) == [])

    manifest = {"recipes": [
        {"title": "Alpha One", "anchor_strength": "weak", "min_example": "draft_only",
         "call_record": {"declared": "none", "evidence": []}, "blockers": ["x"]},
        {"title": "Beta Two", "anchor_strength": "medium", "min_example": "draft_only",
         "call_record": {"declared": "none", "evidence": []}, "blockers": []},
    ]}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        evidence = root / "ev"
        evidence.mkdir()

        built = build(manifest, root, ["Alpha One"], evidence)
        check("T3 build() does not mutate the caller's manifest",
              manifest["recipes"][0]["min_example"] == "draft_only",
              manifest["recipes"][0]["min_example"])
        check("T3b only the named card is filled",
              built["recipes"][0]["min_example"] == "verified"
              and built["recipes"][1]["min_example"] == "draft_only")
        check("T3c the evidence path is repo-relative and exists",
              (root / built["recipes"][0]["min_example_evidence"][0]).is_file(),
              built["recipes"][0]["min_example_evidence"][0])
        check("T3d the evidence path uses forward slashes",
              "\\" not in built["recipes"][0]["call_record"]["evidence"][0])

        versioned = build(manifest, root, [], evidence, version_anchors=True)
        check("T4 version_anchors only lifts 'weak', never invents on strong/medium",
              versioned["recipes"][0]["anchor_strength"] == "medium"
              and versioned["recipes"][1]["anchor_strength"] == "medium")

        counts = facts(manifest)
        check("T5 facts count missing call records", counts["no_call_record"] == 2, str(counts))
        check("T5b facts count cards with zero blockers", counts["cards_with_zero_blockers"] == 1, str(counts))
        check("T5c facts keep the weak anchor titles", counts["weak_anchors"] == ["Alpha One"], str(counts))

    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        print("%-62s %s %s" % (name, "PASS" if ok else "FAIL", "" if ok else "| " + detail))
    print("")
    print("%d/%d checks passed" % (passed, len(results)))
    return 0 if passed == len(results) else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", default=MANIFEST)
    parser.add_argument("--out", default=OUT)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return selftest()

    root = Path(".").resolve()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = run(root, args.manifest, out_dir)
    (out_dir / "probe.json").write_bytes(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8"))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render(report))
    return 0 if all(row["matched"] for row in report["scenarios"]) else 1


if __name__ == "__main__":
    sys.exit(main())
