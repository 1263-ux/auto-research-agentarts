"""One read-only command that gathers what a three-hourly alignment round needs.

Every periodic round currently starts the same way: git status, git log, the
mtime of the protected files, the budget file, and then six gate scripts run one
at a time. That is seven or eight ad-hoc commands, each of which can be got subtly
wrong -- and one of them already was: taking a gate's exit code through a pipe
report returns the pipe's status, so a failing gate reads as success. This script
exists so the round starts from one table instead of from memory.

It is a *report*, not a gate. It prints each exit code verbatim and never collapses
them into a verdict. Collapsing is how a green summary ends up meaning less than
the reader thinks it means, which is the failure this project keeps recording.

A bare exit code is still ambiguous, and this project has now been bitten by that
three times. `rc=1` can mean "the gate judged the object a failure" or "the gate
raised before it judged anything". `rc=2` can be a designed `pending` verdict or
argparse refusing the flag. So each row also carries a `how` column saying which
of those happened: a printed `EXIT n (TOKEN)` line that agrees with the process
code, the same line disagreeing (`VERDICT-MISMATCH`), a `N/M checks passed`
self-test line, a traceback (`crashed`), an argparse rejection (`usage`), or
nothing at all (`silent` / `died`). Reading `rc` alone is what makes an unknown
look like a failure.

What it does not do
-------------------
No writes, no installs, no network, no research actions, no model calls. It does
not decide whether anything is authorised; the authorisation table lives in
docs/project/workbuddy/continuous-status.md and is written by hand on purpose.

Exit codes
  0  the report was produced (regardless of what the gates said)
  2  usage error, or not a repository root

The gates' own exit codes are in the table, and in --json under "gates".
"""

import argparse
import json
import re
from pathlib import Path
import subprocess
import sys
import time

GATES = (
    ("P2 recipe gate", "scripts/p2_recipe_check.py", []),
    ("recipe transcript", "scripts/recipe_transcript_check.py", []),
    ("blocker probe", "scripts/p2_blockers_check.py", []),
    ("W05 card", "scripts/w05_card_check.py",
     ["--card", "docs/project/workbuddy/w05-card-draft-20261120.md"]),
    ("G5 pin probe", "scripts/g5_pin_probe.py", []),
    ("portability selftest", "scripts/portability_scan.py", ["--selftest"]),
    ("blocker selftest", "scripts/p2_blockers_check.py", ["--selftest"]),
    ("pin probe selftest", "scripts/g5_pin_probe.py", ["--selftest"]),
)

# Files whose modification time tells us whether another session is writing.
PROTECTED = (
    "docs/project/current.md",
    "docs/project/latest-report.md",
    "docs/project/workbuddy/continuous-status.md",
)

BUDGET = ".agent/team-budget.json"


def _git(root, *args):
    out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


def repository_state(root):
    head = _git(root, "rev-parse", "--short", "HEAD")
    ahead = _git(root, "rev-list", "--count", "origin/main..HEAD")
    dirty = _git(root, "status", "--porcelain")
    return {
        "head": head,
        "ahead_of_origin": int(ahead) if ahead and ahead.isdigit() else None,
        "dirty": [line for line in (dirty or "").splitlines() if line.strip()],
    }


def newest_write(root, paths):
    """The most recently modified protected file, and how long ago."""
    latest = None
    for relative in paths:
        path = root / relative
        if not path.is_file():
            continue
        moment = path.stat().st_mtime
        if latest is None or moment > latest[0]:
            latest = (moment, relative)
    if latest is None:
        return None
    return {"file": latest[1],
            "minutes_ago": round((time.time() - latest[0]) / 60.0, 1)}


def budget_state(root):
    path = root / BUDGET
    if not path.is_file():
        return {"present": False}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        return {"present": True, "parse_error": type(error).__name__}
    return {"present": True,
            "limit": document.get("cumulative_additional_cash_limit"),
            "confirmed_cash_spent": document.get("confirmed_cash_spent"),
            "status": document.get("status")}


VERDICT_LINE = re.compile(r"^EXIT\s+(-?\d+)\s*(?:\(([^)]*)\))?\s*$")
CHECK_LINE = re.compile(r"^(\d+)/(\d+) checks passed\s*$")
TRACEBACK = "Traceback (most recent call last)"
# argparse's own words. Kept as a list because it has changed wording between
# Python versions and a missed phrase silently degrades `usage` to `died`.
USAGE_MARKERS = ("unrecognized arguments", "the following arguments are required",
                 "invalid choice", "unknown option", "no such option")


def _how(rc, out, err, stated, checks):
    """What does this exit code actually mean? Never 'pass' or 'fail'.

    The order matters. A traceback outranks everything: a gate that raised may
    still have printed a verdict line for an earlier stage, and that line is not
    a statement about the object under test. A usage rejection outranks the codes
    too, because argparse exits 2 and a gate that uses 2 for `pending` would
    otherwise be read as a verdict it never gave.
    """
    if TRACEBACK in err:
        return "crashed"
    if any(marker in err for marker in USAGE_MARKERS):
        return "usage"
    if stated is not None and checks is None:
        return "verdict" if stated == rc else "VERDICT-MISMATCH"
    if checks is not None:
        return "selftest"
    return "silent" if rc == 0 else "died"


def _record(name, script, rc, out, err, started):
    """Turn a finished (or abandoned) run into one row. Pure, so it can be tested."""
    lines = [line for line in out.splitlines() if line.strip()]
    errors = [line for line in err.splitlines()
              if line.strip() and not line.startswith("warning:")]
    stated = None
    stated_token = None
    checks = None
    for line in lines:
        stripped = line.strip()
        match = VERDICT_LINE.match(stripped)
        if match:
            stated, stated_token = int(match.group(1)), (match.group(2) or "").strip()
            continue
        match = CHECK_LINE.match(stripped)
        if match:
            checks = (int(match.group(1)), int(match.group(2)))
    # Prefer the line the gate itself calls its verdict. A git or pip warning on
    # stderr would otherwise become "the last line" and tell the reader nothing.
    summary = next((line for line in lines if VERDICT_LINE.match(line.strip())), None)
    if summary is None:
        summary = next((line for line in lines if CHECK_LINE.match(line.strip())), None)
    if summary is None:
        summary = lines[-1] if lines else (errors[-1] if errors else "")
    return {"name": name, "script": script, "exit_code": rc,
            "how": _how(rc, out, err, stated, checks),
            "stated_exit": stated, "verdict_token": stated_token,
            "checks": None if checks is None else "%d/%d" % checks,
            "last_line": summary, "seconds": round(time.time() - started, 1)}


def run_gate(root, name, script, args, python=None, timeout=300):
    """Run one gate and keep its own exit code.

    Deliberately no shell, no pipe: the whole point is that the code reported is
    the gate's, not some intermediary's.

    A timeout is reported as -9 rather than raised, because a hang is an outcome
    the reader needs to see, not a crash that erases the other rows.
    """
    python = python or sys.executable
    started = time.time()
    try:
        completed = subprocess.run([python, str(root / script), *args],
                                   capture_output=True, text=True, cwd=str(root), timeout=timeout)
        return _record(name, script, completed.returncode,
                       completed.stdout or "", completed.stderr or "", started)
    except subprocess.TimeoutExpired:
        return _record(name, script, -9, "", "timeout after %ss" % timeout, started)


def collect(root, python=None, gates=GATES):
    return {
        "repository": repository_state(root),
        "newest_write": newest_write(root, PROTECTED),
        "budget": budget_state(root),
        "gates": [run_gate(root, name, script, args, python) for name, script, args in gates],
    }


def render(report):
    repo = report["repository"]
    lines = ["REPOSITORY"]
    lines.append("  head            %s" % repo["head"])
    lines.append("  ahead of origin %s" % repo["ahead_of_origin"])
    lines.append("  dirty files     %d" % len(repo["dirty"]))
    for entry in repo["dirty"][:8]:
        lines.append("                  %s" % entry)

    write = report["newest_write"]
    lines.append("")
    lines.append("CONCURRENCY")
    if write:
        lines.append("  newest protected write  %s (%.1f min ago)" % (write["file"], write["minutes_ago"]))
        lines.append("  (small means another session may be writing; do not touch shared files)")
    else:
        lines.append("  no protected file found")

    budget = report["budget"]
    lines.append("")
    lines.append("BUDGET")
    if not budget.get("present"):
        lines.append("  team-budget.json missing")
    else:
        lines.append("  limit %s CNY / confirmed spent %s / status %s"
                     % (budget.get("limit"), budget.get("confirmed_cash_spent"), budget.get("status")))
        if budget.get("confirmed_cash_spent") is None:
            lines.append("  confirmed spent is null -> unknown, not zero")

    lines.append("")
    lines.append("GATES (rc verbatim; how says what that rc means; no pass/fail decision)")
    for gate in report["gates"]:
        lines.append("  rc=%-3s how=%-16s %-22s %s"
                     % (gate["exit_code"], gate.get("how", "?"), gate["name"],
                        gate["last_line"][:92]))
    broken = [gate["name"] for gate in report["gates"]
              if gate.get("how") in ("crashed", "usage", "died", "VERDICT-MISMATCH")]
    if broken:
        lines.append("  NOTE %d row(s) whose rc is not a verdict: %s"
                     % (len(broken), ", ".join(broken)))
        lines.append("       a non-verdict rc must not be quoted as 'the gate still says X'")
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
        (root / "keep.txt").write_text("x", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "x"], check=True)

        # A gate that fails must be reported as failing. This is the exact bug a
        # shell pipeline introduces, so it is the first thing pinned.
        (root / "bad_gate.py").write_text(
            "import sys\nprint('something went wrong')\nsys.exit(3)\n", encoding="utf-8")
        record = run_gate(root, "bad", "bad_gate.py", [])
        check("S1 a failing gate keeps its own exit code", record["exit_code"] == 3, str(record["exit_code"]))
        check("S1b the last line is kept for the reader", "went wrong" in record["last_line"])

        (root / "ok_gate.py").write_text("print('fine')\n", encoding="utf-8")
        check("S2 a passing gate reports 0", run_gate(root, "ok", "ok_gate.py", [])["exit_code"] == 0)

        # A missing script must not look like success.
        record = run_gate(root, "gone", "does_not_exist.py", [])
        check("S3 a missing gate is not reported as 0", record["exit_code"] != 0, str(record["exit_code"]))

        # A hang is neither success nor a gate failure, and must not crash the report.
        # Built from _record rather than by sleeping: subprocess.run with a very small
        # timeout can block inside communicate() on Windows after the kill, which is a
        # property of the harness, not of the gate. The contract to pin is the row.
        record = _record("slow", "slow_gate.py", -9, "", "timeout after 0.3s", time.time())
        check("S3b a timeout is reported as -9 with a reason",
              record["exit_code"] == -9 and "timeout" in record["last_line"], str(record))

        # Dirty detection sees an untracked file.
        (root / "new.txt").write_text("y", encoding="utf-8")
        state = repository_state(root)
        check("S4 an untracked file counts as dirty",
              any("new.txt" in line for line in state["dirty"]), str(state["dirty"]))
        check("S4b head is a short hash", bool(state["head"]) and len(state["head"]) <= 12, str(state["head"]))

        # Budget: null spent must stay null, never become 0.
        (root / ".agent").mkdir()
        (root / ".agent" / "team-budget.json").write_text(
            json.dumps({"cumulative_additional_cash_limit": 5, "confirmed_cash_spent": None,
                        "status": "reconcile_before_next_paid_call"}), encoding="utf-8")
        budget = budget_state(root)
        check("S5 null spend stays null", budget["confirmed_cash_spent"] is None, str(budget))
        text = render({"repository": state, "newest_write": None, "budget": budget, "gates": []})
        check("S5b the report says unknown rather than zero", "unknown, not zero" in text)

        # --- S6..S11: an exit code alone is ambiguous; `how` must disambiguate ---
        def row(rc, out="", err=""):
            return _record("g", "g.py", rc, out, err, time.time())

        record = row(1, "EXIT 1 (FAIL: R5_anchor)\n")
        check("S6 a stated verdict that agrees is 'verdict'", record["how"] == "verdict", record["how"])
        check("S6b the token is kept", record["verdict_token"] == "FAIL: R5_anchor", str(record["verdict_token"]))

        # The dangerous case: the gate says one thing and the process says another.
        record = row(0, "EXIT 1 (FAIL: R5_anchor)\n")
        check("S7 a verdict disagreeing with rc is flagged", record["how"] == "VERDICT-MISMATCH", record["how"])
        record = row(2, "EXIT 0 (PASS)\n")
        check("S7b mismatch is symmetric", record["how"] == "VERDICT-MISMATCH", record["how"])

        # A crash must never be readable as the gate's judgement. rc=1 either way.
        record = row(1, "", "Traceback (most recent call last):\n  ...\nModuleNotFoundError: x\n")
        check("S8 a traceback is 'crashed', not 'verdict'", record["how"] == "crashed", record["how"])
        record = row(1, "EXIT 1 (FAIL: R5_anchor)\n", "Traceback (most recent call last):\nKeyError: x\n")
        check("S8b a traceback outranks a printed verdict", record["how"] == "crashed", record["how"])

        # argparse exits 2; a gate may also use 2 for 'pending'. They differ.
        record = row(2, "", "usage: g.py [-h] [--card C]\ng.py: error: unrecognized arguments: --selftest\n")
        check("S9 argparse rejection is 'usage', not a verdict", record["how"] == "usage", record["how"])
        record = row(2, "EXIT 2 (DRAFT_OK_NEEDS_OWNER)\n")
        check("S9b a designed pending verdict still reads as 'verdict'", record["how"] == "verdict", record["how"])

        record = row(0, "13/13 checks passed\n")
        check("S10 a selftest fraction is 'selftest'", record["how"] == "selftest", record["how"])
        check("S10b the denominator is kept", record["checks"] == "13/13", str(record["checks"]))
        record = row(1, "10/13 checks passed\n")
        check("S10c a failing selftest keeps both numbers", record["checks"] == "10/13", str(record["checks"]))

        record = row(0, "")
        check("S11 silence with rc=0 is 'silent'", record["how"] == "silent", record["how"])
        record = row(4, "")
        check("S11b silence with rc!=0 is 'died'", record["how"] == "died", record["how"])

        # The note must fire for exactly the non-verdict rows, or the reader is
        # back to reading bare codes.
        rows = [row(1, "EXIT 1 (FAIL: R5_anchor)\n"), row(1, "", "Traceback (most recent call last):\n")]
        text = render({"repository": state, "newest_write": None, "budget": budget, "gates": rows})
        check("S12 the note names the row whose rc is not a verdict",
              "1 row(s)" in text and "Traceback" not in text.split("NOTE")[-1], text.split("NOTE")[-1][:80])
        rows_ok = [row(1, "EXIT 1 (FAIL: R5_anchor)\n")]
        text_ok = render({"repository": state, "newest_write": None, "budget": budget, "gates": rows_ok})
        check("S12b a well-formed verdict does not raise the note", "NOTE" not in text_ok)


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
    if not (root / ".git").exists():
        print("not a git repository: %s" % root, file=sys.stderr)
        return 2
    report = collect(root)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
