"""Catalog-driven reachability benchmark harness.

For each input graph and each method in the catalog, this reports index construction time,
index size, and average query time on uniformly random pairs, and checks every method against
the BFS/DFS oracle. Results are printed as a markdown table per dataset and (optionally) written
to a combined CSV.

Datasets are the standard SIGMOD'08 DAGs plus large graphs; fetch them with
``bash benchmarks/fetch_datasets.sh`` (they live in benchmarks/data/, which is gitignored).

Usage:
    python benchmarks/run_benchmark.py benchmarks/data/*.gra
    python benchmarks/run_benchmark.py benchmarks/data/kegg_dag_uniq.gra --queries 100000
    python benchmarks/run_benchmark.py benchmarks/data/cit-Patents.scc.gra.gz --csv out.csv

Methods whose construction is super-linear (e.g. TC, 2-Hop, 3-Hop, Path-Tree) are skipped on
graphs larger than a per-method node cap, shown as "skip" in the table.
"""
import argparse
import csv
import time

import numpy as np

from pyreachability import Graph, catalog
from pyreachability.static import BFSDFS

# Per-method cap on #nodes: methods with super-linear construction skip larger graphs.
# Anything not listed runs on all sizes (linear / near-linear construction).
# Per-method cap on #nodes. These implementations are correctness-first; several have
# super-linear (up to ~O(n^3)) construction, so they are capped to where they finish quickly.
# (The linear/near-linear methods below have no cap and run on every graph.)
NODE_CAP = {
    "twohop": 800,        # greedy densest-subgraph set cover (~O(n^3))
    "3hop": 1_500,        # transitive-closure contour + per-chain densest subgraph
    "optchain": 1_500,    # reachability bitsets + Kuhn matching (~O(n^3))
    "pathtree": 25_000,   # path decomposition + residual TC (adding-rule O(m k^2))
    "pathhop": 1_000,     # residual TC over a tree cover (candidate enumeration ~O(n^2) per round)
    "dual": 2_000,        # transitive link table closure (~O(t^3) in non-tree edges t)
    "hl": 3_000,          # FastCover backbone: per-vertex eps-bounded BFS + domination checks
    "ip": 40_000,         # reachability-set mink labels (n^2 bitset)
    "tc": 60_000,         # n^2 bitset transitive closure
}


def timed(fn):
    t0 = time.perf_counter()
    out = fn()
    return out, time.perf_counter() - t0


def run_dataset(path, n_queries, seed, rows):
    g, t_load = timed(lambda: Graph.from_file(path, fmt="gra" if not path.endswith(".txt") else "edgelist"))
    n, m = g.num_nodes, g.num_edges
    print(f"\n## {path}\n{n:,} nodes, {m:,} edges  (loaded in {t_load:.2f}s)")

    rng = np.random.default_rng(seed)
    pairs = np.stack([rng.integers(0, n, size=n_queries, dtype=np.int32),
                      rng.integers(0, n, size=n_queries, dtype=np.int32)], axis=1)

    oracle = BFSDFS(); oracle.build(g)
    truth, t_truth = timed(lambda: oracle.query_batch(pairs))
    npos = int(truth.sum())
    print(f"queries: {n_queries:,} random pairs ({100.0 * npos / n_queries:.2f}% reachable)")
    print(f"\n| {'method':12s} | {'build (s)':>9s} | {'index (MB)':>10s} | {'query (us)':>10s} | check |")
    print(f"|{'-'*14}|{'-'*11}|{'-'*12}|{'-'*12}|{'-'*7}|")
    print(f"| {'BFSDFS*':12s} | {'-':>9s} | {'-':>10s} | {1e6 * t_truth / n_queries:10.3f} | oracle |")

    for name in catalog.methods(kind="static"):
        if name == "bfsdfs":
            continue
        cap = NODE_CAP.get(name)
        if cap is not None and n > cap:
            print(f"| {name:12s} | {'skip':>9s} | {'skip':>10s} | {'skip':>10s} | n>{cap//1000}k |")
            rows.append([path, n, m, name, "", "", "", "skip"])
            continue
        idx = catalog.get(name)()
        try:
            _, tb = timed(lambda: idx.build(g))
        except Exception as e:  # noqa: BLE001 - report and continue the sweep
            print(f"| {name:12s} | {'ERR':>9s} | {'-':>10s} | {'-':>10s} | {type(e).__name__} |")
            rows.append([path, n, m, name, "", "", "", f"ERR:{type(e).__name__}"])
            continue
        ans, tq = timed(lambda: idx.query_batch(pairs))
        ok = "OK" if np.array_equal(ans, truth) else "DISAGREE"
        mb = idx.index_size_bytes / 1e6
        usq = 1e6 * tq / n_queries
        print(f"| {name:12s} | {tb:9.2f} | {mb:10.2f} | {usq:10.3f} | {ok:5s} |")
        rows.append([path, n, m, name, f"{tb:.4f}", f"{mb:.3f}", f"{usq:.4f}", ok])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help="graph files (.gra/.gra.gz or .txt edge lists)")
    ap.add_argument("--queries", type=int, default=100_000, help="random query pairs per dataset")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--csv", help="write all rows to this CSV file")
    args = ap.parse_args()

    rows = []
    for path in args.paths:
        run_dataset(path, args.queries, args.seed, rows)

    if args.csv:
        with open(args.csv, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["dataset", "nodes", "edges", "method", "build_s", "index_mb", "query_us", "check"])
            w.writerows(rows)
        print(f"\nwrote {len(rows)} rows to {args.csv}")


if __name__ == "__main__":
    main()
