#!/usr/bin/env python3
"""
verify.py - reproduce the three verification legs of the GDPR KG gate.

    python verify.py               # all three legs
    python verify.py --shacl       # pySHACL conformance only
    python verify.py --cq          # SPARQL competency questions under OWL 2 RL
    python verify.py --reasoner    # headless HermiT consistency

Exit code 0 iff every requested leg passes. See SPEC.md section 5.

NOTE on the reasoner leg: it strips owl:imports so HermiT can run offline, which
means external vocabularies (DPV, PROV-O, GDPRtEXT, ELI) are NOT loaded. The
certifying runs were done in Protege with imports resolved. Treat this leg as a
regression check, not as the certification. See SPEC.md section 6.5.
"""
import subprocess, sys, os

ROOT  = os.path.dirname(os.path.abspath(__file__))
TBOX  = os.path.join(ROOT, 'ontology', 'gdpr_kg.ttl')
SHAPES= os.path.join(ROOT, 'ontology', 'shapes.ttl')
ARTS  = [os.path.join(ROOT, 'articles', f'art{n}.ttl') for n in (13, 6, 12, 14, 46)]
FIX   = [(os.path.join(ROOT,'ontology','shacl_test','data_conformant.ttl'),    True),
         (os.path.join(ROOT,'ontology','shacl_test','data_nonconformant.ttl'), False)]
RUNNERS = ['run_owlrl_art6.py', 'run_owlrl_art12.py', 'run_owlrl_art14.py',
           'run_owlrl_art46.py']


def _load(*paths):
    from rdflib import Graph
    g = Graph()
    for p in paths:
        g.parse(p, format='turtle')
    return g


def leg_shacl():
    from pyshacl import validate
    print('== SHACL conformance (pySHACL) ==')
    shapes = _load(SHAPES)
    ok = True
    for a in ARTS:
        c, _, _ = validate(_load(TBOX, a), shacl_graph=shapes, advanced=True)
        print(f'  {os.path.basename(a):24s} Conforms: {c}')
        ok &= c
    c, _, _ = validate(_load(TBOX, *ARTS), shacl_graph=shapes, advanced=True)
    print(f'  {"COMBINED (5 articles)":24s} Conforms: {c}')
    ok &= c
    for path, expected in FIX:
        c, _, _ = validate(_load(TBOX, path), shacl_graph=shapes, advanced=True)
        good = (c == expected)
        print(f'  {os.path.basename(path):24s} Conforms: {c}  expected: {expected}  -> '
              f'{"PASS" if good else "FAIL"}')
        ok &= good
    return ok


def leg_cq():
    print('== Competency questions (SPARQL under OWL 2 RL materialisation) ==')
    ok = True
    cqdir = os.path.join(ROOT, 'cq_sparql')
    for r in RUNNERS:
        p = subprocess.run([sys.executable, r], cwd=cqdir,
                           capture_output=True, text=True)
        tail = [l for l in p.stdout.strip().splitlines() if l.strip()][-1:] or ['(no output)']
        print(f'  {r:24s} exit={p.returncode}  {tail[0][:88]}')
        if p.returncode != 0:
            sys.stderr.write(p.stdout[-3000:] + p.stderr[-2000:])
        ok &= (p.returncode == 0)
    return ok


def leg_reasoner():
    print('== Reasoner consistency (HermiT, headless, imports stripped) ==')
    from rdflib import OWL
    from owlready2 import World, sync_reasoner_hermit, Nothing
    import tempfile
    g = _load(TBOX, *ARTS)
    stripped = list(g.triples((None, OWL.imports, None)))
    for t in stripped:
        g.remove(t)
    tmp = os.path.join(tempfile.mkdtemp(), 'union.owl')
    g.serialize(tmp, format='xml')
    print(f'  stripped {len(stripped)} owl:imports (external vocabularies not loaded)')
    w = World()
    onto = w.get_ontology('file://' + tmp).load()
    try:
        with onto:
            sync_reasoner_hermit(w, debug=0)
    except Exception as e:
        print(f'  HermiT: INCONSISTENT or failed -> {type(e).__name__}: {e}')
        return False
    unsat = [c for c in onto.classes() if Nothing in c.is_a]
    print(f'  HermiT: consistent; unsatisfiable classes: {len(unsat)}')
    return len(unsat) == 0


def main():
    args = set(sys.argv[1:])
    legs = [('--shacl', leg_shacl), ('--cq', leg_cq), ('--reasoner', leg_reasoner)]
    chosen = [(f, fn) for f, fn in legs if f in args] or legs
    results = []
    for flag, fn in chosen:
        results.append((flag, fn()))
        print()
    print('== SUMMARY ==')
    for flag, r in results:
        print(f'  {flag:12s} {"PASS" if r else "FAIL"}')
    return 0 if all(r for _, r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
