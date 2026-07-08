# PyReachability

[![CI](https://github.com/reneveloso/PyReachability/actions/workflows/ci.yml/badge.svg)](https://github.com/reneveloso/PyReachability/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/pyreachability)](https://pypi.org/project/pyreachability/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21251749.svg)](https://doi.org/10.5281/zenodo.21251749)
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
reproducible, catalog-driven benchmark harness (`benchmarks/run_benchmark.py`).

> **Status:** v0.1.0 — **24 methods** implemented and verified against the BFS/DFS oracle,
> covering every static index class of the CSUR 2025 survey (Table 1): traversal and
> transitive-closure baselines, interval/tree-cover labeling, the 2-hop family,
> approximate transitive closure, and chain covers. See the [Roadmap](#roadmap) for
> what's next.

---

## Installation

From PyPI (wheels for Linux/macOS/Windows, Python 3.9–3.13):

```bash
pip install pyreachability
```

From source (a C++17 compiler and CMake ≥ 3.15 are required to build):

```bash
git clone https://github.com/reneveloso/PyReachability.git
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
catalog.methods()          # ['3hop', 'bfl', 'bfsdfs', 'chaincover', 'dl', 'dual', 'feline', 'ferrari', 'grail', 'gripp', 'hl', 'ip', 'optchain', 'oreach', 'pathhop', 'pathtree', 'pll', 'preach', 'sspi', 'tc', 'tfl', 'tol', 'treecover', 'twohop']
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
| `TC` | transitive closure (bitset) | ✅ implemented | Warshall, JACM 1962 |
| `TreeCover` | tree / interval cover | ✅ implemented | Agrawal, Borgida, Jagadish, SIGMOD 1989 |
| `GRAIL` | tree-cover, interval-label pruning | ✅ implemented | Yıldırım, Chaoji, Zaki, PVLDB 2010 |
| `FELINE` | refined online search (2 topological orders) | ✅ implemented | Veloso, Cerf, Meira Jr., Zaki, EDBT 2014 |
| `PLL` | 2-hop labeling | ✅ implemented | Yano, Akiba, Iwata, Yoshida, CIKM 2013 |
| `BFL` | approximate TC (Bloom filters) | ✅ implemented | Su, Zhu, Wei, Yu, TKDE 2017 |
| `ChainCover` | chain-decomposition TC compression | ✅ implemented | Jagadish, ACM TODS 1990 |
| `PReaCH` | contraction hierarchies + bidirectional search | ✅ implemented | Merz & Sanders, ESA 2014 |
| `TwoHop` | 2-hop labeling (near-minimum greedy cover) | ✅ implemented | Cohen, Halperin, Kaplan, Zwick, SICOMP 2003 |
| `TFLabel` | 2-hop labeling via topological folding | ✅ implemented | Cheng, Huang, Wu, Fu, SIGMOD 2013 |
| `TOL` | 2-hop labeling, contribution-score order | ✅ implemented | Zhu, Lin, Wang, Xiao, SIGMOD 2014 |
| `HL` | hierarchical 2-hop (recursive backbone) | ✅ implemented | Jin & Wang, PVLDB 2013 |
| `OReach` | constant-time observations + guided fallback | ✅ implemented | Hanauer, Schulz, Trummer, SEA 2021 |
| `ThreeHop` | 3-hop: chains as highways (TC-contour compression) | ✅ implemented | Jin, Xiang, Ruan, Fuhry, SIGMOD 2009 |
| `PathHop` | path-hop: trees as highways (residual-TC compression) | ✅ implemented | Cai & Poon, CIKM 2010 |
| `Ferrari` | budgeted exact/approx intervals + guided search | ✅ implemented | Seufert, Anand, Bedathur, Weikum, ICDE 2013 |
| `DualLabeling` | tree intervals + transitive link table (sparse graphs) | ✅ implemented | Wang, He, Yang, Yu, Yu, ICDE 2006 |
| `TreeSSPI` | tree-cover + predecessor index + guided search | ✅ implemented | Chen, Gupta, Kurul, VLDB 2005 |
| `GRIPP` | pre/postorder order-tree instances + hop technique | ✅ implemented | Trißl & Leser, SIGMOD 2007 |
| `PathTree` | path-tree cover (3-tuple labels) + residual TC | ✅ implemented | Jin, Ruan, Xiang, Wang, ACM TODS 2011 |
| `IP` | independent-permutation labels (approx TC) + guided search | ✅ implemented | Wei, Yu, Lu, PVLDB 2014 |
| `OptimalChainCover` | minimum-chain decomposition (Dilworth) + chain labels | ✅ implemented | Chen & Chen, ICDE 2008 |
| `DL` | distribution labeling (2-hop, equivalent to PLL) | ✅ implemented | Jin & Wang, PVLDB 2013 |

These span one+ method per index class of the CSUR 2025 survey, plus the baselines. The
catalog will grow to cover the survey's full plain-reachability list — see
[`docs/methods.md`](docs/methods.md) for the source-backed coverage map.

See [`docs/architecture.md`](docs/architecture.md) for how the pieces fit together and how to
add a new method to the catalog, [`docs/fidelity.md`](docs/fidelity.md) for how faithfully each
method follows its source publication, and [`docs/AI_GUIDE.md`](docs/AI_GUIDE.md) for contributor
conventions, the method inclusion policy, and verified references.

## Roadmap

The library is built in milestones, each producing working, tested software:

1. **Foundation** ✅ — build system, CSR graph, SCC condensation, catalog, `BFSDFS` oracle,
   property-based tests, CI.
2. **Representative methods** ✅ — `GRAIL`, `TC`, `TreeCover`, `FELINE`, `PLL` (one+ per index
   class of the survey, plus the baselines).
3. **Benchmark harness + datasets** ✅ — `benchmarks/run_benchmark.py` compares build time,
   index size, and query time across all methods vs the BFS/DFS oracle on standard DAGs
   (`bash benchmarks/fetch_datasets.sh`).
4. **Comprehensive catalog** ✅ — the static **plain-reachability indexes of the CSUR 2025
   survey** (Table 1): 24 methods implemented. The method list is taken from a peer-reviewed
   survey, not chosen ad hoc — see [`docs/methods.md`](docs/methods.md) for the coverage map.
   (U2-hop, the one remaining static method, lands in v0.2.0.)
5. **First public release** — PyPI wheels, Zenodo DOI, GitHub Release. Docs site follows
   in v0.2.0.

Dynamic-graph methods (DAGGER, DBL, Ralf et al.) and label-constrained / path-constrained
reachability (edge-labeled graphs, the survey's Table 2) are planned later extensions.

## Benchmarks

```bash
bash benchmarks/fetch_datasets.sh                     # standard SIGMOD'08 DAGs -> benchmarks/data/
python benchmarks/run_benchmark.py benchmarks/data/*.gra --csv results.csv
```

The harness builds every catalog method on each graph and reports construction time, index size,
and average query time on random pairs, checking each method against the BFS/DFS oracle. Methods
with super-linear construction are capped to smaller graphs (shown as `skip`); a tiny all-methods
graph can be generated with `python benchmarks/make_synthetic.py`.

## Development

```bash
pip install -e ".[test]"     # build + install with test deps
pytest -v                    # Python test suite (incl. property-based tests)

# C++ unit tests (doctest):
cmake -S . -B build-cpp -DCMAKE_BUILD_TYPE=Debug
cmake --build build-cpp --target cpp_tests
./build-cpp/cpp_tests
```

CI runs the suite on Ubuntu for every push to `main`; the full Linux/macOS/Windows ×
Python 3.9–3.13 matrix runs on pull requests and manual dispatches.

## Citing

If you use PyReachability in academic work, please cite it via [`CITATION.cff`](CITATION.cff)
(GitHub renders a "Cite this repository" button). The accompanying *Software Impacts* article
reference will be added on publication.

## License

[MIT](LICENSE) © Renê Rodrigues Veloso
