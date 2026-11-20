"""Decide which recipe blockers are still real, instead of re-reading them.

`p2_recipe_check.py` checks that a blocker list is *present*; `recipe_transcript_check.py`
checks that it is *faithfully transcribed*. Neither answers the question an Owner
actually has: of these 25 blockers, which ones still exist on this machine, which
ones are only blocked by data/licences/credentials that no local probe can settle,
and which ones are already untrue (that is, the card has gone stale).

That distinction matters because a blocker list is what makes the Owner reach for
a "install everything" decision. If half the entries describe an environment that
already changed, the list is not caution, it is noise.

What this script can and cannot do
----------------------------------
It can look for a module and report presence plus version. That settles the
"X not installed" family exactly.

It cannot settle anything that requires downloading data, reading a licence,
obtaining a credential, reaching an upstream repository, or judging whether some
future smoke run would pass. Those are reported as `undecidable` with a reason.
They are NOT counted as satisfied, and they are NOT counted as blocking evidence
either -- they are unknown, which is what they are.

The mapping from blocker text to probe is **hand-built** (it has to be: the text
is free prose, half English and half Chinese in the cards). So the report says how
many blockers the mapping covers. A blocker with no mapping is `unmapped`, which
fails the run -- silently dropping one would turn "I did not check this" into
"this is fine".

Rule set
  R1 contradiction   call_record "none" with an empty blocker list
  R2 contradiction   a draft-only minimal example with an empty blocker list
  R3 coverage        every blocker maps to a probe (else unmapped)
  R4 environment     a module probe decides confirmed / stale
  R5 unknown         external dependencies are undecidable with a stated reason
  R6 determinism     two runs produce identical output (checked in --selftest)

Exit codes
  0  every blocker mapped, none stale, none unmapped
  1  at least one blocker is stale (the card describes an environment that changed)
  2  at least one blocker is unmapped (coverage gap -- not a pass)
"""

import argparse
import importlib.util
import json
from pathlib import Path
import sys

# blocker text -> probe. Keys are (card number, exact blocker string) so that a
# card being reworded shows up as `unmapped` instead of silently matching some
# other rule.
MODULE_PROBES = {
    (2, "fairlearn/lightgbm dependencies"): ["fairlearn", "lightgbm"],
    (3, "asv not installed"): ["asv"],
    (4, "Elasticsearch service"): ["elasticsearch"],
    (4, "pytrec_eval"): ["pytrec_eval"],
    (5, "ortools not installed"): ["ortools"],
    (6, "openml package"): ["openml"],
    (10, "datasetsforecast and pandas versions"): ["datasetsforecast", "pandas"],
}

# A client library is a proxy for a service, not the service. Checking the port
# too keeps "Elasticsearch service" from being confirmed by a missing client
# alone (a client can be installed while nothing listens, and the reverse).
PORT_PROBES = {
    (4, "Elasticsearch service"): [9200, 9300],
}

# Blockers that no local probe can settle, with the reason kept explicit. The
# reason is the point: "unknown because it needs a licence" is a different fact
# from "unknown because I did not look".
UNDECIDABLE = {
    (1, "old venv feasibility"): "requires building an old environment to find out",
    (1, "fold-data hash and sample counts"): "requires the fold data itself",
    (2, "UCI data hash"): "requires the dataset download",
    (2, "rand_seed not pinned"): "upstream code fact, not an environment fact",
    (3, "numpy benchmark tree"): "refers to the asv benchmark tree, not to numpy",
    (3, "comparison commit"): "requires the upstream repository history",
    (4, "independent index (initialisation rebuilds it)"): "requires running the index build",
    (4, "SciFact licence"): "licence question",
    (5, "official page schedule values unknown"): "requires the upstream page; the fetch failed in W04 and was recorded, not retried",
    (6, "task list and split hash"): "requires the OpenML task listing",
    (6, "API key"): "credential",
    (6, "data licence unknown"): "licence question",
    (7, "paid OPENAI/TAVILY key"): "credential and cash",
    (7, "network access"): "depends on what the recipe needs, not on having a link",
    (7, "release not pinned"): "requires the upstream release list",
    (8, "LLM tokens"): "credential and cash",
    (8, "example manuscript availability"): "requires the example artefact",
    (9, "runtime smoke"): "restates 'not executed'; it is the absence of a run, not a cause",
    (9, "model credentials"): "credential",
    (9, "YAML entry and stage artefacts unknown"): "requires the stage artefacts",
    (10, "M4 data and submission-118.zip"): "requires the data download",
    (10, "data licence"): "licence question",
}


def probe_modules(names):
    """Present/absent per module, with the version when it imports."""
    found = {}
    for name in names:
        try:
            spec = importlib.util.find_spec(name)
        except Exception as error:                       # pragma: no cover - defensive
            found[name] = {"state": "error", "detail": repr(error)}
            continue
        if spec is None:
            found[name] = {"state": "absent", "detail": None}
            continue
        version = None
        try:
            module = __import__(name)
            version = getattr(module, "__version__", None)
        except Exception as error:
            found[name] = {"state": "present", "detail": "import failed: %s" % type(error).__name__}
            continue
        found[name] = {"state": "present", "detail": version}
    return found


def probe_ports(ports):
    """Whether anything is listening on each port, checked locally only."""
    import socket
    found = {}
    for port in ports:
        sock = socket.socket()
        sock.settimeout(0.5)
        try:
            sock.connect(("127.0.0.1", port))
            found[port] = {"state": "open", "detail": None}
        except Exception as error:
            found[port] = {"state": "closed", "detail": type(error).__name__}
        finally:
            sock.close()
    return found


def classify(manifest, port_probe=None):
    """Return (verdicts, summary, contradictions). One verdict per blocker, never fewer."""
    port_probe = port_probe or probe_ports
    verdicts = []
    summary = {"confirmed": 0, "stale": 0, "undecidable": 0, "unmapped": 0}
    contradictions = []

    for card in manifest["recipes"]:
        number = card["number"]
        blockers = card.get("blockers") or []

        # R1 / R2: two states that cannot both be true.
        declared = (card.get("call_record") or {}).get("declared")
        if not blockers and declared == "none":
            contradictions.append(
                "card %d: no call record and no blockers -- nothing stopped a run" % number)
        if not blockers and card.get("min_example") == "draft_only":
            contradictions.append(
                "card %d: draft-only minimal example with no blockers" % number)

        for text in blockers:
            key = (number, text)
            record = {"card": number, "blocker": text}
            if key in MODULE_PROBES:
                found = probe_modules(MODULE_PROBES[key])
                missing = [n for n, v in found.items() if v["state"] == "absent"]
                # "stale" only when EVERY module the blocker names is present:
                # one missing dependency still blocks, whatever the others say.
                state = "confirmed" if missing else "stale"
                record.update({"verdict": state, "kind": "module",
                               "detail": found,
                               "note": ("missing: " + ", ".join(missing)) if missing
                                       else "every named module is installed"})
                if key in PORT_PROBES:
                    ports = port_probe(PORT_PROBES[key])
                    shut = [str(p) for p, v in ports.items() if v["state"] != "open"]
                    record["detail"] = dict(found, **{"port:%d" % p: v for p, v in ports.items()})
                    record["kind"] = "module+port"
                    if shut and state == "stale":
                        state = "confirmed"
                    record["verdict"] = state
                    record["note"] = ("nothing listening on " + ", ".join(shut)) if shut \
                                     else "client installed and service answering"
            elif key in UNDECIDABLE:
                record.update({"verdict": "undecidable", "kind": "external",
                               "detail": UNDECIDABLE[key]})
            else:
                record.update({"verdict": "unmapped", "kind": "none",
                               "detail": "no probe built for this wording"})
            summary[record["verdict"]] += 1
            verdicts.append(record)

    return verdicts, summary, contradictions


def exit_code(summary, contradictions):
    if contradictions:
        return 1
    if summary["unmapped"]:
        return 2
    if summary["stale"]:
        return 1
    return 0


def render(code, verdicts, summary, contradictions):
    lines = []
    for record in verdicts:
        detail = record["detail"]
        if isinstance(detail, dict):
            detail = " ".join("%s=%s" % (n, v["state"]) for n, v in detail.items())
        lines.append("card %-2d %-10s %-52s %s"
                     % (record["card"], record["verdict"], record["blocker"][:52], detail or ""))
    lines.append("")
    lines.append("%d blockers: %d confirmed, %d stale, %d undecidable, %d unmapped"
                 % (len(verdicts), summary["confirmed"], summary["stale"],
                    summary["undecidable"], summary["unmapped"]))
    if contradictions:
        lines.append("")
        lines.append("CONTRADICTIONS")
        for item in contradictions:
            lines.append("  " + item)
    labels = {0: "MAPPING_COMPLETE",
              1: "STALE_OR_CONTRADICTION",
              2: "MAPPING_INCOMPLETE"}
    lines.append("EXIT %d (%s)" % (code, labels[code]))
    if code == 0 and summary["undecidable"]:
        lines.append("NOTE: %d of %d blockers are still undecidable. Exit 0 means the mapping "
                     "is complete, NOT that these recipes can run."
                     % (summary["undecidable"], len(verdicts)))
    return "\n".join(lines)


def selftest():
    results = []

    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    def card(number, blockers, declared="none", min_example="draft_only"):
        return {"number": number, "blockers": blockers,
                "call_record": {"declared": declared}, "min_example": min_example}

    # S1: a mapped module blocker that is absent -> confirmed
    verdicts, summary, _ = classify({"recipes": [card(5, ["ortools not installed"])]})
    check("S1 absent module confirms the blocker",
          verdicts[0]["verdict"] == "confirmed", str(verdicts[0]))

    # S2: a mapped blocker naming several modules stays confirmed while one is missing
    verdicts, _, _ = classify({"recipes": [card(2, ["fairlearn/lightgbm dependencies"])]})
    check("S2 one missing module out of two still confirms",
          verdicts[0]["verdict"] == "confirmed", str(verdicts[0]))

    # S3: an unknown wording is unmapped, not passed
    verdicts, summary, _ = classify({"recipes": [card(1, ["something nobody mapped"])]})
    check("S3 unknown wording is unmapped", verdicts[0]["verdict"] == "unmapped")
    check("S3b unmapped exits 2", exit_code(summary, []) == 2)

    # S4: a blocker with no probe and no reason must not be counted as settled
    verdicts, summary, _ = classify({"recipes": [card(1, ["fold-data hash and sample counts"])]})
    check("S4 external blocker is undecidable, never confirmed",
          verdicts[0]["verdict"] == "undecidable")

    # S5 / S6: the two contradictions
    _, summary, contradictions = classify({"recipes": [card(1, [])]})
    check("S5 no blockers with no call record is a contradiction", len(contradictions) == 2)

    # S7: a run with nothing wrong exits 0
    verdicts, summary, contradictions = classify(
        {"recipes": [card(5, ["ortools not installed"], declared="none")]})
    check("S7 everything settled exits 0", exit_code(summary, contradictions) == 0)

    # S8: determinism, because the report quotes these numbers
    first = classify({"recipes": [card(5, ["ortools not installed"]),
                                  card(10, ["datasetsforecast and pandas versions"])]})
    second = classify({"recipes": [card(5, ["ortools not installed"]),
                                   card(10, ["datasetsforecast and pandas versions"])]})
    check("S8 two runs agree", first == second)

    # S9: the service blocker is probed on the port too, not just the client
    verdicts, _, _ = classify({"recipes": [card(4, ["Elasticsearch service"])]},
                              port_probe=lambda ports: {p: {"state": "open", "detail": None} for p in ports})
    check("S9 service blocker records port state",
          any(str(k).startswith("port:") for k in verdicts[0]["detail"]), str(verdicts[0]["detail"]))
    check("S9b a listening port never weakens a missing-client verdict",
          verdicts[0]["verdict"] == "confirmed", str(verdicts[0]["verdict"]))

    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        print("%-58s %s %s" % (name, "PASS" if ok else "FAIL", "" if ok else "| " + detail))
    print("")
    print("%d/%d checks passed" % (passed, len(results)))
    return 0 if passed == len(results) else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--manifest", default="docs/project/workbuddy/recipe-manifest-20261120.json")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    path = Path(args.manifest)
    if not path.is_file():
        print("no manifest at %s" % path, file=sys.stderr)
        return 2
    manifest = json.loads(path.read_text(encoding="utf-8"))
    verdicts, summary, contradictions = classify(manifest)
    code = exit_code(summary, contradictions)
    if args.json:
        print(json.dumps({"exit_code": code, "summary": summary,
                          "contradictions": contradictions, "verdicts": verdicts},
                         indent=2, ensure_ascii=False))
    else:
        print(render(code, verdicts, summary, contradictions))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
