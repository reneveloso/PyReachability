# PyReachability — Architecture

This document explains how PyReachability is put together and how to extend it. See
[`AI_GUIDE.md`](AI_GUIDE.md) for contributor conventions, the method inclusion policy, and
verified references.

## Layers

PyReachability is three thin layers over one C++ core:

```
┌─────────────────────────────────────────────┐
│  Python  (src/pyreachability/)                │
│  • Graph            — load from NumPy / file   │
│  • ReachabilityIndex — common interface (ABC)  │
│  • catalog          — name -> method registry  │
│  • static/          — the 24 static wrappers,  │
│                       grouped by index class   │
│  • dynamic/         — DynamicReachabilityIndex │
│                       (ABC) + the 1 dynamic    │
│                       method wrapper (Feline-PK)│
├─────────────────────────────────────────────┤
│  Cython  (_core.pyx / _core.pxd, C++ mode)     │
│  • Graph cdef class wrapping CSRGraph*          │
│  • per-method cdef cores (e.g. _BFSDFSCore,     │
│                       _FelinePKCore)            │
├─────────────────────────────────────────────┤
│  C++17 core  (src/cpp/)                         │
│  • CSRGraph          — internal representation  │
│  • scc_condense()    — Tarjan condensation       │
│                       (static methods only)     │
│  • bfs_reaches(), ... — algorithms              │
│  • dynamic/          — self-maintaining index   │
│                       cores, own condensation   │
└─────────────────────────────────────────────┘
```

`dynamic/` sits beside `static/` at every layer, not inside it: a dynamic method's
Python wrapper, Cython core, and C++ implementation are each their own module, not a
variant of the static ones. See [Dynamic methods: what differs](#dynamic-methods-what-differs)
below.

The **boundary stays thin**: Python holds the ergonomic API, Cython does the type marshalling,
and all the algorithmic work happens in C++. The build (scikit-build-core + CMake) transpiles
`_core.pyx` to C++ and compiles it together with the core `.cpp` files into a single extension
module, `pyreachability._core`.

## The graph representation: CSR

Internally every graph is a [`CSRGraph`](../src/cpp/include/reachability/csr_graph.hpp)
(Compressed Sparse Row): two arrays, `offsets` (size `n+1`) and `targets` (size `m`). The
out-neighbors of vertex `u` are `targets[offsets[u] : offsets[u+1]]`. This is cache-friendly,
compact, and gives O(1) access to a vertex's adjacency.

Construction (from an edge list) **drops self-loops** (they never change reachability) and
**deduplicates parallel edges** (each adjacency row is sorted and uniqued). Vertex ids are
0-based 32-bit integers (`vid_t = int32_t`).

`Graph.from_edges` marshals NumPy `int32` arrays into the C++ constructor (it accepts either
separate `src`/`dst` arrays or a single `(E, 2)` array). `Graph.from_file` parses a file and
delegates to `from_edges`, dispatching on `fmt`: `"edgelist"` (one `u v` per line) or `"gra"`
(the GRAIL/GREACH adjacency format); paths ending in `.gz` are decompressed transparently. The
format dispatch makes adding readers (SNAP, DIMACS `.gr`, …) straightforward. `Graph.to_edges`
exports the CSR back to `(src, dst)` arrays (the inverse of `from_edges`).

## SCC condensation: from general digraphs to DAGs

Most reachability indexes assume a **DAG**. A general directed graph is reduced to one by
**strongly-connected-component (SCC) condensation**: collapse each SCC into a single node.

> `u` reaches `v` in the original graph **iff** `SCC(u)` reaches `SCC(v)` in the condensed DAG
> (and trivially `u` reaches `v` whenever they are in the same SCC).

[`scc_condense()`](../src/cpp/include/reachability/scc.hpp) implements **Tarjan's algorithm
iteratively** (an explicit stack, so it does not overflow the call stack on deep graphs). It
returns a `Condensation`:

- `comp[v]` — the component id of each vertex `v`;
- `num_comp` — number of components;
- `dag` — the condensed DAG over component ids (deduplicated, self-loop-free);
- `topo_order` — component ids in topological order.

Tarjan assigns component ids in reverse topological order, so the topological order is simply
the descending component id sequence.

**Where condensation is required vs optional** (per the survey's classification):

- **Required** for tree-cover methods (`TreeCover`, `GRAIL`) and `FELINE` (they assume a DAG).
- **Optional optimization** for `PLL` (2-hop labeling works on general graphs directly) and
  `TC`.
- **Not used** by `BFSDFS`, which traverses the original graph directly (it is the oracle).

## The method interface and catalog

Every method implements one Python interface,
[`ReachabilityIndex`](../src/pyreachability/base.py):

```python
class ReachabilityIndex(abc.ABC):
    name: str                                   # registry key
    def build(self, graph) -> None: ...         # build the index
    def query(self, u: int, v: int) -> bool: ...      # u reaches v?
    def query_batch(self, pairs) -> np.ndarray: ...   # (M,2) int -> (M,) bool
    @property
    def index_size_bytes(self) -> int: ...      # for benchmarking
```

Methods register themselves with the [`catalog`](../src/pyreachability/catalog.py) via the
`@catalog.register` class decorator (keyed by `name`). Consumers discover and instantiate
methods by name — `catalog.methods()` lists them, `catalog.get(name)` returns the class. This
registry is what makes the library an **extensible catalog** rather than a fixed set.

### Complete vs. partial indexes

This distinction (from the reachability literature) shapes how `query` is implemented:

- **Complete** indexes (`PLL`, and the planned `TreeCover`/`TC`) answer every query by index
  lookup alone. `PLL` (2-hop) keeps per-vertex sorted landmark sets (L_out / L_in), built by
  pruned BFS in a degree-product order; a query is a sorted-list intersection — no search.
- **Partial** indexes (`GRAIL`, `FELINE`) have **no false negatives**: a lookup decides many
  queries outright, and the undecided ones fall back to a **guided/pruned DFS**. Their `query`
  therefore combines a lookup with a bounded traversal.

`GRAIL` layers three exact constant-time cuts before any DFS: a **negative cut** (interval
containment must hold in every dimension), a **positive cut** (PP — the target's post-order
number lies inside the source's DFS-subtree interval, so it is a true descendant), and a
**topological level filter** (`u` can reach `v` only if `level(u) < level(v)`). The guided DFS
runs only for pairs none of these decide, and it is itself pruned by the same cuts. With
`GRAIL(bidirectional=True)` that fallback becomes a two-sided search (forward from the source,
backward from the target over a reverse CSR) that meets in the middle — faster on hard pairs,
at the cost of an extra reverse-edge array.

`FELINE` labels each vertex with a 2D coordinate (X, Y) from two complementary topological
orders (the second built by the Kornaropoulos heuristic). Reachability implies dominance
(`X[u]≤X[v] ∧ Y[u]≤Y[v]`), so a failed test is an exact negative; it layers the same
**positive-cut** (a min-post spanning-tree interval) and **level filter** before a
dominance-pruned DFS. Its index is linear (O(|V|)), so it builds faster and far smaller than
GRAIL. `FELINE(bidirectional=True)` (FELINE-B) adds a second coordinate system on the reversed
graph for a target-side dominance cut. The shared `topological_levels()` util backs the level
filter of both GRAIL and FELINE.

## How to add a method to the catalog

Adding a method follows the same pattern every time. The implemented **`GRAIL`** is a complete
worked example (C++ core in `src/cpp/grail.{hpp,cpp}`, Cython `_GRAILCore`, Python `GRAIL`
wrapper); the steps below use it for illustration.

**1. Read the paper first.** A method only enters the library if it has a peer-reviewed
publication, and the implementation must follow the published algorithm (document any
deviation). Consult the canonical reference (and the author's reference implementation when
available).

**2. Implement the algorithm in C++** under `src/cpp/`:
- a header `src/cpp/include/reachability/grail.hpp` declaring the index type / functions;
- a translation unit `src/cpp/grail.cpp` with the implementation;
- typically a class holding the built index plus a `build(const CSRGraph&)` and a
  `query(vid_t, vid_t)`.

**3. Write C++ unit tests** in `src/cpp/tests/test_grail.cpp` (doctest) and add the test file
+ source to the `cpp_tests` target in `CMakeLists.txt`. Build and run:
```bash
cmake -S . -B build-cpp -DCMAKE_BUILD_TYPE=Debug
cmake --build build-cpp --target cpp_tests && ./build-cpp/cpp_tests
```

**4. Expose it through Cython.** Declare the C++ symbols in `_core.pxd`, add a `cdef` core
class (e.g. `_GRAILCore`) in `_core.pyx` that wraps the built index and calls into it. Build
on top of `Graph` (and `scc_condense` when the method needs a DAG).

**5. Add the C++ source to the extension** by appending `src/cpp/grail.cpp` to `CORE_SOURCES`
in `CMakeLists.txt`.

**6. Write the Python wrapper** implementing `ReachabilityIndex`, decorate it with
`@catalog.register`, give it a `name`, place it in the `static/` module matching
the method's survey index class (`tree_cover.py`, `two_hop.py`, `approximate_tc.py`,
`chain_cover.py`, `other.py`, or `baselines.py`), and add it to the re-exports in
`static/__init__.py`:
```python
@catalog.register
class GRAIL(ReachabilityIndex):
    name = "grail"
    def __init__(self, d: int = 5): ...
    def build(self, graph): ...
    def query(self, u, v): ...
    def query_batch(self, pairs): ...
    @property
    def index_size_bytes(self): ...
```
Method **variants are constructor parameters, not separate classes** (e.g. `GRAIL(d=5)`).

**7. Test for correctness against the oracle.** The pure-Python reachability oracle
(`pyreachability._oracle`) and `BFSDFS` are ground truth. Add property-based tests
(`hypothesis`) asserting `method.query(u, v) == oracle_query(reach, u, v)` over random graphs,
including cyclic ones (to exercise SCC condensation). This is the standard correctness gate
for every method.

**8. Rebuild and run the full suite:**
```bash
pip install -e . && pytest -v
```

## Dynamic methods: what differs

The recipe above is for a **static** method: `build` freezes an index that never
changes again. A **dynamic** method — seeded from a graph, then maintained under
`insert_edge` / `remove_edge` / `insert_vertex` / `remove_vertex` — follows the same
eight steps with three differences:

- It subclasses [`DynamicReachabilityIndex`](../src/pyreachability/dynamic/base.py)
  (an ABC extending `ReachabilityIndex`), not `ReachabilityIndex` directly.
- It declares `supports`, a `frozenset` naming the update operations it actually
  implements (`EDGE_INSERT`, `EDGE_DELETE`, `VERTEX_INSERT`, `VERTEX_DELETE` —
  abilities — plus flags like `EDGE_INSERT_BATCH` and preconditions like
  `ACYCLIC_INSERT_ONLY`). Capabilities are **data, not a class hierarchy**: the
  published dynamic methods do not form a clean Incremental/FullyDynamic lattice
  (U2-hop has vertex deletion but only acyclic edge insertion; DBL is
  insertion-only), so a type hierarchy would have to lie about some of them.
- `build` **seeds** the index rather than freezing it: it establishes the state the
  update operations then evolve, not a read-only artifact.

**Substrate.** The C++ for a dynamic method lives under `src/cpp/dynamic/` (e.g.
[`feline_pk.hpp`/`feline_pk.cpp`](../src/cpp/dynamic/feline_pk.cpp)), parallel to —
not inside — the static core's `src/cpp/`. Critically, it does **not** call
`scc_condense()`: a one-shot Tarjan pass would already be wrong after the first
update. A dynamic method instead maintains its own condensation incrementally
(typically a union-find over SCC representatives plus an explicitly maintained
condensation DAG), folding a component when an inserted edge closes a cycle and
splitting one when a removed edge breaks it.

**Design note: enumeration cost in Feline-PK's `remove_edge`.** Two operations in
`feline_pk.cpp` scan the whole maintained digraph instead of touching only the
affected component: `components_still_linked` (after an edge is removed, does any
other `E` edge still link the same two components? — O(|V|+|E|), since it walks
every vertex's successor list) and `split_component`'s member collection (union-find
alone cannot list a set's members — O(|V|), since it only inspects each vertex's
representative, not its edges). Two mitigations were considered and deliberately
**not** built: a per-`E_DAG`-edge multiplicity counter, which would make
`components_still_linked` O(1) (decrement and test, no scan); and an explicit
member list maintained per component, which would make the collection O(|C|)
instead of O(|V|). Neither is implemented until profiling shows the scan actually
dominates — this is the note the
`// ... (see the design note on enumeration cost)` comments in `feline_pk.cpp`
point to.

## Testing strategy

- **Oracle:** `BFSDFS` and the independent pure-Python `reachable_set` are ground truth.
- **Property-based:** `hypothesis` generates random digraphs and cross-checks each method's
  answers against the oracle for all vertex pairs.
- **C++ unit tests:** `doctest` covers core components (CSR construction, Tarjan, traversal).
- **CI:** the full suite runs on Linux/macOS/Windows across Python 3.9–3.13.
