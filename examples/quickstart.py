"""PyReachability quickstart — run with: python examples/quickstart.py

Demonstrates building a graph, choosing a method, and answering reachability
queries (single and batched), plus dynamic method discovery via the catalog.
"""
import numpy as np

from pyreachability import Graph, BFSDFS, catalog


def main() -> None:
    # Build a graph from a NumPy edge list.
    # [0, 1, 2] are the source vertices and [1, 2, 0] are the destination vertices;
    #  The edges are defined as paired values in arrays of int32, but the API also accepts a single (E, 2) array.
    #  For example, the same graph could be built with:
    #     edges = np.array([[0, 1], [1, 2], [2, 0]], dtype=np.int32)
    #     g = Graph.from_edges(edges, num_nodes=4)

    # Edges: 0->1, 1->2, 2->0 (a directed cycle); vertex 3 is isolated.
    src = np.array([0, 1, 2], dtype=np.int32)
    dst = np.array([1, 2, 0], dtype=np.int32)
    g = Graph.from_edges(src, dst, num_nodes=4)
    print(f"graph: {g.num_nodes} nodes, {g.num_edges} edges")

    # Pick a method, build its index, then query.
    idx = BFSDFS()
    idx.build(g)

    print("0 -> 2 :", idx.query(0, 2))   # True  (0 -> 1 -> 2)
    print("0 -> 3 :", idx.query(0, 3))   # False (3 is unreachable)
    print("3 -> 3 :", idx.query(3, 3))   # True  (reachability is reflexive)

    # Batch queries: (M, 2) int array -> (M,) bool array.
    pairs = np.array([[0, 2], [2, 0], [0, 3]], dtype=np.int32)
    print("batch  :", idx.query_batch(pairs).tolist())

    # Discover available methods dynamically.
    print("catalog:", catalog.methods())
    method_cls = catalog.get("bfsdfs")
    print("by name:", method_cls.__name__)


if __name__ == "__main__":
    main()
