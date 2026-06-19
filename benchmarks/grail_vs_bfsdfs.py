"""Quick harness: GRAIL vs BFSDFS on a real graph in GRAIL's .gra(.gz) format.

Usage:
    python benchmarks/grail_vs_bfsdfs.py benchmarks/data/cit-Patents.scc.gra.gz

Reports build time and index size for GRAIL, checks that GRAIL agrees with the
BFSDFS oracle on a sample of queries, and compares query throughput.
"""
import argparse
import time

import numpy as np

from pyreachability import Graph, GRAIL, BFSDFS


def sample_pairs(n, src, dst, k_random, k_edge, seed=0):
    """Mix random pairs (mostly negative) with real edges (guaranteed positive)."""
    rng = np.random.default_rng(seed)
    ru = rng.integers(0, n, size=k_random, dtype=np.int32)
    rv = rng.integers(0, n, size=k_random, dtype=np.int32)
    ei = rng.integers(0, src.shape[0], size=k_edge)
    pu = np.concatenate([ru, src[ei]])
    pv = np.concatenate([rv, dst[ei]])
    return np.stack([pu, pv], axis=1).astype(np.int32)


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
    ap.add_argument("--bfs-queries", type=int, default=200)
    ap.add_argument("--grail-queries", type=int, default=50000)
    ap.add_argument("--deep-queries", type=int, default=2000)
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

    # --- correctness: GRAIL must agree with the BFSDFS oracle ---
    check = sample_pairs(n, src, dst, args.bfs_queries // 2, args.bfs_queries // 2, seed=1)
    disagree = 0
    pos = 0
    (_, t_bfs) = timed(lambda: [bfs.query(int(u), int(v)) for u, v in check])
    bfs_ans = [bfs.query(int(u), int(v)) for u, v in check]
    grail_ans = [grail.query(int(u), int(v)) for u, v in check]
    for a, b in zip(bfs_ans, grail_ans):
        pos += int(b)
        disagree += int(a != b)
    print(f"\ncorrectness on {len(check)} pairs ({pos} reachable): "
          f"{'AGREE ✓' if disagree == 0 else f'{disagree} DISAGREEMENTS ✗'}")
    print(f"BFSDFS: {t_bfs:.3f}s for {len(check)} queries "
          f"({1000 * t_bfs / len(check):.3f} ms/query)")

    # --- throughput: GRAIL on a much larger sample ---
    big = sample_pairs(n, src, dst, args.grail_queries // 2, args.grail_queries // 2, seed=2)
    _, t_grail = timed(lambda: [grail.query(int(u), int(v)) for u, v in big])
    print(f"GRAIL : {t_grail:.3f}s for {len(big):,} queries "
          f"({1e6 * t_grail / len(big):.2f} us/query)")

    # --- deep positives: where the index pays off (BFS must traverse far) ---
    off, targets = build_adj(n, src, dst)
    du, dv = deep_positive_pairs(off, targets, n, args.deep_queries, args.deep_steps)
    if len(du) == 0:
        print("\n(no deep positives sampled)")
        return
    deep = np.stack([du, dv], axis=1)
    bfs_deep, t_bfs_deep = timed(lambda: [bfs.query(int(u), int(v)) for u, v in deep])
    grail_deep, t_grail_deep = timed(lambda: [grail.query(int(u), int(v)) for u, v in deep])
    disagree = sum(int(a != b) for a, b in zip(bfs_deep, grail_deep))
    print(f"\ndeep positives: {len(deep):,} multi-hop reachable pairs "
          f"({'AGREE ✓' if disagree == 0 else f'{disagree} DISAGREEMENTS ✗'})")
    print(f"BFSDFS: {1000 * t_bfs_deep / len(deep):.3f} ms/query")
    print(f"GRAIL : {1000 * t_grail_deep / len(deep):.3f} ms/query   "
          f"(speedup x{t_bfs_deep / t_grail_deep:.0f})")


if __name__ == "__main__":
    main()
