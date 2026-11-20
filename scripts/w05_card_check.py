"""Mechanical check for the W05 approval-card draft.

Reads the card's machine-readable block and the planning artifact, then applies
fourteen rules. It never imports `src.autoresearch`, never touches the network and
never writes into a frozen packet: the point is to make the card reviewable, not
to decide anything for the Owner.

Exit codes
  0  PASS                     every field frozen, card signed
  2  DRAFT_OK_NEEDS_OWNER     structure sound, at least one field open/blocked, undecided or unsigned
  1  FAIL                     a rule is violated; card must not reach execution

A rule reports one of three states rather than pass/fail, because "the Owner has
not chosen yet" and "the card says something wrong" are different problems: a
`pending` rule keeps the draft reviewable (exit 2), a `fail` stops it (exit 1).
R13/R14 use that split: an undecided expansion policy is pending, an unknown
policy or an arm that disagrees with scripts/w05a_rm3.PROTOCOL is a failure.

The numeric rule (R9) recomputes the expected values from the planning artifact
instead of trusting numbers typed into prose, so a stale figure fails the check.
R14 does the same for the arm: the card's numbers must equal the module's, which
is how the two cannot drift apart quietly.
"""
import argparse
import copy
import json
import re
import sys
from pathlib import Path

FIELDS = ("F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9")
STATUSES = {"frozen", "open", "blocked"}
DIRECTIONS = {"one_sided_greater", "one_sided_less", "two_sided"}
PLACEHOLDERS = ("TODO", "TBD", "待定", "待补")
BLOCK_START = "```w05card"
BLOCK_END = "```"
ORIGINAL_TERM_POLICIES = ("combined_top_k", "always_retain")
ARM_KEYS = ("k1", "b", "top_k", "candidate_depth", "fb_docs", "fb_terms", "orig_weight")


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def extract_block(text):
    """Return (dict, error). The block must exist exactly once and parse as JSON."""
    start = text.find(BLOCK_START)
    if start < 0:
        return None, "machine-readable block missing"
    body_start = text.find("\n", start)
    end = text.find(BLOCK_END, body_start)
    if body_start < 0 or end < 0:
        return None, "machine-readable block not terminated"
    body = text[body_start:end]
    if body.count(BLOCK_START) > 1:
        return None, "machine-readable block declared more than once"
    try:
        return json.loads(body), None
    except json.JSONDecodeError as exc:
        return None, "machine-readable block is not valid JSON: " + str(exc)


def expected_numbers(plan):
    """Derive every number the card is allowed to quote from the planning artifact."""
    continuous = plan["continuous_plans"]
    observed = plan["observed"]
    return {
        "mdes_mrr10_at_n24": continuous["mrr@10"]["mdes_at_observed_n"],
        "n_for_delta_010_mrr10": continuous["mrr@10"]["n_for_delta_0.10"],
        "n_for_delta_010_ndcg10": continuous["ndcg@10"]["n_for_delta_0.10"],
        "n_for_delta_010_recall20": continuous["recall@20"]["n_for_delta_0.10"],
        "tost_margin_005_mrr10": plan["tost"]["mrr@10"]["margin_0.05"],
        "recall20_ties": observed["recall@20"]["ties"],
        "recall20_movable": observed["recall@20"]["movable"],
    }


def check(text, plan):
    """Apply the rules. Returns (exit_code, results) with one dict per rule.

    Each result carries `state` in {pass, pending, fail}. `ok` is kept as the
    pass/fail projection so existing readers of check.json keep working.
    """
    results = []

    def record(rule, state, detail):
        results.append({"rule": rule, "ok": state == "pass", "state": state, "detail": detail})

    def add(rule, ok, detail):
        record(rule, "pass" if ok else "fail", detail)

    def pending(rule, detail):
        record(rule, "pending", detail)

    card, error = extract_block(text)
    add("R1_block", card is not None, error or "machine-readable block parsed")
    if card is None:
        return 1, results

    fields = card.get("fields") or {}
    missing = [name for name in FIELDS if name not in fields]
    add("R2_fields", not missing, "missing: " + ", ".join(missing) if missing else "F1-F9 all present")
    if missing:
        return 1, results

    bad_status = {name: fields[name].get("status") for name in FIELDS
                  if fields[name].get("status") not in STATUSES}
    add("R3_status", not bad_status, "invalid status: " + json.dumps(bad_status, ensure_ascii=False)
        if bad_status else "every status in {frozen, open, blocked}")

    no_stamp = [name for name in FIELDS
                if fields[name]["status"] == "frozen" and not str(fields[name].get("frozen_at") or "").strip()]
    add("R4_frozen_stamp", not no_stamp,
        "frozen without frozen_at: " + ", ".join(no_stamp) if no_stamp else "every frozen field carries a timestamp")

    no_reason = [name for name in FIELDS
                 if fields[name]["status"] in ("open", "blocked")
                 and len(str(fields[name].get("open_reason") or "").strip()) < 15]
    add("R5_open_reason", not no_reason,
        "open/blocked without a substantive reason: " + ", ".join(no_reason) if no_reason
        else "every open/blocked field explains why")

    fake_choice = [name for name in FIELDS
                   if fields[name]["status"] == "open" and len(fields[name].get("options") or []) < 2]
    add("R6_real_options", not fake_choice,
        "open field with fewer than two options: " + ", ".join(fake_choice) if fake_choice
        else "every open field offers a real choice")

    budget = fields["F6"]
    budget_ok = (isinstance(budget.get("actions_max"), int) and 0 <= budget["actions_max"] <= 2
                 and budget.get("model_requests") == 0 and budget.get("cash_cny") == 0
                 and budget.get("reopen_old") is False)
    add("R7_budget", budget_ok,
        "F6 actions_max=%r model=%r cash=%r reopen_old=%r" % (
            budget.get("actions_max"), budget.get("model_requests"),
            budget.get("cash_cny"), budget.get("reopen_old")))

    endpoint = fields["F3"]
    endpoint_ok = (endpoint.get("primary") == "mrr@10"
                   and endpoint.get("direction") in DIRECTIONS
                   and endpoint.get("alpha") == 0.05
                   and endpoint.get("tost_claimed") is False)
    add("R8_endpoint", endpoint_ok,
        "F3 primary=%r direction=%r alpha=%r tost_claimed=%r"
        % (endpoint.get("primary"), endpoint.get("direction"),
           endpoint.get("alpha"), endpoint.get("tost_claimed")))

    wanted = expected_numbers(plan)
    numeric = fields["F7"]
    diffs = []
    for key, want in wanted.items():
        got = numeric.get(key)
        if isinstance(want, float):
            if not isinstance(got, (int, float)) or abs(got - want) > 1e-6:
                diffs.append("%s got %r want %.12f" % (key, got, want))
        elif got != want:
            diffs.append("%s got %r want %r" % (key, got, want))
    add("R9_numbers", not diffs, "; ".join(diffs) if diffs else "F7 matches the planning artifact on 7 values")

    keys = fields["F8"]
    keys_ok = (keys.get("requires_partition") is True
               and "(id, kept_as)" in (keys.get("forbidden_keys") or []))
    add("R10_key_contract", keys_ok,
        "F8 requires_partition=%r forbidden=%r" % (keys.get("requires_partition"), keys.get("forbidden_keys")))

    signed = card.get("signature") is not None and str(card.get("signature")).strip() not in ("", "None")
    execution = card.get("execution")
    add("R11_unsigned_execution", execution == "not_authorized" or signed,
        "execution=%r signature=%r" % (execution, card.get("signature")))

    placeholders = []
    for name in FIELDS:
        blob = json.dumps(fields[name], ensure_ascii=False)
        if any(token in blob for token in PLACEHOLDERS):
            placeholders.append(name)
    add("R12_no_placeholder", not placeholders,
        "placeholder text in: " + ", ".join(placeholders) if placeholders else "no TODO/TBD markers")

    f2 = fields["F2"]
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import w05a_rm3
        protocol = w05a_rm3.PROTOCOL
    except Exception as exc:  # noqa: BLE001 - a missing module must fail the rule, not the run
        protocol = None
        add("R14_arm_matches_module", False, "cannot load w05a_rm3: " + str(exc))

    policy = f2.get("original_term_policy", "<missing>")
    if policy == "<missing>":
        add("R13_term_policy", False,
            "F2 does not encode original_term_policy; how the expanded term list is chosen is unstated")
    elif policy is None:
        pending("R13_term_policy",
                "F2 original_term_policy undecided; Owner picks " + " / ".join(ORIGINAL_TERM_POLICIES))
    elif policy not in ORIGINAL_TERM_POLICIES:
        add("R13_term_policy", False, "F2 original_term_policy=%r is outside the closed set" % (policy,))
    elif protocol is not None and policy != protocol["original_term_policy"]:
        # Deciding on paper is not enough: the module would still run its own
        # default, so the card and the code would disagree in silence.
        add("R13_term_policy", False,
            "F2 says %r but w05a_rm3.PROTOCOL says %r; align one of them"
            % (policy, protocol["original_term_policy"]))
    else:
        add("R13_term_policy", True, "F2 original_term_policy=%r matches the module" % (policy,))

    if protocol is not None:
        arm = f2.get("arm")
        if not isinstance(arm, dict):
            add("R14_arm_matches_module", False, "F2 does not encode machine-readable arm numbers")
        else:
            drift = []
            for key in ARM_KEYS:
                got, want = arm.get(key, "<missing>"), protocol[key]
                if isinstance(want, float):
                    numeric = isinstance(got, (int, float)) and not isinstance(got, bool)
                    if not numeric or abs(got - want) > 1e-12:
                        drift.append("%s card=%r module=%r" % (key, got, want))
                elif got != want:
                    drift.append("%s card=%r module=%r" % (key, got, want))
            add("R14_arm_matches_module", not drift,
                "; ".join(drift) if drift else "F2 arm equals w05a_rm3.PROTOCOL on 7 values")

    states = [item["state"] for item in results]
    if "fail" in states:
        return 1, results
    unresolved = [name for name in FIELDS if fields[name]["status"] != "frozen"]
    if "pending" in states or unresolved or not signed:
        return 2, results
    return 0, results


def render(results, code):
    lines = ["%-24s %-7s %s" % (item["rule"], item["state"].upper(), item["detail"])
             for item in results]
    lines.append("")
    lines.append("EXIT %d (%s)" % (code, {0: "PASS", 1: "FAIL", 2: "DRAFT_OK_NEEDS_OWNER"}[code]))
    return "\n".join(lines)


MUTATIONS = [
    ("baseline draft", lambda card: None, 2),
    ("drop field F5", lambda card: card["fields"].pop("F5"), 1),
    ("unknown status", lambda card: card["fields"]["F2"].__setitem__("status", "done"), 1),
    ("frozen without stamp", lambda card: card["fields"]["F2"].pop("frozen_at"), 1),
    ("open without reason", lambda card: card["fields"]["F1"].__setitem__("open_reason", "n/a"), 1),
    ("open with one option", lambda card: card["fields"]["F1"].__setitem__("options", ["O2"]), 1),
    ("budget over two actions", lambda card: card["fields"]["F6"].__setitem__("actions_max", 3), 1),
    ("budget with a model call", lambda card: card["fields"]["F6"].__setitem__("model_requests", 1), 1),
    ("budget reopening old runs", lambda card: card["fields"]["F6"].__setitem__("reopen_old", True), 1),
    ("endpoint without direction", lambda card: card["fields"]["F3"].pop("direction"), 1),
    ("endpoint with two-sided default", lambda card: card["fields"]["F3"].__setitem__("alpha", 0.05) or card["fields"]["F3"].__setitem__("direction", "we'll see"), 1),
    ("endpoint claiming TOST", lambda card: card["fields"]["F3"].__setitem__("tost_claimed", True), 1),
    ("stale MDES figure", lambda card: card["fields"]["F7"].__setitem__("mdes_mrr10_at_n24", 0.20), 1),
    ("stale query count", lambda card: card["fields"]["F7"].__setitem__("n_for_delta_010_mrr10", 100), 1),
    ("key contract drops (id, kept_as)", lambda card: card["fields"]["F8"].__setitem__("forbidden_keys", []), 1),
    ("partition no longer required", lambda card: card["fields"]["F8"].__setitem__("requires_partition", False), 1),
    ("execute while unsigned", lambda card: card.__setitem__("execution", "authorized"), 1),
    ("placeholder left in a field", lambda card: card["fields"]["F9"].__setitem__("value", "TODO"), 1),
    ("strip the expansion policy", lambda card: card["fields"]["F2"].pop("original_term_policy"), 1),
    ("policy outside the closed set", lambda card: card["fields"]["F2"].__setitem__(
        "original_term_policy", "keep_everything"), 1),
    ("policy disagrees with the module default", lambda card: card["fields"]["F2"].__setitem__(
        "original_term_policy", "always_retain"), 1),
    ("arm drift on fb_terms", lambda card: card["fields"]["F2"]["arm"].__setitem__("fb_terms", 5), 1),
    ("arm drift on k1", lambda card: card["fields"]["F2"]["arm"].__setitem__("k1", 1.5), 1),
    ("arm numbers absent", lambda card: card["fields"]["F2"].pop("arm"), 1),
    ("signed and frozen but policy undecided", lambda card: (
        card.__setitem__("signature", "selftest-owner"),
        card.__setitem__("execution", "authorized"),
        [card["fields"][name].__setitem__("status", "frozen") for name in ("F1", "F4")],
        [card["fields"][name].__setitem__("frozen_at", "2026-11-20T03:00+08:00") for name in ("F1", "F4")],
    ), 2),
    ("signed and fully frozen", lambda card: (
        card.__setitem__("signature", "selftest-owner"),
        card.__setitem__("execution", "authorized"),
        card["fields"]["F2"].__setitem__("original_term_policy", "combined_top_k"),
        [card["fields"][name].__setitem__("status", "frozen") for name in ("F1", "F4")],
        [card["fields"][name].__setitem__("frozen_at", "2026-11-20T03:00+08:00") for name in ("F1", "F4")],
    ), 0),
]


def splice(text, card):
    """Replace the machine-readable block in `text` with the mutated `card`."""
    start = text.find(BLOCK_START)
    body_start = text.find("\n", start)
    end = text.find(BLOCK_END, body_start)
    payload = "\n" + json.dumps(card, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return text[:body_start] + payload + text[end:]


def self_test(card_path, plan_path, out_dir):
    """Fault injection: every mutated card must return the expected exit code."""
    text = read_text(card_path)
    plan = json.loads(read_text(plan_path))
    original, error = extract_block(text)
    if original is None:
        return 1, [{"mutation": "load", "ok": False, "detail": error}]

    results = []
    for name, mutate, expected in MUTATIONS:
        card = copy.deepcopy(original)
        mutate(card)
        code, _ = check(splice(text, card), plan)
        results.append({"mutation": name, "ok": code == expected, "expected": expected, "got": code})

    scratch = Path(out_dir) / "selftest"
    scratch.mkdir(parents=True, exist_ok=True)
    first = render(check(text, plan)[1], check(text, plan)[0])
    second = render(check(text, plan)[1], check(text, plan)[0])
    results.append({"mutation": "determinism", "ok": first == second, "detail": "two runs byte-identical"})

    passed = sum(1 for item in results if item["ok"])
    (scratch / "results.json").write_bytes(
        json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8"))
    return (0 if passed == len(results) else 1), results


def main(argv):
    parser = argparse.ArgumentParser(description="Check the W05 card against its own machine-readable block.")
    parser.add_argument("--card", default="docs/project/workbuddy/w05-card-draft-20261120.md")
    parser.add_argument("--plan", default="runs/mdes-20261119/plan.json")
    parser.add_argument("--out", default="runs/w05-card-check-20261120")
    parser.add_argument("--json", action="store_true", help="emit machine-readable results")
    parser.add_argument("--self-test", action="store_true", help="fault injection over the eleven rules")
    args = parser.parse_args(argv)

    if args.self_test:
        code, results = self_test(args.card, args.plan, args.out)
        passed = sum(1 for item in results if item["ok"])
        if args.json:
            print(json.dumps({"self_test": results, "passed": passed, "total": len(results)},
                             ensure_ascii=False, indent=2, sort_keys=True))
        else:
            for item in results:
                print("%-38s %s" % (item["mutation"], "PASS" if item["ok"] else "FAIL"))
            print("\nSELF-TEST %d/%d" % (passed, len(results)))
        return 0 if code == 0 else 1

    plan = json.loads(read_text(args.plan))
    code, results = check(read_text(args.card), plan)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"exit_code": code, "card": args.card, "plan": args.plan, "results": results}
    (out_dir / "check.json").write_bytes(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8"))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render(results, code))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
