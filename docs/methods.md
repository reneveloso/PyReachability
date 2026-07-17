# Method catalog & coverage

PyReachability's method list is **not arbitrary**: it follows the peer-reviewed survey

> Chao Zhang, Angela Bonifati, M. Tamer Özsu. *Indexing Techniques for Graph Reachability
> Queries.* ACM Computing Surveys 58(6), Article 156, 2025. DOI `10.1145/3776737`.
> (Preliminary tutorial: *An Overview of Reachability Indexes on Graphs*, SIGMOD-Companion
> 2023, DOI `10.1145/3555041.3589408`.)

**Goal:** implement the survey's **plain-reachability** indexes (Table 1) under one common
interface and benchmark harness. The catalog is extensible — each method is a plug-in — so
coverage grows over releases. Edge-labeled / path-constrained (LCR) indexes (the survey's
Table 2) are a planned later extension.

Inclusion rule: a method enters the library only if it has a peer-reviewed publication; we
read its paper (and reference implementation, when one exists) before porting it.

## Plain-reachability indexes (CSUR 2025, Table 1)

Status: ✅ implemented · ⬜ planned. Each method is classified by the survey's index class.

### Baselines (survey §2.2)
- ✅ **BFS/DFS** — online traversal (correctness oracle).
- ✅ **TC** — full transitive closure (bitset). Warshall, JACM 1962.

### Tree Cover class
- ✅ **Tree Cover** — Agrawal, Borgida, Jagadish, SIGMOD 1989.
- ✅ **GRAIL** — Yıldırım, Chaoji, Zaki, PVLDB 2010 (+ PP, level filter, bidirectional).
- ✅ **Tree+SSPI** — Chen, Gupta, Kurul, VLDB 2005 (tree-cover + surrogate/surplus predecessor index).
- ✅ **Dual labeling** — Wang, He, Yang, Yu, Yu, ICDE 2006 (tree intervals + transitive link table).
- ✅ **GRIPP** — Trißl & Leser, SIGMOD 2007 (pre/postorder order-tree instances + hop technique).
- ✅ **Path-tree** — Jin, Ruan, Xiang, Wang, ACM TODS 2011 (path-tree cover + 3-tuple labeling + residual TC).
- ✅ **Ferrari** — Seufert, Anand, Bedathur, Weikum, ICDE 2013 (budgeted exact/approx intervals + guided search).
- ⬜ **DAGGER** (dynamic, I&D) — Yıldırım, Chaoji, Zaki, arXiv:1301.0977, 2013. GRAIL extended to
  dynamic graphs: k-dimensional *relaxed* interval labels (deliberately loose, so a split SCC can
  share its parent's interval), over an SCC condensation maintained incrementally by union-find.
  Two caveats verified against the paper and the reference code, both of which affect porting:
  **(a)** it is a preprint — no peer-reviewed venue found — so it does not meet the inclusion rule
  above and would enter, like Feline-PK, with its provenance declared; **(b)** the reference code
  (<https://github.com/zakimjz/dagger-index>) is **GPL v3**, incompatible with this project's MIT
  licence, so it must be implemented from the paper alone, not ported.

### 2-Hop class
- ✅ **PLL** — Yano, Akiba, Iwata, Yoshida, CIKM 2013.
- ✅ **2-Hop** — Cohen, Halperin, Kaplan, Zwick, SIAM J. Comput. 2003 (greedy densest-subgraph cover).
- ✅ **3-Hop** — Jin, Xiang, Ruan, Fuhry, SIGMOD 2009 (TC contour + greedy factorization).
- ⬜ **U2-hop** (dynamic, I&D) — Bramandia, Choi, Ng, TKDE 22(5):682–698, 2010 (earlier version:
  WWW 2008, 845–854). Maintains 2-hop labels under updates; its primitives are node-centric
  (node deletion is the paper's central algorithm). Note the false friend: "incremental
  maintenance" in the title means *without rebuilding*, **not** insertion-only — the survey marks
  it I&D. It condenses SCCs **once** on input (Tarjan, one scan) and assumes insertions never
  create a cycle, so it never maintains the condensation. The survey notes it does not scale to
  large graphs.
- ✅ **Path-hop** — Cai & Poon, CIKM 2010 (residual TC + greedy path-hop set cover; trees as highways).
- ✅ **TFL** (Topological Folding Labeling) — Cheng, Huang, Wu, Fu, SIGMOD 2013.
- ✅ **DL** (Distribution Labeling) — Jin & Wang, PVLDB 2013 (Algorithm 2; survey-proven equivalent to PLL).
- ✅ **HL** (Hierarchical Labeling) — Jin & Wang, PVLDB 2013 (recursive reachability backbone).
- ✅ **TOL** (Total Order Labeling) — Zhu, Lin, Wang, Xiao, SIGMOD 2014 (contribution-score order).
- ⬜ **DBL** (dynamic, **I — insertion-only**) — Lyu, Li, He, Gong, DASFAA 2021, 761–777
  (`10.1007/978-3-030-73197-7_52`; full version arXiv:2101.09441). The only insertion-only row of
  Table 1: deletions are future work by the authors' own statement. Two complementary partial
  indexes — Dynamic Landmark (DL, top-k degree landmarks; decides True) and Bidirectional Leaf
  (BL, a hash set over leaf nodes in bit vectors; decides False) — with a pruned BFS in between.
  Explicitly **DAG-free**: its stated contribution is avoiding SCC maintenance, which it argues is
  prohibitively expensive. (The survey describes DBL as adding *BFL*; the paper never mentions BFL
  or Bloom filters — the component is **BL**. Follow the paper.)
- ✅ **O'Reach** — Hanauer, Schulz, Trummer, ACM JEA 2022 (constant-time observations + guided fallback).
- ⬜ **HOPI** (dynamic 2-hop, I&D) — Schenkel, Theobald, Weikum, *Efficient creation and incremental
  maintenance of the HOPI index for complex XML document collections*, ICDE 2005, 360–371
  (`10.1109/ICDE.2005.57`). 2-hop labels over a general graph (no DAG assumption, so no SCC
  maintenance). The survey notes it does not scale to large graphs.
  <a id="fn-ralf"></a>**Naming:** CSUR 2025 lists this row as *"Ralf et al. [78]"* — the survey
  mistakes Schenkel's **first** name for his surname. We use the correct name; the footnote exists
  so this entry can still be matched to its Table 1 row.

### Approximate TC class
- ✅ **IP** (Independent Permutation) — Wei, Yu, Lu, Jin, PVLDB 2014 (k-min-wise permutation labels + guided DFS).
- ✅ **BFL** (Bloom Filter Labeling) — Su, Zhu, Wei, Yu, TKDE 2017.

### Chain Cover class
- ✅ **Chain Cover** — Jagadish, ACM TODS 1990 (greedy chain decomposition).
- ✅ **Optimal Chain Cover** — Chen & Chen, ICDE 2008 (minimum chains via max bipartite matching / Dilworth).

### Other
- ✅ **FELINE** — Veloso, Cerf, Meira Jr., Zaki, EDBT 2014 (canonical reference impl).
- ✅ **PReaCH** — Merz & Sanders, ESA 2014 (ported from paper; oracle-verified).

## Status summary

Implemented: 24 methods — **all 22 static plain-reachability techniques of the
survey's Table 1** (26 rows total), plus the two baselines the survey discusses
(online BFS/DFS and materialized TC). The four Table-1 rows not implemented are
exactly those whose contribution is dynamic index maintenance: DAGGER, U2-hop, DBL,
and HOPI (listed by the survey as "Ralf et al." — [see the naming note](#fn-ralf)).

Note on the survey's *Dynamic* column: Table 1 also flags Path-tree, TOL, IP, Chain
Cover, and Optimal Chain Cover as dynamic (I&D). Those are static indexes with
additional dynamic-maintenance support; PyReachability implements their static form.
"Deferred" above means *dynamic-only*: methods whose novelty is the maintenance
procedure itself.

Deferred to a future extension alongside the dynamic methods: the path-constrained
(label-constrained) indexes of the survey's Table 2. Exact citations are taken from
CSUR 2025 Table 1 and confirmed against the primary source at implementation time.

### Where we diverge from the survey

Confirming the four dynamic rows against their primary sources turned up two errors in
CSUR 2025. We follow the primary source and record the divergence here, so that this
catalog stays checkable against Table 1:

- **"Ralf et al." is Schenkel et al.** — the survey uses the first author's given name as
  a surname ([above](#fn-ralf)).
- **DBL uses BL, not BFL** — the survey states DBL "also adds BFL"; the paper (including
  the full arXiv version) never mentions BFL or Bloom filters. The component is the
  Bidirectional Leaf label, which is Bloom-*like* but is not Su et al.'s BFL.

One further caveat, not an error but a reading trap: the *Dynamic* column is defined purely
over **edge** insertions/deletions (I / I&D). It says nothing about vertex operations, which
Feline-PK, U2-hop, and DBL all support. Do not read a row's I&D as describing its full update
API.

## Beyond the survey: dynamic methods from other sources

The survey's Table 1 is the catalog's spine, but it is not a ceiling. Methods
below come from elsewhere; each declares its provenance, and none is counted in
the Table 1 coverage claim above.

- ✅ **Feline-PK** (dynamic, I&D + vertex ops) — the incremental Feline of the
  author's PhD thesis (Algs. 6–10, §4.1): R. R. Veloso, *Consultas de
  alcançabilidade em grafos muito grandes*. It extends FELINE (Veloso, Cerf,
  Meira Jr., Zaki, EDBT 2014) by maintaining the X/Y dominance drawing under
  updates instead of rebuilding it, and by maintaining the SCC condensation
  itself — folding a component when an insertion closes a cycle, splitting one
  when a removal breaks it.
  **Provenance note:** a thesis is not a peer-reviewed publication in the sense
  of the inclusion rule above, and this is the library author's own method. It is
  listed here, separately from the survey's techniques, so that neither the rule
  nor the Table 1 coverage claim is quietly stretched to cover it.
  **Fidelity note:** the implementation deliberately departs from the thesis's
  Alg. 10 in two coupled ways, because the text's reorder is unsound as written —
  see [`fidelity.md`](fidelity.md). Being faithful to that text would be a bug.
  **Known limits, both inherited from the reference implementation:**
  *(a)* **batch insertion is future work** — `insert_edges` works, but it is the
  ABC's default loop over `insert_edge`, which is why `FelinePK.supports` does not
  declare `edge_insert_batch`; *(b)* **`remove_edge` scans the vertex set**, so it
  is linear in |V| on both of its branches, while `insert_edge` is local. The
  trade-off and the two known fixes are in
  [`architecture.md`](architecture.md#dynamic-methods-what-differs); neither is
  implemented until profiling says it matters.
