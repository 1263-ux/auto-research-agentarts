"""Self-test for scripts/w05a_rm3.py.

Synthetic fixtures only: nothing here reads a frozen packet, a run directory or
the corpus. The point is to make the RM3 module falsifiable *before* W05 is
authorised, so that approval can be followed by a single execution instead of a
debugging session.

Run with the project interpreter (needs `src` importable for the cross-check):

    .venv/Scripts/python.exe scripts/w05a_selftest.py

Exit 0 = every check passed, 1 = at least one failed, 2 = cross-check skipped
because `autoresearch` could not be imported.
"""
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import w05a_rm3 as rm3  # noqa: E402

RESULTS = []


def check(name, condition, detail=""):
    RESULTS.append((name, bool(condition), detail))
    print(("PASS " if condition else "FAIL ") + name + (("  | " + detail) if detail and not condition else ""))
    return bool(condition)


def expect_error(name, code, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except rm3.ProtocolError as error:
        return check(name, error.code == code, "got " + error.code + " want " + code)
    except Exception as error:  # noqa: BLE001 - a wrong exception type is a failure
        return check(name, False, type(error).__name__ + ": " + str(error))
    return check(name, False, "no error raised")


DOCS = {
    "d1": {"title": "Alpha Beta", "text": "gamma delta alpha"},
    "d2": {"title": "", "text": "alpha epsilon"},
    "d3": {"title": "", "text": "beta gamma zeta"},
    "d4": {"title": "", "text": "eta theta iota"},
    "d5": {"title": "", "text": "alpha beta beta"},
}

# Corpus built so that the feedback model is dominated by a term the query does
# not contain: the classic query-drift case, which must be visible, not silent.
DRIFT_DOCS = {
    "e1": {"title": "", "text": "alpha beta"},
    "e2": {"title": "", "text": "alpha" + " gamma" * 20},
    "e3": {"title": "", "text": "beta" + " gamma" * 20},
    "e4": {"title": "", "text": "alpha beta" + " gamma" * 20},
}

TIE_DOCS = {
    "b_second": {"title": "", "text": "kappa lambda"},
    "a_first": {"title": "", "text": "kappa lambda"},
    "c_third": {"title": "", "text": "kappa lambda"},
}


def adapter():
    sys.path.insert(0, str(HERE.parent / "src"))
    import autoresearch.relevance_retrieval_adapter as module  # noqa: PLC0415
    from autoresearch import retrieval_lexical as lexical  # noqa: PLC0415
    return module, lexical


def f1_protocol_and_cross_implementation():
    try:
        module, lexical = adapter()
    except Exception as error:  # noqa: BLE001
        print("SKIP F1 (autoresearch import failed: " + str(error) + ")")
        return None
    comparison = module.COMPARISON
    for key in ("k1", "b", "top_k", "tokenizer", "tie_break"):
        check("F1 protocol constant matches COMPARISON." + key,
              rm3.PROTOCOL[key] == comparison[key],
              repr(rm3.PROTOCOL[key]) + " != " + repr(comparison[key]))
    check("F1 tokenizer identical on awkward input",
          all(rm3.tokens(text) == lexical.tokens(text)
              for text in ("Alpha_Beta 42!", "FOO-bar", "ünïcode 42", "  ", "a1b2")),
          "tokenizer drift")

    index_adapter = lexical.build_index(DOCS)
    index_ours = rm3.build_index(DOCS)
    same = True
    detail = []
    for query in ("alpha", "alpha beta", "gamma zeta", "alpha alpha beta"):
        theirs = module.retrieve(query, index_adapter, "bm25", exclude_doc_id=None)
        ours = rm3.single_pass_rank(query, DOCS, index=index_ours)
        if theirs != ours:
            same = False
            detail.append(query + ": " + repr(theirs) + " vs " + repr(ours))
    check("F1 stage-1 ranking equals adapter.retrieve(bm25) on 4 synthetic queries",
          same, "; ".join(detail))

    excluded_theirs = module.retrieve("alpha", index_adapter, "bm25", exclude_doc_id="d1")
    excluded_ours = rm3.single_pass_rank("alpha", DOCS, index=index_ours, exclude_doc_id="d1")
    check("F1 exclusion identical to adapter", excluded_theirs == excluded_ours,
          repr(excluded_theirs) + " vs " + repr(excluded_ours))
    return True


def f2_orig_weight_one_is_the_single_pass_arm():
    plain = rm3.single_pass_rank("alpha beta", DOCS)
    stage = rm3.two_stage_rank("alpha beta", DOCS, {"orig_weight": 1.0})
    check("F2 orig_weight=1.0 reproduces the single-pass top-k exactly",
          stage["ranking"] == plain, repr(stage["ranking"]) + " vs " + repr(plain))
    check("F2 orig_weight=1.0 still ran the two stages",
          stage["diagnostics"]["candidate_count"] > len(stage["ranking"])
          or stage["diagnostics"]["candidate_count"] >= 4,
          str(stage["diagnostics"]["candidate_count"]))


def f3_empty_feedback():
    stage = rm3.two_stage_rank("zzz", DOCS)
    check("F3 no matching document yields an empty ranking, no exception", stage["ranking"] == [])
    check("F3 empty feedback flagged", stage["diagnostics"]["empty_feedback"] is True)
    check("F3 empty feedback keeps the query terms", stage["diagnostics"]["selected_terms"] == 1)


def f4_not_two_stage():
    expect_error("F4 candidate_depth == top_k is rejected", "NOT_TWO_STAGE",
                 rm3.two_stage_rank, "alpha", DOCS, {"candidate_depth": 20})
    expect_error("F4 candidate_depth < top_k is rejected", "NOT_TWO_STAGE",
                 rm3.two_stage_rank, "alpha", DOCS, {"candidate_depth": 5})


def f5_f6_clamping():
    stage = rm3.two_stage_rank("alpha", DOCS, {"fb_docs": 50})
    check("F5 fb_docs larger than the candidate list is clamped, not an error",
          stage["diagnostics"]["feedback_doc_count"] == stage["diagnostics"]["candidate_count"]
          and stage["diagnostics"]["feedback_clamped"] is True)
    wide = rm3.two_stage_rank("alpha beta", DOCS, {"fb_terms": 10 ** 4})
    check("F6 fb_terms beyond the vocabulary selects everything and says so",
          wide["diagnostics"]["selected_terms"] == wide["diagnostics"]["combined_vocabulary"]
          and wide["diagnostics"]["fb_terms_clamped"] is True)


def f7_determinism_and_tie_break():
    first = rm3.two_stage_rank("kappa", TIE_DOCS)
    second = rm3.two_stage_rank("kappa", TIE_DOCS)
    digest = lambda value: hashlib.sha256(  # noqa: E731
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    check("F7 two runs are byte-identical", digest(first) == digest(second))
    check("F7 equal scores break ties by document id ascending",
          first["stage1"] == ["a_first", "b_second", "c_third"], repr(first["stage1"]))
    check("F7 equal weights break ties by term ascending",
          [term for term, _ in sorted(rm3.expand("kappa lambda", ["a_first"], TIE_DOCS,
                                                rm3.build_index(TIE_DOCS))["weights"].items(),
                                      key=lambda pair: (-pair[1], pair[0]))]
          == ["kappa", "lambda"])


def f8_exclusion():
    docs = dict(DOCS)
    docs["q1"] = {"title": "", "text": "alpha beta gamma"}
    without = rm3.two_stage_rank("alpha", docs)
    stage = rm3.two_stage_rank("alpha", docs, exclude_doc_id="q1")
    check("F8 excluded id never enters the candidate list", "q1" not in stage["stage1"])
    check("F8 excluded id never enters the ranking", "q1" not in stage["ranking"])
    # candidate_count counts documents that scored, not documents that exist:
    # exclusion has to remove exactly one scored document, not perturb idf.
    check("F8 exclusion removes exactly one candidate and no statistic",
          stage["diagnostics"]["candidate_count"] == without["diagnostics"]["candidate_count"] - 1,
          str(stage["diagnostics"]["candidate_count"]) + " vs "
          + str(without["diagnostics"]["candidate_count"]))
    check("F8 index statistics still include the excluded document",
          "q1" in [doc for doc, _ in rm3.build_index(docs)["postings"]["alpha"]]
          and without["diagnostics"]["candidate_count"] == 4,
          "exclusion must not change df or avgdl")


def f9_policy_and_drift():
    combined = rm3.two_stage_rank("alpha beta", DRIFT_DOCS, {"fb_terms": 1})
    retained = rm3.two_stage_rank("alpha beta", DRIFT_DOCS,
                                  {"fb_terms": 1, "original_term_policy": "always_retain"})
    check("F9 combined_top_k can drop every original term (drift is visible)",
          combined["diagnostics"]["original_terms_dropped"] == ["alpha", "beta"],
          repr(combined["diagnostics"]["original_terms_dropped"]))
    check("F9 always_retain keeps every original term",
          retained["diagnostics"]["original_terms_retained"] == 2
          and retained["diagnostics"]["original_terms_added_back"] == ["alpha", "beta"],
          repr(retained["diagnostics"]))
    check("F9 the two policies are not interchangeable on this fixture",
          combined["weights"].keys() != retained["weights"].keys())
    plain = rm3.single_pass_rank("alpha beta", DRIFT_DOCS)
    check("F9 expansion actually changes the ranking on a drift-prone corpus",
          combined["ranking"] != plain, repr(combined["ranking"]) + " vs " + repr(plain))


def f10_no_side_effects():
    source = (HERE / "w05a_rm3.py").read_text(encoding="utf-8")
    forbidden = ["import os", "import io", "import json", "import socket", "import subprocess",
                 "import urllib", "import requests", "import pathlib", "from pathlib import Path",
                 "open(", "numpy", "input("]
    hits = [token for token in forbidden if token in source]
    check("F10 module has no file/network/model surface", not hits, ", ".join(hits))
    check("F10 module imports only math and re",
          sorted({line.split()[1] for line in source.splitlines()
                  if line.startswith("import ")}) == ["math", "re"])


def fault_injection():
    cases = [
        ("BAD_ORIG_WEIGHT", {"orig_weight": 1.5}),
        ("NOT_FLOAT", {"orig_weight": 1}),
        ("BAD_K1", {"k1": 0.0}),
        ("BAD_B", {"b": 1.5}),
        ("BAD_TOP_K", {"top_k": 0}),
        ("BAD_FB_TERMS", {"fb_terms": 0}),
        ("BAD_FB_DOCS", {"fb_docs": 0}),
        ("BAD_DEPTH", {"candidate_depth": 0}),
        ("NOT_INT", {"fb_docs": 2.0}),
        ("BAD_TOKENIZER", {"tokenizer": "whitespace"}),
        ("BAD_TIE_BREAK", {"tie_break": "score_desc"}),
        ("BAD_POLICY", {"original_term_policy": "bogus"}),
        ("UNKNOWN_FIELD", {"stopwords": []}),
    ]
    for code, override in cases:
        expect_error("inject " + code + " <- " + json.dumps(override, sort_keys=True),
                     code, rm3.two_stage_rank, "alpha", DOCS, override)
    expect_error("inject BAD_DOCS <- empty corpus dict", "BAD_DOCS", rm3.build_index, {})
    expect_error("inject BAD_DOC_ROW <- row without text", "BAD_DOC_ROW",
                 rm3.build_index, {"d1": {"title": "x"}})
    expect_error("inject BAD_DOC_TEXT <- non-str text", "BAD_DOC_TEXT",
                 rm3.build_index, {"d1": {"text": 3}})
    expect_error("inject EMPTY_CORPUS <- whitespace-only text", "EMPTY_CORPUS",
                 rm3.build_index, {"d1": {"text": "   "}})
    expect_error("inject EMPTY_QUERY <- punctuation-only query", "EMPTY_QUERY",
                 rm3.two_stage_rank, "!!!", DOCS)
    expect_error("inject NOT_TEXT <- non-str query tokenization", "NOT_TEXT", rm3.tokens, None)


def main():
    cross = f1_protocol_and_cross_implementation()
    f2_orig_weight_one_is_the_single_pass_arm()
    f3_empty_feedback()
    f4_not_two_stage()
    f5_f6_clamping()
    f7_determinism_and_tie_break()
    f8_exclusion()
    f9_policy_and_drift()
    f10_no_side_effects()
    fault_injection()

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    failed = [name for name, ok, _ in RESULTS if not ok]
    print("\n" + str(passed) + "/" + str(len(RESULTS)) + " checks passed")
    if failed:
        print("FAILED: " + "; ".join(failed))
        return 1
    if cross is None:
        print("NOTE: cross-implementation check skipped; rerun with the project .venv")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
