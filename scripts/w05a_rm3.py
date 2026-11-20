"""W05a: RM3 pseudo-relevance feedback for the frozen two-stage card (planning only).

Pure functions. No file, network, model or project-state access: this module
never reads a frozen packet. Every ranking it can produce comes from documents
handed to it in memory.

The A arm (single-pass BM25) is NOT re-implemented here with new constants.
`bm25_scores` takes the k1/b of the frozen protocol and the caller is expected
to prove equality with `relevance_retrieval_adapter.retrieve` on synthetic
input (scripts/w05a_selftest.py F1). Two implementations of one ranking is the
known hazard from `m1-preflight-20261119.md`; this module keeps the parameter
surface explicit so the drift is detectable instead of silent.

Scope discipline: W05's card freezes `fb_docs=20`, `fb_terms=10`,
`orig_weight=0.5`, `candidate_depth=100`, `top_k=20` and leaves the *selection
policy* unspecified. Two policies are implemented because the choice moves the
numbers (`combined_top_k` is the Indri/Lemur reading; `always_retain` keeps
every original query term). The card must name one before execution; see
docs/project/workbuddy/w05a-rm3-20261120.md.
"""
import math
import re

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

ORIGINAL_TERM_POLICIES = ("combined_top_k", "always_retain")

# Frozen by W05 card v0.1 F2. Kept here as data, and asserted equal to
# relevance_retrieval_adapter.COMPARISON by the selftest, so a change on either
# side fails loudly instead of silently diverging.
PROTOCOL = {
    "k1": 1.2,
    "b": 0.75,
    "top_k": 20,
    "candidate_depth": 100,
    "fb_docs": 20,
    "fb_terms": 10,
    "orig_weight": 0.5,
    "tokenizer": "ascii_alnum_lower_v1",
    "tie_break": "doc_id_ascending",
    "original_term_policy": "combined_top_k",
}


class ProtocolError(ValueError):
    """Raised when the feedback protocol is not internally coherent.

    Carries a stable code so the selftest can assert *which* rule fired
    instead of only that something failed.
    """

    def __init__(self, code, message):
        super().__init__(code + ": " + message)
        self.code = code


def tokens(text):
    """ascii_lower + [a-z0-9]+ runs, byte-for-byte the frozen tokenizer."""
    if type(text) is not str:
        raise ProtocolError("NOT_TEXT", "tokenizer input must be str")
    return TOKEN_PATTERN.findall(text.lower())


def _require(condition, code, message):
    if not condition:
        raise ProtocolError(code, message)


def check_protocol(params=None):
    """Validate the protocol before any scoring. Returns a normalised copy."""
    merged = dict(PROTOCOL)
    if params:
        unknown = set(params) - set(PROTOCOL)
        _require(not unknown, "UNKNOWN_FIELD", "unknown protocol fields: " + ", ".join(sorted(unknown)))
        merged.update(params)
    for key in ("top_k", "candidate_depth", "fb_docs", "fb_terms"):
        _require(type(merged[key]) is int, "NOT_INT", key + " must be int, not bool or float")
    _require(merged["top_k"] >= 1, "BAD_TOP_K", "top_k must be >= 1")
    _require(merged["candidate_depth"] >= 1, "BAD_DEPTH", "candidate_depth must be >= 1")
    _require(merged["fb_docs"] >= 1, "BAD_FB_DOCS", "fb_docs must be >= 1")
    _require(merged["fb_terms"] >= 1, "BAD_FB_TERMS", "fb_terms must be >= 1")
    # A "two-stage" arm whose candidate list is no deeper than its output has no
    # second stage to speak of; that is a protocol error, not a silent no-op.
    _require(merged["candidate_depth"] > merged["top_k"], "NOT_TWO_STAGE",
             "candidate_depth must exceed top_k, else the arm is single-pass")
    for key in ("k1", "b", "orig_weight"):
        _require(type(merged[key]) is float, "NOT_FLOAT", key + " must be float")
    _require(merged["k1"] > 0.0, "BAD_K1", "k1 must be > 0")
    _require(0.0 <= merged["b"] <= 1.0, "BAD_B", "b must be in [0,1]")
    _require(0.0 <= merged["orig_weight"] <= 1.0, "BAD_ORIG_WEIGHT", "orig_weight must be in [0,1]")
    _require(merged["tokenizer"] == "ascii_alnum_lower_v1", "BAD_TOKENIZER", "frozen tokenizer only")
    _require(merged["tie_break"] == "doc_id_ascending", "BAD_TIE_BREAK", "frozen tie-break only")
    _require(merged["original_term_policy"] in ORIGINAL_TERM_POLICIES, "BAD_POLICY",
             "original_term_policy must be one of " + ", ".join(ORIGINAL_TERM_POLICIES))
    return merged


def _check_docs(docs):
    _require(type(docs) is dict and docs, "BAD_DOCS", "docs must be a nonempty dict")
    for doc_id, row in docs.items():
        _require(type(doc_id) is str and doc_id, "BAD_DOC_ID", "doc ids must be nonempty str")
        _require(type(row) is dict and "text" in row, "BAD_DOC_ROW", "row needs a text field")
        _require(type(row["text"]) is str, "BAD_DOC_TEXT", "text must be str")
        _require(type(row.get("title", "")) is str, "BAD_DOC_TITLE", "title must be str")


def doc_terms(row):
    """Term frequency of one document, title and text concatenated with a space."""
    return _counter(tokens(row.get("title", "") + " " + row["text"]))


def _counter(values):
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def build_index(docs):
    """Postings, lengths, idf and average length, computed once per corpus.

    Same statistics as the frozen pair: df over the whole corpus, length = sum
    of term counts, average over all documents.
    """
    _check_docs(docs)
    postings = {}
    lengths = {}
    for doc_id in sorted(docs):
        terms = doc_terms(docs[doc_id])
        lengths[doc_id] = sum(terms.values())
        for term, count in terms.items():
            postings.setdefault(term, []).append((doc_id, count))
    n = len(docs)
    total = sum(lengths.values())
    _require(total > 0, "EMPTY_CORPUS", "corpus has no tokens")
    idfs = {term: math.log((n + 1) / (len(rows) + 1)) + 1 for term, rows in postings.items()}
    return {"postings": postings, "lengths": lengths, "idfs": idfs, "n": n, "avgdl": total / n}


def bm25_idf(index, term):
    """BM25 idf with the frozen (n - df + .5) smoothing, not the index idf."""
    rows = index["postings"].get(term, ())
    return math.log(1 + (index["n"] - len(rows) + .5) / (len(rows) + .5))


def bm25_scores(weights, index, k1=1.2, b=0.75, only_docs=None):
    """Weighted BM25. `weights` maps term -> query weight.

    With every weight equal this is exactly the frozen single-pass scorer, which
    is what makes the orig_weight=1.0 degenerate fixture a real equality test
    rather than a smoke test.
    """
    scores = {}
    for term in sorted(weights):
        weight = weights[term]
        if weight == 0.0:
            continue
        rows = index["postings"].get(term)
        if not rows:
            continue
        idf = bm25_idf(index, term)
        for doc_id, tf in rows:
            if only_docs is not None and doc_id not in only_docs:
                continue
            norm = tf + k1 * (1 - b + b * index["lengths"][doc_id] / index["avgdl"])
            scores[doc_id] = scores.get(doc_id, 0.0) + weight * idf * tf * (k1 + 1) / norm
    return scores


def rank(scores, top_k, exclude_doc_id=None):
    """Score-descending, doc-id-ascending tie-break, exclusion before cutoff."""
    ordered = sorted((doc for doc in scores if doc != exclude_doc_id),
                     key=lambda doc: (-scores[doc], doc))
    return ordered[:top_k]


def query_model(query):
    """P(w|Q) = tf(w,Q) / |Q|."""
    counts = _counter(tokens(query))
    total = sum(counts.values())
    _require(total > 0, "EMPTY_QUERY", "query has no tokens")
    return {term: counts[term] / total for term in sorted(counts)}


def feedback_model(docs, doc_ids):
    """P(w|R) = mean over feedback docs of tf(w,d)/|d|.

    Empty feedback set returns an empty model rather than raising: the caller
    falls back to the original query, which is the documented degenerate path.
    """
    model = {}
    if not doc_ids:
        return model
    for doc_id in doc_ids:
        terms = doc_terms(docs[doc_id])
        total = sum(terms.values())
        if not total:
            continue
        for term in sorted(terms):
            model[term] = model.get(term, 0.0) + terms[term] / total
    for term in model:
        model[term] = model[term] / len(doc_ids)
    return model


def expand(query, feedback_doc_ids, docs, index, params=None):
    """Combine P(w|Q) and P(w|R), then pick the terms that will be scored.

    Selection is the one thing W05's card does not freeze, so both readings are
    available and the choice is recorded in the diagnostics.
    """
    protocol = check_protocol(params)
    qmodel = query_model(query)
    fmodel = feedback_model(docs, feedback_doc_ids)
    weight = protocol["orig_weight"]
    vocabulary = sorted(set(qmodel) | set(fmodel))
    combined = {term: weight * qmodel.get(term, 0.0) + (1.0 - weight) * fmodel.get(term, 0.0)
                for term in vocabulary}
    ordered = sorted((term for term in vocabulary if combined[term] > 0.0),
                     key=lambda term: (-combined[term], term))
    selected = ordered[:protocol["fb_terms"]]
    policy = protocol["original_term_policy"]
    added_back = []
    if policy == "always_retain":
        for term in sorted(qmodel):
            if term not in selected:
                selected.append(term)
                added_back.append(term)
    diagnostics = {
        "original_term_policy": policy,
        "combined_vocabulary": len(ordered),
        "selected_terms": len(selected),
        "fb_terms_clamped": len(selected) < protocol["fb_terms"],
        "original_terms_total": len(qmodel),
        "original_terms_retained": sum(1 for term in qmodel if term in selected),
        "original_terms_dropped": sorted(term for term in qmodel if term not in selected),
        "original_terms_added_back": added_back,
        "original_terms_absent_from_index": sorted(term for term in qmodel if term not in index["postings"]),
        "feedback_vocabulary": len(fmodel),
    }
    return {"weights": {term: combined[term] for term in selected}, "diagnostics": diagnostics}


def two_stage_rank(query, docs, params=None, index=None, exclude_doc_id=None):
    """A arm-equivalent stage 1, RM3 expansion, then re-rank the candidates.

    Stage 2 scores only the depth-`candidate_depth` candidate list, as the card
    specifies, and returns at most `top_k`.
    """
    protocol = check_protocol(params)
    index = index if index is not None else build_index(docs)
    qmodel = query_model(query)
    stage1_scores = bm25_scores(qmodel, index, protocol["k1"], protocol["b"])
    stage1 = rank(stage1_scores, protocol["candidate_depth"], exclude_doc_id)
    diagnostics = {
        "original_term_policy": protocol["original_term_policy"],
        "candidate_depth_requested": protocol["candidate_depth"],
        "candidate_count": len(stage1),
        "candidate_shortfall": len(stage1) < protocol["candidate_depth"],
        "fb_docs_requested": protocol["fb_docs"],
        "feedback_doc_count": min(protocol["fb_docs"], len(stage1)),
        "feedback_clamped": len(stage1) < protocol["fb_docs"],
        "empty_feedback": not stage1,
    }
    if not stage1:
        diagnostics.update({"selected_terms": len(qmodel), "original_terms_dropped": [],
                            "original_terms_retained": len(qmodel)})
        return {"ranking": [], "stage1": [], "weights": {}, "diagnostics": diagnostics}
    feedback_ids = stage1[:protocol["fb_docs"]]
    expansion = expand(query, feedback_ids, docs, index, protocol)
    diagnostics.update(expansion["diagnostics"])
    weights = expansion["weights"]
    candidate_set = set(stage1)
    stage2_scores = bm25_scores(weights, index, protocol["k1"], protocol["b"], only_docs=candidate_set)
    ranking = rank(stage2_scores, protocol["top_k"], exclude_doc_id)
    return {"ranking": ranking, "stage1": stage1, "weights": weights, "diagnostics": diagnostics}


def single_pass_rank(query, docs, params=None, index=None, exclude_doc_id=None):
    """The A arm, expressed through this module so the fixtures share one path."""
    protocol = check_protocol(params)
    index = index if index is not None else build_index(docs)
    scores = bm25_scores(query_model(query), index, protocol["k1"], protocol["b"])
    return rank(scores, protocol["top_k"], exclude_doc_id)
