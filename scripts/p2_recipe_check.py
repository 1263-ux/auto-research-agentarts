"""P2 recipe-library gate: recompute the verdict instead of re-arguing it.

`docs/project/workbuddy/recipe-library-index-20261120.md` concludes "P2 未通过"
in prose. This script takes the same facts from
`recipe-manifest-20261120.json` and decides again, mechanically, so the next
round does not have to trust a paragraph.

What it does check: counts, numbering, that each declared source card really
exists in the file it names, category spread, anchor strength, whether a claimed
call record has a file behind it, whether a minimal example is more than a draft,
and that blocked recipes name a substitute or a next acceptance step.

What it does NOT check: whether the nine per-card fields are present in the
prose. Grepping the cards for field labels produced false "missing" results
because the same field is worded differently per card (原产物 appears only on the
W04c cards). Those booleans are transcriptions, printed as such; the gate does
not pretend to verify them.

Exit codes
  0  PASS        every rule satisfied; P2 met as specified by this gate
  1  FAIL        at least one rule violated; the failing rules are named
"""
import argparse
import copy
import json
from pathlib import Path
import re
import sys

CATEGORIES = ("research", "data_evaluation", "engineering_computation")
CATEGORY_ZH = {"research": "资料研究", "data_evaluation": "数据评测", "engineering_computation": "工程计算"}
STRENGTHS = ("strong", "medium", "weak")
MIN_EXAMPLE_STATES = ("verified", "draft_only", "absent")
CALL_STATES = ("present", "none")
MIN_RECIPES = 10
CARD_HEADING = re.compile(r"(?m)^### 卡 (\d+) · ")
INDEX_ROW = re.compile(r"(?m)^\| (\d+) \| ")


def record(rule, ok, detail):
    return {"rule": rule, "ok": bool(ok), "detail": detail}


def check(manifest, root):
    """Apply the rules. `root` resolves relative evidence paths."""
    root = Path(root)
    results = []
    recipes = manifest.get("recipes") or []

    results.append(record("R1_count", len(recipes) >= MIN_RECIPES,
                          "%d recipes, need at least %d" % (len(recipes), MIN_RECIPES)))

    numbers = [item.get("number") for item in recipes]
    good_numbering = (all(isinstance(value, int) and value >= 1 for value in numbers)
                      and sorted(numbers) == list(range(1, len(recipes) + 1)))
    results.append(record("R2_numbering", good_numbering, "numbers: " + repr(numbers)))

    card_problems = []
    for item in recipes:
        source = item.get("source") or {}
        path = root / str(source.get("file", ""))
        if not path.is_file():
            card_problems.append("%s: missing %s" % (item.get("title"), source.get("file")))
            continue
        headings = [int(value) for value in CARD_HEADING.findall(path.read_text(encoding="utf-8"))]
        if source.get("card") not in headings:
            card_problems.append("%s: no '### 卡 %s' in %s" % (item.get("title"), source.get("card"), source.get("file")))
    results.append(record("R3_source_cards", not card_problems,
                          "; ".join(card_problems) if card_problems else "every declared card heading exists"))

    bad_category = [item.get("title") for item in recipes if item.get("category") not in CATEGORIES]
    tally = {name: sum(1 for item in recipes if item.get("category") == name) for name in CATEGORIES}
    empty_category = [CATEGORY_ZH[name] for name in CATEGORIES if tally[name] == 0]
    results.append(record("R4_categories", not bad_category and not empty_category,
                          ("unknown category: " + ", ".join(bad_category)) if bad_category
                          else ("category not covered: " + ", ".join(empty_category)) if empty_category
                          else "tally " + ", ".join("%s=%d" % (CATEGORY_ZH[name], tally[name]) for name in CATEGORIES)))

    bad_strength = [item.get("title") for item in recipes if item.get("anchor_strength") not in STRENGTHS]
    weak = [item.get("title") for item in recipes if item.get("anchor_strength") == "weak"]
    detail = []
    if bad_strength:
        detail.append("unknown strength: " + ", ".join(bad_strength))
    if weak:
        detail.append("not versioned (weak anchor): " + ", ".join(weak))
    results.append(record("R5_anchor", not detail,
                          "; ".join(detail) if detail else "every recipe carries a usable version anchor"))

    missing_evidence = []
    no_record = []
    for item in recipes:
        call = item.get("call_record") or {}
        declared = call.get("declared")
        evidence = [str(path) for path in (call.get("evidence") or [])]
        if declared == "present":
            absent = [path for path in evidence if not (root / path).is_file()]
            if not evidence:
                no_record.append("%s: claims a call record with no evidence path" % item.get("title"))
            elif absent:
                missing_evidence.append("%s: missing %s" % (item.get("title"), ", ".join(absent)))
        elif declared == "none":
            no_record.append("%s: no call record" % item.get("title"))
        else:
            no_record.append("%s: call_record.declared=%r is not in %r" % (item.get("title"), declared, CALL_STATES))
    results.append(record("R6_call_record", not missing_evidence and not no_record,
                          "; ".join(missing_evidence + no_record) if (missing_evidence or no_record)
                          else "every recipe has a call record with a file behind it"))

    example_problems = []
    for item in recipes:
        state = item.get("min_example")
        evidence = [str(path) for path in (item.get("min_example_evidence") or [])]
        if state not in MIN_EXAMPLE_STATES:
            example_problems.append("%s: min_example=%r not in %r" % (item.get("title"), state, MIN_EXAMPLE_STATES))
        elif state != "verified":
            example_problems.append("%s: minimal example is %s, never run" % (item.get("title"), state))
        elif not evidence or any(not (root / path).is_file() for path in evidence):
            example_problems.append("%s: claims a verified example without a log" % item.get("title"))
    results.append(record("R7_min_example", not example_problems,
                          "; ".join(example_problems) if example_problems
                          else "every recipe has a re-run log for its minimal example"))

    no_substitute = [item.get("title") for item in recipes
                     if (item.get("blockers") or [])
                     and len(str(item.get("substitute_or_next_acceptance") or "").strip()) < 20]
    results.append(record("R8_blocked_with_substitute", not no_substitute,
                          "blocked without a substitute or next acceptance: " + ", ".join(no_substitute)
                          if no_substitute else "every blocked recipe names a way forward"))

    missing_field = [item.get("title") for item in recipes
                     if not (item.get("ict_change") and item.get("failure_conditions") and item.get("feedback_branch"))]
    results.append(record("R9_required_fields", not missing_field,
                          "missing ICT change / failure condition / feedback branch: " + ", ".join(missing_field)
                          if missing_field else "ICT change, failure condition and feedback branch all declared"))

    titles = [item.get("title") for item in recipes]
    results.append(record("R10_unique_titles", len(set(titles)) == len(titles),
                          "duplicate titles" if len(set(titles)) != len(titles) else "titles unique"))

    index_path = root / str(manifest.get("source_index", ""))
    if index_path.is_file():
        rows = len(INDEX_ROW.findall(index_path.read_text(encoding="utf-8")))
        results.append(record("R11_index_rows", rows == len(recipes),
                              "index has %d rows, manifest has %d" % (rows, len(recipes))))
    else:
        results.append(record("R11_index_rows", False, "index not found at " + str(manifest.get("source_index"))))

    code = 0 if all(item["ok"] for item in results) else 1
    return code, results


def render(results, code):
    lines = ["%-28s %s  %s" % (item["rule"], "PASS" if item["ok"] else "FAIL", item["detail"])
             for item in results]
    failing = [item["rule"] for item in results if not item["ok"]]
    lines.append("")
    lines.append("EXIT %d (%s)" % (code, "PASS" if code == 0 else "FAIL: " + ", ".join(failing)))
    return "\n".join(lines)


def passing_manifest(root):
    """A synthetic manifest that satisfies every rule, used to prove the gate can pass."""
    (root / "evidence").mkdir(parents=True, exist_ok=True)
    (root / "evidence" / "call.txt").write_text("synthetic call record\n", encoding="utf-8")
    (root / "evidence" / "example.txt").write_text("synthetic example log\n", encoding="utf-8")
    card = root / "cards.md"
    card.write_text("\n".join("### 卡 %d · synthetic %d" % (n, n) for n in range(1, 11)), encoding="utf-8")
    index = root / "index.md"
    index.write_text("\n".join("| %d | synthetic |" % n for n in range(1, 11)), encoding="utf-8")
    return {
        "source_index": "index.md",
        "recipes": [{
            "number": n, "title": "synthetic %d" % n,
            "category": CATEGORIES[n % 3],
            "source": {"file": "cards.md", "card": n},
            "anchor_strength": "strong",
            "anchor_value": "commit c0ffee",
            "min_example": "verified", "min_example_evidence": ["evidence/example.txt"],
            "call_record": {"declared": "present", "evidence": ["evidence/call.txt"]},
            "blockers": [], "substitute_or_next_acceptance": "",
            "ict_change": True, "failure_conditions": True, "feedback_branch": True,
        } for n in range(1, 11)],
    }


MUTATIONS = [
    ("baseline (nothing satisfied)", lambda m, root: None, {"R6_call_record", "R7_min_example"}),
    ("drop a recipe from the middle", lambda m, root: m["recipes"].pop(4),
     {"R1_count", "R2_numbering", "R11_index_rows"}),
    ("duplicate a number", lambda m, root: m["recipes"][1].__setitem__("number", 1), {"R2_numbering"}),
    ("point at a card that does not exist", lambda m, root: m["recipes"][0]["source"].__setitem__("card", 99),
     {"R3_source_cards"}),
    ("unknown category", lambda m, root: m["recipes"][0].__setitem__("category", "misc"), {"R4_categories"}),
    ("weak anchor", lambda m, root: m["recipes"][0].__setitem__("anchor_strength", "weak"), {"R5_anchor"}),
    ("claim a record with no evidence", lambda m, root: m["recipes"][0].__setitem__(
        "call_record", {"declared": "present", "evidence": []}), {"R6_call_record"}),
    ("claim a record pointing at nothing", lambda m, root: m["recipes"][0].__setitem__(
        "call_record", {"declared": "present", "evidence": ["evidence/nope.txt"]}), {"R6_call_record"}),
    ("verified example without a log", lambda m, root: m["recipes"][0].__setitem__(
        "min_example_evidence", []), {"R7_min_example"}),
    ("blocked with no way forward", lambda m, root: (
        m["recipes"][0].__setitem__("blockers", ["needs a key"]),
        m["recipes"][0].__setitem__("substitute_or_next_acceptance", "")), {"R8_blocked_with_substitute"}),
    ("drop the ICT change", lambda m, root: m["recipes"][0].__setitem__("ict_change", False), {"R9_required_fields"}),
    ("duplicate a title", lambda m, root: m["recipes"][1].__setitem__("title", m["recipes"][0]["title"]),
     {"R10_unique_titles"}),
    ("index rows disagree", lambda m, root: (root / "index.md").write_text("| 1 | only one |\n", encoding="utf-8"),
     {"R11_index_rows"}),
]


def self_test(root):
    scratch = root / "selftest"
    scratch.mkdir(parents=True, exist_ok=True)
    baseline = passing_manifest(scratch)
    results = []

    code, rules = check(baseline, scratch)
    results.append({"mutation": "synthetic fully-satisfied manifest", "ok": code == 0,
                    "detail": "exit %d, failing %r" % (code,
                             [item["rule"] for item in rules if not item["ok"]])})

    for name, mutate, expected in MUTATIONS:
        # Each mutation gets its own directory so evidence writes cannot leak.
        case_dir = scratch / re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        case_dir.mkdir(parents=True, exist_ok=True)
        if name == "baseline (nothing satisfied)":
            # Same ten synthetic cards, but with the real index and no records:
            # this is the shape of today's library.
            manifest = {"source_index": str(Path("docs/project/workbuddy/recipe-library-index-20261120.md").resolve()),
                        "recipes": []}
            for entry in passing_manifest(case_dir)["recipes"]:
                entry.update({"call_record": {"declared": "none", "evidence": []},
                              "min_example": "draft_only"})
                del entry["min_example_evidence"]
                manifest["recipes"].append(entry)
            mutate(manifest, case_dir)
            code, rules = check(manifest, case_dir)
            failing = {item["rule"] for item in rules if not item["ok"]}
            results.append({"mutation": name, "ok": expected <= failing,
                            "detail": "failing %r, expected to include %r" % (sorted(failing), sorted(expected))})
            continue
        manifest = copy.deepcopy(passing_manifest(case_dir))
        manifest["source_index"] = "index.md"
        mutate(manifest, case_dir)
        code, rules = check(manifest, case_dir)
        failing = {item["rule"] for item in rules if not item["ok"]}
        results.append({"mutation": name, "ok": code == 1 and expected <= failing,
                        "detail": "exit %d, failing %r" % (code, sorted(failing))})

    code_a, rules_a = check(passing_manifest(scratch / "det_a"), scratch / "det_a")
    code_b, rules_b = check(passing_manifest(scratch / "det_b"), scratch / "det_b")
    first, second = render(rules_a, code_a), render(rules_b, code_b)
    results.append({"mutation": "determinism", "ok": first.replace("det_a", "X") == second.replace("det_b", "X"),
                    "detail": "two runs identical modulo the directory name"})

    passed = sum(1 for item in results if item["ok"])
    (scratch / "results.json").write_bytes(
        json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8"))
    return (0 if passed == len(results) else 1), results


def main(argv):
    parser = argparse.ArgumentParser(description="Recompute the P2 recipe-library verdict.")
    parser.add_argument("--manifest", default="docs/project/workbuddy/recipe-manifest-20261120.json")
    parser.add_argument("--out", default="runs/p2-gate-20261120")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    root = Path(".").resolve()

    if args.self_test:
        code, results = self_test(root / args.out)
        passed = sum(1 for item in results if item["ok"])
        if args.json:
            print(json.dumps({"self_test": results, "passed": passed, "total": len(results)},
                             ensure_ascii=False, indent=2, sort_keys=True))
        else:
            for item in results:
                print("%-42s %s  %s" % (item["mutation"], "PASS" if item["ok"] else "FAIL", item["detail"]))
            print("\nSELF-TEST %d/%d" % (passed, len(results)))
        return code

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    code, results = check(manifest, root)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"exit_code": code, "manifest": args.manifest, "results": results,
               "field_completeness_verified": manifest.get("field_completeness_verified", False)}
    (out_dir / "check.json").write_bytes(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8"))
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) if args.json else render(results, code))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
