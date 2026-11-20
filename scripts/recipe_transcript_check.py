"""Check that the recipe manifest is a faithful transcription of the cards.

`p2_recipe_check.py` verifies structure and evidence, and declares in the manifest
that it does NOT verify transcription (`field_completeness_verified: false`). That
declaration is honest but leaves a blind spot: if the manifest drifts from the
cards, every downstream check still passes while describing something the cards
no longer say.

This script closes that gap for the parts of transcription that can be decided
mechanically:

  R1 heading     every manifest row points at an existing `### 卡 N ·` heading
  R2 title       the manifest title and the heading share a distinctive token
  R3 anchors     every commit SHA / version pin in the manifest appears verbatim
  R4 drafts      `min_example == draft_only` agrees with the card's draft marker
  R5 field set   each card carries all three boolean-flagged fields
  R6 numbers     the card files and heading numbers match the manifest's sources

Every rule reports `match` / `mismatch` / `undecidable`, and only `mismatch` fails
the run. The cards word the same field several ways (`原产物`,
`原产物（上游公布，非本项目）`, `L0 上游公布值（非本项目）`), so a checker that
demands one exact label will report false failures -- that mistake was already made
once in this project. When a rule cannot decide, it says so instead of guessing.

Exit codes
  0  no rule mismatched (undecidable verdicts are printed and counted)
  1  at least one rule mismatched
  2  usage error
"""

import argparse
import json
from pathlib import Path
import re
import sys

# Canonical field -> base label after normalisation. The cards qualify labels
# freely (`失败条件（g0）`, `固定版本/提交（g0 manifest）`, `可重跑最小例（草案，未执行且未完整定义）`),
# so exact matching against a variant list reports false gaps. That mistake was
# already made once here: card 9 was reported as missing `失败条件` while the card
# plainly carried `失败条件（g0）`.
BASE_LABELS = {
    "原入口": "source_entry",
    "固定版本": "anchor",
    "git blob SHA": "anchor",
    "数据与许可": "licensed_data",
    "典型输入": "typical_input",
    "原产物": "upstream_artifact",
    "原基线": "upstream_artifact",
    "L0 上游公布值": "upstream_artifact",
    "失败条件": "failure_conditions",
    "反馈分支": "feedback_branch",
    "ICT 改造点": "ict_change",
    "可重跑最小例": "min_example",
    "状态": "status",
    "处理方式": "substitute",
}

PAREN_RE = re.compile(r"[（(][^）)]*[）)]")

DRAFT_MARKERS = ("草案", "未执行", "未实跑", "未运行")
SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
VERSION_RE = re.compile(r"\b\d+\.\d+(?:\.\d+)*\b")
HEADING_RE = re.compile(r"(?m)^### 卡 (\d+) · (.+)$")


def normalise_label(label):
    """`失败条件（g0）` -> `失败条件`; `失败条件/阻塞` -> `失败条件`."""
    text = PAREN_RE.sub("", label).strip()
    text = text.split("/")[0].strip()
    return text


def collect_labels(body):
    """Field labels, tolerant of a qualifier between the bold run and the colon.

    `- **失败条件**（g0）：...` puts the qualifier outside the bold markers. A
    pattern that demands `**：` drops the whole line, which read as "card 9 has no
    failure-conditions field" while the field was right there.
    """
    return re.findall(r"(?m)^- \*\*(.+?)\*\*[^：:\n]{0,24}[：:]", body)


def canonical(field_label):
    return BASE_LABELS.get(normalise_label(field_label))


def split_cards(text):
    """number -> {"title", "body", "labels", "fields"} from one card file."""
    cards = {}
    parts = HEADING_RE.split(text)
    for index in range(1, len(parts), 3):
        number, title, body = parts[index], parts[index + 1], parts[index + 2]
        labels = collect_labels(body)
        fields = {}
        for label in labels:
            name = canonical(label)
            if name and name not in fields:
                fields[name] = label
        cards[int(number)] = {"title": title, "body": body,
                              "labels": labels, "fields": fields}
    return cards


def load_cards(root, files):
    cards, per_file = {}, {}
    for rel in files:
        text = (root / rel).read_text(encoding="utf-8")
        parsed = split_cards(text)
        per_file[rel] = sorted(parsed)
        for number, card in parsed.items():
            card["file"] = rel
            cards.setdefault(number, card)
    return cards, per_file


def tokens(value):
    """Distinctive identifiers in a manifest anchor: commit SHAs and version pins."""
    found = []
    for match in SHA_RE.findall(value.lower()):
        if len(match) >= 7 and any(ch.isdigit() for ch in match):
            found.append(match)
    for match in VERSION_RE.findall(value):
        if "." in match and len(match) >= 3:
            found.append(match)
    return sorted(set(found))


def sig_words(title):
    """Words distinctive enough to compare two titles."""
    raw = re.split(r"[^\w\u4e00-\u9fff]+", title)
    return [w for w in raw if len(w) >= 4]


def check(manifest, root):
    files = sorted({item["source"]["file"] for item in manifest["recipes"]})
    cards, per_file = load_cards(root, files)
    results = []

    def add(rule, verdict, detail):
        results.append({"rule": rule, "verdict": verdict, "detail": detail})

    # R1 -- every manifest row resolves to a card heading
    missing = []
    for item in manifest["recipes"]:
        number = item["source"]["card"]
        if number not in cards:
            missing.append("card %d" % number)
        elif cards[number]["file"] != item["source"]["file"]:
            missing.append("card %d is in %s, manifest says %s"
                           % (number, cards[number]["file"], item["source"]["file"]))
    add("R1_heading", "mismatch" if missing else "match",
        "; ".join(missing) if missing else "%d rows map to %d headings in %d files"
        % (len(manifest["recipes"]), len(cards), len(files)))

    # R2 -- titles agree on at least one distinctive token
    undecided, disagreed = [], []
    for item in manifest["recipes"]:
        card = cards.get(item["source"]["card"])
        if not card:
            continue
        mine, theirs = sig_words(item["title"]), sig_words(card["title"])
        if not mine or not theirs:
            undecided.append("card %d: title too short to compare" % item["source"]["card"])
        elif not set(w.lower() for w in mine) & set(w.lower() for w in theirs):
            disagreed.append("card %d: manifest=%r heading=%r"
                             % (item["source"]["card"], item["title"], card["title"][:40]))
    if disagreed:
        add("R2_title", "mismatch", "; ".join(disagreed))
    elif undecided:
        add("R2_title", "undecidable", "; ".join(undecided))
    else:
        add("R2_title", "match", "all %d titles share a distinctive token" % len(manifest["recipes"]))

    # R3 -- every pin in the manifest appears verbatim in the card
    absent, checked = [], 0
    for item in manifest["recipes"]:
        card = cards.get(item["source"]["card"])
        if not card:
            continue
        body = (card["title"] + "\n" + card["body"]).lower()
        for token in tokens(item["anchor_value"]):
            checked += 1
            if token not in body:
                absent.append("card %d: %r (from %r)"
                              % (item["source"]["card"], token, item["anchor_value"][:48]))
    if absent:
        add("R3_anchors", "mismatch", "; ".join(absent))
    elif checked == 0:
        add("R3_anchors", "undecidable", "no commit or version pins found in any anchor_value")
    else:
        add("R3_anchors", "match", "%d pins from anchor_value found verbatim in the cards" % checked)

    # R4 -- `draft_only` agrees with the card's own draft marker. Both directions
    # matter: a manifest that invents a run is as wrong as one that hides one.
    wrong, undecided = [], []
    for item in manifest["recipes"]:
        card = cards.get(item["source"]["card"])
        if not card:
            continue
        label = card["fields"].get("min_example")
        if label is None:
            undecided.append("card %d: no min_example label to compare against %r"
                             % (item["source"]["card"], item["min_example"]))
            continue
        card_draft = "草案" in label
        manifest_draft = item["min_example"] == "draft_only"
        if card_draft != manifest_draft:
            wrong.append("card %d: card label %r vs manifest %r"
                         % (item["source"]["card"], label, item["min_example"]))
    if wrong:
        add("R4_drafts", "mismatch", "; ".join(wrong))
    elif undecided:
        add("R4_drafts", "undecidable", "; ".join(undecided))
    else:
        add("R4_drafts", "match", "every draft_only row has a card-side draft label")

    # R5 -- the three boolean-flagged fields are physically present in the card
    gaps = []
    for item in manifest["recipes"]:
        card = cards.get(item["source"]["card"])
        if not card:
            continue
        wanted = []
        if item.get("failure_conditions"):
            wanted.append("failure_conditions")
        if item.get("feedback_branch"):
            wanted.append("feedback_branch")
        if item.get("ict_change"):
            wanted.append("ict_change")
        for name in wanted:
            if name not in card["fields"]:
                gaps.append("card %d: no label for %s" % (item["source"]["card"], name))
    add("R5_field_set", "mismatch" if gaps else "match",
        "; ".join(gaps) if gaps else "all flagged fields have a card-side label")

    # R6 -- card numbering is complete across the declared files
    declared = sorted(item["number"] for item in manifest["recipes"])
    found = sorted(cards)
    if declared != found:
        add("R6_numbering", "mismatch",
            "manifest numbers %s vs headings %s" % (declared, found))
    else:
        add("R6_numbering", "match", "numbers %s..%s present in both" % (declared[0], declared[-1]))

    failed = [item for item in results if item["verdict"] == "mismatch"]
    return (1 if failed else 0), results, cards


def render(code, results, cards):
    lines = ["%-16s %-12s %s" % (item["rule"], item["verdict"].upper(), item["detail"])
             for item in results]
    undecided = sum(1 for item in results if item["verdict"] == "undecidable")
    lines.append("")
    lines.append("%d rules, %d matched, %d mismatched, %d undecidable, %d cards parsed"
                 % (len(results),
                    sum(1 for i in results if i["verdict"] == "match"),
                    sum(1 for i in results if i["verdict"] == "mismatch"),
                    undecided, len(cards)))
    lines.append("EXIT %d (%s)" % (code, "TRANSCRIPT_MISMATCH" if code else "TRANSCRIPT_CONSISTENT"))
    return "\n".join(lines)


def passing_manifest():
    """A manifest that matches the fixture cards exactly."""
    return {"recipes": [
        {"number": 1, "title": "Alpha toolkit eval", "anchor_value": "alpha==1.2.3 / commit aaaaaaa1",
         "min_example": "draft_only", "ict_change": True, "failure_conditions": True,
         "feedback_branch": True, "source": {"file": "cards.md", "card": 1}},
        {"number": 2, "title": "Beta scheduler", "anchor_value": "commit bbbbbbb2",
         "min_example": "draft_only", "ict_change": True, "failure_conditions": True,
         "feedback_branch": True, "source": {"file": "cards.md", "card": 2}},
    ]}


CARDS_FIXTURE = """### 卡 1 · Alpha toolkit eval（固定提交 aaaaaaa1）

- **原入口**：`https://example.invalid/alpha`
- **固定版本/提交**：alpha==1.2.3，commit aaaaaaa1
- **数据与许可**：unknown
- **典型输入**：a
- **原产物（上游公布，非本项目）**：b
- **失败条件（g0）**：c
- **反馈分支**：d
- **ICT 改造点**：e
- **可重跑最小例（草案，未执行）**：
- **状态**：未实跑

### 卡 2 · Beta scheduler

- **原入口**：`https://example.invalid/beta`
- **固定版本/提交**：commit bbbbbbb2
- **数据与许可**：unknown
- **典型输入**：a
- **原基线**：b
- **失败条件/阻塞**：c
- **反馈分支**：d
- **ICT 改造点**：e
- **可重跑最小例（草案，未执行且未完整定义）**：
- **状态**：未执行
"""


def selftest():
    import tempfile
    results = []

    def check_rule(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "cards.md").write_text(CARDS_FIXTURE, encoding="utf-8")
        baseline = passing_manifest()

        # Baseline: a faithful manifest must come out clean. Without this a checker
        # that always fails would look rigorous.
        code, rules, cards = check(json.loads(json.dumps(baseline)), root)
        baseline_result = (code, rules)
        check_rule("S1 faithful transcription passes", code == 0,
                   render(code, rules, cards))

        def mutate(fn):
            import copy
            bad = copy.deepcopy(baseline)
            fn(bad["recipes"])
            return check(bad, root)

        def rule(tag, c, rs):
            return next(r for r in rs if r["rule"] == tag)

        code, rules, _ = mutate(lambda r: r[0].update({"source": {"file": "cards.md", "card": 9}}))
        check_rule("S2 a missing heading is a mismatch",
                   code == 1 and rule("R1_heading", code, rules)["verdict"] == "mismatch")

        code, rules, _ = mutate(lambda r: r[0].update({"title": "Totally unrelated name"}))
        check_rule("S3 an unrelated title is a mismatch",
                   code == 1 and rule("R2_title", code, rules)["verdict"] == "mismatch")

        code, rules, _ = mutate(lambda r: r[0].update({"anchor_value": "commit ccccccc3"}))
        check_rule("S4 a pin absent from the card is a mismatch",
                   code == 1 and rule("R3_anchors", code, rules)["verdict"] == "mismatch")

        code, rules, _ = mutate(lambda r: r[0].update({"min_example": "verified"}))
        check_rule("S5 claiming a run while the card says draft is a mismatch",
                   rule("R4_drafts", code, rules)["verdict"] == "mismatch")

        code, rules, _ = mutate(lambda r: r[0].update({"failure_conditions": False,
                                                      "ict_change": True}))
        # dropping a flag is not a gap; only an asserted-true field must exist
        check_rule("S6 a false flag does not demand a card label",
                   rule("R5_field_set", code, rules)["verdict"] == "match")

        code, rules, _ = check({"recipes": [
            {"number": 1, "title": "Alpha toolkit eval", "anchor_value": "commit aaaaaaa1",
             "min_example": "draft_only", "ict_change": True, "failure_conditions": True,
             "feedback_branch": True, "source": {"file": "cards.md", "card": 1}}]}, root)
        check_rule("S7 dropping a row is a numbering mismatch",
                   code == 1 and rule("R6_numbering", code, rules)["verdict"] == "mismatch")

        code, rules, _ = check({"recipes": [
            {"number": 1, "title": "Alpha toolkit eval", "anchor_value": "no pins here",
             "min_example": "draft_only", "ict_change": True, "failure_conditions": True,
             "feedback_branch": True, "source": {"file": "cards.md", "card": 1}}]}, root)
        check_rule("S8 an unpinnable anchor is undecidable, not a failure",
                   rule("R3_anchors", code, rules)["verdict"] == "undecidable")

        # determinism: the report quotes this output. Compare against the baseline
        # captured before the mutations, not against whatever ran last.
        code2, rules2, _ = check(json.loads(json.dumps(baseline)), root)
        check_rule("S9 two runs agree", baseline_result == (code2, rules2))

        # S10: the false failure that the first real run produced. Card 9 carries
        # `失败条件（g0）`, which exact-variant matching reported as a missing field.
        check_rule("S10 parenthetical qualifiers do not hide a field",
                   canonical("失败条件（g0）") == "failure_conditions"
                   and canonical("固定版本/提交（g0 manifest）") == "anchor"
                   and canonical("失败条件/阻塞") == "failure_conditions"
                   and canonical("可重跑最小例（草案，未执行且未完整定义）") == "min_example"
                   and canonical("原产物（上游公布，非本项目）") == "upstream_artifact",
                   "%r %r" % (canonical("失败条件（g0）"), canonical("固定版本/提交（g0 manifest）")))

    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        print("%-56s %s %s" % (name, "PASS" if ok else "FAIL", "" if ok else "| " + detail))
    print("")
    print("%d/%d checks passed" % (passed, len(results)))
    return 0 if passed == len(results) else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--manifest", default="docs/project/workbuddy/recipe-manifest-20261120.json")
    ap.add_argument("--root", default=".")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    root = Path(args.root)
    manifest_path = root / args.manifest
    if not manifest_path.exists():
        print("no manifest at %s" % manifest_path, file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    code, results, cards = check(manifest, root)
    if args.json:
        print(json.dumps({"exit_code": code, "results": results,
                          "cards_parsed": sorted(cards)}, indent=2, ensure_ascii=False))
    else:
        print(render(code, results, cards))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
