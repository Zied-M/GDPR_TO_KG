#!/usr/bin/env python3
# =====================================================================
#  kg_root.py — ONE place that answers "which tree am I reading, and
#  exactly which TBox did I read?"
#
#  Added 2026-08-18 for REPAIR-PLAN.md S-B (the §9.3 decision). Before
#  it, every runner hard-coded os.path.join('..', 'ontology', ...) and
#  resolved it against the CURRENT WORKING DIRECTORY, so the foundation
#  tree — which had no ontology/gdpr_kg.ttl — could not run any of them,
#  and a missing-TBox path failure was indistinguishable from a genuine
#  CQ failure to any caller reading $?.
#
#  ROOT resolution, first hit wins:
#      1. --root <dir>   /  --root=<dir>      (command line)
#      2. GDPR_KG_ROOT                        (environment)
#      3. the tree this file lives in         (dirname(__file__)/..)
#
#  (3) is deliberately SCRIPT-relative, not cwd-relative and not an
#  absolute path to the foundation tree:
#    * in gdpr-kg-foundation/ it resolves to the foundation tree, which
#      now holds the CANONICAL TBox and shapes — so the default IS the
#      canonical source of truth, which is the decision;
#    * in publish-gdpr-kg/ it resolves to the published snapshot, so an
#      evaluator's standalone checkout stays self-contained and
#      reproducible with no sibling directory and no flag. An absolute
#      default pointing at the foundation tree would break every
#      evaluator clone, which is why it is not done that way;
#    * being script-relative rather than cwd-relative, every documented
#      invocation ("run from the cq_sparql/ directory") keeps working
#      unchanged, and the runners now also work from anywhere else.
#
#  MISSING TBOX IS EXIT 2, NOT EXIT 1. require() below gives the path
#  failure of §9.3 its own exit code so that a caller reading $? can
#  tell "I could not find the graph" (2) from "the graph is wrong" (1).
#
#  This file must stay byte-identical in both trees (REPAIR-PLAN §10.2).
# =====================================================================
import hashlib
import os
import sys

EXIT_MISSING_INPUT = 2


def resolve_root(argv=None):
    """Return the absolute, normalised repository root for this run."""
    argv = list(sys.argv if argv is None else argv)
    root = None
    for i, a in enumerate(argv):
        if a == '--root' and i + 1 < len(argv):
            root = argv[i + 1]
            break
        if a.startswith('--root='):
            root = a.split('=', 1)[1]
            break
    if root is None:
        root = os.environ.get('GDPR_KG_ROOT') or None
    if root is None:
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    return os.path.normpath(os.path.abspath(root))


def strip_root_args(argv=None):
    """argv with --root/--root=... removed, so existing flag parsing (-v etc.)
    is unaffected by the new option."""
    argv = list(sys.argv if argv is None else argv)
    out, skip = [], False
    for a in argv:
        if skip:
            skip = False
            continue
        if a == '--root':
            skip = True
            continue
        if a.startswith('--root='):
            continue
        out.append(a)
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def require(*paths, **kw):
    """Exit 2 with a named, unambiguous message if any input is missing.

    Distinct from the exit 1 that every runner uses for 'the counts do not
    match', so $? still carries information when the tree is wrong. Callers
    that already give 2 another meaning pass code=3 (reason_check.py: 2 is
    INCONSISTENT; shacl_check.py: 2 is usage).
    """
    code = kw.pop("code", EXIT_MISSING_INPUT)
    assert not kw, "unexpected kwargs: %r" % sorted(kw)
    missing = [p for p in paths if not os.path.isfile(p)]
    if missing:
        sys.stderr.write(
            "[INPUT MISSING] this is a PATH failure, not a CQ failure "
            "(REPAIR-PLAN.md 9.3 / S-B):\n")
        for p in missing:
            sys.stderr.write("    not found: %s\n" % p)
        sys.stderr.write(
            "    Pass --root <dir> or set GDPR_KG_ROOT to the tree holding "
            "ontology/ and articles/.\n")
        sys.exit(code)
    return paths[0] if len(paths) == 1 else paths


def provenance(root, tbox, extra=()):
    """Print the resolved root and the sha256 of the TBox actually read.

    Every runner calls this before it loads anything, so the printed counts can
    never be read back without knowing which bytes produced them. `extra` takes
    (label, path) pairs for shapes or fixture graphs.
    """
    print("[ROOT] %s" % root)
    print("[TBOX] %s" % os.path.relpath(tbox, root).replace(os.sep, '/'))
    print("       sha256=%s" % sha256(tbox))
    for label, p in extra:
        print("[%s] %s" % (label, os.path.relpath(p, root).replace(os.sep, '/')))
        print("       sha256=%s" % sha256(p))
