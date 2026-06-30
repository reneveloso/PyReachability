"""Generate a small synthetic random DAG in GRAIL .gra format.

A tiny graph on which *every* method in the catalog (including the ones with super-linear
construction) can be built, for an all-methods correctness/benchmark table. Output goes to
benchmarks/data/ (gitignored).

Usage:
    python benchmarks/make_synthetic.py                       # 600 nodes, ~2.5n edges
    python benchmarks/make_synthetic.py --nodes 1000 --degree 3 --out benchmarks/data/synth.gra
"""
import argparse
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", type=int, default=600)
    ap.add_argument("--degree", type=float, default=2.5, help="target edges per node")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="benchmarks/data/synth_small.gra")
    args = ap.parse_args()

    n = args.nodes
    rng = np.random.default_rng(args.seed)
    perm = rng.permutation(n)
    pos = {int(v): i for i, v in enumerate(perm)}   # a random topological order
    adj = {i: set() for i in range(n)}
    target = int(args.degree * n)
    cnt = tries = 0
    while cnt < target and tries < target * 20:
        tries += 1
        a, b = int(rng.integers(0, n)), int(rng.integers(0, n))
        if pos[a] < pos[b] and b not in adj[a]:   # forward in topo order => acyclic
            adj[a].add(b); cnt += 1

    with open(args.out, "w") as f:
        f.write("graph_for_greach\n%d\n" % n)
        for i in range(n):
            f.write("%d: %s #\n" % (i, " ".join(str(x) for x in sorted(adj[i]))))
    print(f"wrote {args.out}: {n} nodes, {cnt} edges")


if __name__ == "__main__":
    main()
