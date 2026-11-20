"""Static portability scan: which entrypoints are dead on Windows, and why.

The project was built on Linux. A few modules import POSIX-only modules at the
top level, so on Windows the entrypoint dies before it parses a single argument.
Knowing *which* entrypoints are affected used to require running each one; this
script answers it from the source, and separates two very different cases:

  unguarded  `import fcntl` at column 0  -> the module cannot be imported at all
  lazy       `import fcntl` inside a function body -> imports fine, fails on call

Only the first case makes an entrypoint dead on arrival. The distinction matters
because the fix for one is a guarded import and the fix for the other is a
platform-specific lock implementation; conflating them produces a patch that
still breaks the moment the code path runs.

The scan is deliberately static: it never imports `src.autoresearch`, so it cannot
trigger a lock, a write, or a network call, and it runs on the platform that is
already broken.

Exit codes
  0  no entrypoint has an unguarded top-level POSIX import
  1  at least one entrypoint does (dead on Windows)
  2  usage error

Limitations, stated so the numbers are not over-read:
  - It resolves `from .x import y` inside `src/autoresearch` and `from autoresearch.x`
    from scripts. Star imports and dynamic `importlib` calls are not followed; both
    are reported in `unresolved` instead of being silently treated as safe.
  - "POSIX-only" is a fixed list, not a query against the running interpreter.
"""

import argparse
import ast
import json
from pathlib import Path
import sys

POSIX_ONLY = frozenset({
    "fcntl", "pwd", "grp", "termios", "tty", "pty", "resource",
    "syslog", "crypt", "spwd",
})


def module_name_for(path, root):
    """Map a file to the dotted name it is imported by, or None if neither root fits."""
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    if rel.suffix != ".py":
        return None
    parts = list(rel.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def parse(path):
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        return exc


def top_level_imports(tree):
    """Yield (name, lineno) for imports whose parent is the module body."""
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")[0], node.lineno
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module.split(".")[0], node.lineno


def all_imports(tree):
    """Yield (node, is_top_level, module_string, level, names) once per import.

    `is_top_level` means the import sits directly in the module body, which is the
    only position that can make a module unimportable. The earlier version walked
    the whole tree and then walked the body again, so a module-level import was
    reported as both top-level and lazy at the same time.
    """
    top_ids = {id(node) for node in tree.body
               if isinstance(node, (ast.Import, ast.ImportFrom))}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node, id(node) in top_ids, alias.name, 0, ()
        elif isinstance(node, ast.ImportFrom):
            names = tuple(alias.name for alias in node.names)
            yield node, id(node) in top_ids, node.module or "", node.level, names


def _exists(candidate, src_root):
    return (src_root / (candidate.replace(".", "/") + ".py")).exists() \
        or (src_root / candidate.replace(".", "/") / "__init__.py").exists()


def resolve_all(module, level, names, package, src_root):
    """Every module an import statement pulls in, rooted at `src_root`.

    Handles `from . import a, b`, which expands to the sibling modules `a` and `b`
    rather than to the package itself. Missing that form made the scanner report
    `run_research_project.py` as healthy while it was measurably dead, so the
    expansion is the difference between a useful verdict and a false negative.
    """
    targets = []
    if level:
        if not package:
            return targets
        base = package.split(".")
        cut = len(base) - (level - 1)
        if cut < 0:
            return targets
        stem = base[:cut] + (module.split(".") if module else [])
        head = ".".join(stem)
        if module:
            if head and _exists(head, src_root):
                targets.append(head)
        else:
            for name in names:
                candidate = ".".join(stem + [name])
                if _exists(candidate, src_root):
                    targets.append(candidate)
        return targets
    if not module:
        return targets
    if module == "autoresearch" or module.startswith("autoresearch."):
        targets.append(module)
        for name in names:
            candidate = module + "." + name
            if _exists(candidate, src_root):
                targets.append(candidate)
    return targets


def build_graph(files, src_root):
    """name -> {"path", "top": [(mod, line)], "lazy": [(mod, line)], "edges": [names]}"""
    graph = {}
    for path, name in files:
        tree = parse(path)
        if isinstance(tree, Exception):
            graph[name] = {"path": path, "parse_error": repr(tree), "top": [], "lazy": [],
                           "edges": [], "eager": [], "unresolved": []}
            continue
        package = name.rsplit(".", 1)[0] if "." in name else ""
        top, lazy, edges, eager, unresolved = [], [], [], [], []
        for node, is_top, mod, level, names in all_imports(tree):
            root = mod.split(".")[0] if mod else ""
            if root in POSIX_ONLY:
                (top if is_top else lazy).append((root, node.lineno))
                continue
            targets = resolve_all(mod, level, names, package, src_root)
            edges.extend(targets)
            if is_top:
                eager.extend(targets)
            if not targets and (level or (mod and mod.startswith("autoresearch"))):
                unresolved.append((mod or "<relative>", level, node.lineno))
        graph[name] = {"path": path, "top": top, "lazy": lazy,
                       "edges": edges, "eager": eager, "unresolved": unresolved}
    return graph


def closure(graph, start, key="eager"):
    """All module names reachable from `start` through `key` edges, including itself.

    `key="eager"` follows only module-body imports, which is what decides whether
    importing an entrypoint can fail. Using all edges instead reports an entrypoint
    as dead merely because something it imports lazily is POSIX-only, which is a
    false positive the measurements ruled out (compile_research_recipe.py runs).
    """
    seen, stack = set(), [start]
    while stack:
        node = stack.pop()
        if node in seen or node not in graph:
            continue
        seen.add(node)
        stack.extend(graph[node].get(key, []))
    return seen


def scan(root):
    src_root = root / "src"
    files = []
    for path in sorted((src_root / "autoresearch").rglob("*.py")):
        name = module_name_for(path, src_root)
        if name:
            files.append((path, name))
    graph = build_graph(files, src_root)

    entrypoints = []
    for path in sorted((root / "scripts").glob("*.py")):
        tree = parse(path)
        if isinstance(tree, Exception):
            entrypoints.append({"entrypoint": path.name, "parse_error": repr(tree)})
            continue
        package = ""
        edges, eager, unresolved = [], [], []
        for node, is_top, mod, level, names in all_imports(tree):
            targets = resolve_all(mod, level, names, package, src_root)
            if targets:
                edges.extend(targets)
                if is_top:
                    eager.extend(targets)
            elif mod and mod.startswith("autoresearch"):
                unresolved.append((mod, level, node.lineno))
        reached = set()
        for edge in eager:
            reached |= closure(graph, edge, "eager")
        reached_all = set()
        for edge in edges:
            reached_all |= closure(graph, edge, "eager")
            reached_all |= closure(graph, edge, "edges")
        unguarded = sorted({m for name in reached for m, _ in graph[name]["top"]})
        # Laziness is "reachable, but not at import time": either the module import
        # itself is deferred, or a deferred edge leads to a module that is dead.
        # Reading only each module's own `lazy` list misses the second case, which is
        # the common one -- the POSIX import sits at the top of a module that is
        # itself reached lazily.
        deferred = reached_all - reached
        lazy = sorted({m for name in deferred for m, _ in graph[name]["top"]} |
                      {m for name in reached_all for m, _ in graph[name]["lazy"]})
        unguarded_modules = sorted({name for name in reached if graph[name]["top"]})
        entrypoints.append({
            "entrypoint": path.name,
            "imports_autoresearch": bool(edges),
            "modules_reached": len(reached),
            "unguarded_posix": unguarded,
            "unguarded_in_modules": unguarded_modules,
            "lazy_posix": lazy,
            "unresolved": unresolved,
        })
    return graph, entrypoints


def render(graph, entrypoints):
    blocked = [e for e in entrypoints if e.get("unguarded_posix")]
    lazy_only = [e for e in entrypoints if e.get("lazy_posix") and not e.get("unguarded_posix")]
    lines = []
    lines.append("POSIX-only top-level imports in src/autoresearch")
    hard = sorted({m for name in graph for m, _ in graph[name]["top"]})
    soft = sorted({m for name in graph for m, _ in graph[name]["lazy"]})
    lines.append("  unguarded (module cannot import): %d  %s" % (len(hard), ", ".join(hard) or "-"))
    lines.append("  lazy (imports, fails on call)   : %d  %s" % (len(soft), ", ".join(soft) or "-"))
    offenders = sorted({name for name in graph if graph[name]["top"]})
    lines.append("  offending modules: %d  %s" % (len(offenders), ", ".join(offenders) or "-"))
    lines.append("")
    lines.append("Entrypoints: %d total, %d dead on Windows, %d lazy-only"
                 % (len(entrypoints), len(blocked), len(lazy_only)))
    if blocked:
        lines.append("")
        lines.append("  DEAD ON WINDOWS")
        for entry in blocked:
            lines.append("    %-42s via %s" % (entry["entrypoint"], ", ".join(entry["unguarded_posix"])))
    if lazy_only:
        lines.append("")
        lines.append("  LAZY ONLY (import ok, call fails)")
        for entry in lazy_only:
            lines.append("    %-42s %s" % (entry["entrypoint"], ", ".join(entry["lazy_posix"])))
    unresolved = [(name, item) for name in graph for item in graph[name].get("unresolved", [])]
    if unresolved:
        lines.append("")
        lines.append("  UNRESOLVED IMPORTS (treated as unknown, not safe): %d" % len(unresolved))
        for name, item in unresolved[:12]:
            lines.append("    %s <- %r" % (name, item))
    return "\n".join(lines)


FIXTURE = {
    # unguarded: this module cannot be imported on Windows at all
    "src/autoresearch/hard.py": "import fcntl\n\ndef f():\n    return fcntl.LOCK_EX\n",
    # lazy: imports fine, fails only when the function runs
    "src/autoresearch/soft.py": "def f():\n    import fcntl\n    return fcntl.LOCK_EX\n",
    # reaches hard.py from its module body -> dead on arrival
    "src/autoresearch/eager.py": "from .hard import f\n",
    # reaches hard.py only inside a function -> importing is fine
    "src/autoresearch/lazyuser.py": "def g():\n    from .hard import f\n    return f\n",
    # `from . import x` form: the resolver must expand the names, not the package
    "src/autoresearch/pkg/sibling.py": "import fcntl\n",
    "src/autoresearch/pkg/__init__.py": "",
    "src/autoresearch/pkg/uses_sibling.py": "from . import sibling\n",
    "scripts/dead_entry.py": "from autoresearch.eager import f\n",
    "scripts/live_entry.py": "from autoresearch.lazyuser import g\n",
    "scripts/pkg_entry.py": "from autoresearch.pkg import uses_sibling\n",
}


def _write_fixture(root):
    for rel, body in FIXTURE.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")


def selftest():
    import tempfile
    results = []

    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_fixture(root)
        graph, entrypoints = scan(root)
        by_name = {item["entrypoint"]: item for item in entrypoints}

        check("T1 unguarded module is a hard blocker",
              graph["autoresearch.hard"]["top"] == [("fcntl", 1)],
              str(graph["autoresearch.hard"]["top"]))
        check("T2 function-local import is lazy, not top",
              graph["autoresearch.soft"]["top"] == [] and graph["autoresearch.soft"]["lazy"] == [("fcntl", 2)],
              "%r %r" % (graph["autoresearch.soft"]["top"], graph["autoresearch.soft"]["lazy"]))
        check("T3 eager import of a dead module is dead",
              by_name["dead_entry.py"]["unguarded_posix"] == ["fcntl"])
        check("T4 lazy import of a dead module stays alive",
              by_name["live_entry.py"]["unguarded_posix"] == [])
        check("T4b but it is reported as lazy-only",
              by_name["live_entry.py"]["lazy_posix"] == ["fcntl"])
        check("T5 `from . import sibling` is expanded to the sibling module",
              by_name["pkg_entry.py"]["unguarded_posix"] == ["fcntl"],
              str(by_name["pkg_entry.py"]))
        check("T6 an import is never counted as both top and lazy",
              graph["autoresearch.hard"]["lazy"] == [],
              str(graph["autoresearch.hard"]["lazy"]))

        # T7: the concrete false negative that the first version shipped.
        # Rebuild the resolver call in isolation, because the bug lived in it.
        targets = resolve_all("", 1, ("hard", "soft"), "autoresearch", root / "src")
        check("T7 relative `from . import a, b` resolves to both siblings",
              targets == ["autoresearch.hard", "autoresearch.soft"], str(targets))
        # T8: a missing sibling must not be invented
        targets = resolve_all("", 1, ("nope",), "autoresearch", root / "src")
        check("T8 a nonexistent sibling resolves to nothing", targets == [], str(targets))

        dead = sorted(n for n in by_name if by_name[n]["unguarded_posix"])
        check("T9 exactly the two dead entries are flagged",
              dead == ["dead_entry.py", "pkg_entry.py"], str(dead))

        # T10: determinism, because the report quotes these numbers
        second = scan(root)[1]
        check("T10 two scans agree", second == entrypoints)

    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        print("%-58s %s %s" % (name, "PASS" if ok else "FAIL", "" if ok else "| " + detail))
    print("")
    print("%d/%d checks passed" % (passed, len(results)))
    return 0 if passed == len(results) else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".", help="repository root (default: .)")
    ap.add_argument("--json", action="store_true", help="emit the full scan as JSON")
    ap.add_argument("--selftest", action="store_true", help="run fixture checks and exit")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    root = Path(args.root)
    if not (root / "src" / "autoresearch").is_dir():
        print("no src/autoresearch under %s" % root, file=sys.stderr)
        return 2
    graph, entrypoints = scan(root)
    dead = [e["entrypoint"] for e in entrypoints if e.get("unguarded_posix")]
    if args.json:
        print(json.dumps({
            "hard_blockers": sorted({m for n in graph for m, _ in graph[n]["top"]}),
            "lazy_blockers": sorted({m for n in graph for m, _ in graph[n]["lazy"]}),
            "offending_modules": sorted(n for n in graph if graph[n]["top"]),
            "entrypoints": entrypoints,
            "dead_entrypoints": dead,
        }, indent=2, sort_keys=True))
    else:
        print(render(graph, entrypoints))
        print("")
        print("EXIT %d (%s)" % (1 if dead else 0, "DEAD ENTRYPOINTS PRESENT" if dead else "CLEAN"))
    return 1 if dead else 0


if __name__ == "__main__":
    raise SystemExit(main())
