# Contributor Guide

Guidance for contributors — human or AI assistant — working on PyReachability. For the
system design, read [`architecture.md`](architecture.md) first.

## Project shape

- **C++17 core** (`src/cpp/`) holds all algorithmic work. **Cython** (`_core.pyx` / `_core.pxd`,
  C++ mode) is a thin marshalling boundary. **Python** (`src/pyreachability/`) holds the
  ergonomic API. Keep the boundary thin: no algorithms in Python.
- Graphs are stored as **CSR**; general digraphs are reduced to DAGs via **SCC condensation**
  (Tarjan) where a method requires it.
- Methods are plug-ins implementing the `ReachabilityIndex` interface and registering in the
  `catalog`. Variants are **constructor parameters, not separate classes**.

## Method inclusion policy

A method is admitted **only if it has a peer-reviewed publication.** Before implementing a
method, **read its source paper** and follow the published algorithm; document any deviation
(engineering optimizations, etc.) in code comments. Consult the author's reference
implementation when one exists.

**FELINE — canonical reference implementation.** The library's FELINE
(`src/cpp/feline.{hpp,cpp}`) is authored by a FELINE author (Renê Veloso) and is the
**current canonical reference implementation** of the method. It was validated against the
original 2014 C++ code: it reproduces the algorithm exactly (DFS reverse-postorder X, Kahn
argmax-X Y, dominance cut, level filter, GRAIL-style min-post positive cut) and agrees with
it on 100% of a 500k-query test on cit-Patents, while being faster (CSR + iterative search).
The 2014 code is a validation reference only and is not distributed.

## Correctness gate (required for every method)

Validate each method against ground truth before considering it done:

- `BFSDFS` and the pure-Python oracle (`pyreachability._oracle`) are the ground truth.
- Add **property-based tests** (`hypothesis`) asserting `method.query(u, v)` equals the oracle
  for all vertex pairs over random digraphs — **including cyclic graphs**, to exercise SCC
  condensation.
- Add **C++ unit tests** (`doctest`) for new core components.

The step-by-step "add a method to the catalog" recipe is in
[`architecture.md`](architecture.md#how-to-add-a-method-to-the-catalog).

## Build & test

```bash
pip install -e ".[test]"     # build + install with test deps
pytest -v                    # Python suite (incl. property-based tests)

cmake -S . -B build-cpp -DCMAKE_BUILD_TYPE=Debug   # C++ unit tests
cmake --build build-cpp --target cpp_tests && ./build-cpp/cpp_tests
```

## Conventions

- **Commits:** small and frequent; Conventional Commits style (`feat:`, `fix:`, `docs:`,
  `test:`, `build:`, `ci:`).
- **TDD:** write the failing test first, then the minimal implementation.
- **Do not commit copyrighted reference PDFs** (`docs/*.pdf` is git-ignored).
- Vertex ids are 0-based `int32`. Reachability is reflexive (`query(u, u)` is `True`).

## Canonical references (verified against primary sources)

The library's methods and their publications:

| Method | Reference | DOI |
|---|---|---|
| `TC` | Warshall, *A Theorem on Boolean Matrices*, JACM 9(1):11–12, 1962 | `10.1145/321105.321107` |
| `TreeCover` | Agrawal, Borgida, Jagadish, *Efficient Management of Transitive Relationships in Large Data and Knowledge Bases*, SIGMOD 1989, 253–262 | `10.1145/67544.66950` |
| `GRAIL` | Yıldırım, Chaoji, Zaki, *GRAIL: Scalable Reachability Index for Large Graphs*, PVLDB 3(1‑2):276–284, 2010 | `10.14778/1920841.1920879` |
| `FELINE` | Veloso, Cerf, Meira Jr., Zaki, *Reachability Queries in Very Large Graphs: A Fast Refined Online Search Approach*, EDBT 2014, 511–522 | `10.5441/002/edbt.2014.46` |
| `PLL` | Yano, Akiba, Iwata, Yoshida, *Fast and Scalable Reachability Queries on Graphs by Pruned Labeling with Landmarks and Paths*, CIKM 2013, 1601–1606 | `10.1145/2505515.2505724` |

Survey for the method landscape: Zhang, Bonifati, Özsu, *Indexing Techniques for Graph
Reachability Queries*, ACM Computing Surveys, 2025 (`10.1145/3776737`).

Author reference implementations to consult when porting: GRAIL —
<https://code.google.com/archive/p/grail/>; PLL — <https://github.com/y3eadgbe/PrunedLabeling>.
