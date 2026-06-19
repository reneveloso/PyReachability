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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--d", type=int, default=5)
    ap.add_argument("--bfs-queries", type=int, default=200)
    ap.add_argument("--grail-queries", type=int, default=50000)
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


if __name__ == "__main__":
    main()
