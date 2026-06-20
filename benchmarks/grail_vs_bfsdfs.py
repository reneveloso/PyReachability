"""Quick harness comparing the indexing methods (GRAIL, GRAIL-bidirectional, FELINE)
against the BFSDFS oracle, on a real graph in GRAIL's .gra(.gz) format.

Usage:
    python benchmarks/grail_vs_bfsdfs.py benchmarks/data/cit-Patents.scc.gra.gz

Reports build time and index size per method, checks that every method agrees with
the BFSDFS oracle, and compares query time (including deep multi-hop positives).
"""
import argparse
import time

import numpy as np

from pyreachability import Graph, GRAIL, FELINE, BFSDFS


def timed(fn):
    t0 = time.perf_counter()
    out = fn()
    return out, time.perf_counter() - t0


def edge_arrays(g):
    """Recover (src, dst) from a built Graph for query sampling, via its CSR view."""
    src, dst = g.to_edges()
    return src, dst


def build_adj(n, src, dst):
    """CSR-style offsets/targets in Python (src is already grouped by source)."""
    deg = np.bincount(src, minlength=n)
    off = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(deg, out=off[1:])
    return off, dst


def deep_positive_pairs(off, targets, n, k, max_steps, seed=3):
    """Generate (start, end) pairs reachable via multi-hop random walks.

    These are *deep* positives: the target sits several hops down, so the BFSDFS
    oracle must explore a large frontier, while GRAIL's cuts usually decide them
    outright. Returns fewer than k pairs if walks keep hitting sinks.
    """
    rng = np.random.default_rng(seed)
    us, vs = [], []
    attempts = 0
    while len(us) < k and attempts < k * 20:
        attempts += 1
        s = int(rng.integers(0, n))
        x = s
        steps = int(rng.integers(2, max_steps + 1))
        moved = 0
        for _ in range(steps):
            a, b = off[x], off[x + 1]
            if b <= a:
                break
            x = int(targets[rng.integers(a, b)])
            moved += 1
        if moved >= 1 and x != s:
            us.append(s); vs.append(x)
    return np.array(us, np.int32), np.array(vs, np.int32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--d", type=int, default=5)
    ap.add_argument("--random-queries", type=int, default=500000)
    ap.add_argument("--deep-queries", type=int, default=50000)
    ap.add_argument("--deep-steps", type=int, default=20)
    args = ap.parse_args()

    g, t_load = timed(lambda: Graph.from_file(args.path, fmt="gra"))
    print(f"loaded {args.path}: {g.num_nodes:,} nodes, {g.num_edges:,} edges  ({t_load:.1f}s)")
    n = g.num_nodes
    src, dst = edge_arrays(g)

    bfs = BFSDFS(); bfs.build(g)
    grail = GRAIL(d=args.d)
    _, t_build = timed(lambda: grail.build(g))
    print(f"GRAIL(d={args.d}) build: {t_build:.2f}s, "
          f"index size: {grail.index_size_bytes / 1e6:.1f} MB")
    grail_bi = GRAIL(d=args.d, bidirectional=True)
    _, t_build_bi = timed(lambda: grail_bi.build(g))
    print(f"GRAIL(d={args.d}, bidirectional) build: {t_build_bi:.2f}s, "
          f"index size: {grail_bi.index_size_bytes / 1e6:.1f} MB")
    feline = FELINE()
    _, t_build_f = timed(lambda: feline.build(g))
    print(f"FELINE build: {t_build_f:.2f}s, "
          f"index size: {feline.index_size_bytes / 1e6:.1f} MB")
    feline_b = FELINE(bidirectional=True)
    _, t_build_fb = timed(lambda: feline_b.build(g))
    print(f"FELINE-B build: {t_build_fb:.2f}s, "
          f"index size: {feline_b.index_size_bytes / 1e6:.1f} MB")

    # Methods to compare. Timing uses query_batch, whose loop runs in C++ with the GIL
    # released — so we measure the methods, not Python per-call overhead.
    methods = [("GRAIL", grail), ("GRAIL-bidirectional", grail_bi),
               ("FELINE", feline), ("FELINE-B", feline_b)]

    def report(title, pairs):
        truth = bfs.query_batch(pairs)
        npos = int(truth.sum())
        print(f"\n{title}: {len(pairs):,} pairs "
              f"({npos:,} reachable, {100.0 * npos / len(pairs):.2f}% positive)")
        ans, t = timed(lambda: bfs.query_batch(pairs))
        print(f"  {'BFSDFS':20s}: {1e6 * t / len(pairs):8.3f} us/query")
        for name, m in methods:
            a, t = timed(lambda m=m: m.query_batch(pairs))
            ok = "AGREE ✓" if np.array_equal(a, truth) else "DISAGREE ✗"
            print(f"  {name:20s}: {1e6 * t / len(pairs):8.3f} us/query   ({ok})")

    # Paper methodology: uniformly random pairs (mostly negative on a large sparse DAG).
    rng = np.random.default_rng(1)
    rp = np.stack([rng.integers(0, n, size=args.random_queries, dtype=np.int32),
                   rng.integers(0, n, size=args.random_queries, dtype=np.int32)], axis=1)
    report("random pairs", rp)

    # Deep multi-hop positives (where a naive search must traverse far).
    off, targets = build_adj(n, src, dst)
    du, dv = deep_positive_pairs(off, targets, n, args.deep_queries, args.deep_steps)
    if len(du):
        report("deep positives", np.stack([du, dv], axis=1))


if __name__ == "__main__":
    main()
