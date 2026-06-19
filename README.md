# PyReachability

[![CI](https://github.com/ReneVeloso/PyReachability/actions/workflows/ci.yml/badge.svg)](https://github.com/ReneVeloso/PyReachability/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Fast graph reachability methods with a C++17 core and an ergonomic Python API.**

A *reachability query* asks: given a directed graph and two vertices `u` and `v`, is there
a directed path from `u` to `v`? PyReachability packages a representative, best-in-class set
of reachability **indexing methods** under a single, common interface — so you can build an
index once and answer millions of queries fast, and swap methods to fit your graph's
size/memory/query-time trade-off.

The library has a high-performance **C++17 core** exposed through **Cython** (C++ mode), an
**extensible method catalog** (each method is a plug-in implementing one interface), and a
reproducible benchmark harness (planned). It accompanies a *Software Impacts* article.

> **Status:** v0.1.0 — *Foundation* + first indexing method. The core, the catalog, graph
> ingestion, SCC condensation, the **BFS/DFS** baseline, and **GRAIL** (the first indexing
> method, using SCC condensation + label-guided search) are implemented and tested. The
> remaining methods below land in subsequent releases (see [Roadmap](#roadmap)).

---

## Installation

From source (a C++17 compiler and CMake ≥ 3.15 are required to build):

```bash
git clone https://github.com/ReneVeloso/PyReachability.git
cd PyReachability
pip install .
```

For development (editable install + test extras):

```bash
pip install -e ".[test]"
```

Pre-built wheels on PyPI (`pip install pyreachability`, no compiler needed) are planned for a
later milestone.

## Quickstart

```python
import numpy as np
from pyreachability import Graph, BFSDFS

# Build a graph from a NumPy edge list: edges 0->1, 1->2, 2->0 (a cycle), 3 isolated.
src = np.array([0, 1, 2], dtype=np.int32)
dst = np.array([1, 2, 0], dtype=np.int32)
g = Graph.from_edges(src, dst, num_nodes=4)

# Pick a method, build its index, then query.
idx = BFSDFS()
idx.build(g)

idx.query(0, 2)        # True  (0 -> 1 -> 2)
idx.query(0, 3)        # False (3 is unreachable)
idx.query(3, 3)        # True  (reachability is reflexive)

# Batch queries: (M, 2) int array -> (M,) bool array.
pairs = np.array([[0, 2], [2, 0], [0, 3]], dtype=np.int32)
idx.query_batch(pairs) # array([ True,  True, False])
```

`from_edges` also accepts a single `(E, 2)` array of `[u, v]` rows:

```python
edges = np.array([[0, 1], [1, 2], [2, 0]], dtype=np.int32)
g = Graph.from_edges(edges, num_nodes=4)
```

Load a graph from a file (`.gz` is decompressed transparently):

```python
g = Graph.from_file("graph.txt", fmt="edgelist")        # one "u v" edge per line
g = Graph.from_file("graph.scc.gra.gz", fmt="gra")      # GRAIL/GREACH adjacency format
```

Export the edges back out (inverse of `from_edges`, reconstructed from CSR):

```python
src, dst = g.to_edges()
```

Discover available methods dynamically through the catalog:

```python
from pyreachability import catalog
catalog.methods()          # ['bfsdfs']  (grows as methods are added)
Method = catalog.get("bfsdfs")
idx = Method()
```

A runnable version of this walkthrough lives in [`examples/quickstart.py`](examples/quickstart.py).

## Methods

Every method implements the same [`ReachabilityIndex`](src/pyreachability/base.py) interface
(`build` / `query` / `query_batch` / `index_size_bytes`) and is registered in the catalog.
A method only enters the library if it has a peer-reviewed publication.

| Method | Family | Status | Reference |
|---|---|---|---|
| `BFSDFS` | online traversal (baseline / oracle) | ✅ implemented | CLRS, *Introduction to Algorithms* |
| `TC` | transitive closure (bitset) | 🔜 planned | Warshall, JACM 1962 |
| `TreeCover` | tree / interval cover | 🔜 planned | Agrawal, Borgida, Jagadish, SIGMOD 1989 |
| `GRAIL` | tree-cover, interval-label pruning | ✅ implemented | Yıldırım, Chaoji, Zaki, PVLDB 2010 |
| `FELINE` | refined online search (2 topological orders) | 🔜 planned | Veloso, Cerf, Meira Jr., Zaki, EDBT 2014 |
| `PLL` | 2-hop labeling | 🔜 planned | Yano, Akiba, Iwata, Yoshida, CIKM 2013 |

See [`docs/architecture.md`](docs/architecture.md) for how the pieces fit together and how to
add a new method to the catalog, and [`docs/AI_GUIDE.md`](docs/AI_GUIDE.md) for contributor
conventions, the method inclusion policy, and verified references.

## Roadmap

The library is built in milestones, each producing working, tested software:

1. **Foundation** *(this release)* — build system, CSR graph, SCC condensation, catalog,
   `BFSDFS` oracle, property-based tests, CI.
2. **Tree-cover family** — `TC`, `TreeCover`, `GRAIL`.
3. **`FELINE` + `PLL`.**
4. **Benchmark harness + datasets** — reproducible build/memory/query-time comparisons.
5. **Docs site, PyPI wheels, Zenodo DOI.**

Label-constrained reachability (edge-labeled graphs) is a planned future extension.

## Development

```bash
pip install -e ".[test]"     # build + install with test deps
pytest -v                    # Python test suite (incl. property-based tests)

# C++ unit tests (doctest):
cmake -S . -B build-cpp -DCMAKE_BUILD_TYPE=Debug
cmake --build build-cpp --target cpp_tests
./build-cpp/cpp_tests
```

CI runs the full suite on Linux/macOS/Windows across Python 3.9–3.13.

## Citing

If you use PyReachability in academic work, please cite it via [`CITATION.cff`](CITATION.cff)
(GitHub renders a "Cite this repository" button). The accompanying *Software Impacts* article
reference will be added on publication.

## License

[MIT](LICENSE) © Renê Rodrigues Veloso
